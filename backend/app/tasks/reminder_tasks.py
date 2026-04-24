"""Celery tasks for follow-up reminders. Full implementation in Phase 4."""
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.reminder_tasks.check_followup_reminders")
def check_followup_reminders() -> dict:
    """Check leads with next_followup_at <= now and create calendar reminders."""
    return {"status": "not_implemented"}
