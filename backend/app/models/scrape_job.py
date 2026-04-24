import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.database import Base


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    sources: Mapped[list] = mapped_column(ARRAY(String(50)), nullable=False)
    query_term: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    bounding_box: Mapped[dict | None] = mapped_column(JSONB)  # {sw_lat, sw_lng, ne_lat, ne_lng}
    max_results: Mapped[int] = mapped_column(SmallInteger, default=30)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    # pending | running | done | failed | cancelled

    celery_task_id: Mapped[str | None] = mapped_column(String(255))
    leads_found: Mapped[int] = mapped_column(Integer, default=0)
    leads_new: Mapped[int] = mapped_column(Integer, default=0)
    leads_merged: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)

    started_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    lead_sources: Mapped[list["LeadSource"]] = relationship("LeadSource", back_populates="scrape_job")
