from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ScrapeJobCreate(BaseModel):
    sources: list[str]  # ["google_maps", "pages_jaunes", "yelp", "linkedin", "instagram", "facebook"]
    query_term: str
    location: str | None = None
    bounding_box: dict | None = None  # {sw_lat, sw_lng, ne_lat, ne_lng}
    max_results: int = 30


class ScrapeJobResponse(BaseModel):
    id: UUID
    sources: list[str]
    query_term: str
    location: str | None
    max_results: int
    status: str
    celery_task_id: str | None
    leads_found: int
    leads_new: int
    leads_merged: int
    error_message: str | None
    started_by: UUID
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScrapeProgressEvent(BaseModel):
    job_id: str
    source: str
    progress: int  # 0-100
    leads_found: int
    message: str
