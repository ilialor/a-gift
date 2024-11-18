import logging  
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from app.dao.dao import UserDAO
from app.bot.keyboards.kbs import main_keyboard, record_keyboard  # Удален импорт create_webapp_button
from app.dao.session_maker import connection 
from app.giftme.schemas import UserPydantic, ProfilePydantic, UserFilterPydantic
from app.twa.auth import TWAAuthManager  
from app.config import settings  

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

        logging.info(f"Access token: {access_token}")
        logging.info(f"Refresh token: {refresh_token}")

        webapp_url = f"{settings.BASE_SITE}?tgWebAppStartParam={access_token}&refresh_token={refresh_token}"
        logging.info(f"WebApp URL: {webapp_url}")
        
        webapp_btn = main_keyboard(webapp_url)  
        
        await message.answer("Welcome!", reply_markup=webapp_btn)

    except Exception as e:
        logging.error(f"Error in cmd_start: {e}")  
        await message.answer("Error. Please try again later.")


# @router.callback_query(F.data == 'show_my_record')
# @connection()
# async def get_user_rating(call: CallbackQuery, session, **kwargs):
#     await call.answer()

#     # Удаление старого сообщения
#     await call.message.delete()

#     # Получаем позицию пользователя в рейтинге
#     record_info = await UserDAO.get_user_rank(session=session, telegram_id=call.from_user.id)
#     rank = record_info['rank']
#     best_score = record_info['best_score']

#     # Определяем текст сообщения в зависимости от ранга
#     if rank == 1:
#         text = (
#             f"🥇 Поздравляем! Вы на первом месте с рекордом {best_score} очков! Вы — чемпион!\n\n"
#             "Держите планку и защищайте свой титул. Нажмите кнопку ниже, чтобы начать игру и "
#             "попробовать улучшить свой результат!"
#         )
#     elif rank == 2:
#         text = (
#             f"🥈 Великолепно! Вы занимаете второе место с результатом {best_score} очков!\n\n"
#             "Еще немного — и вершина ваша! Нажмите кнопку ниже, чтобы попробовать стать первым!"
#         )
#     elif rank == 3:
#         text = (
#             f"🥉 Отличный результат! Вы на третьем месте с {best_score} очками!\n\n"
#             "Почти вершина! Попробуйте свои силы еще раз, нажав кнопку ниже, и возьмите золото!"
#         )
#     else:
#         text = (
#             f"📊 Ваш рекорд: {best_score} очков. Вы находитесь на {rank}-ом месте в общем рейтинг��.\n\n"
#             "С каждым разом вы становитесь лучше! Нажмите кнопку ниже, чтобы попробовать "
#             "подняться выше и побить свой рекорд!"
#         )

    # Отправляем но��ое сообщение с текстом и клавиатурой
    # await call.message.answer(text, reply_markup=record_keyboard())
