import asyncio
import os
import sqlite3
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

SCRAPE_URL = os.environ["SCRAPE_URL"]
POST_URL = os.environ["POST_URL"]
API_KEY = os.environ["API_KEY"]
DB_PATH = os.environ["DB_PATH"]


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            url TEXT PRIMARY KEY,
            title TEXT,
            published_at DATETIME,
            content TEXT,
            scraped_at DATETIME
        )
    """)
    conn.commit()
    return conn


def is_article_saved(conn: sqlite3.Connection, url: str) -> bool:
    return conn.execute("SELECT 1 FROM articles WHERE url = ?", (url,)).fetchone() is not None


def save_article(conn: sqlite3.Connection, url: str, title: str | None, published_at: str | None, content: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO articles (url, title, published_at, content, scraped_at) VALUES (?, ?, ?, ?, ?)",
        (url, title, published_at, content, datetime.now().isoformat()),
    )
    conn.commit()


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

def parse_article_details(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    title_section = soup.select_one('[class="news-detail-title"]')
    print("title section:", title_section)
    title = title_section.find("h2").get_text(strip=True) if title_section and title_section.find("h2") else None
    print("title: ", title)
    published_at = title_section.find(class_="date").get_text(strip=True) if title_section and title_section.find(class_="date") else None
    print("published_at: ", published_at)

    article = soup.find(class_="article-content")
    content = article.get_text(strip=True) if article else None

    return {"title": title, "published_at": published_at, "content": content}


def parse_news_items(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.find_all(class_="news-item")
    return [item.find("a")["href"] for item in items if item.find("a")]


async def main():
    conn = init_db(DB_PATH)

    html = await fetch_page(SCRAPE_URL, "recent-news")
    news_items = parse_news_items(html)
    print(news_items)

    for news_item in news_items:
        article_url = SCRAPE_URL + news_item
        if is_article_saved(conn, article_url):
            print(f"[skip] 已存在，跳過: {article_url}")
            continue

        article_html = await fetch_page(article_url, "article-content")
        details = parse_article_details(article_html)
        print(details)
        if details["content"]:
            save_article(conn, article_url, details["title"], details["published_at"], details["content"])
            print(f"[save] 已儲存: {article_url}")
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    POST_URL,
                    json={"url": article_url, **details},
                    headers={"X-Api-Key": API_KEY},
                )
                print(f"[post] 狀態碼: {resp.status_code}")
                await asyncio.sleep(5)


    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
