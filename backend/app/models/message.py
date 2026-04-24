import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index

from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"))

    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # email | sms | voip_script
    direction: Mapped[str] = mapped_column(String(10), nullable=False, default="outbound")  # outbound | inbound
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    # draft | pending_approval | approved | sent | delivered | failed | rejected

    subject: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)

    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Delivery metadata
    twilio_sid: Mapped[str | None] = mapped_column(String(100))
    gmail_message_id: Mapped[str | None] = mapped_column(String(255))
    gmail_thread_id: Mapped[str | None] = mapped_column(String(255), index=True)

    # Inbound reply linkage + AI suggestion
    reply_to_message_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"))
    ai_reply_suggestion: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="messages")
    campaign: Mapped["Campaign | None"] = relationship("Campaign", back_populates="messages")
    approver: Mapped["User | None"] = relationship("User", back_populates="approved_messages", foreign_keys=[approved_by])
    interactions: Mapped[list["Interaction"]] = relationship("Interaction", back_populates="message")
    replies: Mapped[list["Message"]] = relationship("Message", foreign_keys=[reply_to_message_id])

    __table_args__ = (
        Index("idx_messages_lead", "lead_id"),
        Index("idx_messages_status", "status"),
        Index("idx_messages_channel", "channel"),
    )
