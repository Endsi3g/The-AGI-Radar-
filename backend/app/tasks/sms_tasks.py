"""Celery tasks for Twilio SMS sending."""
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


@celery_app.task(name="app.tasks.sms_tasks.send_sms_message", max_retries=3, default_retry_delay=60)
def send_sms_message(message_id: str) -> dict:
    """Send an approved SMS via Twilio."""
    return _run_async(_send_sms_async(message_id))


async def _send_sms_async(message_id: str) -> dict:
    from datetime import datetime, timezone
    from uuid import UUID
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from app.models.message import Message
    from app.models.lead import Lead
    from app.models.interaction import Interaction
    from app.services.twilio_service import send_sms
    from app.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Message).where(Message.id == UUID(message_id)))
        msg = result.scalar_one_or_none()
        if not msg:
            return {"error": "message not found"}

        if msg.status != "approved":
            return {"skipped": True}

        lead_result = await db.execute(select(Lead).where(Lead.id == msg.lead_id))
        lead = lead_result.scalar_one_or_none()
        if not lead or not lead.phone:
            msg.status = "failed"
            await db.commit()
            return {"error": "lead has no phone"}

        # Ensure E.164 format (+1XXXXXXXXXX for Canada)
        phone = lead.phone
        if not phone.startswith("+"):
            digits = "".join(d for d in phone if d.isdigit())
            if len(digits) == 10:
                phone = f"+1{digits}"
            elif len(digits) == 11 and digits.startswith("1"):
                phone = f"+{digits}"

        try:
            sent = await send_sms(to_number=phone, body=msg.body)
            msg.status = "sent"
            msg.sent_at = datetime.now(timezone.utc)
            msg.twilio_sid = sent["twilio_sid"]

            interaction = Interaction(
                lead_id=msg.lead_id,
                user_id=msg.approved_by or msg.created_by,
                message_id=msg.id,
                type="sms_sent",
                notes=f"SMS envoyé au {phone} via Twilio",
            )
            db.add(interaction)

            lead.last_contacted_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info("sms_sent_ok", message_id=message_id, to=phone)
            return {"sent": True, "twilio_sid": sent["twilio_sid"]}

        except Exception as exc:
            msg.status = "failed"
            await db.commit()
            logger.error("sms_send_failed", error=str(exc), message_id=message_id)
            raise

    await engine.dispose()
