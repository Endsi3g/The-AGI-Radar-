import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Index

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Business identity
    business_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(100), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Contact info
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(500))
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    province: Mapped[str] = mapped_column(String(50), default="Québec")
    postal_code: Mapped[str | None] = mapped_column(String(10))
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))

    # Social presence
    google_place_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    google_rating: Mapped[float | None] = mapped_column(Numeric(2, 1))
    google_reviews: Mapped[int | None] = mapped_column(Integer)
    yelp_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    instagram_handle: Mapped[str | None] = mapped_column(String(100))
    facebook_url: Mapped[str | None] = mapped_column(String(500))

    # Owner / decision-maker
    owner_name: Mapped[str | None] = mapped_column(String(255))
    owner_title: Mapped[str | None] = mapped_column(String(100))
    owner_linkedin: Mapped[str | None] = mapped_column(String(500))

    # Language detection
    detected_language: Mapped[str] = mapped_column(String(5), default="fr")

    # Pipeline status
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="nouveau", index=True)
    # nouveau | contacté | réponse | rdv | fermé | perdu

    # AI scoring
    ai_score: Mapped[int | None] = mapped_column(SmallInteger)
    score_rationale: Mapped[str | None] = mapped_column(Text)

    # Source tracking (list of source names)
    source_flags: Mapped[dict] = mapped_column(JSONB, default=list)

    # Business hours
    business_hours: Mapped[dict | None] = mapped_column(JSONB)

    # Assignment
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_followup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    assignee: Mapped["User | None"] = relationship("User", back_populates="assigned_leads", foreign_keys=[assigned_to])
    sources: Mapped[list["LeadSource"]] = relationship("LeadSource", back_populates="lead", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="lead", cascade="all, delete-orphan")
    interactions: Mapped[list["Interaction"]] = relationship("Interaction", back_populates="lead", cascade="all, delete-orphan")
    calendar_events: Mapped[list["CalendarEvent"]] = relationship("CalendarEvent", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_leads_status", "status"),
        Index("idx_leads_city", "city"),
        Index("idx_leads_industry", "industry"),
    )
