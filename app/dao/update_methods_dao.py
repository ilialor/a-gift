import asyncio
# from pydantic import create_model
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.dao import UserDAO
from app.dao.session_maker import connection

# @connection(commit=True)
# async def update_username(session: AsyncSession, user_id: int, new_username: str):
#     ValueModel = create_model('ValueModel', username=(str, ...))
#     await UserDAO.add_user_with_profile(session=session, 
                                        ##"username": "bob_smith",
    # "email": "bob.smith@example.com",
    # "profile": {
    #     "first_name": "Bob",
    #     "last_name": "Smith",
    #     "age": 25,
    #     "gender": "мужчина",
    #     "profession": "дизайнер",
    #     "interests": ["gaming", "photography", "traveling"],
    #     "contacts": {
    #         "phone": "+987654321",
    #         "email": "bob.smith@example.com"
    #     }
    # }


                                        # data_id=user_id, values=ValueModel(username=new_username)
                                        # )

@connection(commit=True)
async def add_test_user(session: AsyncSession):
    user_data = {
        "username": "test_user",
        "email": "test_user@example.com",
        "password": "test_password",
        "first_name": "Test",
        "last_name": "User",
        "age": 30,
        "gender": "unknown",
        "profession": "Tester",
        "interests": ["testing", "automation"],
        "contacts": {
            "phone": "+123456789",
            "email": "test_user@example.com"
        }
    }
    await UserDAO.add_user_with_profile(session=session, user_data=user_data)

asyncio.run(add_test_user())
# asyncio.run(update_username(user_id=1, new_username='yakvenalexx'))
