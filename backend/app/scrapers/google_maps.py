"""Google Maps scraper — JSON-LD + Playwright stealth strategy."""
from __future__ import annotations

import json
import re
from typing import AsyncIterator
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.core.logging import logger
from app.scrapers.base import BaseScraper, RawLead
from app.scrapers.utils.anti_bot import human_scroll, random_delay, safe_goto, short_delay
from app.scrapers.utils.browser import new_page
from app.scrapers.utils.normalizer import (
    clean_text,
    detect_language,
    normalize_phone,
    normalize_website,
)

_SEARCH_URL = "https://www.google.com/maps/search/{query}+{location}"


class GoogleMapsScraper(BaseScraper):
    source_name = "google_maps"

    async def scrape(self) -> AsyncIterator[RawLead]:
        url = _SEARCH_URL.format(
            query=quote_plus(self.query),
            location=quote_plus(self.location),
        )

        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="networkidle", timeout=40_000):
                logger.warning("google_maps_load_failed", url=url)
                return

            await random_delay(2000, 3500)
            await human_scroll(page, steps=3)

            # Accept cookies if banner appears
            try:
                btn = page.locator('button[aria-label*="Accept"], button[jsname="b3VHJd"]').first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    await short_delay()
            except Exception:
                pass

            count = 0
            seen_place_ids: set[str] = set()

            # Scroll result panel and collect listing links
            listing_links: list[str] = []
            panel_selector = '[role="feed"]'
            try:
                await page.wait_for_selector(panel_selector, timeout=15_000)
                for _ in range(8):
                    links = await page.eval_on_selector_all(
                        'a[href*="/maps/place/"]',
                        "els => els.map(e => e.href)",
                    )
                    for link in links:
                        if link not in listing_links:
                            listing_links.append(link)
                    if len(listing_links) >= self.max_results:
                        break
                    await page.mouse.wheel(0, 600)
                    await short_delay(600, 1200)
            except Exception:
                # Fallback: collect any place links from the page
                links = await page.eval_on_selector_all(
                    'a[href*="/maps/place/"]',
                    "els => els.map(e => e.href)",
                )
                listing_links = list(dict.fromkeys(links))

            logger.info("google_maps_links_found", count=len(listing_links))

        # Visit each listing detail page
        for link in listing_links[: self.max_results]:
            if count >= self.max_results:
                break
            lead = await self._scrape_detail(link, seen_place_ids)
            if lead:
                seen_place_ids.add(lead.google_place_id or "")
                yield lead
                count += 1
            await random_delay(1500, 3500)

    async def _scrape_detail(self, url: str, seen: set[str]) -> RawLead | None:
        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=30_000):
                return None

            await random_delay(800, 2000)
            html = await page.content()

        return self._parse_detail(html, url, seen)

    def _parse_detail(self, html: str, url: str, seen: set[str]) -> RawLead | None:
        soup = BeautifulSoup(html, "lxml")

        # 1) Try JSON-LD first (most reliable)
        lead = self._from_json_ld(soup, url)

        # 2) Fallback: heuristic meta / h1 parsing
        if not lead:
            lead = self._from_heuristics(soup, url)

        if not lead:
            return None

        # Dedup within same scrape run
        if lead.google_place_id and lead.google_place_id in seen:
            return None

        return lead

    # ------------------------------------------------------------------ JSON-LD
    def _from_json_ld(self, soup: BeautifulSoup, url: str) -> RawLead | None:
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string or "")
            except Exception:
                continue

            items = data if isinstance(data, list) else [data]
            for item in items:
                t = item.get("@type", "")
                if t not in ("LocalBusiness", "Restaurant", "FoodEstablishment",
                             "Store", "HealthAndBeautyBusiness", "HomeAndConstructionBusiness",
                             "LodgingBusiness", "Plumber", "Electrician", "HairSalon"):
                    continue

                name = clean_text(item.get("name"))
                if not name:
                    continue

                addr = item.get("address") or {}
                phone = normalize_phone(item.get("telephone"))
                website = normalize_website(item.get("url"))

                geo = item.get("geo") or {}
                lat = _to_float(geo.get("latitude"))
                lng = _to_float(geo.get("longitude"))

                rating = _to_float(item.get("aggregateRating", {}).get("ratingValue"))
                reviews = _to_int(item.get("aggregateRating", {}).get("reviewCount"))

                place_id = _extract_place_id(url)
                desc = clean_text(item.get("description"))
                city = clean_text(addr.get("addressLocality") or addr.get("streetAddress", "").split(",")[-1].strip())

                hours_raw = item.get("openingHoursSpecification") or []
                hours = _parse_hours(hours_raw)

                return RawLead(
                    source=self.source_name,
                    business_name=name,
                    industry=clean_text(t.replace("Business", "").lower()) or self.query,
                    phone=phone,
                    website=website,
                    address=clean_text(addr.get("streetAddress")),
                    city=city,
                    province=addr.get("addressRegion", "Québec"),
                    postal_code=clean_text(addr.get("postalCode")),
                    latitude=lat,
                    longitude=lng,
                    google_place_id=place_id,
                    google_rating=rating,
                    google_reviews=reviews,
                    description=desc,
                    business_hours=hours or None,
                    detected_language=detect_language(desc or name),
                    source_url=url,
                    raw_data=item,
                )
        return None

    # --------------------------------------------------------------- Heuristics
    def _from_heuristics(self, soup: BeautifulSoup, url: str) -> RawLead | None:
        title = soup.find("h1")
        name = clean_text(title.get_text()) if title else None
        if not name:
            og_title = soup.find("meta", property="og:title")
            name = clean_text(og_title.get("content", "")) if og_title else None
        if not name:
            return None

        place_id = _extract_place_id(url)

        return RawLead(
            source=self.source_name,
            business_name=name,
            google_place_id=place_id,
            industry=self.query,
            city=self.location,
            detected_language="fr",
            source_url=url,
            raw_data={"url": url},
        )


# ------------------------------------------------------------------ helpers

def _extract_place_id(url: str) -> str | None:
    m = re.search(r"place/[^/]+/([^/?]+)", url)
    if m:
        return m.group(1)[:255]
    m = re.search(r"0x[0-9a-fA-F]+:0x[0-9a-fA-F]+", url)
    return m.group(0) if m else None


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


def _parse_hours(specs: list) -> dict:
    result: dict[str, str] = {}
    day_map = {
        "Monday": "lundi", "Tuesday": "mardi", "Wednesday": "mercredi",
        "Thursday": "jeudi", "Friday": "vendredi", "Saturday": "samedi", "Sunday": "dimanche",
    }
    for spec in specs:
        day = spec.get("dayOfWeek", "")
        opens = spec.get("opens", "")
        closes = spec.get("closes", "")
        day_fr = day_map.get(day, day)
        if opens and closes:
            result[day_fr] = f"{opens}–{closes}"
    return result
