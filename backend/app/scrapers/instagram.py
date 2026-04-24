"""Instagram business scraper — uses instagrapi Private API."""
from __future__ import annotations

from typing import AsyncIterator

from app.config import settings
from app.core.logging import logger
from app.scrapers.base import BaseScraper, RawLead
from app.scrapers.utils.normalizer import clean_text, detect_language, normalize_website


class InstagramScraper(BaseScraper):
    source_name = "instagram"

    async def scrape(self) -> AsyncIterator[RawLead]:
        username = getattr(settings, "instagram_username", None)
        password = getattr(settings, "instagram_password", None)
        if not username or not password:
            logger.warning("instagram_no_credentials_skipping")
            return

        try:
            from instagrapi import Client  # type: ignore
        except ImportError:
            logger.warning("instagrapi_not_installed")
            return

        try:
            cl = Client()
            cl.login(username, password)
        except Exception as exc:
            logger.error("instagram_login_failed", error=str(exc))
            return

        try:
            # Search hashtag or location
            search_term = f"{self.query} {self.location}".lower().replace(" ", "")
            medias = cl.hashtag_medias_top(search_term, amount=self.max_results * 2)
        except Exception:
            medias = []

        seen_usernames: set[str] = set()
        count = 0

        for media in medias:
            if count >= self.max_results:
                break
            try:
                user_id = media.user.pk
                if str(user_id) in seen_usernames:
                    continue
                seen_usernames.add(str(user_id))

                user_info = cl.user_info(user_id)
                if not user_info.is_business:
                    continue

                name = clean_text(user_info.full_name) or user_info.username
                bio = clean_text(user_info.biography)
                website = normalize_website(str(user_info.external_url) if user_info.external_url else None)

                yield RawLead(
                    source=self.source_name,
                    business_name=name,
                    industry=self.query,
                    website=website,
                    instagram_handle=user_info.username,
                    city=self.location,
                    description=bio,
                    detected_language=detect_language(bio),
                    source_url=f"https://instagram.com/{user_info.username}",
                    raw_data={
                        "username": user_info.username,
                        "followers": user_info.follower_count,
                        "is_business": user_info.is_business,
                    },
                )
                count += 1
            except Exception as exc:
                logger.debug("instagram_user_fetch_error", error=str(exc))
                continue
