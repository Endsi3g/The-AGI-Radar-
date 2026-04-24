"""Celery tasks for email sending and Gmail inbox polling."""
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


@celery_app.task(name="app.tasks.email_tasks.send_email_message", max_retries=3, default_retry_delay=60)
def send_email_message(message_id: str) -> dict:
    """Send an approved email message via Gmail API."""
    return _run_async(_send_email_async(message_id))


@celery_app.task(name="app.tasks.email_tasks.poll_gmail_inbox")
def poll_gmail_inbox() -> dict:
    """Poll Gmail inboxes of all connected users for unread replies."""
    return _run_async(_poll_gmail_async())


async def _send_email_async(message_id: str) -> dict:
    from datetime import datetime, timezone
    from uuid import UUID
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from app.models.message import Message
    from app.models.lead import Lead
    from app.models.user import User
    from app.models.interaction import Interaction
    from app.services.gmail_service import send_email, refresh_token_if_needed
    from app.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Message).where(Message.id == UUID(message_id)))
        msg = result.scalar_one_or_none()
        if not msg:
            logger.error("email_task_message_not_found", message_id=message_id)
            return {"error": "message not found"}

        if msg.status != "approved":
            logger.warning("email_task_wrong_status", status=msg.status)
            return {"skipped": True}

        # Get lead email
        lead_result = await db.execute(select(Lead).where(Lead.id == msg.lead_id))
        lead = lead_result.scalar_one_or_none()
        if not lead or not lead.email:
            msg.status = "failed"
            await db.commit()
            return {"error": "lead has no email"}

        # Get sender user (approver or creator)
        sender_id = msg.approved_by or msg.created_by
        if not sender_id:
            msg.status = "failed"
            await db.commit()
            return {"error": "no sender user"}

        user_result = await db.execute(select(User).where(User.id == sender_id))
        user = user_result.scalar_one_or_none()
        if not user or not user.google_access_token:
            msg.status = "failed"
            await db.commit()
            logger.error("email_task_no_gmail_token", user_id=str(sender_id))
            return {"error": "user has no Gmail token"}

        user = await refresh_token_if_needed(user, db)

        try:
            sent = await send_email(
                user=user,
                to_email=lead.email,
                subject=msg.subject or f"Message de HGI Digital",
                body=msg.body,
                thread_id=msg.gmail_thread_id,
            )
            msg.status = "sent"
            msg.sent_at = datetime.now(timezone.utc)
            msg.gmail_message_id = sent["gmail_message_id"]
            msg.gmail_thread_id = sent.get("gmail_thread_id") or msg.gmail_thread_id

            # Log interaction
            interaction = Interaction(
                lead_id=msg.lead_id,
                user_id=sender_id,
                message_id=msg.id,
                type="email_sent",
                notes=f"Email envoyé à {lead.email} via Gmail",
            )
            db.add(interaction)

            # Update lead last_contacted_at
            lead.last_contacted_at = datetime.now(timezone.utc)

            await db.commit()
            logger.info("email_sent_ok", message_id=message_id, to=lead.email)
            return {"sent": True, "gmail_message_id": sent["gmail_message_id"]}

        except Exception as exc:
            msg.status = "failed"
            await db.commit()
            logger.error("email_send_failed", error=str(exc), message_id=message_id)
            raise

    await engine.dispose()


async def _poll_gmail_async() -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from app.models.user import User
    from app.models.message import Message
    from app.models.interaction import Interaction
    from app.services.gmail_service import poll_inbox, mark_as_read, refresh_token_if_needed
    from app.services.ai_service import suggest_reply
    from app.config import settings

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    total_processed = 0

    async with AsyncSessionLocal() as db:
        # Get all users with Gmail tokens
        result = await db.execute(select(User).where(User.google_access_token.isnot(None)))
        users = result.scalars().all()

        for user in users:
            try:
                user = await refresh_token_if_needed(user, db)
                inbox_messages = await poll_inbox(user)

                for inbound in inbox_messages:
                    thread_id = inbound["gmail_thread_id"]
                    if not thread_id:
                        continue

                    # Find the outbound message with this thread_id
                    sent_result = await db.execute(
                        select(Message).where(
                            Message.gmail_thread_id == thread_id,
                            Message.direction == "outbound",
                        )
                    )
                    sent_msg = sent_result.scalar_one_or_none()
                    if not sent_msg:
                        continue

                    # Check if we already stored this inbound message
                    existing = await db.execute(
                        select(Message).where(
                            Message.gmail_message_id == inbound["gmail_message_id"],
                            Message.direction == "inbound",
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue

                    # Generate AI reply suggestion
                    ai_suggestion = None
                    try:
                        lead_result = await db.execute(
                            select(Message.lead_id).where(Message.id == sent_msg.id)
                        )
                        from app.models.lead import Lead
                        from sqlalchemy import select as _select
                        lead_q = await db.execute(
                            _select(Lead).where(Lead.id == sent_msg.lead_id)
                        )
                        lead = lead_q.scalar_one_or_none()
                        if lead:
                            reply = await suggest_reply(
                                inbound["body"],
                                {
                                    "business_name": lead.business_name,
                                    "detected_language": lead.detected_language,
                                },
                            )
                            ai_suggestion = f"Sujet: {reply.subject}\n\n{reply.body}"
                    except Exception:
                        pass

                    # Store inbound message
                    inbound_msg = Message(
                        lead_id=sent_msg.lead_id,
                        channel="email",
                        direction="inbound",
                        status="draft",
                        subject=inbound["subject"],
                        body=inbound["body"],
                        ai_generated=False,
                        gmail_message_id=inbound["gmail_message_id"],
                        gmail_thread_id=thread_id,
                        reply_to_message_id=sent_msg.id,
                        ai_reply_suggestion=ai_suggestion,
                        created_by=user.id,
                    )
                    db.add(inbound_msg)

                    # Log interaction
                    interaction = Interaction(
                        lead_id=sent_msg.lead_id,
                        user_id=user.id,
                        type="email_received",
                        notes=f"Réponse reçue de {inbound['from_email']}",
                    )
                    db.add(interaction)

                    await mark_as_read(user, inbound["gmail_message_id"])
                    total_processed += 1

                await db.commit()

            except Exception as exc:
                logger.error("gmail_poll_user_failed", user_id=str(user.id), error=str(exc))

    await engine.dispose()
    logger.info("gmail_poll_done", processed=total_processed)
    return {"processed": total_processed}
