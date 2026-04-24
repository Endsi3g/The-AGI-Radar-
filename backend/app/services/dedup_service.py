import re
from urllib.parse import urlparse

from rapidfuzz import fuzz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.lead import Lead
from app.models.lead_source import LeadSource
from app.schemas.lead import LeadCreate


def normalize_phone(phone: str | None) -> str | None:
    """Strip all non-digits, remove leading country code (+1 or 1), return 10-digit string."""
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits if len(digits) == 10 else None


def normalize_domain(url: str | None) -> str | None:
    """Extract bare domain from URL (strips www, scheme, path)."""
    if not url:
        return None
    try:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        domain = parsed.netloc or parsed.path
        return domain.lower().removeprefix("www.").split("/")[0].strip()
    except Exception:
        return None


FUZZY_THRESHOLD = 85  # WRatio score 0-100


class DedupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_duplicate(self, data: LeadCreate) -> Lead | None:
        """
        Returns existing lead if a duplicate is detected, else None.
        Priority: google_place_id → phone → website domain → fuzzy name×city
        """
        # 1. google_place_id — definitive match
        if data.google_place_id:
            result = await self.db.execute(
                select(Lead).where(Lead.google_place_id == data.google_place_id)
            )
            lead = result.scalar_one_or_none()
            if lead:
                return lead

        # 2. Phone match
        phone_norm = normalize_phone(data.phone)
        if phone_norm:
            result = await self.db.execute(
                select(Lead).where(Lead.phone.isnot(None))
            )
            candidates = result.scalars().all()
            for c in candidates:
                if normalize_phone(c.phone) == phone_norm:
                    # Cross-check name similarity > 60% to avoid false positives
                    if fuzz.WRatio(data.business_name, c.business_name) > 60:
                        return c

        # 3. Website domain match
        domain = normalize_domain(data.website)
        if domain:
            result = await self.db.execute(
                select(Lead).where(Lead.website.isnot(None))
            )
            candidates = result.scalars().all()
            for c in candidates:
                if normalize_domain(c.website) == domain:
                    return c

        # 4. Fuzzy name × city (most expensive, runs last)
        if data.city:
            result = await self.db.execute(
                select(Lead).where(Lead.city.ilike(f"%{data.city[:10]}%"))
            )
            candidates = result.scalars().all()
            for c in candidates:
                score = fuzz.WRatio(data.business_name.lower(), c.business_name.lower())
                if score >= FUZZY_THRESHOLD:
                    return c

        return None

    async def merge_into(
        self,
        existing: Lead,
        data: LeadCreate,
        scrape_job_id: str | None = None,
        source: str = "unknown",
        source_url: str | None = None,
    ) -> Lead:
        """
        Merge new scraped data into an existing lead (prefer non-null values).
        Adds a lead_source record and updates source_flags.
        """
        # Merge fields: prefer existing non-null, fill in missing
        merge_fields = [
            "phone", "email", "website", "address", "latitude", "longitude",
            "google_rating", "google_reviews", "owner_name", "owner_title",
            "owner_linkedin", "yelp_url", "linkedin_url", "instagram_handle",
            "facebook_url", "description", "business_hours",
        ]
        for field in merge_fields:
            new_val = getattr(data, field, None)
            if new_val and not getattr(existing, field):
                setattr(existing, field, new_val)

        # Update Google rating if new one is higher (more reviews = more accurate)
        if data.google_reviews and existing.google_reviews:
            if data.google_reviews > existing.google_reviews:
                existing.google_rating = data.google_rating
                existing.google_reviews = data.google_reviews
        elif data.google_reviews and not existing.google_reviews:
            existing.google_rating = data.google_rating
            existing.google_reviews = data.google_reviews

        # Update source_flags
        flags: list = existing.source_flags or []
        if source not in flags:
            flags = flags + [source]
            existing.source_flags = flags

        # Add lead_source record
        from uuid import UUID as _UUID
        import uuid
        lead_source = LeadSource(
            lead_id=existing.id,
            scrape_job_id=_UUID(scrape_job_id) if scrape_job_id else None,
            source=source,
            source_url=source_url,
            raw_data=data.model_dump(),
        )
        self.db.add(lead_source)
        await self.db.commit()
        await self.db.refresh(existing)
        return existing

    async def create_with_source(
        self,
        data: LeadCreate,
        scrape_job_id: str | None = None,
        source: str = "unknown",
        source_url: str | None = None,
    ) -> Lead:
        """Create a brand-new lead with its lead_source record."""
        from uuid import UUID as _UUID
        lead = Lead(**data.model_dump())
        self.db.add(lead)
        await self.db.flush()  # Get lead.id without committing

        lead_source = LeadSource(
            lead_id=lead.id,
            scrape_job_id=_UUID(scrape_job_id) if scrape_job_id else None,
            source=source,
            source_url=source_url,
            raw_data=data.model_dump(),
        )
        self.db.add(lead_source)
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def process(
        self,
        data: LeadCreate,
        scrape_job_id: str | None = None,
        source: str = "unknown",
        source_url: str | None = None,
    ) -> tuple[Lead, bool]:
        """
        Main entrypoint: returns (lead, is_new).
        is_new=True → new lead created
        is_new=False → merged into existing
        """
        existing = await self.find_duplicate(data)
        if existing:
            lead = await self.merge_into(existing, data, scrape_job_id, source, source_url)
            return lead, False
        else:
            lead = await self.create_with_source(data, scrape_job_id, source, source_url)
            return lead, True
