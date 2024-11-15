import asyncio
from datetime import datetime
import logging  
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select, text
from app.dao.dao import UserDAO, GiftDAO, GiftListDAO, UserListDAO
from app.dao.session_maker import async_session_maker
from pydantic import BaseModel
from app.giftme.models import Gift, Profile, UserList  

logging.basicConfig(level=logging.INFO)  

class UserListFilter(BaseModel):
    gift_list_id: int          
    added_user_id: int      

async def clear_userlists_dao():
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(text("DELETE FROM userlists"))
        logging.info("UserLists cleared.")
        print("UserLists cleared.")

async def clear_gift_lists_dao():
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(text("DELETE FROM giftlists"))
        logging.info("GiftLists cleared.")
        print("GiftLists cleared.")

async def clear_gifts_dao():
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(text("DELETE FROM gifts"))
        logging.info("Gifts cleared.")
        print("Gifts cleared.")

async def clear_users_dao():
    async with async_session_maker() as session:
        async with session.begin():
            await session.execute(text("DELETE FROM users"))
        logging.info("Users cleared.")
        print("Users cleared.")


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
            "date_of_birth": datetime.fromisoformat("1990-01-01T00:00:00"),  
            "interests": ["testing", "development"],
            "contacts": {"email": "testuser@example.com"}
        }
        user = await user_dao.add_user_with_profile(session, user_data)
        logging.info(f"Created User - Username: {user.username}, Email: {user.email}, Telegram ID: {user.telegram_id}")
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
                print(f"Profile Details: First Name - {profile.first_name}, Last Name - {profile.last_name}, Date of Birth - {profile.date_of_birth}")
            else:
                print("Associated profile does not exist.")
        else:
            print("Test user does not exist.")

async def delete_test_user_dao(user_id: int):
    async with async_session_maker() as session:
        user_dao = UserDAO(session)
        await user_dao.delete_user(user_id)
        logging.info(f"Deleted User - User ID: {user_id}")
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

async def create_test_gift_dao(user_id: int) -> Gift:
    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        gift_data = {
            "name": "Test Gift",
            "description": "A gift for testing.",
            "price": 19.99,
            "owner_id": user_id
        }
        gift = await gift_dao.create_gift(gift_data)
        logging.info(f"Created Gift - Name: {gift.name}, Description: {gift.description}, Price: {gift.price}, Owner ID: {gift.owner_id}")
        print("Test gift created.")
        return gift

async def check_test_gift_dao(gift_name: str):
    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        gift = await gift_dao.get_gift_by_name(gift_name)
        if gift:
            logging.info(f"Test gift with name {gift_name} exists.")
        else:
            print("Test gift does not exist.")

async def delete_test_gift_dao(gift_id: int):
    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        await gift_dao.delete_gift(gift_id)
        logging.info(f"Deleted Gift - Gift ID: {gift_id}")
        print("Test gift deleted.")

async def create_test_gift_list_dao(user_id: int) -> int:
    async with async_session_maker() as session:
        gift_list_dao = GiftListDAO(session)
        gift_list_data = {
            "name": "Test Gift List",
            "owner_id": user_id
        }
        gift_list = await gift_list_dao.create_gift_list(gift_list_data)
        logging.info(f"Created GiftList - Name: {gift_list.name}, Owner ID: {gift_list.owner_id}, List ID: {gift_list.id}")
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
        logging.info(f"Deleted GiftList - GiftList ID: {gift_list_id}")
        print("Test gift list deleted.")

async def create_test_user_list_dao(user_id: int, gift_list_id: int, added_user_id: int):
    logging.info(f"Creating UserList")
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        user_list_data = {
            "id": user_id + 1000,
            "user_id": user_id,
            "gift_list_id": gift_list_id,
            "added_user_id": added_user_id,
            "name": "Test List",
            "description": "This is a test user list."
        }
        logging.info(f"Adding UserList with id: {user_list_data['id']}")

        user_list = await user_list_dao.add_user_to_list(user_list_data)
        if user_list:
            logging.info(
                f"Added UserList - User ID: {user_list['user_id']}, "
                f"Gift List ID: {user_list['gift_list_id']}, "
                f"Added User ID: {user_list['added_user_id']}, "
                f"Name: {user_list['name']}, Description: {user_list['description']}"
            )
            print("User added to user list.")
            return user_list['id']
        else:
            print("Failed to add user to user list.")
            return None

async def check_test_user_list_dao(user_id: int, gift_list_id: int, added_user_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        filters = UserListFilter(
            gift_list_id=gift_list_id,
            added_user_id=added_user_id
        )
        user_list = await user_list_dao.find_one_or_none(session, filters=filters)
        if user_list:
            print("User is in the user list.")
        else:
            print("User is not in the user list.")

async def remove_test_user_list_dao(user_list_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        await user_list_dao.remove_user_from_list(user_list_id)
        logging.info(f"Removed UserList - ID: {user_list_id}")
        print("User list removed successfully.")

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

### Add new test functions for UserList using ID

async def test_remove_user_list_dao(user_list_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        await user_list_dao.remove_user_from_list(user_list_id)
        logging.info(f"Removed UserList - ID: {user_list_id}")
        print("User list removed successfully.")

async def test_update_user_list_dao(user_list_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        updated_name = "Updated Test List"
        updated_description = "This is an updated test user list."
        update_values = await user_list_dao.update_user_list(user_list_id, name=updated_name, description=updated_description)
        assert update_values.get('name') == updated_name
        assert update_values.get('description') == updated_description
        logging.info(f"Updated UserList - ID: {user_list_id}, Name: {updated_name}, Description: {updated_description}")
        print("User list updated successfully.")

async def test_get_user_list_by_id_dao(user_list_id: int):
    async with async_session_maker() as session:
        user_list_dao = UserListDAO(session)
        user_list = await user_list_dao.get_user_list_by_id(user_list_id)
        if user_list:
            print(f"Retrieved UserList - ID: {user_list['id']}, Name: {user_list['name']}, Description: {user_list['description']}")
        else:
            print("UserList not found.")

### Integrate the new test functions into the main workflow

async def main():
    await clear_userlists_dao()
    await clear_gift_lists_dao()
    await clear_gifts_dao()
    await clear_users_dao()

    await test_db_connection_dao()
    user_id = await create_test_user_dao()
    await check_test_user_dao()
    
    gift = await create_test_gift_dao(user_id)
    await check_test_gift_dao(gift.name)
    
    gift_list_id = await create_test_gift_list_dao(user_id)
    await check_test_gift_list_dao(gift_list_id)
    
    related_user_id = await create_related_user()
    user_list_id = await create_test_user_list_dao(user_id, gift_list_id, related_user_id)
    if user_list_id:
        await check_test_user_list_dao(user_id, gift_list_id, related_user_id)
        
        # New test cases using UserList ID
        await test_update_user_list_dao(user_list_id)
        await test_get_user_list_by_id_dao(user_list_id)
        await remove_test_user_list_dao(user_list_id)
    
    await delete_test_gift_list_dao(gift_list_id)
    await delete_test_gift_dao(gift.id)
    await delete_test_user_dao(user_id)
    await delete_test_user_dao(related_user_id)

if __name__ == "__main__":
    asyncio.run(main())
