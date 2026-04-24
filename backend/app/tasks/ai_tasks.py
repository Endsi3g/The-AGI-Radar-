"""Celery tasks for AI processing. Full implementation in Phase 3."""
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.ai_tasks.score_leads_batch")
def score_leads_batch(lead_ids: list[str]) -> dict:
    """Score a batch of leads using Ollama/Mistral."""
    return {"lead_ids": lead_ids, "status": "not_implemented"}


@celery_app.task(name="app.tasks.ai_tasks.generate_campaign_messages")
def generate_campaign_messages(campaign_id: str, lead_ids: list[str]) -> dict:
    """Generate personalized messages for a campaign."""
    return {"campaign_id": campaign_id, "status": "not_implemented"}
