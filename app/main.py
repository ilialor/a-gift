import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from aiogram.types import Update
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.bot.create_bot import bot, dp, stop_bot, start_bot
from app.bot.handlers.router import router as bot_router
from app.config import settings
from app.giftme.router import router as giftme_router
from app.twa.router import router as twa_router
from app.middleware.auth import TelegramWebAppMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Контекстный менеджер жизненного цикла приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом бота"""
    try:
        logger.info("Starting bot setup...")
        dp.include_router(bot_router)
        await start_bot()
        
        # Устанавливаем вебхук только если мы не в режиме разработки
        if not settings.IS_DEV:
            webhook_url = settings.get_webhook_url()
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True
            )
            logger.info(f"Webhook set to {webhook_url}")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        
    yield  # Приложение работает
    
    try:
        logger.info("Shutting down bot...")
        if not settings.IS_DEV:
            await bot.delete_webhook()
        await stop_bot()
        logger.info("Bot shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Создаем приложение FastAPI
app = FastAPI(lifespan=lifespan)

# Add HTTPS redirect middleware in production
if not settings.IS_DEV:
    app.add_middleware(HTTPSRedirectMiddleware)

# Настройка для раздачи статических файлов с правильным путем
app.mount("/static", StaticFiles(directory="app/static", html=True, check_dir=True), name="static")

# Добавляем middleware
app.add_middleware(TelegramWebAppMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://web.telegram.org", "https://giftme-avalabs.amvera.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(giftme_router)
app.include_router(twa_router)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования запросов"""
    logger.info(f"Incoming request: method={request.method}, url={request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/webhook")
async def webhook(request: Request) -> None:
    """Обработчик вебхуков от Telegram"""
    try:
        logger.info("Received webhook request")
        update = Update.model_validate(await request.json(), context={"bot": bot})
        await dp.feed_update(bot, update)
        logger.info("Update processed successfully")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности"""
    return {
        "status": "healthy",
        "environment": "vercel" if not settings.IS_DEV else "development"
    }

# Экспортируем handler для Vercel
handler = app
