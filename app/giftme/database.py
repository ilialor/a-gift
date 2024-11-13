from datetime import datetime
from typing import Annotated
from sqlalchemy import Integer, func, DateTime  
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

from config import settings

uniq_str_an = Annotated[str, mapped_column(unique=True)]
DATABASE_URL = settings.get_db_url()  # Uses the updated get_db_url from config.py

# Создаем асинхронный движок для работы с базой данных
engine = create_async_engine(url=DATABASE_URL)
# Создаем фабрику сессий для взаимодействия с базой данных
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех моделей
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True  # Класс абстрактный, чтобы не создавать отдельную таблицу для него

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

def connection(method):
    async def wrapper(*args, **kwargs):
        session = kwargs.get('session')
        if session is None:
            async with engine.begin() as conn:
                async with async_session_maker(bind=conn) as session:
                    try:
                        kwargs['session'] = session
                        return await method(*args, **kwargs)
                    except Exception as e:
                        await session.rollback()
                        raise e
        else:
            kwargs['session'] = session
            return await method(*args, **kwargs)
    return wrapper
