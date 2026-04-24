"""Yelp scraper — mobile endpoint approach (less protected)."""
from __future__ import annotations

import json
import re
from typing import AsyncIterator
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.core.logging import logger
from app.scrapers.base import BaseScraper, RawLead
from app.scrapers.utils.anti_bot import human_scroll, random_delay, safe_goto
from app.scrapers.utils.browser import new_page
from app.scrapers.utils.normalizer import (
    clean_text,
    detect_language,
    normalize_phone,
    normalize_website,
)

_SEARCH_URL = "https://www.yelp.ca/search?find_desc={query}&find_loc={location}"


class YelpScraper(BaseScraper):
    source_name = "yelp"

    async def scrape(self) -> AsyncIterator[RawLead]:
        url = _SEARCH_URL.format(
            query=quote_plus(self.query),
            location=quote_plus(self.location),
        )

        listing_slugs: list[str] = []

        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=30_000):
                logger.warning("yelp_load_failed", url=url)
                return

            await random_delay(1500, 3000)
            await human_scroll(page, steps=4)

            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            for a in soup.select('a[href*="/biz/"]'):
                href = a.get("href", "")
                m = re.search(r"/biz/([\w-]+)", href)
                if m and m.group(1) not in listing_slugs:
                    listing_slugs.append(m.group(1))
                if len(listing_slugs) >= self.max_results:
                    break

        logger.info("yelp_slugs_found", count=len(listing_slugs))

        for slug in listing_slugs[: self.max_results]:
            lead = await self._scrape_biz(slug)
            if lead:
                yield lead
            await random_delay(1500, 4000)

    async def _scrape_biz(self, slug: str) -> RawLead | None:
        url = f"https://www.yelp.ca/biz/{slug}"
        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=25_000):
                return None
            await random_delay(800, 2000)
            html = await page.content()

        soup = BeautifulSoup(html, "lxml")

        # JSON-LD first
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") in ("Restaurant", "LocalBusiness", "FoodEstablishment"):
                        name = clean_text(item.get("name"))
                        if not name:
                            continue
                        addr = item.get("address") or {}
                        geo = item.get("geo") or {}
                        rating_data = item.get("aggregateRating") or {}
                        return RawLead(
                            source=self.source_name,
                            business_name=name,
                            industry=self.query,
                            phone=normalize_phone(item.get("telephone")),
                            website=normalize_website(item.get("url")),
                            address=clean_text(addr.get("streetAddress")),
                            city=clean_text(addr.get("addressLocality")) or self.location,
                            province=addr.get("addressRegion", "Québec"),
                            postal_code=clean_text(addr.get("postalCode")),
                            latitude=_to_float(geo.get("latitude")),
                            longitude=_to_float(geo.get("longitude")),
                            google_rating=_to_float(rating_data.get("ratingValue")),
                            google_reviews=_to_int(rating_data.get("reviewCount")),
                            yelp_url=url,
                            description=clean_text(item.get("description")),
                            detected_language=detect_language(item.get("description", "")),
                            source_url=url,
                            raw_data=item,
                        )
            except Exception:
                continue

        # Heuristic fallback
        name_el = soup.select_one("h1")
        name = clean_text(name_el.get_text()) if name_el else None
        if not name:
            return None

        phone_el = soup.select_one('p[class*="phone"], [class*="phone-number"]')
        phone = normalize_phone(phone_el.get_text() if phone_el else None)

        return RawLead(
            source=self.source_name,
            business_name=name,
            industry=self.query,
            phone=phone,
            yelp_url=url,
            city=self.location,
            detected_language="fr",
            source_url=url,
            raw_data={"slug": slug},
        )


def _to_float(val) -> float | None:
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
