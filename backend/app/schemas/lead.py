from datetime import datetime
from uuid import UUID
from typing import Any
from pydantic import BaseModel


class LeadCreate(BaseModel):
    business_name: str
    industry: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    province: str = "Québec"
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None
    google_rating: float | None = None
    google_reviews: int | None = None
    yelp_url: str | None = None
    linkedin_url: str | None = None
    instagram_handle: str | None = None
    facebook_url: str | None = None
    owner_name: str | None = None
    owner_title: str | None = None
    owner_linkedin: str | None = None
    detected_language: str = "fr"
    source_flags: list[str] = []
    business_hours: dict[str, Any] | None = None


class LeadUpdate(BaseModel):
    status: str | None = None
    assigned_to: UUID | None = None
    next_followup_at: datetime | None = None
    ai_score: int | None = None
    score_rationale: str | None = None
    owner_name: str | None = None
    owner_title: str | None = None
    email: str | None = None
    phone: str | None = None


class LeadResponse(LeadCreate):
    id: UUID
    status: str
    ai_score: int | None
    score_rationale: str | None
    assigned_to: UUID | None
    last_contacted_at: datetime | None
    next_followup_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadGeoJSON(BaseModel):
    id: UUID
    business_name: str
    status: str
    ai_score: int | None
    latitude: float
    longitude: float
    city: str | None
    industry: str | None
