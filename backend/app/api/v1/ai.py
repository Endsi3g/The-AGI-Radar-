"""AI generation routes — email, SMS, call script, lead scoring."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.lead import Lead
from app.models.message import Message
from app.models.user import User
from app.core.exceptions import NotFoundError, BadRequestError
from app.services import ai_service
from app.services.scoring_service import apply_score
from app.core.logging import logger

router = APIRouter(prefix="/ai", tags=["ai"])


# ──────────────────────────────────────────── request / response schemas

class GenerateEmailRequest(BaseModel):
    lead_id: UUID
    save_as_draft: bool = True


class GenerateSMSRequest(BaseModel):
    lead_id: UUID
    save_as_draft: bool = True


class GenerateScriptRequest(BaseModel):
    lead_id: UUID


class ScoreLeadRequest(BaseModel):
    use_ai: bool = True


class BatchGenerateRequest(BaseModel):
    lead_ids: list[UUID]
    channel: str  # email | sms | voip_script


class BatchScoreRequest(BaseModel):
    lead_ids: list[UUID]
    use_ai: bool = True


class EmailResponse(BaseModel):
    subject: str
    body: str
    language: str
    message_id: UUID | None = None


class SMSResponse(BaseModel):
    body: str
    language: str
    message_id: UUID | None = None


class ScriptResponse(BaseModel):
    intro: str
    value_prop: str
    objection_handlers: list[str]
    close: str
    language: str
    message_id: UUID | None = None


class ScoreResponse(BaseModel):
    lead_id: UUID
    score: int
    rationale: str


# ──────────────────────────────────────────── helpers

def _lead_to_dict(lead: Lead) -> dict:
    return {
        "business_name": lead.business_name,
        "industry": lead.industry,
        "city": lead.city,
        "google_rating": float(lead.google_rating) if lead.google_rating else None,
        "google_reviews": lead.google_reviews,
        "website": lead.website,
        "email": lead.email,
        "owner_name": lead.owner_name,
        "instagram_handle": lead.instagram_handle,
        "facebook_url": lead.facebook_url,
        "description": lead.description,
        "detected_language": lead.detected_language,
    }


async def _get_lead(lead_id: UUID, db: AsyncSession) -> Lead:
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead")
    return lead


async def _save_message(
    db: AsyncSession,
    lead_id: UUID,
    channel: str,
    subject: str | None,
    body: str,
    current_user: User,
) -> Message:
    msg = Message(
        lead_id=lead_id,
        channel=channel,
        subject=subject,
        body=body,
        ai_generated=True,
        status="pending_approval",
        created_by=current_user.id,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


# ──────────────────────────────────────────── endpoints

@router.post("/generate-email", response_model=EmailResponse)
async def generate_email(
    body: GenerateEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    lead = await _get_lead(body.lead_id, db)
    result = await ai_service.generate_email(_lead_to_dict(lead))

    msg_id = None
    if body.save_as_draft:
        msg = await _save_message(db, lead.id, "email", result.subject, result.body, current_user)
        msg_id = msg.id

    return EmailResponse(subject=result.subject, body=result.body, language=result.language, message_id=msg_id)


@router.post("/generate-sms", response_model=SMSResponse)
async def generate_sms(
    body: GenerateSMSRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    lead = await _get_lead(body.lead_id, db)
    result = await ai_service.generate_sms(_lead_to_dict(lead))

    msg_id = None
    if body.save_as_draft:
        msg = await _save_message(db, lead.id, "sms", None, result.body, current_user)
        msg_id = msg.id

    return SMSResponse(body=result.body, language=result.language, message_id=msg_id)


@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script(
    body: GenerateScriptRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    lead = await _get_lead(body.lead_id, db)
    result = await ai_service.generate_call_script(_lead_to_dict(lead))

    # Store script as a voip_script message
    full_script = (
        f"=== INTRO ===\n{result.intro}\n\n"
        f"=== PROPOSITION DE VALEUR ===\n{result.value_prop}\n\n"
        f"=== OBJECTIONS ===\n"
        + "\n".join(f"{i+1}. {o}" for i, o in enumerate(result.objection_handlers))
        + f"\n\n=== CLOSE ===\n{result.close}"
    )
    msg = await _save_message(db, lead.id, "voip_script", "Script d'appel", full_script, current_user)

    return ScriptResponse(
        intro=result.intro,
        value_prop=result.value_prop,
        objection_handlers=result.objection_handlers,
        close=result.close,
        language=result.language,
        message_id=msg.id,
    )


@router.post("/leads/{lead_id}/score", response_model=ScoreResponse)
async def score_lead_endpoint(
    lead_id: UUID,
    body: ScoreLeadRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    lead = await _get_lead(lead_id, db)
    lead = await apply_score(lead, db, use_ai=body.use_ai)
    return ScoreResponse(lead_id=lead.id, score=lead.ai_score, rationale=lead.score_rationale or "")


@router.post("/batch-score", status_code=status.HTTP_202_ACCEPTED)
async def batch_score(
    body: BatchScoreRequest,
    _: Annotated[User, Depends(get_current_user)],
):
    """Enqueue Celery batch scoring task."""
    from app.tasks.ai_tasks import score_leads_batch
    task = score_leads_batch.delay([str(lid) for lid in body.lead_ids], body.use_ai)
    return {"task_id": task.id, "lead_count": len(body.lead_ids)}


@router.post("/batch-generate", status_code=status.HTTP_202_ACCEPTED)
async def batch_generate(
    body: BatchGenerateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Enqueue Celery batch message generation task."""
    if body.channel not in ("email", "sms", "voip_script"):
        raise BadRequestError("channel must be email, sms or voip_script")
    from app.tasks.ai_tasks import generate_messages_batch
    task = generate_messages_batch.delay(
        [str(lid) for lid in body.lead_ids],
        body.channel,
        str(current_user.id),
    )
    return {"task_id": task.id, "lead_count": len(body.lead_ids), "channel": body.channel}
