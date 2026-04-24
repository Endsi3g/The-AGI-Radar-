"""Celery Beat task — check follow-up reminders every hour."""
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


@celery_app.task(name="app.tasks.reminder_tasks.check_followup_reminders")
def check_followup_reminders() -> dict:
    """Find leads with next_followup_at <= now and create reminder interactions."""
    return _run_async(_check_reminders_async())


async def _check_reminders_async() -> dict:
    from datetime import datetime, timezone
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from app.models.lead import Lead
    from app.models.interaction import Interaction
    from app.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    triggered = 0

    async with AsyncSessionLocal() as db:
        # Find leads with overdue follow-ups that haven't been contacted recently
        result = await db.execute(
            select(Lead).where(
                Lead.next_followup_at.isnot(None),
                Lead.next_followup_at <= now,
                Lead.status.notin_(["fermé", "perdu"]),
            )
        )
        leads = result.scalars().all()

        for lead in leads:
            try:
                # Check if a reminder was already created today
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                existing_result = await db.execute(
                    select(Interaction).where(
                        Interaction.lead_id == lead.id,
                        Interaction.type == "followup_reminder",
                        Interaction.occurred_at >= today_start,
                    )
                )
                if existing_result.scalar_one_or_none():
                    continue

                interaction = Interaction(
                    lead_id=lead.id,
                    type="followup_reminder",
                    notes=f"Relance prévue — {lead.business_name} ({lead.city}). Statut: {lead.status}",
                )
                db.add(interaction)

                # Clear the next_followup_at so it doesn't repeat
                lead.next_followup_at = None
                triggered += 1

            except Exception as exc:
                logger.error("reminder_lead_error", lead_id=str(lead.id), error=str(exc))

        await db.commit()

    await engine.dispose()
    logger.info("reminders_checked", triggered=triggered)
    return {"triggered": triggered, "checked_at": now.isoformat()}
