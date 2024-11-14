import asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text
from app.dao.dao import UserDAO, GiftDAO, GiftListDAO, UserListDAO
from app.dao.session_maker import async_session_maker
from pydantic import BaseModel
from app.giftme.models import Profile

class UserListFilter(BaseModel):
    user_id: int
    list_id: int
    related_user_id: int

async def test_db_connection_dao():
    try:
        async with async_session_maker() as session:
            user_dao = UserDAO(session)
            await user_dao.session.execute(text("SELECT 1"))  
            print("Database connection successful.")
    except SQLAlchemyError as e:
        print(f"Database connection failed: {e}")

async def create_test_user_dao():
    async with async_session_maker() as session:
        user_dao = UserDAO(session)
        user_data = {
            "username": "testuser2",
            "email": "testuser2@example.com",
            "password": "password123",
            "telegram_id": 123456780,
            "first_name": "Test",
            "last_name": "User",
            "age": 30,
            "interests": ["testing", "development"],
            "contacts": {"email": "testuser@example.com"}
        }
        user = await user_dao.add_user_with_profile(session, user_data)
        print("Test user with profile created and saved to the database.")
        return user.id

async def check_test_user_dao():
    async with async_session_maker() as session:
        user_dao = UserDAO(session)
        user = await user_dao.get_user_by_username("testuser2")
        if user:
            print("Test user exists.")
            # Check associated profile
            profile = await session.get(Profile, user.profile.id)
            if profile:
                print("Associated profile exists.")
                print(f"Profile Details: First Name - {profile.first_name}, Last Name - {profile.last_name}, Age - {profile.age}")
            else:
                print("Associated profile does not exist.")
        else:
            print("Test user does not exist.")

async def delete_test_user_dao(user_id: int):
    async with async_session_maker() as session:
        user_dao = UserDAO(session)
        await user_dao.delete_user(user_id)
        print("Test user deleted.")
        # Verify profile deletion
        profile = await session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        profile = profile.scalars().first()
        if not profile:
            print("Associated profile successfully deleted.")
        else:
            print("Associated profile was not deleted.")

async def create_test_gift_dao(user_id: int) -> int:
    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        gift_data = {
            "name": "Test Gift",
            "description": "A gift for testing.",
            "price": 19.99,
            "owner_id": user_id
        }
        gift = await gift_dao.create_gift(gift_data)
        print("Test gift created.")
        return gift.id

async def check_test_gift_dao(gift_id: int):
    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        gift = await gift_dao.get_gift_by_name("Test Gift")
        if gift:
            print("Test gift exists.")
        else:
            print("Test gift does not exist.")

async def delete_test_gift_dao(gift_id: int):
    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        await gift_dao.delete_gift(gift_id)
        print("Test gift deleted.")

async def create_test_gift_list_dao(user_id: int) -> int:
    async with async_session_maker() as session:
        gift_list_dao = GiftListDAO(session)
        gift_list_data = {
            "name": "Test Gift List",
            "owner_id": user_id
        }
        gift_list = await gift_list_dao.create_gift_list(gift_list_data)
        print("Test gift list created.")
        return gift_list.id

async def check_test_gift_list_dao(gift_list_id: int):
    async with async_session_maker() as session:
        gift_list_dao = GiftListDAO(session)
        gift_list = await gift_list_dao.find_one_or_none_by_id(gift_list_id, session)
        if gift_list:
            print("Test gift list exists.")
        else:
            print("Test gift list does not exist.")

async def delete_test_gift_list_dao(gift_list_id: int):
    async with async_session_maker() as session:
        gift_list_dao = GiftListDAO(session)
        await gift_list_dao.delete_gift_list(gift_list_id)
        print("Test gift list deleted.")

async def create_test_user_list_dao(user_id: int, gift_list_id: int, related_user_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        user_list_data = {
            "user_id": user_id,
            "list_id": gift_list_id,
            "related_user_id": related_user_id
        }
        user_list = await user_list_dao.add_user_to_list(user_list_data)
        print("User added to user list.")
        return user_list

async def check_test_user_list_dao(user_id: int, gift_list_id: int, related_user_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        filters = UserListFilter(
            user_id=user_id,
            list_id=gift_list_id,
            related_user_id=related_user_id
        )
        user_list = await user_list_dao.find_one_or_none(session, filters=filters)
        if user_list:
            print("User is in the user list.")
        else:
            print("User is not in the user list.")

async def remove_test_user_list_dao(user_id: int, gift_list_id: int, related_user_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        user_list_data = {
            "user_id": user_id,
            "list_id": gift_list_id,
            "related_user_id": related_user_id
        }
        await user_list_dao.remove_user_from_list(user_list_data)
        print("User removed from user list.")

async def create_related_user():
    async with async_session_maker() as session:
        user_dao = UserDAO(session)
        user_data = {
            "username": "relateduser",
            "email": "relateduser@example.com",
            "password": "password123",
            "telegram_id": 123456789
        }
        user = await user_dao.create_user(user_data)
        print("Related user created and saved to the database.")
        return user.id

async def main():
    await test_db_connection_dao()
    user_id = await create_test_user_dao()
    await check_test_user_dao()
    
    gift_id = await create_test_gift_dao(user_id)
    await check_test_gift_dao(gift_id)
    
    gift_list_id = await create_test_gift_list_dao(user_id)
    await check_test_gift_list_dao(gift_list_id)
    
    related_user_id = await create_related_user()
    user_list = await create_test_user_list_dao(user_id, gift_list_id, related_user_id)
    await check_test_user_list_dao(user_id, gift_list_id, related_user_id)
    
    await remove_test_user_list_dao(user_id, gift_list_id, related_user_id)
    await delete_test_gift_list_dao(gift_list_id)
    await delete_test_gift_dao(gift_id)
    await delete_test_user_dao(user_id)
    await delete_test_user_dao(related_user_id)
if __name__ == "__main__":    asyncio.run(main())
