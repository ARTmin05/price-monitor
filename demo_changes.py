"""Демо: меняет сохранённый снимок, будто при прошлом запуске каталог был другим.

На учебном сайте цены не меняются, поэтому для демонстрации мониторинга
подправляем «вчерашние» данные. После этого запустите: python main.py --notify
"""

import json
import random

from main import SNAPSHOT

products = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
random.seed(7)
sample = random.sample(products, 12)

for p in sample[:4]:          # сегодня эти товары окажутся дешевле
    p["price"] = round(p["price"] * 1.25, 2)
for p in sample[4:6]:         # а эти — дороже
    p["price"] = round(p["price"] * 0.8, 2)
for p in sample[6:8]:         # «вчера» их не было в наличии
    p["in_stock"] = False
removed_ids = {p["id"] for p in sample[8:11]}   # «вчера» этих товаров не было → сегодня новые
products = [p for p in products if p["id"] not in removed_ids]
products.append({**sample[11], "id": "999999", "title": "Discontinued Book (demo)"})  # пропадёт

SNAPSHOT.write_text(json.dumps(products, ensure_ascii=False, indent=1), encoding="utf-8")
print("Снимок изменён. Теперь запустите: python main.py --notify")
