from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

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

@app.post("/api/gifts", response_model=GiftResponse)
async def create_gift(gift: GiftCreate):
    try:
        # Здесь будет интеграция с БД
        mock_response = GiftResponse(
            id=1,
            name=gift.name,
            description=gift.description,
            price=gift.price,
            owner_id=gift.owner_id
        )
        return mock_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
