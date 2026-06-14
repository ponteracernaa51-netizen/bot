# English Translation Bot

Telegram bot for practicing translations from Russian or Uzbek into English.

AI phrase generation is removed. The bot uses only ready-made phrases saved in Supabase.
Translation checking remains deterministic.

Supported practice levels: `B1`, `B2`.

## Quick Start

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Telegram Controls

The bot registers Telegram commands in the input menu:

- `/practice` - choose a topic and start practice
- `/settings` - change direction or level
- `/stats` - show statistics
- `/repeat` - repeat the last phrase after mistakes
- `/help` - show available commands

The bot also shows persistent input buttons:

- `Practice`
- `Settings`
- `Statistics`
- `Repeat mistakes`

## Environment

```env
BOT_TOKEN=
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=

SEMANTIC_MODEL=sentence-transformers/all-MiniLM-L6-v2
ANTISPAM_WINDOW_SECONDS=2
ANTISPAM_MAX_EVENTS=4
PHRASE_SIMILARITY_THRESHOLD=75
```

Use `SUPABASE_SERVICE_ROLE_KEY` only on the backend. Do not expose it publicly.

## Database

Run `db/schema.sql` in Supabase SQL Editor.

The `phrases.level` column accepts only:

- `B1`
- `B2`

## Load Phrases

Create `phrases.csv`:

```csv
topic_id,level,text_ru,text_uz,english_answer,alternative_answers
1,B1,Я опоздал на встречу.,Men uchrashuvga kech qoldim.,I was late for the meeting.,I arrived late for the meeting|I was late to the meeting
1,B2,Если бы я знал об этом раньше, я бы предупредил тебя.,Agar buni oldinroq bilganimda, seni ogohlantirgan bo'lardim.,If I had known about it earlier, I would have warned you.,Had I known earlier, I would have warned you
```

Run:

```bash
python admin/load_phrases.py phrases.csv
```

## Architecture

```text
english_bot/
├── main.py
├── config.py
├── handlers/
│   ├── start.py
│   ├── translation.py
│   └── stats.py
├── services/
│   ├── generator.py      # loads saved phrases from DB
│   └── checker.py        # deterministic scoring, no AI calls
├── db/
│   ├── supabase_client.py
│   └── schema.sql
├── utils/
│   ├── antispam.py
│   └── keyboards.py
└── admin/
    ├── load_topics.py
    └── load_phrases.py
```

## Notes

- `sentence-transformers` downloads the semantic model on first use.
- `language-tool-python` may require Java depending on the environment.
- If optional validation engines are unavailable, the checker falls back to local heuristics.
