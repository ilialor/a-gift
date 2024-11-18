import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings  # Import settings

bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


async def start_bot():
    logging.info("Bot started")
    try:
        for admin_id in settings.ADMIN_IDS:
            await bot.send_message(admin_id, f'Я запущен🥳.')
    except:
        pass


async def stop_bot():
    logging.info("Bot stopped")
    try:
        for admin_id in settings.ADMIN_IDS:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except:
        pass
