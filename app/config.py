import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_NAME: str

    def get_db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = '.env'  # Specify your .env file path if needed
    
settings = Settings()
