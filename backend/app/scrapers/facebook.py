"""Facebook public business page scraper via Playwright."""
from __future__ import annotations

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

_SEARCH = "https://www.facebook.com/search/pages/?q={query}+{location}"


class FacebookScraper(BaseScraper):
    source_name = "facebook"

    async def scrape(self) -> AsyncIterator[RawLead]:
        url = _SEARCH.format(
            query=quote_plus(self.query),
            location=quote_plus(self.location),
        )

        page_urls: list[str] = []

        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=30_000):
                logger.warning("facebook_search_failed")
                return

            await random_delay(2000, 4000)

            # Decline cookie consent if shown
            try:
                btn = page.locator('[data-testid="cookie-policy-manage-dialog-accept-button"]').first
                if await btn.is_visible(timeout=3000):
                    await btn.click()
                    await random_delay(800, 1500)
            except Exception:
                pass

            await human_scroll(page, steps=5)

            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                # Facebook page links match /pagename or /pages/name/id
                if re.search(r"facebook\.com/(?!search|login|groups|events|marketplace)", href):
                    full = href if href.startswith("http") else "https://www.facebook.com" + href
                    if full not in page_urls:
                        page_urls.append(full)
                if len(page_urls) >= self.max_results:
                    break

        logger.info("facebook_pages_found", count=len(page_urls))

        for page_url in page_urls[: self.max_results]:
            lead = await self._scrape_page(page_url)
            if lead:
                yield lead
            await random_delay(2000, 5000)

    async def _scrape_page(self, url: str) -> RawLead | None:
        async with new_page() as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=25_000):
                return None
            await random_delay(1000, 2500)
            html = await page.content()

        soup = BeautifulSoup(html, "lxml")

        og_name = soup.find("meta", property="og:site_name") or soup.find("meta", property="og:title")
        name = clean_text(og_name.get("content", "") if og_name else "")
        if not name:
            h1 = soup.find("h1")
            name = clean_text(h1.get_text()) if h1 else None
        if not name:
            return None

        phone_el = soup.find(string=re.compile(r"\(\d{3}\)\s?\d{3}[-\s]\d{4}"))
        phone = normalize_phone(phone_el) if phone_el else None

        website_el = soup.find("a", href=re.compile(r"https?://(?!www\.facebook\.com)"))
        website = normalize_website(website_el.get("href") if website_el else None)

        desc_meta = soup.find("meta", property="og:description")
        desc = clean_text(desc_meta.get("content", "") if desc_meta else "")

        return RawLead(
            source=self.source_name,
            business_name=name,
            industry=self.query,
            phone=phone,
            website=website,
            city=self.location,
            facebook_url=url,
            description=desc,
            detected_language=detect_language(desc or name),
            source_url=url,
            raw_data={"url": url},
        )
