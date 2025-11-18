from typing import List, Optional
from datetime import time as datetime_time

from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert

from src.db.engine import async_session_factory
from src.db.models import (
    User,
    Topic,
    Level,
    Phrase,
    UserScore,
    UserTopicProgress,
)


async def get_or_create_user(telegram_id: int) -> User:
    """
    Retrieve a user by telegram_id. If not found, create a new one, add to session,
    commit, and return it.
    """
    async with async_session_factory() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


# src/db/repository.py

async def update_user(telegram_id: int, **kwargs) -> User | None:
    """
    Находит пользователя по telegram_id и обновляет его поля.
    Возвращает обновленный объект пользователя.
    """
    async with async_session_factory() as session:
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(**kwargs)
            .returning(User) # Эта строка важна для получения обновленного объекта
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()


async def get_user(telegram_id: int) -> Optional[User]:
    """
    Retrieve user data by telegram_id.
    """
    async with async_session_factory() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_topics() -> List[Topic]:
    """
    Retrieve a list of all topics.
    """
    async with async_session_factory() as session:
        stmt = select(Topic)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_levels() -> List[Level]:
    """
    Retrieve a list of all levels.
    """
    async with async_session_factory() as session:
        stmt = select(Level)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_next_phrase(user_id: int, topic_id: int, level_id: int) -> Optional[Phrase]:
    """
    Key function for sequential phrase delivery.
    1. Find last_phrase_id from UserTopicProgress for user_id and topic_id.
    2. If last_phrase_id found, query next phrase: Phrase.topic_id == topic_id,
       Phrase.level_id == level_id, Phrase.id > last_phrase_id, ordered by id, limit 1.
    3. If last_phrase_id not found, query first phrase: Phrase.topic_id == topic_id,
       Phrase.level_id == level_id, ordered by id, limit 1.
    4. Return Phrase object or None if phrases are exhausted.
    """
    async with async_session_factory() as session:
        # Step 1: Find last_phrase_id
        progress_stmt = select(UserTopicProgress.last_phrase_id).where(
            UserTopicProgress.user_id == user_id,
            UserTopicProgress.topic_id == topic_id,
        )
        progress_result = await session.execute(progress_stmt)
        last_phrase_id = progress_result.scalar_one_or_none()

        # Steps 2-3: Query next or first phrase
        phrase_stmt = select(Phrase).where(
            Phrase.topic_id == topic_id,
            Phrase.level_id == level_id,
        )
        if last_phrase_id is not None:
            phrase_stmt = phrase_stmt.where(Phrase.id > last_phrase_id)
        phrase_stmt = phrase_stmt.order_by(Phrase.id).limit(1)
        result = await session.execute(phrase_stmt)
        return result.scalar_one_or_none()


async def save_score(user_id: int, phrase_id: int, score: int) -> None:
    """
    Create a new record in UserScore.
    """
    async with async_session_factory() as session:
        stmt = insert(UserScore).values(user_id=user_id, phrase_id=phrase_id, score=score)
        await session.execute(stmt)
        await session.commit()


async def update_user_topic_progress(user_id: int, topic_id: int, phrase_id: int) -> None:
    """
    Update or create a record in UserTopicProgress with last_phrase_id.
    Uses upsert logic via PostgreSQL's on_conflict_do_update.
    """
    async with async_session_factory() as session:
        stmt = pg_insert(UserTopicProgress).values(
            user_id=user_id,
            topic_id=topic_id,
            last_phrase_id=phrase_id,
        ).on_conflict_do_update(
            index_elements=['user_id', 'topic_id'],
            set_={'last_phrase_id': phrase_id},
        )
        await session.execute(stmt)
        await session.commit()


async def get_user_average_score(user_id: int) -> float:
    """
    Calculate the average score for the user across all their UserScore records.
    Returns 0.0 if no scores exist.
    """
    async with async_session_factory() as session:
        stmt = (
            select(func.avg(UserScore.score))
            .where(UserScore.user_id == user_id)
            .scalar_subquery()
        )
        result = await session.execute(select(stmt))
        avg_score = result.scalar() or 0.0
        return float(avg_score)


async def get_phrases_for_repetition(user_id: int, topic_id: int, level_id: int) -> list[Phrase]:
    """
    Выбирает все фразы из текущей темы и уровня, у которых
    МАКСИМАЛЬНЫЙ балл пользователя < 90.
    """
    async with async_session_factory() as session:
        # 1. Создаем подзапрос: находим ID всех фраз, где макс. балл < 90
        subquery = (
            select(UserScore.phrase_id)
            .where(UserScore.user_id == user_id)
            .group_by(UserScore.phrase_id)
            .having(func.max(UserScore.score) < 90)
        ).scalar_subquery()

        # 2. Основной запрос: выбираем полные объекты фраз,
        #    ID которых есть в нашем подзапросе
        stmt = (
            select(Phrase)
            .where(
                Phrase.id.in_(subquery),
                Phrase.topic_id == topic_id,
                Phrase.level_id == level_id
            )
        )
        
        result = await session.execute(stmt)
        return result.scalars().all()


async def update_user_notifications(
    user_id: int, enabled: bool, notification_time: Optional[datetime_time] = None
) -> None:
    """
    Update notifications_enabled and optionally notification_time for the user.
    Note: Assumes user_id corresponds to User.id.
    """
    async with async_session_factory() as session:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(notifications_enabled=enabled, notification_time=notification_time)
        )
        await session.execute(stmt)
        await session.commit()


async def get_users_for_notification(current_time: datetime_time) -> List[int]:
    """
    Return list of telegram_id for users where notifications_enabled is True
    and notification_time matches current_time.
    """
    async with async_session_factory() as session:
        stmt = (
            select(User.telegram_id)
            .where(
                User.notifications_enabled.is_(True),
                User.notification_time == current_time,
            )
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]

# Добавьте эти три функции в ваш src/db/repository.py

async def get_user_by_id(user_id: int) -> User | None:
    """Получает данные пользователя по его ID в базе данных (PK)."""
    async with async_session_factory() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_topic_by_id(topic_id: int) -> Topic | None:
    """Получает данные темы по ее ID."""
    async with async_session_factory() as session:
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_level_by_id(level_id: int) -> Level | None:
    """Получает данные уровня по его ID."""
    async with async_session_factory() as session:
        stmt = select(Level).where(Level.id == level_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
# Добавьте эту функцию в src/db/repository.py

async def get_phrase_by_id(phrase_id: int) -> Phrase | None:
    """Получает объект фразы по ее ID."""
    async with async_session_factory() as session:
        stmt = select(Phrase).where(Phrase.id == phrase_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()