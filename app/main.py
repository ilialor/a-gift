import logging
import os  
from contextlib import asynccontextmanager

from app.bot.create_bot import bot, dp, stop_bot, start_bot
from app.bot.handlers.router import router as bot_router
from app.config import settings
from app.dao.dao import GiftDAO
from app.giftme.router import router as giftme_router
from app.twa.router import router as twa_router
from fastapi.staticfiles import StaticFiles
from aiogram.types import Update
from fastapi import FastAPI, Request
from app.middleware.auth import TelegramWebAppMiddleware
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Добавляем конфигурацию для корректной работы на Vercel
app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting bot setup...")
    dp.include_router(bot_router)
    await start_bot()
    webhook_url = settings.get_webhook_url()
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    logging.info(f"Webhook set to {webhook_url}")
    yield
    logging.info("Shutting down bot...")
    await bot.delete_webhook()
    await stop_bot()
    logging.info("Webhook deleted")

app = FastAPI(lifespan=lifespan)

app.add_middleware(TelegramWebAppMiddleware)

app.mount('/static', StaticFiles(directory='app/static'), 'static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers after adding middleware
app.include_router(giftme_router)
app.include_router(twa_router)

async def log_requests(request: Request, call_next):
    logging.info(f"Incoming request: method={request.method}, url={request.url}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code}")
    return response

@app.post("/webhook")
async def webhook(request: Request) -> None:
    logging.info("Received webhook request")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    logging.info("Update processed")

# Добавляем handler для корневого пути
@app.get("/")
async def root():
    return {"status": "ok", "message": "GiftMe Bot API is running"}

# Экспортируем handler для Vercel
handler = app
