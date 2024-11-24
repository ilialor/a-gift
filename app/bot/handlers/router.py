import logging  
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from app.dao.dao import UserDAO
from app.bot.keyboards.kbs import main_keyboard
from app.dao.session_maker import connection 
from app.giftme.schemas import UserPydantic, ProfilePydantic, UserFilterPydantic, UserCreate
from app.twa.auth import TWAAuthManager  
from app.config import settings  
from app.utils.bot_instance import telegram_bot
from app.bot.handlers.payments import router as payments_router

auth_manager = TWAAuthManager(settings.secret_key)

router = Router()
router.include_router(payments_router)

@router.message(CommandStart())
@connection()
async def cmd_start(message: Message, session, **kwargs):  
    try:
        user_id = message.from_user.id
        logging.info(f"Received user_id: {user_id}")

        # Extract start parameters
        start_args = message.text.strip().split()
        start_param = start_args[1] if len(start_args) > 1 else None
        
        # Default welcome message
        welcome_text = (
            "🎮 Welcome to Giftme! 🧩\n\n"
            "Here you can create your gift lists and share them!\n\n"
            "Let's start! 🚀"
        )
        button_text = "Open GiftMe"

        # Base webapp URL
        webapp_url = f"{settings.BASE_SITE}/twa/"

        # Handle different start parameters
        if start_param:
            if start_param.startswith('startapp_'):
                # Parse the path, example: startapp_gifts_11
                parts = start_param.split('_')
                if len(parts) >= 3 and parts[1] == 'gifts':
                    gift_id = parts[2]
                    webapp_url = f"{settings.BASE_SITE}/twa/public/gifts/{gift_id}"
                    welcome_text = "Click button below to see the gift:"
                    button_text = "Open Gift"
            elif start_param.startswith('auth_'):
                # Handle auth redirects
                return_url = start_param[5:]
                if return_url:
                    webapp_url = f"{settings.BASE_SITE}{return_url}"

        # User auth logic
        filter_model = UserFilterPydantic(telegram_id=user_id)
        user_info = await UserDAO.find_one_or_none(session=session, filters=filter_model)

        if not user_info:
            # Create new user
            profile = ProfilePydantic(
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            values = UserCreate(
                telegram_id=user_id,
                username=message.from_user.username,
                profile=profile
            )
            user = await UserDAO.add(session=session, values=values)
            access_token = auth_manager.create_access_token(user.id)
            refresh_token = auth_manager.create_refresh_token(user.id)
            await UserDAO.update_refresh_token(session, user.id, refresh_token)
        else:
            access_token = auth_manager.create_access_token(user_info.id)
            refresh_token = auth_manager.create_refresh_token(user_info.id)
            await UserDAO.update_refresh_token(session, user_info.id, refresh_token)

        # Build webapp URL with auth params
        auth_params = f"startParam={access_token}&refresh_token={refresh_token}"
        webapp_url = f"{webapp_url}{'?' if '?' not in webapp_url else '&'}{auth_params}"

        # Create button with dynamic text
        login_btn = InlineKeyboardButton(
            text=button_text,
            web_app=WebAppInfo(url=webapp_url)
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[login_btn]])
        
        await message.answer(welcome_text, reply_markup=keyboard)

    except Exception as e:
        logging.error(f"Error in cmd_start: {e}")
        await message.answer("An error occurred. Please try again later.")
