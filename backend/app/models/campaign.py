import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)  # email | sms | voip
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    # draft | active | paused | completed

    template_subject: Mapped[str | None] = mapped_column(Text)
    template_body: Mapped[str | None] = mapped_column(Text)
    industry_target: Mapped[str | None] = mapped_column(String(100))
    language: Mapped[str] = mapped_column(String(5), default="fr")

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="campaign")
