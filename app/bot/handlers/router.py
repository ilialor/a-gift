import logging  
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, LoginUrl
from app.dao.dao import UserDAO
from app.bot.keyboards.kbs import main_keyboard
from app.dao.session_maker import connection 
from app.giftme.schemas import UserPydantic, ProfilePydantic, UserFilterPydantic
from app.twa.auth import TWAAuthManager  
from app.config import settings  
from fastapi import Request  

auth_manager = TWAAuthManager(settings.secret_key)

router = Router()

@router.message(CommandStart())
@connection()
async def cmd_start(message: Message, session, **kwargs):  
    welcome_text = (
        "🎮 Welcome to Giftme! 🧩\n\n"
        "Here you can create your gift lists and share them!\n\n"
        "Let's start! 🚀"
    )

    try:
        user_id = message.from_user.id
        logging.info(f"Received user_id: {user_id}")  
        filter_model = UserFilterPydantic(telegram_id=user_id)  
        logging.info(f"Filter model: {filter_model.model_dump()}")  
        user_info = await UserDAO.find_one_or_none(session=session, filters=filter_model)

        if not user_info:
            profile = ProfilePydantic(
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            values = UserPydantic(
                telegram_id=user_id,
                username=message.from_user.username,
                profile=profile
            )
            logging.info(f"Creating new user with values: {values.model_dump()}") 
            user = await UserDAO.add(session=session, values=values)
            
            access_token = auth_manager.create_access_token(user.id)
            refresh_token = auth_manager.create_refresh_token(user.id)
            
            await UserDAO.update_refresh_token(session, user.id, refresh_token)

        else:
            access_token = auth_manager.create_access_token(user_info.id)
            refresh_token = auth_manager.create_refresh_token(user_info.id)
            
            await UserDAO.update_refresh_token(session, user_info.id, refresh_token)

        # Changed URL to point directly to index page with auth params
        webapp_url = f"{settings.BASE_SITE}/twa/?startParam={access_token}&refresh_token={refresh_token}"
        # login_url = LoginUrl(
        #     url=webapp_url,
        #     request_write_access=True
        # )
        login_btn = InlineKeyboardButton(text="Open Giftme", url=webapp_url)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[login_btn]])
        
        await message.answer(welcome_text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in cmd_start: {e}")
        await message.answer("An error occurred during authentication. Please try again later.")
