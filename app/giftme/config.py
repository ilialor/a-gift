# filepath: /d:/A-Gift/app/giftme/config.py
import logging  # Added import

from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv(Path(__file__).parent / ".env")

class Settings(BaseSettings):
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str

    def get_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = Path(__file__).parent / ".env"

settings = Settings()

# Add logging to confirm loaded settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info(f"Loaded settings: {settings.dict()}")
