import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_pw: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="sales")  # admin|sales|viewer
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    locale: Mapped[str] = mapped_column(String(5), nullable=False, default="fr")

    # Google OAuth tokens (encrypted at rest)
    google_access_token: Mapped[str | None] = mapped_column(Text)
    google_refresh_token: Mapped[str | None] = mapped_column(Text)
    google_token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    google_email: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    assigned_leads: Mapped[list["Lead"]] = relationship("Lead", back_populates="assignee", foreign_keys="Lead.assigned_to")
    approved_messages: Mapped[list["Message"]] = relationship("Message", back_populates="approver", foreign_keys="Message.approved_by")
    calendar_events: Mapped[list["CalendarEvent"]] = relationship("CalendarEvent", back_populates="user")

    @property
    def google_connected(self) -> bool:
        return self.google_refresh_token is not None
