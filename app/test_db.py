import asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text  
from app.dao.session_maker import async_session_maker
from app.giftme.models import User, Profile, Gift
from app.dao.dao import UserDAO, GiftDAO
from sqlalchemy.future import select  
from sqlalchemy.orm import selectinload  
from app.giftme.models import GiftList, UserList  

async def test_db_connection():
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))  
            print("Database connection successful.")
    except SQLAlchemyError as e:
        print(f"Database connection failed: {e}")

async def create_test_user():
    async with async_session_maker() as session:
        user = User(
            username="testuser2",
            email="testuser2@example.com",
            password="password123",
            telegram_id=123456780
        )
        profile = Profile(
            first_name="Test",
            last_name="User",
            age=30,
            interests=["testing", "development"],
            contacts={"email": "testuser@example.com"},
            user=user
        )
        session.add(user)
        await session.commit()
        print("Test user created and saved to the database.")
        return user.id  # Return the created user's ID

async def check_test_user():
    try:
        async with async_session_maker() as session:
            stmt = select(User).where(User.username == 'testuser2')
            result = await session.execute(stmt)
            user = result.scalars().first()
            if user:
                print("Test user exists.")
            else:
                print("Test user does not exist.")
    except SQLAlchemyError as e:
        print(f"Error checking test user: {e}")

async def delete_test_user(user_id: int):
    try:
        async with async_session_maker() as session:
            user = await session.get(User, user_id)  # Fetch the user by ID
            if user:
                await session.delete(user)
                await session.commit()
                print("Test user deleted.")
            else:
                print("Test user not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting test user: {e}")

async def create_test_gift(user_id: int):
    try:
        async with async_session_maker() as session:
            gift = Gift(
                name="Test Gift",
                description="A gift for testing.",
                price=9.99,
                owner_id=user_id 
            )
            session.add(gift)
            await session.commit()
            print("Test gift created.")
            return gift.id  
    except SQLAlchemyError as e:
        print(f"Error creating test gift: {e}")

async def check_gift():
    try:
        async with async_session_maker() as session:
            stmt = select(Gift).where(Gift.name == 'Test Gift')
            result = await session.execute(stmt)
            gift = result.scalars().first()
            if gift:
                print("Test gift exists.")
            else:
                print("Test gift does not exist.")
    except SQLAlchemyError as e:
        print(f"Error checking test gift: {e}")

async def delete_gift(gift_id: int):
    try:
        async with async_session_maker() as session:
            gift = await session.get(Gift, gift_id)
            if gift:
                await session.delete(gift)
                await session.commit()
                print("Test gift deleted.")
            else:
                print("Test gift not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting test gift: {e}")

async def create_test_gift_list(user_id: int) -> int:
    try:
        async with async_session_maker() as session:
            gift_list = GiftList(
                name="Test Gift List",
                owner_id=user_id
            )
            session.add(gift_list)
            await session.commit()
            print("Test gift list created.")
            return gift_list.id  # Return the created gift list's ID
    except SQLAlchemyError as e:
        print(f"Error creating test gift list: {e}")

async def add_gift_to_list(gift_list_id: int, gift_id: int):
    try:
        async with async_session_maker() as session:
            gift_list = await session.get(GiftList, gift_list_id)
            gift = await session.get(Gift, gift_id)
            if gift_list and gift:
                gift_list.gifts.append(gift)
                await session.commit()
                print("Gift added to the gift list.")
            else:
                print("Gift list or gift not found.")
    except SQLAlchemyError as e:
        print(f"Error adding gift to list: {e}")

async def check_gift_in_list(gift_list_id: int, gift_id: int):
    try:
        async with async_session_maker() as session:
            stmt = select(GiftList).where(GiftList.id == gift_list_id).options(
                selectinload(GiftList.gifts)
            )
            result = await session.execute(stmt)
            gift_list = result.scalars().first()
            if gift_list and any(g.id == gift_id for g in gift_list.gifts):
                print("Gift is in the gift list.")
            else:
                print("Gift is not in the gift list.")
    except SQLAlchemyError as e:
        print(f"Error checking gift in list: {e}")

async def remove_gift_from_list(gift_list_id: int, gift_id: int):
    try:
        async with async_session_maker() as session:
            gift_list = await session.get(GiftList, gift_list_id)
            gift = await session.get(Gift, gift_id)
            if gift_list and gift and gift in gift_list.gifts:
                gift_list.gifts.remove(gift)
                await session.commit()
                print("Gift removed from the gift list.")
            else:
                print("Gift or gift list not found, or gift not in the list.")
    except SQLAlchemyError as e:
        print(f"Error removing gift from list: {e}")

async def delete_gift_list(gift_list_id: int):
    try:
        async with async_session_maker() as session:
            gift_list = await session.get(GiftList, gift_list_id)
            if gift_list:
                await session.delete(gift_list)
                await session.commit()
                print("Test gift list deleted.")
            else:
                print("Test gift list not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting test gift list: {e}")

async def create_related_user():
    async with async_session_maker() as session:
        user = User(
            username="relateduser",
            email="relateduser@example.com",
            password="password123",
            telegram_id=123456789
        )
        session.add(user)
        await session.commit()
        print("Related user created and saved to the database.")
        return user.id  # Return the created related user's ID
    
async def create_user_list(user_id: int, gift_list_id: int, related_user_id: int):
    try:
        async with async_session_maker() as session:
            user_list = UserList(
                user_id=user_id,
                list_id=gift_list_id,
                related_user_id=related_user_id
            )
            session.add(user_list)
            await session.commit()
            print("User list created.")
            return user_list  # Return the UserList instance
    except SQLAlchemyError as e:
        print(f"Error creating user list: {e}")

async def add_user_to_user_list(user_id: int, gift_list_id: int, related_user_id: int):
    try:
        async with async_session_maker() as session:
            user_list = await session.execute(
                select(UserList).where(
                    UserList.user_id == user_id,
                    UserList.list_id == gift_list_id,
                    UserList.related_user_id == related_user_id
                )
            )
            user_list = user_list.scalar_one_or_none()
            if not user_list:
                user_list = UserList(
                    user_id=user_id,
                    list_id=gift_list_id,
                    related_user_id=related_user_id
                )
                session.add(user_list)
                await session.commit()
                print("User added to the user list.")
            else:
                print("User is already in the user list.")
    except SQLAlchemyError as e:
        print(f"Error adding user to user list: {e}")

async def check_user_in_user_list(user_id: int, gift_list_id: int, related_user_id: int):
    try:
        async with async_session_maker() as session:
            stmt = select(UserList).where(
                UserList.user_id == user_id,
                UserList.list_id == gift_list_id,
                UserList.related_user_id == related_user_id
            )
            result = await session.execute(stmt)
            user_list = result.scalars().first()
            if user_list:
                print("User is in the user list.")
            else:
                print("User is not in the user list.")
    except SQLAlchemyError as e:
        print(f"Error checking user in user list: {e}")

async def remove_user_from_user_list(user_id: int, gift_list_id: int, related_user_id: int):
    try:
        async with async_session_maker() as session:
            stmt = select(UserList).where(
                UserList.user_id == user_id,
                UserList.list_id == gift_list_id,
                UserList.related_user_id == related_user_id
            )
            result = await session.execute(stmt)
            user_list = result.scalars().first()
            if user_list:
                await session.delete(user_list)
                await session.commit()
                print("User removed from the user list.")
            else:
                print("User not found in the user list.")
    except SQLAlchemyError as e:
        print(f"Error removing user from user list: {e}")

async def delete_user_list(user_id: int, gift_list_id: int, related_user_id: int):
    try:
        async with async_session_maker() as session:
            user_list = await session.execute(
                select(UserList).where(
                    UserList.user_id == user_id,
                    UserList.list_id == gift_list_id,
                    UserList.related_user_id == related_user_id
                )
            )
            user_list = user_list.scalar_one_or_none()
            if user_list:
                await session.delete(user_list)
                await session.commit()
                print("User list deleted.")
            else:
                print("User list not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting user list: {e}")

async def main():
    await test_db_connection()
    user_id = await create_test_user()
    await check_test_user()
    gift_id = await create_test_gift(user_id)  # Capture the gift ID
    await check_gift()
    
    gift_list_id = await create_test_gift_list(user_id)  # Create and get gift list ID
    await add_gift_to_list(gift_list_id, gift_id)  # Add gift to the gift list
    await check_gift_in_list(gift_list_id, gift_id)  # Verify the gift is in the list
    
    # Add user to user list
    related_user_id = await create_related_user()  # Create a related user
    user_list = await create_user_list(user_id, gift_list_id, related_user_id)  # Create the user list with user_id
    await add_user_to_user_list(user_id, gift_list_id, related_user_id)  # Add the user to the list
    await check_user_in_user_list(user_id, gift_list_id, related_user_id)  # Verify the addition
    
    await remove_user_from_user_list(user_id, gift_list_id, related_user_id)  # Remove the user from the list
    await check_user_in_user_list(user_id, gift_list_id, related_user_id)  # Verify removal
    
    await delete_gift_list(gift_list_id)  # Delete the gift list
    await delete_gift(gift_id)  # Delete the gift
    await delete_user_list(user_id, gift_list_id, related_user_id)  # Delete the user list
    await delete_test_user(user_id)  # Delete the original test user
    await delete_test_user(related_user_id)  # Delete the related user

if __name__ == "__main__":
    asyncio.run(main())
