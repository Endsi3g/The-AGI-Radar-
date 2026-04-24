"""Abstract base class for all scrapers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class RawLead:
    """Normalised intermediate before dedup + DB persistence."""
    source: str
    business_name: str
    industry: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    address: str | None = None
    city: str | None = None
    province: str = "Québec"
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None
    google_rating: float | None = None
    google_reviews: int | None = None
    yelp_url: str | None = None
    linkedin_url: str | None = None
    instagram_handle: str | None = None
    facebook_url: str | None = None
    owner_name: str | None = None
    owner_title: str | None = None
    owner_linkedin: str | None = None
    description: str | None = None
    business_hours: dict | None = None
    detected_language: str = "fr"
    source_url: str | None = None
    raw_data: dict = field(default_factory=dict)


class BaseScraper(ABC):
    """Async generator-based scraper.  Yields RawLead as they are found."""

    source_name: str = "unknown"

    def __init__(self, query: str, location: str, max_results: int = 30) -> None:
        self.query = query
        self.location = location
        self.max_results = max_results

    @abstractmethod
    async def scrape(self) -> AsyncIterator[RawLead]:
        """Yield RawLead instances one by one."""
        ...

    def __aiter__(self) -> AsyncIterator[RawLead]:
        return self.scrape()
