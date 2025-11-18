from datetime import datetime, time
from typing import Optional

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ==================== НАЧАЛО ИЗМЕНЕНИЙ ====================
# Заменяем `Base = DeclarativeBase()` на классовый синтаксис.
# Это современный и правильный способ для SQLAlchemy 2.0.
class Base(DeclarativeBase):
    pass
# ===================== КОНЕЦ ИЗМЕНЕНИЙ =====================


class User(Base):
    __tablename__ = "users"

    # Комментарии к полям для ясности
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    language_code: Mapped[str] = mapped_column(default="ru")
    topic_id: Mapped[Optional[int]] = mapped_column(ForeignKey("topics.id"))
    level_id: Mapped[Optional[int]] = mapped_column(ForeignKey("levels.id"))
    direction: Mapped[Optional[str]] = mapped_column()
    is_repeating_errors: Mapped[bool] = mapped_column(default=False)
    notifications_enabled: Mapped[bool] = mapped_column(default=False)
    notification_time: Mapped[Optional[time]] = mapped_column(Time)


class Level(Base):
    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_ru: Mapped[str]
    name_en: Mapped[str]
    name_uz: Mapped[str]


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_ru: Mapped[str]
    name_en: Mapped[str]
    name_uz: Mapped[str]


class Phrase(Base):
    __tablename__ = "phrases"

    id: Mapped[int] = mapped_column(primary_key=True)
    text_ru: Mapped[str]
    text_en: Mapped[str]
    text_uz: Mapped[str]
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    level_id: Mapped[int] = mapped_column(ForeignKey("levels.id"))

    # Связи для удобного доступа к объектам Topic и Level из объекта Phrase
    topic: Mapped["Topic"] = relationship(lazy="joined")
    level: Mapped["Level"] = relationship(lazy="joined")


class UserScore(Base):
    __tablename__ = "user_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    phrase_id: Mapped[int] = mapped_column(ForeignKey("phrases.id"))
    score: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    last_phrase_id: Mapped[int] = mapped_column(ForeignKey("phrases.id"))

    # Гарантирует, что для пары (user_id, topic_id) будет только одна запись
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="idx_user_topic"),)