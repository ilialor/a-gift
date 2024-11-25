from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from typing import AsyncGenerator
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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

class GiftResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    owner_id: int

@app.get("/")
async def root():
    return {"status": "ok", "message": "GiftMe Bot API is running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.1",
        "database": "configured"
    }

# Database config
DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}?sslmode=require"

# Create engine and session maker as module-level variables
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

@app.post("/api/users")
async def create_user(user: UserCreate, profile: ProfileCreate, session: AsyncSession = Depends(get_session)):
    try:
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
        
        await session.commit()
        return {"id": user_id, **user.model_dump()}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gifts", response_model=GiftResponse)
async def create_gift(gift: GiftCreate, session: AsyncSession = Depends(get_session)):
    try:
        query = text("""
            INSERT INTO gifts (name, description, price, owner_id) 
            VALUES (:name, :description, :price, :owner_id) 
            RETURNING id, name, description, price, owner_id
        """)
        result = await session.execute(query, gift.model_dump())
        gift_data = result.mappings().one()
        await session.commit()
        return GiftResponse(**gift_data)
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
