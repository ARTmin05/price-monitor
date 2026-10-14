"""Парсер каталога books.toscrape.com — учебного сайта, созданного для практики парсинга.

Обходит все категории и их страницы, собирает название, цену, рейтинг, наличие и ссылку.
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (price-monitor portfolio project)"


def fetch(url: str, retries: int = 3) -> BeautifulSoup:
    """Загружает страницу; при сетевой ошибке повторяет с паузой."""
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=20)
            response.raise_for_status()
            response.encoding = "utf-8"
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            if attempt == retries:
                raise
            logging.warning("Ошибка %s (%s), повтор через %s c", url, e, attempt * 2)
            time.sleep(attempt * 2)


def get_categories() -> dict[str, str]:
    """{название категории: ссылка на её первую страницу}"""
    soup = fetch(BASE_URL)
    return {
        a.get_text(strip=True): urljoin(BASE_URL, a["href"])
        for a in soup.select(".side_categories ul li ul li a")
    }


def parse_product(card, page_url: str, category: str) -> dict:
    link = card.select_one("h3 a")
    price_text = card.select_one(".price_color").get_text(strip=True)
    rating_class = card.select_one(".star-rating")["class"][1]
    url = urljoin(page_url, link["href"])
    return {
        "id": re.search(r"_(\d+)/index\.html", url).group(1),
        "title": link["title"],  # в тексте ссылки название обрезано, полное — в title
        "category": category,
        "price": float(re.sub(r"[^\d.]", "", price_text)),
        "rating": RATINGS.get(rating_class, 0),
        "in_stock": "In stock" in card.select_one(".availability").get_text(),
        "url": url,
    }


def scrape_category(category: str, url: str) -> list[dict]:
    products = []
    while url:
        soup = fetch(url)
        products += [parse_product(card, url, category) for card in soup.select("article.product_pod")]
        next_link = soup.select_one("li.next a")
        url = urljoin(url, next_link["href"]) if next_link else None
    return products


def scrape_all(workers: int = 5) -> list[dict]:
    """Собирает весь каталог; категории обходятся параллельно в несколько потоков."""
    categories = get_categories()
    logging.info("Категорий: %s", len(categories))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(lambda item: scrape_category(*item), categories.items())
    products = [p for chunk in results for p in chunk]
    logging.info("Собрано товаров: %s", len(products))
    return products
