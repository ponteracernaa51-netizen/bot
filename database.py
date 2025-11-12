import logging
import config
from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)
pool: AsyncConnectionPool = None

async def connect_db():
    global pool
    conninfo = (
        f"dbname='{config.DB_NAME}' "
        f"user='{config.DB_USER}' "
        f"password='{config.DB_PASS}' "
        f"host='{config.DB_HOST}' "
        f"port='{config.DB_PORT}'"
    )
    try:
        pool = AsyncConnectionPool(conninfo=conninfo, min_size=1, max_size=2, open=False)
        await pool.open()
        logger.info("Пул подключений к PostgreSQL успешно создан.")
    except Exception as e:
        logger.critical(f"Не удалось подключиться к PostgreSQL: {e}")
        pool = None

async def close_db_pool():
    if pool:
        await pool.close()
        logger.info("Пул подключений к PostgreSQL успешно закрыт.")

def row_to_dict(row, cursor):
    if row is None:
        return None
    return {desc[0]: value for desc, value in zip(cursor.description, row)}

async def get_random_phrase(topic: str, difficulty: str) -> dict | None:
    if not pool:
        logger.error("Пул подключений не инициализирован.")
        return None
    sql = f"SELECT * FROM {config.TABLE_PHRASES} WHERE topic = %s AND difficulty = %s ORDER BY RANDOM() LIMIT 1;"
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, (topic, difficulty))
                phrase_row = await cur.fetchone()
                return row_to_dict(phrase_row, cur)
    except Exception as e:
        logger.error(f"Ошибка при получении фразы из PostgreSQL: {e}")
        return None

async def update_user_stats(user_id: int, score: int):
    if not pool: return
    sql = f"INSERT INTO {config.TABLE_USER_STATS} (user_id, phrases_count, total_score) VALUES (%s, 1, %s) ON CONFLICT (user_id) DO UPDATE SET phrases_count = {config.TABLE_USER_STATS}.phrases_count + 1, total_score = {config.TABLE_USER_STATS}.total_score + %s;"
    try:
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(sql, (user_id, score, score))
    except Exception as e:
        logger.error(f"Ошибка обновления статистики для user_id={user_id}: {e}")