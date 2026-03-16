#!/usr/bin/env python3
"""Capture full-page screenshots of all key DepoHire pages."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE = "https://depohire.com"
OUT = Path(__file__).parent / "screenshots"
OUT.mkdir(exist_ok=True)

PAGES = [
    ("01-homepage", "/"),
    ("02-homepage-search-zip", "/", "zip"),
    ("03-city-page-new-york", "/new-york/"),
    ("04-city-page-filters", "/new-york/", "filters"),
    ("05-city-page-multi-select", "/new-york/", "multiselect"),
    ("06-listing-detail", "/listing/vanan-services-inc-new-york/"),
    ("07-listing-contact-form", "/listing/vanan-services-inc-new-york/", "scroll_form"),
    ("08-search-page", "/search/"),
    ("09-blog-index", "/blog/"),
    ("10-blog-post", "/blog/complete-guide-deposition-videographers/"),
    ("11-blog-city-cta", "/blog/complete-guide-deposition-videographers/", "scroll_cta"),
    ("12-states-all", "/states/all/"),
    ("13-state-page", "/states/california/"),
    ("14-pricing", "/pricing/"),
    ("15-advertise", "/advertise/"),
    ("16-about", "/about/"),
    ("17-statistics", "/statistics/"),
    ("18-privacy", "/privacy/"),
]


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await context.new_page()

        for entry in PAGES:
            name = entry[0]
            url = entry[1]
            action = entry[2] if len(entry) > 2 else None

            print(f"  Capturing {name}...")
            await page.goto(BASE + url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(1500)

            if action == "zip":
                # Type a zip code in the search bar
                search = page.locator("#smart-search")
                if await search.count() > 0:
                    await search.fill("90210")
                    await page.wait_for_timeout(2000)

            elif action == "filters":
                # Click the "Has Reviews" filter
                btn = page.locator('[data-filter="has-reviews"]')
                if await btn.count() > 0:
                    await btn.click()
                    await page.wait_for_timeout(500)

            elif action == "multiselect":
                # Check first 3 checkboxes
                checkboxes = page.locator(".select-quote-checkbox")
                count = await checkboxes.count()
                for i in range(min(3, count)):
                    await checkboxes.nth(i).check()
                    await page.wait_for_timeout(200)
                await page.wait_for_timeout(500)

            elif action == "scroll_form":
                # Scroll to the contact form
                form = page.locator("#contact-form-card")
                if await form.count() > 0:
                    await form.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)

            elif action == "scroll_cta":
                # Scroll to the city CTA section in blog
                cta = page.locator("#city-search")
                if await cta.count() > 0:
                    await cta.scroll_into_view_if_needed()
                    await page.wait_for_timeout(500)

            await page.screenshot(
                path=str(OUT / f"{name}.png"),
                full_page=(action not in ("zip", "filters", "multiselect", "scroll_form", "scroll_cta")),
            )

        await browser.close()
    print(f"\nDone! {len(PAGES)} screenshots saved to {OUT}")


asyncio.run(main())
