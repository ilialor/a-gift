import logging
import json
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
import sys

# Настройка логирования
logger = logging.getLogger("vercel_api")
logger.setLevel(logging.INFO)

# Добавляем вывод в stdout для Vercel
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI()

# Определяем путь к директории static
# static_dir = Path(__file__).parent / "static"
# static_dir.mkdir(exist_ok=True)  # Создаем директорию, если её нет

# # Монтируем статические файлы
# app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    logger.info(f"Client IP: {request.client.host}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    logger.info(f"Response status: {response.status_code}")
    return response

class UserCreate(BaseModel):
    username: str
    telegram_id: int

class ProfileCreate(BaseModel):
    first_name: str
    last_name: str | None = None

class GiftCreate(BaseModel):
    name: str
    description: str
    price: float
    owner_id: int

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "status": "ok",
        "message": "GiftMe Bot API is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health():
    logger.info("Health check endpoint called")
    try:
        # Проверяем наличие переменных окружения
        db_config = {
            "user": os.getenv("DB_USER"),
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
        }
        db_status = "configured" if all(db_config.values()) else "not configured"
        logger.info(f"Database status: {db_status}")
        
        response_data = {
            "status": "healthy",
            "version": "1.0.2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "environment": os.getenv("VERCEL_ENV", "development")
        }
        logger.info(f"Health check response: {json.dumps(response_data)}")
        return response_data
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Настройка подключения к базе данных
try:
    DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    engine = create_async_engine(DATABASE_URL, echo=True)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("Database connection configured successfully")
except Exception as e:
    logger.error(f"Failed to configure database connection: {str(e)}")

@app.post("/api/users")
async def create_user(user: UserCreate, profile: ProfileCreate):
    logger.info(f"Creating new user: {user.username}")
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                logger.debug(f"Starting user creation transaction")
                
                # Создаем пользователя
                query_user = text("""
                    INSERT INTO users (username, telegram_id) 
                    VALUES (:username, :telegram_id) 
                    RETURNING id
                """)
                result = await session.execute(query_user, user.model_dump())
                user_id = result.scalar_one()
                logger.info(f"Created user with ID: {user_id}")
                
                # Создаем профиль
                query_profile = text("""
                    INSERT INTO profiles (user_id, first_name, last_name) 
                    VALUES (:user_id, :first_name, :last_name)
                """)
                await session.execute(query_profile, {
                    "user_id": user_id,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name
                })
                logger.info(f"Created profile for user ID: {user_id}")
                
            return {"id": user_id, **user.model_dump()}
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gifts")
async def create_gift(gift: GiftCreate):
    logger.info(f"Creating new gift: {gift.name}")
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                query = text("""
                    INSERT INTO gifts (name, description, price, owner_id) 
                    VALUES (:name, :description, :price, :owner_id) 
                    RETURNING id, name, description, price, owner_id
                """)
                logger.debug(f"Executing gift creation query with data: {gift.model_dump()}")
                result = await session.execute(query, gift.model_dump())
                gift_data = result.mappings().one()
                logger.info(f"Created gift with ID: {gift_data['id']}")
            
            return gift_data
        except Exception as e:
            logger.error(f"Error creating gift: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
