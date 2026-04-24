"""LinkedIn company page scraper — uses li_at session cookie."""
from __future__ import annotations

import re
from typing import AsyncIterator
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from app.config import settings
from app.core.logging import logger
from app.scrapers.base import BaseScraper, RawLead
from app.scrapers.utils.anti_bot import human_scroll, random_delay, safe_goto
from app.scrapers.utils.browser import new_page
from app.scrapers.utils.normalizer import clean_text, detect_language, normalize_website

_SEARCH = "https://www.linkedin.com/search/results/companies/?keywords={query}+{location}"


class LinkedInScraper(BaseScraper):
    source_name = "linkedin"

    def _get_cookies(self) -> list[dict] | None:
        li_at = getattr(settings, "linkedin_li_at_cookie", None)
        if not li_at:
            return None
        return [
            {"name": "li_at", "value": li_at, "domain": ".linkedin.com", "path": "/"}
        ]

    async def scrape(self) -> AsyncIterator[RawLead]:
        cookies = self._get_cookies()
        if not cookies:
            logger.warning("linkedin_no_cookie_skipping")
            return

        url = _SEARCH.format(
            query=quote_plus(self.query),
            location=quote_plus(self.location),
        )

        company_urls: list[str] = []

        async with new_page(cookies=cookies) as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=30_000):
                logger.warning("linkedin_search_failed")
                return

            await random_delay(2000, 4000)
            await human_scroll(page, steps=5)

            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            for a in soup.select('a[href*="/company/"]'):
                href = a.get("href", "")
                m = re.search(r"(https://www\.linkedin\.com/company/[^/?]+)", href)
                if m and m.group(1) not in company_urls:
                    company_urls.append(m.group(1))
                if len(company_urls) >= self.max_results:
                    break

        logger.info("linkedin_companies_found", count=len(company_urls))

        for company_url in company_urls[: self.max_results]:
            lead = await self._scrape_company(company_url, cookies)
            if lead:
                yield lead
            await random_delay(2000, 5000)

    async def _scrape_company(self, url: str, cookies: list[dict]) -> RawLead | None:
        async with new_page(cookies=cookies) as page:
            if not await safe_goto(page, url, wait_until="domcontentloaded", timeout=25_000):
                return None
            await random_delay(1500, 3000)
            html = await page.content()

        soup = BeautifulSoup(html, "lxml")

        name_el = soup.select_one("h1, .top-card-layout__title, .org-top-card-summary__title")
        name = clean_text(name_el.get_text()) if name_el else None
        if not name:
            return None

        website_el = soup.select_one('a[href*="://"][data-field="website"]')
        website = normalize_website(website_el.get("href") if website_el else None)

        desc_el = soup.select_one(".top-card-layout__second-subline, .org-top-card-summary__tagline, .about-us")
        desc = clean_text(desc_el.get_text()) if desc_el else None

        return RawLead(
            source=self.source_name,
            business_name=name,
            industry=self.query,
            website=website,
            city=self.location,
            linkedin_url=url,
            description=desc,
            detected_language=detect_language(desc or name),
            source_url=url,
            raw_data={"url": url},
        )
