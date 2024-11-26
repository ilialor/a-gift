from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
from aiogram.types import Update, LabeledPrice
from contextlib import asynccontextmanager
from app.bot.create_bot import bot, dp, stop_bot, start_bot
from app.bot.handlers.router import router as bot_router

# Базовая настройка FastAPI
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Контекстный менеджер жизненного цикла приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом бота"""
    try:
        dp.include_router(bot_router)
        await start_bot()
        
        # Устанавливаем вебхук только если мы не в режиме разработки
        if not os.getenv("IS_DEV"):
            webhook_url = f"{os.getenv('BASE_SITE')}/webhook"
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
    except Exception:
        pass
        
    yield
    
    try:
        if not os.getenv("IS_DEV"):
            await bot.delete_webhook()
        await stop_bot()
    except Exception:
        pass

# Модели данных
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

# Настройка базы данных
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?sslmode=require"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Базовые эндпоинты
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "GiftMe Bot API is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health")
async def health():
    try:
        db_config = {
            "user": os.getenv("DB_USER"),
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
        }
        db_status = "configured" if all(db_config.values()) else "not configured"
        
        return {
            "status": "healthy",
            "version": "1.0.3",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "environment": os.getenv("VERCEL_ENV", "development")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Эндпоинты для работы с пользователями
@app.post("/api/users")
async def create_user(user: UserCreate, profile: ProfileCreate):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                query_user = text("""
                    INSERT INTO users (username, telegram_id) 
                    VALUES (:username, :telegram_id) 
                    RETURNING id
                """)
                result = await session.execute(query_user, user.model_dump())
                user_id = result.scalar_one()
                
                query_profile = text("""
                    INSERT INTO profiles (user_id, first_name, last_name) 
                    VALUES (:user_id, :first_name, :last_name)
                """)
                await session.execute(query_profile, {
                    "user_id": user_id,
                    "first_name": profile.first_name,
                    "last_name": profile.last_name
                })
                
            return {"id": user_id, **user.model_dump()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# Эндпоинты для работы с подарками
@app.post("/api/gifts")
async def create_gift(gift: GiftCreate):
    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                query = text("""
                    INSERT INTO gifts (name, description, price, owner_id) 
                    VALUES (:name, :description, :price, :owner_id) 
                    RETURNING id, name, description, price, owner_id
                """)
                result = await session.execute(query, gift.model_dump())
                gift_data = result.mappings().one()
            
            return gift_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

# Webhook для Telegram бота
@app.post("/webhook")
async def webhook(request: Request) -> None:
    try:
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Эндпоинт для создания платежа
@app.post("/api/payments/{gift_id}/pay")
async def initiate_payment(gift_id: int, request: Request):
    try:
        async with AsyncSessionLocal() as session:
            # Получаем информацию о подарке
            query = text("SELECT * FROM gifts WHERE id = :gift_id")
            result = await session.execute(query, {"gift_id": gift_id})
            gift = result.mappings().first()
            
            if not gift:
                raise HTTPException(status_code=404, detail="Gift not found")

            # Получаем данные о пользователе
            query = text("SELECT telegram_id FROM users WHERE id = :user_id")
            result = await session.execute(query, {"user_id": gift['owner_id']})
            user = result.mappings().first()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Создаем инвойс для Telegram
            amount = int(float(gift['price']) * 100)  # Конвертируем в копейки
            
            await bot.send_invoice(
                chat_id=user['telegram_id'],
                title=f"🎁 {gift['name']}",
                description=f"Gift payment: {gift['name']}",
                payload=str(gift_id),
                provider_token="",  # Пустой для Stars
                currency="XTR",
                prices=[LabeledPrice(
                    label=f"Gift: {gift['name'][:20]}",
                    amount=amount
                )],
                start_parameter=f"gift_{gift_id}"
            )
            
            return {"status": "success", "message": "Payment initiated"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
