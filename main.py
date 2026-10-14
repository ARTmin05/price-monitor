"""Мониторинг цен: парсит каталог, сравнивает с прошлым запуском, сохраняет Excel и шлёт отчёт в Telegram.

Запуск:  python main.py            — собрать данные и отчёт
         python main.py --notify   — то же + уведомление в Telegram
"""

import argparse
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import compare
import export
import notify
import scraper

ROOT = Path(__file__).parent
SNAPSHOT = ROOT / "data" / "last_snapshot.json"
REPORTS = ROOT / "reports"


def main():
    parser = argparse.ArgumentParser(description="Price monitor")
    parser.add_argument("--notify", action="store_true", help="отправить отчёт в Telegram")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(ROOT / ".env")

    products = scraper.scrape_all()
    previous = compare.load_snapshot(SNAPSHOT)
    if previous is None:
        logging.info("Первый запуск — сравнивать не с чем, сохраняю базовый снимок")
        changes = []
    else:
        changes = compare.find_changes(previous, products)
        logging.info("Изменений: %s", len(changes))

    report = export.save_report(products, changes, REPORTS / f"report_{datetime.now():%Y-%m-%d_%H-%M-%S}.xlsx")
    compare.save_snapshot(products, SNAPSHOT)
    logging.info("Отчёт: %s", report)

    if args.notify:
        token, chat_id = os.getenv("BOT_TOKEN"), os.getenv("CHAT_ID")
        if not token or not chat_id:
            raise SystemExit("Для --notify заполните BOT_TOKEN и CHAT_ID в .env")
        notify.send(token, chat_id, notify.build_message(changes, len(products)), report)
        logging.info("Уведомление отправлено")


if __name__ == "__main__":
    main()
