from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "hgi_radar",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.scrape_tasks",
        "app.tasks.ai_tasks",
        "app.tasks.email_tasks",
        "app.tasks.sms_tasks",
        "app.tasks.reminder_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Toronto",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24h
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Poll Gmail inbox every 15 minutes for replies
    "poll-gmail-inbox": {
        "task": "app.tasks.email_tasks.poll_gmail_inbox",
        "schedule": crontab(minute="*/15"),
    },
    # Check follow-up reminders every hour
    "check-followup-reminders": {
        "task": "app.tasks.reminder_tasks.check_followup_reminders",
        "schedule": crontab(minute=0),  # Every hour on the hour
    },
}
