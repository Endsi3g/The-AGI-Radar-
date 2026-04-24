"""Playwright browser context manager with stealth and session pooling."""
from __future__ import annotations

import asyncio
import random
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from app.core.logging import logger

# User-agents rotated per context
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
]

_VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 800},
]

# Singleton playwright instance reused across tasks
_playwright: Playwright | None = None
_browser: Browser | None = None
_lock = asyncio.Lock()


async def get_browser() -> Browser:
    global _playwright, _browser
    async with _lock:
        if _browser is None or not _browser.is_connected():
            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--no-zygote",
                ],
            )
            logger.info("playwright_browser_started")
    return _browser


async def close_browser() -> None:
    global _playwright, _browser
    async with _lock:
        if _browser:
            await _browser.close()
            _browser = None
        if _playwright:
            await _playwright.stop()
            _playwright = None


@asynccontextmanager
async def new_context(
    extra_headers: dict | None = None,
    cookies: list[dict] | None = None,
    locale: str = "fr-CA",
) -> AsyncGenerator[BrowserContext, None]:
    """Yield a fresh stealth browser context."""
    browser = await get_browser()
    ua = random.choice(_USER_AGENTS)
    vp = random.choice(_VIEWPORTS)

    context = await browser.new_context(
        user_agent=ua,
        viewport=vp,
        locale=locale,
        timezone_id="America/Toronto",
        extra_http_headers=extra_headers or {},
        java_script_enabled=True,
        ignore_https_errors=False,
    )

    # Apply stealth patches directly (playwright-stealth may not be available in all envs)
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['fr-CA', 'fr', 'en-CA', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'permissions', {
            get: () => ({ query: async () => ({ state: 'granted' }) })
        });
    """)

    if cookies:
        await context.add_cookies(cookies)

    try:
        yield context
    finally:
        await context.close()


@asynccontextmanager
async def new_page(
    extra_headers: dict | None = None,
    cookies: list[dict] | None = None,
    locale: str = "fr-CA",
) -> AsyncGenerator[Page, None]:
    """Yield a new page inside a fresh stealth context."""
    async with new_context(extra_headers=extra_headers, cookies=cookies, locale=locale) as ctx:
        page = await ctx.new_page()
        yield page
