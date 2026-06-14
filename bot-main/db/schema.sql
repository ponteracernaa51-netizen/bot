-- ============================================================
-- Database schema for English Translation Bot
-- Run in Supabase SQL Editor (idempotent — safe to re-run)
-- ============================================================

-- ─── TOPICS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS topics (
    id         SERIAL PRIMARY KEY,
    name_ru    TEXT NOT NULL,
    name_uz    TEXT NOT NULL,
    emoji      TEXT DEFAULT '📚',
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── LEVELS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS levels (
    code        TEXT PRIMARY KEY,
    name_en     TEXT NOT NULL,
    description TEXT NOT NULL,
    sort_order  INT  DEFAULT 0,
    is_active   BOOLEAN DEFAULT TRUE
);

INSERT INTO levels (code, name_en, description, sort_order) VALUES
    ('A2', 'Elementary',       'Simple everyday phrases',              1),
    ('B1', 'Intermediate',     'Conversational English',               2),
    ('B2', 'Upper-Intermediate','Complex sentences and nuances',       3),
    ('C1', 'Advanced',         'Near-native fluency and precision',    4)
ON CONFLICT (code) DO UPDATE
    SET name_en     = EXCLUDED.name_en,
        description = EXCLUDED.description,
        sort_order  = EXCLUDED.sort_order;

-- ─── PHRASES ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS phrases (
    id                  SERIAL PRIMARY KEY,
    topic_id            INT  REFERENCES topics(id) ON DELETE CASCADE,
    text_ru             TEXT NOT NULL,
    text_uz             TEXT NOT NULL,
    english_answer      TEXT NOT NULL,
    alternative_answers JSONB DEFAULT '[]',
    phrase_key          TEXT,
    level               TEXT NOT NULL REFERENCES levels(code),
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE phrases
    ADD COLUMN IF NOT EXISTS alternative_answers JSONB DEFAULT '[]';

ALTER TABLE phrases
    ADD COLUMN IF NOT EXISTS phrase_key TEXT;

-- Back-fill phrase_key for existing rows
UPDATE phrases
SET phrase_key = lower(
    regexp_replace(
        regexp_replace(english_answer, '[^a-zA-Z0-9'' ]', ' ', 'g'),
        '\s+', ' ', 'g'
    )
)
WHERE phrase_key IS NULL;

-- ─── USERS ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username    TEXT,
    language    TEXT DEFAULT 'en',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── SCORES ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scores (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id)   ON DELETE CASCADE,
    phrase_id   INT REFERENCES phrases(id) ON DELETE SET NULL,
    user_answer TEXT NOT NULL,
    score       INT  NOT NULL CHECK (score BETWEEN 1 AND 100),
    errors_json JSONB DEFAULT '[]',
    feedback    TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── USER PHRASE HISTORY (уникальные фразы без повторов) ─────
-- Хранит какие фразы пользователь уже видел в разрезе topic+level.
-- Когда все фразы пройдены — история сбрасывается (бот начинает заново).
CREATE TABLE IF NOT EXISTS user_phrase_history (
    id        SERIAL PRIMARY KEY,
    user_id   INT  REFERENCES users(id)   ON DELETE CASCADE,
    phrase_id INT  REFERENCES phrases(id) ON DELETE CASCADE,
    topic_id  INT  NOT NULL,
    level     TEXT NOT NULL,
    seen_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ─── INDEXES ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_phrases_topic_level
    ON phrases(topic_id, level);

CREATE UNIQUE INDEX IF NOT EXISTS idx_phrases_unique_key
    ON phrases(topic_id, level, phrase_key)
    WHERE phrase_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_scores_user_id_created
    ON scores(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id
    ON users(telegram_id);

-- Уникальность: один пользователь видит каждую фразу один раз
CREATE UNIQUE INDEX IF NOT EXISTS idx_uph_user_phrase
    ON user_phrase_history(user_id, phrase_id);

-- Быстрый поиск непросмотренных фраз
CREATE INDEX IF NOT EXISTS idx_uph_user_topic_level
    ON user_phrase_history(user_id, topic_id, level);

-- ─── SEED TOPICS ─────────────────────────────────────────────
INSERT INTO topics (name_ru, name_uz, emoji) VALUES
    ('Семья',           'Oila',              '👨‍👩‍👧'),
    ('Еда и напитки',   'Ovqat va ichimlik', '🍎'),
    ('Работа и офис',   'Ish va ofis',       '💼'),
    ('Путешествия',     'Sayohat',           '✈️'),
    ('Здоровье',        'Sog''liq',          '🏥'),
    ('Технологии',      'Texnologiya',       '💻'),
    ('Природа',         'Tabiat',            '🌿'),
    ('Спорт',           'Sport',             '⚽'),
    ('Образование',     'Ta''lim',           '🎓'),
    ('Бизнес',          'Biznes',            '📊')
ON CONFLICT DO NOTHING;
