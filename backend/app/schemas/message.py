from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class MessageCreate(BaseModel):
    lead_id: UUID
    campaign_id: UUID | None = None
    channel: str  # email | sms | voip_script
    subject: str | None = None
    body: str
    ai_generated: bool = True


class MessageUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None


class MessageApprove(BaseModel):
    body: str | None = None  # Optional final edit before sending
    subject: str | None = None


class MessageReject(BaseModel):
    reason: str | None = None


class MessageResponse(BaseModel):
    id: UUID
    lead_id: UUID
    campaign_id: UUID | None
    channel: str
    direction: str
    status: str
    subject: str | None
    body: str
    ai_generated: bool
    approved_by: UUID | None
    approved_at: datetime | None
    sent_at: datetime | None
    twilio_sid: str | None
    gmail_message_id: str | None
    gmail_thread_id: str | None
    ai_reply_suggestion: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
