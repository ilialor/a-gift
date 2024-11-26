import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(title="GiftMe Test API")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Конфигурация базы данных
def get_database_url() -> str:
    """Формирует URL подключения к базе данных"""
    db_params = {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'name': os.getenv('DB_NAME'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    # Проверяем наличие всех необходимых параметров
    missing_params = [k for k, v in db_params.items() if not v]
    if missing_params:
        raise ValueError(f"Missing required database parameters: {', '.join(missing_params)}")
        
    return (
        f"postgresql+asyncpg://{db_params['user']}:{db_params['password']}@"
        f"{db_params['host']}:{db_params['port']}/{db_params['name']}"
    )

try:
    DATABASE_URL = get_database_url()
    engine = create_async_engine(
        DATABASE_URL,
        echo=True,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_pre_ping=True
    )
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("Database engine initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database engine: {e}")
    raise

class EnvironmentInfo(BaseModel):
    python_version: str
    environment_variables: Dict[str, str]
    current_directory: str
    sys_path: list[str]

class DatabaseTestResult(BaseModel):
    connection_successful: bool
    tables_found: Optional[list[str]] = None
    error_message: Optional[str] = None

@app.get("/")
async def root():
    """Базовый эндпоинт для проверки работоспособности"""
    return {
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/environment")
async def get_environment_info() -> EnvironmentInfo:
    """Получение информации об окружении"""
    # Фильтруем конфиденциальные переменные окружения
    safe_env = {
        k: v for k, v in os.environ.items() 
        if not any(secret in k.lower() for secret in ['password', 'secret', 'token', 'key'])
    }
    
    return EnvironmentInfo(
        python_version=sys.version,
        environment_variables=safe_env,
        current_directory=os.getcwd(),
        sys_path=sys.path
    )

@app.get("/database/test")
async def test_database_connection() -> DatabaseTestResult:
    """Тестирование подключения к базе данных"""
    try:
        async with async_session() as session:
            # Проверяем подключение
            await session.execute(text("SELECT 1"))
            
            # Получаем список таблиц
            result = await session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            
            return DatabaseTestResult(
                connection_successful=True,
                tables_found=tables
            )
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return DatabaseTestResult(
            connection_successful=False,
            error_message=str(e)
        )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования запросов"""
    start_time = datetime.utcnow()
    try:
        response = await call_next(request)
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Duration: {duration:.3f}s"
        )
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url.path} Error: {str(e)}")
        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Глобальный обработчик исключений"""
    logger.error(f"Global error handler caught: {str(exc)}", exc_info=True)
    return {
        "error": True,
        "message": str(exc),
        "path": request.url.path,
        "timestamp": datetime.utcnow().isoformat()
    }

# Экспортируем для Vercel
handler = app
