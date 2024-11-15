import logging  # Add this import
from functools import wraps
from typing import Optional
from sqlalchemy import text
from app.dao.database import async_session_maker
from app.config import settings

DATABASE_URL = settings.get_db_url()

# Configure logging if not already configured
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def connection(isolation_level: Optional[str] = None, commit: bool = True):
    """
    Декоратор для управления сессией с возможностью настройки уровня изоляции и коммита.
    Параметры:
    - `isolation_level`: уровень изоляции для транзакции (например, "SERIALIZABLE").
    - `commit`: если `True`, выполняется коммит после вызова метода.
    """
    def decorator(method):
        @wraps(method)
        async def wrapper(*args, **kwargs):
            async with async_session_maker() as session:
                try:
                    if isolation_level:
                        await session.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
                    result = await method(*args, session=session, **kwargs)
                    if commit:
                        await session.commit()
                    return result
                except Exception as e:
                    logger.error(f"Error in {method.__name__}: {e}")  # Add logging
                    await session.rollback()
                    raise
                finally:
                    await session.close()
        return wrapper
    return decorator
