from datetime import datetime
from typing import Annotated, List

from sqlalchemy import Integer, func, Text, String, ARRAY
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, class_mapper
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from app.config import settings

# Обновлённый URL для Neon DB с поддержкой SSL
DATABASE_URL = settings.get_db_url()

# Создаем асинхронный движок для работы с базой данных с SSL настройками
engine = create_async_engine(
    url=DATABASE_URL,
    echo=True,  # Для логирования SQL запросов
    pool_size=20,  # Оптимальный размер пула для Neon
    max_overflow=10,  # Максимальное количество дополнительных соединений
    pool_timeout=30,  # Таймаут для получения соединения из пула
    pool_recycle=1800,  # Переподключение каждые 30 минут
    pool_pre_ping=True,  # Проверка соединения перед использованием    
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

uniq_str_an = Annotated[str, mapped_column(unique=True)]
content_an = Annotated[str | None, mapped_column(Text)]
array_or_none_an = Annotated[List[str] | None, mapped_column(ARRAY(String))]

# Базовый класс для всех моделей
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

    def to_dict(self) -> dict:
        """Универсальный метод для конвертации объекта SQLAlchemy в словарь"""
        columns = class_mapper(self.__class__).columns
        return {column.key: getattr(self, column.key) for column in columns}
