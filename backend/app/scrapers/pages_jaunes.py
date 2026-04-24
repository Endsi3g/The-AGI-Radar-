"""Pages Jaunes Canada scraper (pagejaunesca.com)."""
from __future__ import annotations

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

_BASE = "https://www.pagesjaunes.ca"
_SEARCH = _BASE + "/search/si/1/{query}/{location}"


class PagesJaunesScraper(BaseScraper):
    source_name = "pages_jaunes"

    async def scrape(self) -> AsyncIterator[RawLead]:
        url = _SEARCH.format(
            query=quote_plus(self.query),
            location=quote_plus(self.location),
        )

        listing_urls: list[str] = []

        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=30_000):
                logger.warning("pages_jaunes_load_failed", url=url)
                return

            await random_delay(1500, 3000)
            await human_scroll(page, steps=4)

            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            for a in soup.select("a.listing__name--link, h3.listing__name a"):
                href = a.get("href", "")
                if href.startswith("/"):
                    href = _BASE + href
                if href and href not in listing_urls:
                    listing_urls.append(href)
                if len(listing_urls) >= self.max_results:
                    break

            # Try next pages if needed
            page_num = 2
            while len(listing_urls) < self.max_results and page_num <= 5:
                next_url = re.sub(r"/si/\d+/", f"/si/{page_num}/", url)
                if not await safe_goto(page, next_url, wait_until="domcontentloaded"):
                    break
                await random_delay(1200, 2500)
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")
                new_links = [
                    (_BASE + a["href"]) if a.get("href", "").startswith("/") else a.get("href", "")
                    for a in soup.select("a.listing__name--link, h3.listing__name a")
                    if a.get("href")
                ]
                if not new_links:
                    break
                for l in new_links:
                    if l not in listing_urls:
                        listing_urls.append(l)
                page_num += 1

        logger.info("pages_jaunes_links_found", count=len(listing_urls))

        count = 0
        for link in listing_urls[: self.max_results]:
            lead = await self._scrape_detail(link)
            if lead:
                yield lead
                count += 1
            await random_delay(1500, 3500)

    async def _scrape_detail(self, url: str) -> RawLead | None:
        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=25_000):
                return None
            await random_delay(800, 1800)
            html = await page.content()

        soup = BeautifulSoup(html, "lxml")

        name_el = soup.select_one("h1.business-name, .merchant-name, h1")
        name = clean_text(name_el.get_text()) if name_el else None
        if not name:
            return None

        phone_el = soup.select_one('[class*="phone"] a, .phones a, .phoneNumber')
        phone = normalize_phone(phone_el.get_text() if phone_el else None)

        website_el = soup.select_one('a[href^="http"][class*="website"], .website a')
        website = normalize_website(website_el.get("href") if website_el else None)

        addr_el = soup.select_one("address, .address, .streetAddress")
        address = clean_text(addr_el.get_text(separator=" ")) if addr_el else None

        city_el = soup.select_one(".locality, .city, [itemprop='addressLocality']")
        city = clean_text(city_el.get_text()) if city_el else self.location

        desc_el = soup.select_one(".business-description, .description, .about")
        desc = clean_text(desc_el.get_text()) if desc_el else None

        return RawLead(
            source=self.source_name,
            business_name=name,
            industry=self.query,
            phone=phone,
            website=website,
            address=address,
            city=city,
            description=desc,
            detected_language=detect_language(desc or name),
            source_url=url,
            raw_data={"url": url, "name": name},
        )
