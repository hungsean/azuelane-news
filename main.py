import asyncio
import os

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

SCRAPE_URL = os.environ["SCRAPE_URL"]
POST_URL = os.environ["POST_URL"]
API_KEY = os.environ["API_KEY"]


async def fetch_page(url: str, wait_class: str) -> str:
    print("[fetch] 啟動瀏覽器...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"[fetch] 前往 {url}")
        await page.goto(url, wait_until="domcontentloaded")

        selector = f".{wait_class}"
        print(f"[fetch] 等待元素 {selector} 出現...")
        await page.wait_for_selector(selector, state="visible")
        print("[fetch] 元素已出現，擷取頁面內容")

        html = await page.content()
        await browser.close()
        print("[fetch] 完成，瀏覽器已關閉")
        return html

def parse_article_content(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find(class_="article-content")
    return article.get_text(strip=True) if article else None


def parse_news_items(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all(class_="news-item")
    return [item.find("a")["href"] for item in items if item.find("a")]


async def main():
    html = await fetch_page(SCRAPE_URL, "recent-news")
    news_items = parse_news_items(html)
    print(news_items)
    for news_item in news_items:
        article_html = await fetch_page(SCRAPE_URL + news_item, "article-content")
        content = parse_article_content(article_html)
        print(content)

if __name__ == "__main__":
    asyncio.run(main())
