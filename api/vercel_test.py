from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class GiftCreate(BaseModel):
    name: str
    description: str
    price: float
    owner_id: int

@app.post("/api/gifts")
async def create_gift(gift: GiftCreate):
    async with async_session() as session:
        try:
            query = "INSERT INTO gifts (name, description, price, owner_id) VALUES (:name, :description, :price, :owner_id) RETURNING id"
            result = await session.execute(query, gift.dict())
            gift_id = result.scalar_one()
            await session.commit()
            return {"id": gift_id, **gift.dict()}
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
