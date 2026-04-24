"""Celery tasks for email sending and Gmail polling. Full implementation in Phase 4-5."""
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.email_tasks.send_email_message")
def send_email_message(message_id: str) -> dict:
    """Send an approved email message via Gmail API."""
    return {"message_id": message_id, "status": "not_implemented"}


@celery_app.task(name="app.tasks.email_tasks.poll_gmail_inbox")
def poll_gmail_inbox() -> dict:
    """Poll Gmail inbox for replies to sent messages."""
    return {"status": "not_implemented"}
