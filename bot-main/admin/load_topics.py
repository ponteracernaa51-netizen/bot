"""
admin/load_topics.py

Загрузка тем в Supabase из CSV файла.

Формат CSV:
  name_ru,name_uz,emoji
  Семья,Oila,👨‍👩‍👧
  Еда,Ovqat,🍎

Запуск:
  python admin/load_topics.py topics.csv
"""

import sys
import csv
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")


def load_topics(csv_path: str):
    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Найдено {len(rows)} тем в файле")

    inserted = 0
    skipped = 0
    for row in rows:
        name_ru = row.get("name_ru", "").strip()
        name_uz = row.get("name_uz", "").strip()
        emoji   = row.get("emoji", "📚").strip()

        if not name_ru or not name_uz:
            print(f"  ⚠️  Пропускаю пустую строку: {row}")
            skipped += 1
            continue

        # Проверяем дубликат
        existing = db.table("topics").select("id").eq("name_ru", name_ru).execute()
        if existing.data:
            print(f"  ⏭️  Уже существует: {name_ru}")
            skipped += 1
            continue

        db.table("topics").insert({
            "name_ru": name_ru,
            "name_uz": name_uz,
            "emoji":   emoji,
        }).execute()
        print(f"  ✅ Добавлено: {emoji} {name_ru} / {name_uz}")
        inserted += 1

    print(f"\nГотово: добавлено {inserted}, пропущено {skipped}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python admin/load_topics.py <путь_к_csv>")
        sys.exit(1)
    load_topics(sys.argv[1])
