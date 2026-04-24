"""Celery tasks for scraping with Redis pub/sub progress reporting."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import redis as sync_redis

from app.tasks.celery_app import celery_app
from app.config import settings


def _publish(redis_client: sync_redis.Redis, job_id: str, event: dict) -> None:
    """Push a progress event to the job's Redis channel."""
    redis_client.publish(f"job:{job_id}", json.dumps(event))


def _run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.tasks.scrape_tasks.run_scrape_job", max_retries=2)
def run_scrape_job(self, job_id: str) -> dict:
    """Orchestrate scraping for all requested sources in a ScrapeJob."""
    return _run_async(_run_scrape_job_async(job_id))


async def _run_scrape_job_async(job_id: str) -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    from app.models.scrape_job import ScrapeJob
    from app.scrapers.google_maps import GoogleMapsScraper
    from app.scrapers.pages_jaunes import PagesJaunesScraper
    from app.scrapers.yelp import YelpScraper
    from app.scrapers.linkedin import LinkedInScraper
    from app.scrapers.instagram import InstagramScraper
    from app.scrapers.facebook import FacebookScraper
    from app.scrapers.base import RawLead
    from app.services.dedup_service import DedupService
    from app.schemas.lead import LeadCreate
    from app.core.logging import logger

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    r = sync_redis.from_url(settings.redis_url)

    async with AsyncSessionLocal() as db:
        # Load job
        result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error("scrape_job_not_found", job_id=job_id)
            return {"error": "job not found"}

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        _publish(r, job_id, {
            "type": "started",
            "job_id": job_id,
            "sources": job.sources,
            "message": "Démarrage du scraping...",
        })

        scraper_map = {
            "google_maps": GoogleMapsScraper,
            "pages_jaunes": PagesJaunesScraper,
            "yelp": YelpScraper,
            "linkedin": LinkedInScraper,
            "instagram": InstagramScraper,
            "facebook": FacebookScraper,
        }

        total_found = 0
        total_new = 0
        total_merged = 0

        sources = [s for s in job.sources if s in scraper_map]
        per_source_max = max(1, job.max_results // max(len(sources), 1))

        for idx, source_name in enumerate(sources):
            ScraperClass = scraper_map[source_name]
            scraper = ScraperClass(
                query=job.query_term,
                location=job.location or "Montréal",
                max_results=per_source_max,
            )

            source_count = 0
            _publish(r, job_id, {
                "type": "source_started",
                "job_id": job_id,
                "source": source_name,
                "message": f"Scraping {source_name}…",
                "progress": int(idx / len(sources) * 100),
            })

            try:
                async for raw in scraper.scrape():
                    lead_data = _raw_to_lead_create(raw)
                    dedup = DedupService(db)
                    _, is_new = await dedup.process(
                        data=lead_data,
                        scrape_job_id=str(job.id),
                        source=source_name,
                        source_url=raw.source_url,
                    )
                    source_count += 1
                    total_found += 1
                    if is_new:
                        total_new += 1
                    else:
                        total_merged += 1

                    # Publish per-lead progress
                    _publish(r, job_id, {
                        "type": "lead_found",
                        "job_id": job_id,
                        "source": source_name,
                        "lead_name": raw.business_name,
                        "is_new": is_new,
                        "leads_found": total_found,
                        "leads_new": total_new,
                        "leads_merged": total_merged,
                        "progress": int((idx / len(sources) + source_count / (per_source_max * len(sources))) * 100),
                    })

                    # Update job counters periodically
                    job.leads_found = total_found
                    job.leads_new = total_new
                    job.leads_merged = total_merged
                    await db.commit()

            except Exception as exc:
                logger.error("scraper_error", source=source_name, error=str(exc))
                _publish(r, job_id, {
                    "type": "source_error",
                    "job_id": job_id,
                    "source": source_name,
                    "message": f"Erreur {source_name}: {str(exc)[:200]}",
                })

            _publish(r, job_id, {
                "type": "source_done",
                "job_id": job_id,
                "source": source_name,
                "count": source_count,
                "progress": int((idx + 1) / len(sources) * 100),
            })

        # Finalize
        job.status = "done"
        job.completed_at = datetime.now(timezone.utc)
        job.leads_found = total_found
        job.leads_new = total_new
        job.leads_merged = total_merged
        await db.commit()

        _publish(r, job_id, {
            "type": "completed",
            "job_id": job_id,
            "leads_found": total_found,
            "leads_new": total_new,
            "leads_merged": total_merged,
            "progress": 100,
            "message": f"Terminé — {total_new} nouveau(x) lead(s), {total_merged} fusionné(s)",
        })

        logger.info(
            "scrape_job_done",
            job_id=job_id,
            found=total_found,
            new=total_new,
            merged=total_merged,
        )

    r.close()
    await engine.dispose()
    return {"job_id": job_id, "leads_found": total_found, "leads_new": total_new}


def _raw_to_lead_create(raw) -> "LeadCreate":
    from app.schemas.lead import LeadCreate
    return LeadCreate(
        business_name=raw.business_name,
        industry=raw.industry,
        description=raw.description,
        phone=raw.phone,
        email=raw.email,
        website=raw.website,
        address=raw.address,
        city=raw.city,
        province=raw.province,
        postal_code=raw.postal_code,
        latitude=raw.latitude,
        longitude=raw.longitude,
        google_place_id=raw.google_place_id,
        google_rating=raw.google_rating,
        google_reviews=raw.google_reviews,
        yelp_url=raw.yelp_url,
        linkedin_url=raw.linkedin_url,
        instagram_handle=raw.instagram_handle,
        facebook_url=raw.facebook_url,
        owner_name=raw.owner_name,
        owner_title=raw.owner_title,
        owner_linkedin=raw.owner_linkedin,
        detected_language=raw.detected_language,
        source_flags=[raw.source],
        business_hours=raw.business_hours,
    )
