"""
Load ready-made practice phrases into Supabase from CSV.

CSV format:
topic_id,level,text_ru,text_uz,english_answer,alternative_answers
1,B1,Я опоздал на встречу.,Men uchrashuvga kech qoldim.,I was late for the meeting.,I arrived late for the meeting|I was late to the meeting
"""

import csv
import os
import re
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
ALLOWED_LEVELS = {"B1", "B2"}


def phrase_key(text: str) -> str:
    value = text.lower()
    value = re.sub(r"[^a-z0-9\s']", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def split_alternatives(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def load_phrases(csv_path: str) -> None:
    db = create_client(SUPABASE_URL, SUPABASE_KEY)

    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    inserted = 0
    skipped = 0
    for row in rows:
        topic_id = row.get("topic_id", "").strip()
        level = row.get("level", "").strip().upper()
        text_ru = row.get("text_ru", "").strip()
        text_uz = row.get("text_uz", "").strip()
        english_answer = row.get("english_answer", "").strip()
        alternatives = split_alternatives(row.get("alternative_answers", ""))

        if level not in ALLOWED_LEVELS:
            print(f"SKIP invalid level: {level}")
            skipped += 1
            continue
        if not topic_id or not text_ru or not text_uz or not english_answer:
            print(f"SKIP incomplete row: {row}")
            skipped += 1
            continue

        key = phrase_key(english_answer)
        existing = (
            db.table("phrases")
            .select("id")
            .eq("topic_id", int(topic_id))
            .eq("level", level)
            .eq("phrase_key", key)
            .limit(1)
            .execute()
        )
        if existing.data:
            print(f"SKIP duplicate: {english_answer}")
            skipped += 1
            continue

        if english_answer not in alternatives:
            alternatives.insert(0, english_answer)

        db.table("phrases").insert(
            {
                "topic_id": int(topic_id),
                "level": level,
                "text_ru": text_ru,
                "text_uz": text_uz,
                "english_answer": english_answer,
                "alternative_answers": alternatives,
                "phrase_key": key,
            }
        ).execute()
        print(f"OK {level}: {english_answer}")
        inserted += 1

    print(f"Done. inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python admin/load_phrases.py phrases.csv")
        sys.exit(1)
    load_phrases(sys.argv[1])
