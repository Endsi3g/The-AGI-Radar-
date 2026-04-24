import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index

from app.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    type: Mapped[str] = mapped_column(String(30), nullable=False)
    # email_sent | email_received | sms_sent | sms_received
    # call_made | call_received | note_added | status_changed | score_updated

    notes: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
    # e.g., {call_duration: 120, recording_url: "...", previous_status: "nouveau", new_status: "contacté"}

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="interactions")
    message: Mapped["Message | None"] = relationship("Message", back_populates="interactions")

    __table_args__ = (
        Index("idx_interactions_lead", "lead_id"),
        Index("idx_interactions_type", "type"),
    )
