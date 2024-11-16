import logging  
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from app.dao.dao import UserDAO
from app.bot.keyboards.kbs import main_keyboard, record_keyboard
from app.dao.session_maker import connection 
from app.giftme.schemas import UserPydantic, ProfilePydantic, UserFilterPydantic

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
            await UserDAO.add(session=session, values=values)

        await message.answer(welcome_text, reply_markup=main_keyboard())

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
#             f"📊 Ваш рекорд: {best_score} очков. Вы находитесь на {rank}-ом месте в общем рейтинге.\n\n"
#             "С каждым разом вы становитесь лучше! Нажмите кнопку ниже, чтобы попробовать "
#             "подняться выше и побить свой рекорд!"
#         )

    # Отправляем новое сообщение с текстом и клавиатурой
    # await call.message.answer(text, reply_markup=record_keyboard())
