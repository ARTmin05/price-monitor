"""Уведомление в Telegram: краткая сводка изменений + Excel-отчёт файлом."""

import html
import logging
from collections import Counter
from pathlib import Path

import requests

ICONS = {"Price down": "📉", "Price up": "📈", "New": "🆕", "Removed": "❌",
         "Back in stock": "✅", "Out of stock": "⛔"}
LABELS = {"Price down": "подешевели", "Price up": "подорожали", "New": "новые",
          "Removed": "пропали", "Back in stock": "снова в наличии", "Out of stock": "закончились"}
MAX_LINES = 10


def _line(c: dict) -> str:
    title = html.escape(c["title"][:60])
    if "diff" in c:
        return f'{ICONS[c["type"]]} <a href="{c["url"]}">{title}</a>: £{c["old_price"]} → £{c["new_price"]}'
    return f'{ICONS[c["type"]]} <a href="{c["url"]}">{title}</a>'


def build_message(changes: list[dict], total: int) -> str:
    if not changes:
        return f"🔎 Мониторинг каталога: изменений нет.\nТоваров в каталоге: {total}"

    counts = Counter(c["type"] for c in changes)
    summary = "\n".join(f"{ICONS[t]} {LABELS[t]}: {n}" for t, n in counts.items())
    lines = "\n".join(_line(c) for c in changes[:MAX_LINES])
    more = f"\n…и ещё {len(changes) - MAX_LINES} — в отчёте" if len(changes) > MAX_LINES else ""
    return (f"🔔 <b>Мониторинг каталога: {len(changes)} изменений</b>\n\n{summary}\n\n"
            f"{lines}{more}\n\nТоваров в каталоге: {total}")


def send(token: str, chat_id: str, text: str, report: Path) -> None:
    api = f"https://api.telegram.org/bot{token}"
    try:
        requests.post(f"{api}/sendMessage", timeout=30, data={
            "chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True,
        }).raise_for_status()
        with report.open("rb") as f:
            requests.post(f"{api}/sendDocument", timeout=60, data={"chat_id": chat_id},
                          files={"document": (report.name, f)}).raise_for_status()
    except requests.RequestException as e:
        # токен попадает в URL — в лог пишем только тип ошибки
        logging.error("Не удалось отправить уведомление в Telegram: %s", type(e).__name__)
