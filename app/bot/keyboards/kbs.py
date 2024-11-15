from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import settings


def main_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="🎮 Start", web_app=WebAppInfo(url=settings.BASE_SITE))
    kb.button(text="🏆 My gift lists", web_app=WebAppInfo(url=f"{settings.BASE_SITE}/giftlists"))
    # kb.button(text="📈 My friend lists", callback_data="show_my_record")

    kb.adjust(1)
    return kb.as_markup()


def record_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(text="🎮 Start", web_app=WebAppInfo(url=settings.BASE_SITE))
    kb.button(text="🏆 My gift lists", web_app=WebAppInfo(url=f"{settings.BASE_SITE}/giftlists"))
    # kb.button(text="🔄 My friend lists", callback_data="show_my_record")
    kb.adjust(1)
    return kb.as_markup()
