import asyncio
import sys
from playwright.async_api import async_playwright

URL = "https://www.azurlane.tw/"


async def fetch_page(url: str) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, wait_until="networkidle")

        html = await page.content()
        await browser.close()
        return html


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else URL
    html = await fetch_page(url)
    print(html)


if __name__ == "__main__":
    asyncio.run(main())
