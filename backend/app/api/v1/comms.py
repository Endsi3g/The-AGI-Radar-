"""Communications router — Twilio SMS/Voice webhooks + call initiation."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.lead import Lead
from app.models.message import Message
from app.models.interaction import Interaction
from app.models.user import User
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import logger

router = APIRouter(prefix="/comms", tags=["comms"])


# ──────────────────── Twilio SMS webhook (inbound)

@router.post("/sms/webhook", status_code=status.HTTP_200_OK)
async def sms_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Receive inbound SMS from Twilio. Match to lead by phone number."""
    form = await request.form()
    from app.services.twilio_service import parse_inbound_sms
    data = parse_inbound_sms(dict(form))

    from_number_digits = "".join(d for d in data["from_number"] if d.isdigit())
    if from_number_digits.startswith("1") and len(from_number_digits) == 11:
        from_number_digits = from_number_digits[1:]

    # Find lead by phone
    result = await db.execute(select(Lead).where(Lead.phone.isnot(None)))
    leads = result.scalars().all()
    matched_lead = None
    for lead in leads:
        lead_digits = "".join(d for d in (lead.phone or "") if d.isdigit())
        if lead_digits.endswith(from_number_digits[-10:]):
            matched_lead = lead
            break

    if matched_lead:
        # Find most recent outbound SMS to this lead
        sent_result = await db.execute(
            select(Message).where(
                Message.lead_id == matched_lead.id,
                Message.channel == "sms",
                Message.direction == "outbound",
                Message.status == "sent",
            ).order_by(Message.sent_at.desc())
        )
        sent_msg = sent_result.scalars().first()

        inbound_msg = Message(
            lead_id=matched_lead.id,
            channel="sms",
            direction="inbound",
            status="draft",
            body=data["body"],
            ai_generated=False,
            reply_to_message_id=sent_msg.id if sent_msg else None,
        )
        db.add(inbound_msg)

        interaction = Interaction(
            lead_id=matched_lead.id,
            type="sms_received",
            notes=f"SMS reçu : {data['body'][:200]}",
        )
        db.add(interaction)
        await db.commit()
        logger.info("inbound_sms_stored", lead_id=str(matched_lead.id))
    else:
        logger.warning("inbound_sms_no_lead_match", from_number=data["from_number"])

    # Return empty TwiML response (no auto-reply)
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


# ──────────────────── Twilio Voice webhooks

@router.post("/voice/webhook", status_code=status.HTTP_200_OK)
async def voice_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Handle Twilio voice call status callbacks."""
    form = await request.form()
    from app.services.twilio_service import parse_call_status
    data = parse_call_status(dict(form))

    logger.info("voice_webhook", call_sid=data["call_sid"], status=data["call_status"])

    # Find message by twilio_sid
    result = await db.execute(
        select(Message).where(Message.twilio_sid == data["call_sid"])
    )
    msg = result.scalar_one_or_none()

    if msg and data["call_status"] in ("completed", "failed", "no-answer", "busy"):
        interaction = Interaction(
            lead_id=msg.lead_id,
            type="call_made",
            notes=(
                f"Appel {data['call_status']} — durée: {data.get('duration', '?')}s"
                + (f" — enregistrement disponible" if data.get("recording_url") else "")
            ),
            metadata_={
                "call_sid": data["call_sid"],
                "call_status": data["call_status"],
                "duration": data.get("duration"),
                "recording_url": data.get("recording_url"),
            },
        )
        db.add(interaction)
        await db.commit()

    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )


@router.post("/voice/recording-callback")
async def recording_callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Store recording URL when Twilio finishes processing."""
    form = await request.form()
    from app.services.twilio_service import parse_recording_callback
    data = parse_recording_callback(dict(form))
    logger.info("recording_ready", recording_sid=data["recording_sid"])
    return {"status": "ok"}


# ──────────────────── Outbound call initiation

class InitiateCallRequest(BaseModel):
    lead_id: UUID
    script_message_id: UUID | None = None


@router.post("/voice/call", status_code=status.HTTP_201_CREATED)
async def initiate_call(
    body: InitiateCallRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Initiate a Twilio VoIP call to a lead."""
    result = await db.execute(select(Lead).where(Lead.id == body.lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise NotFoundError("Lead")
    if not lead.phone:
        raise BadRequestError("Lead has no phone number")

    phone = lead.phone
    if not phone.startswith("+"):
        digits = "".join(d for d in phone if d.isdigit())
        phone = f"+1{digits}" if len(digits) == 10 else f"+{digits}"

    from app.config import settings
    from app.services.twilio_service import initiate_call as twilio_initiate_call

    # TwiML URL — simple dial with recording
    base_url = settings.google_redirect_uri.rsplit("/google", 1)[0]
    twiml_url = f"{base_url}/comms/voice/twiml"

    call_data = await twilio_initiate_call(to_number=phone, script_url=twiml_url)

    # Store as voip message
    msg = Message(
        lead_id=lead.id,
        channel="voip_script",
        direction="outbound",
        status="sent",
        body=f"Appel initié vers {phone}",
        ai_generated=False,
        twilio_sid=call_data["call_sid"],
        sent_at=datetime.now(timezone.utc),
        created_by=current_user.id,
    )
    db.add(msg)

    interaction = Interaction(
        lead_id=lead.id,
        user_id=current_user.id,
        message_id=msg.id,
        type="call_initiated",
        notes=f"Appel VoIP initié vers {phone}",
    )
    db.add(interaction)
    lead.last_contacted_at = datetime.now(timezone.utc)
    await db.commit()

    return {"call_sid": call_data["call_sid"], "status": call_data["status"]}


@router.get("/voice/twiml")
async def twiml_response():
    """Simple TwiML for outbound calls — just records the call."""
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="fr-CA">Bonjour, ceci est un appel de HGI Digital.</Say>
    <Record maxLength="300" transcribe="false" playBeep="false"/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")
