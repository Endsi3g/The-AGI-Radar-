"""Celery tasks for AI batch processing."""
from __future__ import annotations

import asyncio

from app.tasks.celery_app import celery_app
from app.core.logging import logger


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.tasks.ai_tasks.score_leads_batch", max_retries=1)
def score_leads_batch(self, lead_ids: list[str], use_ai: bool = True) -> dict:
    """Score a batch of leads. Publishes progress to Redis."""
    return _run_async(_score_leads_async(lead_ids, use_ai))


@celery_app.task(bind=True, name="app.tasks.ai_tasks.generate_messages_batch", max_retries=1)
def generate_messages_batch(self, lead_ids: list[str], channel: str, user_id: str) -> dict:
    """Generate AI messages for a batch of leads."""
    return _run_async(_generate_messages_async(lead_ids, channel, user_id))


async def _score_leads_async(lead_ids: list[str], use_ai: bool) -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from app.models.lead import Lead
    from app.services.scoring_service import apply_score
    from app.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    done = 0
    failed = 0

    async with AsyncSessionLocal() as db:
        for lead_id in lead_ids:
            try:
                from uuid import UUID
                result = await db.execute(select(Lead).where(Lead.id == UUID(lead_id)))
                lead = result.scalar_one_or_none()
                if not lead:
                    continue
                await apply_score(lead, db, use_ai=use_ai)
                done += 1
                logger.debug("lead_scored", lead_id=lead_id, score=lead.ai_score)
            except Exception as exc:
                logger.error("lead_score_error", lead_id=lead_id, error=str(exc))
                failed += 1

    await engine.dispose()
    return {"scored": done, "failed": failed, "total": len(lead_ids)}


async def _generate_messages_async(lead_ids: list[str], channel: str, user_id: str) -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    from uuid import UUID
    from app.models.lead import Lead
    from app.models.message import Message
    from app.services import ai_service
    from app.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    done = 0
    failed = 0

    async with AsyncSessionLocal() as db:
        for lead_id in lead_ids:
            try:
                result = await db.execute(select(Lead).where(Lead.id == UUID(lead_id)))
                lead = result.scalar_one_or_none()
                if not lead:
                    continue

                lead_dict = {
                    "business_name": lead.business_name,
                    "industry": lead.industry,
                    "city": lead.city,
                    "google_rating": float(lead.google_rating) if lead.google_rating else None,
                    "google_reviews": lead.google_reviews,
                    "website": lead.website,
                    "email": lead.email,
                    "owner_name": lead.owner_name,
                    "instagram_handle": lead.instagram_handle,
                    "description": lead.description,
                    "detected_language": lead.detected_language,
                }

                subject = None
                body = ""

                if channel == "email":
                    res = await ai_service.generate_email(lead_dict)
                    subject = res.subject
                    body = res.body
                elif channel == "sms":
                    res = await ai_service.generate_sms(lead_dict)
                    body = res.body
                elif channel == "voip_script":
                    res = await ai_service.generate_call_script(lead_dict)
                    body = (
                        f"=== INTRO ===\n{res.intro}\n\n"
                        f"=== PROPOSITION DE VALEUR ===\n{res.value_prop}\n\n"
                        f"=== OBJECTIONS ===\n"
                        + "\n".join(f"{i+1}. {o}" for i, o in enumerate(res.objection_handlers))
                        + f"\n\n=== CLOSE ===\n{res.close}"
                    )
                    subject = "Script d'appel"

                msg = Message(
                    lead_id=lead.id,
                    channel=channel,
                    subject=subject,
                    body=body,
                    ai_generated=True,
                    status="pending_approval",
                    created_by=UUID(user_id),
                )
                db.add(msg)
                await db.commit()
                done += 1
                logger.debug("message_generated", lead_id=lead_id, channel=channel)

            except Exception as exc:
                logger.error("message_generation_error", lead_id=lead_id, channel=channel, error=str(exc))
                failed += 1

    await engine.dispose()
    return {"generated": done, "failed": failed, "total": len(lead_ids), "channel": channel}
