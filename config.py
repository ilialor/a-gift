import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str  # Add this line to get DATABASE_URL from environment
    BOT_TOKEN: str
    ADMIN_IDS: List[int]
    BASE_SITE: str
    SESSION_SECRET_KEY: str
    secret_key: str
    algorithm: str
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_PHONE: str

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    )

    def get_webhook_url(self) -> str:
        """Возвращает URL вебхука с кодированием специальных символов."""
        return f"{self.BASE_SITE}/webhook"
        
settings = Settings()
database_url = settings.DATABASE_URL  # Use DATABASE_URL directly



