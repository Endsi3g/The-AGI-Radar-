"""Celery tasks for scraping. Actual scraper implementations in Phase 2."""
from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.scrape_tasks.run_scrape_job", max_retries=2)
def run_scrape_job(self, job_id: str) -> dict:
    """Launch a scrape job by job_id. Delegates to each source scraper."""
    # Placeholder — full implementation in Phase 2
    return {"job_id": job_id, "status": "not_implemented"}
