from datetime import datetime, timezone
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram.types import Update, LabeledPrice
from sqlalchemy import text

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.dao.dao import UserDAO
from app.bot.create_bot import bot, dp

from app.giftme.schemas import GiftCreate, UserPydantic, ProfilePydantic

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

# Настройка базы данных
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class UserProfileCreate(BaseModel):
    user: dict
    profile: dict

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Получение пользователя по ID"""
    async with AsyncSessionLocal() as session:
        try:
            # Получаем пользователя и его профиль одним запросом
            query = text("""
                SELECT u.id, u.username, u.telegram_id, 
                       p.first_name, p.last_name
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                WHERE u.id = :user_id
            """)
            
            result = await session.execute(query, {"user_id": user_id})
            user_data = result.mappings().first()
            
            if not user_data:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "id": user_data["id"],
                "username": user_data["username"],
                "telegram_id": user_data["telegram_id"],
                "profile": {
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"]
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users")
async def create_user(user_data: UserProfileCreate):
    """Создание нового пользователя с профилем"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                # Проверяем существование пользователя
                check_query = text("""
                    SELECT id FROM users 
                    WHERE telegram_id = :telegram_id
                """)
                result = await session.execute(
                    check_query, 
                    {"telegram_id": user_data.user["telegram_id"]}
                )
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=409,
                        detail="User with this telegram_id already exists"
                    )

                # Создаем пользователя
                create_user_query = text("""
                    INSERT INTO users (username, telegram_id)
                    VALUES (:username, :telegram_id)
                    RETURNING id
                """)
                result = await session.execute(
                    create_user_query,
                    {
                        "username": user_data.user["username"],
                        "telegram_id": user_data.user["telegram_id"]
                    }
                )
                user_id = result.scalar_one()

                # Создаем профиль
                create_profile_query = text("""
                    INSERT INTO profiles (user_id, first_name, last_name)
                    VALUES (:user_id, :first_name, :last_name)
                """)
                await session.execute(
                    create_profile_query,
                    {
                        "user_id": user_id,
                        "first_name": user_data.profile["first_name"],
                        "last_name": user_data.profile.get("last_name")
                    }
                )

                await session.commit()

                return {
                    "id": user_id,
                    "username": user_data.user["username"],
                    "telegram_id": user_data.user["telegram_id"],
                    "profile": {
                        "first_name": user_data.profile["first_name"],
                        "last_name": user_data.profile.get("last_name")
                    }
                }

            except HTTPException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Проверка работоспособности сервиса"""
    try:
        db_config = {
            "user": os.getenv("DB_USER"),
            "host": os.getenv("DB_HOST"),
            "database": os.getenv("DB_NAME"),
        }
        db_status = "configured" if all(db_config.values()) else "not configured"
        
        return {
            "status": "healthy",
            "version": "1.0.5",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": db_status,
            "environment": os.getenv("VERCEL_ENV", "development")
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Health check failed")

# Эндпоинт для корневого пути
@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "GiftMe Bot API is running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Эндпоинты для работы с пользователями
# @app.post("/api/users")
# async def create_user(user: UserCreate, profile: ProfileCreate):
#     async with AsyncSessionLocal() as session:
#         try:
#             async with session.begin():
#                 query_user = text("""
#                     INSERT INTO users (username, telegram_id) 
#                     VALUES (:username, :telegram_id) 
#                     RETURNING id
#                 """)
#                 result = await session.execute(query_user, user.model_dump())
#                 user_id = result.scalar_one()
                
#                 query_profile = text("""
#                     INSERT INTO profiles (user_id, first_name, last_name) 
#                     VALUES (:user_id, :first_name, :last_name)
#                 """)
#                 await session.execute(query_profile, {
#                     "user_id": user_id,
#                     "first_name": profile.first_name,
#                     "last_name": profile.last_name
#                 })
                
#             return {"id": user_id, **user.model_dump()}
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=str(e))



# @app.get("/api/users/{user_id}")
# async def get_user(user_id: int):
#     async with AsyncSessionLocal() as session:
#         try:
#             query = text("""
#                 SELECT u.id, u.username, u.telegram_id, 
#                        p.first_name, p.last_name
#                 FROM users u
#                 LEFT JOIN profiles p ON u.id = p.user_id
#                 WHERE u.id = :user_id
#             """)
#             result = await session.execute(query, {"user_id": user_id})
#             user = result.mappings().first()
            
#             if not user:
#                 raise HTTPException(status_code=404, detail="User not found")
            
#             return {
#                 "id": user["id"],
#                 "username": user["username"],
#                 "telegram_id": user["telegram_id"],
#                 "profile": {
#                     "first_name": user["first_name"],
#                     "last_name": user["last_name"]
#                 }
#             }
#         except Exception as e:
#             raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gifts/{gift_id}")
async def get_gift(gift_id: int):
    async with AsyncSessionLocal() as session:
        try:
            query = text("""
                SELECT id, name, description, price, owner_id 
                FROM gifts 
                WHERE id = :gift_id
            """)
            result = await session.execute(query, {"gift_id": gift_id})
            gift = result.mappings().first()
            
            if not gift:
                raise HTTPException(status_code=404, detail="Gift not found")
            
            return gift
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/gifts")
async def get_user_gifts(user_id: int):
    async with AsyncSessionLocal() as session:
        try:
            query = text("""
                SELECT id, name, description, price, owner_id 
                FROM gifts 
                WHERE owner_id = :user_id
            """)
            result = await session.execute(query, {"user_id": user_id})
            gifts = result.mappings().all()
            
            return gifts
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
