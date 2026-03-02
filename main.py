import asyncio
import os

import httpx
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

SCRAPE_URL = os.environ["SCRAPE_URL"]
POST_URL = os.environ["POST_URL"]
API_KEY = os.environ["API_KEY"]


async def fetch_page(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle")

        html = await page.content()
        await browser.close()
        return html


async def post_html(html: str) -> None:
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"url": SCRAPE_URL, "html": html}

    async with httpx.AsyncClient() as client:
        response = await client.post(POST_URL, json=payload, headers=headers)
        response.raise_for_status()


async def main():
    html = await fetch_page(SCRAPE_URL)
    await post_html(html)


if __name__ == "__main__":
    asyncio.run(main())
