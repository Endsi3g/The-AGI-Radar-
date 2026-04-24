from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CampaignCreate(BaseModel):
    name: str
    channel: str  # email | sms | voip
    template_subject: str | None = None
    template_body: str | None = None
    industry_target: str | None = None
    language: str = "fr"


class CampaignUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
    template_subject: str | None = None
    template_body: str | None = None
    industry_target: str | None = None


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    channel: str
    status: str
    template_subject: str | None
    template_body: str | None
    industry_target: str | None
    language: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
