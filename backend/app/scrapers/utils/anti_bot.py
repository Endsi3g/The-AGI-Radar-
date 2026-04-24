"""Anti-bot helpers: random delays, mouse simulation, scroll patterns."""
from __future__ import annotations

import asyncio
import random

from playwright.async_api import Page


async def random_delay(min_ms: float = 1500, max_ms: float = 4000) -> None:
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)


async def short_delay(min_ms: float = 400, max_ms: float = 900) -> None:
    await asyncio.sleep(random.uniform(min_ms, max_ms) / 1000)


async def human_scroll(page: Page, steps: int = 3) -> None:
    """Simulate human-like scrolling down the page."""
    for _ in range(steps):
        scroll_y = random.randint(200, 600)
        await page.mouse.wheel(0, scroll_y)
        await short_delay(300, 700)


async def human_mouse_move(page: Page) -> None:
    """Move mouse to a random position to appear human."""
    vp = page.viewport_size or {"width": 1280, "height": 800}
    x = random.randint(100, vp["width"] - 100)
    y = random.randint(100, vp["height"] - 100)
    await page.mouse.move(x, y)
    await short_delay(200, 500)


async def human_type(page: Page, selector: str, text: str) -> None:
    """Type text with randomised per-key delay to mimic human typing."""
    await page.click(selector)
    await short_delay()
    for char in text:
        await page.keyboard.type(char)
        await asyncio.sleep(random.uniform(0.05, 0.18))


async def safe_goto(
    page: Page,
    url: str,
    wait_until: str = "domcontentloaded",
    timeout: int = 30_000,
) -> bool:
    """Navigate to URL; return False on timeout/error instead of raising."""
    try:
        await page.goto(url, wait_until=wait_until, timeout=timeout)
        await random_delay(800, 1800)
        return True
    except Exception:
        return False


async def wait_for_selector_safe(
    page: Page,
    selector: str,
    timeout: int = 10_000,
) -> bool:
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False
