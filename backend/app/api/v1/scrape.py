from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis
import json

from app.database import get_db
from app.models.scrape_job import ScrapeJob
from app.models.user import User
from app.schemas.scrape import ScrapeJobCreate, ScrapeJobResponse
from app.dependencies import get_current_user
from app.tasks.scrape_tasks import run_scrape_job
from app.core.exceptions import NotFoundError
from app.config import settings

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/jobs", response_model=ScrapeJobResponse, status_code=status.HTTP_201_CREATED)
async def launch_scrape_job(
    body: ScrapeJobCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    job = ScrapeJob(
        sources=body.sources,
        query_term=body.query_term,
        location=body.location,
        bounding_box=body.bounding_box,
        max_results=body.max_results,
        started_by=current_user.id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Enqueue Celery task
    task = run_scrape_job.delay(str(job.id))
    job.celery_task_id = task.id
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/jobs", response_model=list[ScrapeJobResponse])
async def list_scrape_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    limit: int = 20,
    offset: int = 0,
):
    result = await db.execute(
        select(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(limit).offset(offset)
    )
    return result.scalars().all()


@router.get("/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_scrape_job(
    job_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(ScrapeJob).where(ScrapeJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("ScrapeJob")
    return job


@router.websocket("/jobs/{job_id}/stream")
async def scrape_job_stream(websocket: WebSocket, job_id: str):
    """Real-time progress stream via Redis pub/sub."""
    await websocket.accept()
    redis = aioredis.from_url(settings.redis_url)
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"job:{job_id}")
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"].decode())
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(f"job:{job_id}")
        await redis.aclose()
