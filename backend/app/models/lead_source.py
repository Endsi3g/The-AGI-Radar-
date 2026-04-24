import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.database import Base


class LeadSource(Base):
    __tablename__ = "lead_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id", ondelete="CASCADE"))
    scrape_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scrape_jobs.id", ondelete="SET NULL"))

    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # google_maps | yelp | pages_jaunes | linkedin | instagram | facebook

    source_url: Mapped[str | None] = mapped_column(String(1000))
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    lead: Mapped["Lead | None"] = relationship("Lead", back_populates="sources")
    scrape_job: Mapped["ScrapeJob | None"] = relationship("ScrapeJob", back_populates="lead_sources")
