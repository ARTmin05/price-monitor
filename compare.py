"""Сравнение с прошлым запуском: новые и пропавшие товары, изменения цены и наличия."""

import json
from pathlib import Path


def load_snapshot(path: Path) -> dict[str, dict] | None:
    if not path.exists():
        return None
    return {p["id"]: p for p in json.loads(path.read_text(encoding="utf-8"))}


def save_snapshot(products: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(products, ensure_ascii=False, indent=1), encoding="utf-8")


def _change(kind: str, product: dict, **extra) -> dict:
    return {"type": kind, "title": product["title"], "category": product["category"],
            "url": product["url"], **extra}


def find_changes(old: dict[str, dict], products: list[dict]) -> list[dict]:
    new = {p["id"]: p for p in products}
    changes = []

    for pid, p in new.items():
        before = old.get(pid)
        if before is None:
            changes.append(_change("New", p, new_price=p["price"]))
            continue
        if p["price"] != before["price"]:
            diff = round(p["price"] - before["price"], 2)
            changes.append(_change("Price down" if diff < 0 else "Price up", p,
                                   old_price=before["price"], new_price=p["price"], diff=diff))
        if p["in_stock"] != before["in_stock"]:
            changes.append(_change("Back in stock" if p["in_stock"] else "Out of stock", p,
                                   new_price=p["price"]))

    for pid, p in old.items():
        if pid not in new:
            changes.append(_change("Removed", p, old_price=p["price"]))

    order = ["Price down", "Back in stock", "New", "Price up", "Out of stock", "Removed"]
    return sorted(changes, key=lambda c: order.index(c["type"]))
