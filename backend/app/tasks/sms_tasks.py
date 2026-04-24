"""Celery tasks for SMS sending. Full implementation in Phase 4."""
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.sms_tasks.send_sms_message")
def send_sms_message(message_id: str) -> dict:
    """Send an approved SMS via Twilio."""
    return {"message_id": message_id, "status": "not_implemented"}
