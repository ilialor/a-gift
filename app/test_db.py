import asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text  # Import text from sqlalchemy
from app.dao.session_maker import async_session_maker
from app.giftme.models import User, Profile, Gift
from app.dao.dao import UserDAO, GiftDAO
from sqlalchemy.future import select  # Add import for ORM select

async def test_db_connection():
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))  # Wrap the SQL statement with text()
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
                owner_id=user_id  # Use the actual user_id
            )
            session.add(gift)
            await session.commit()
            print("Test gift created.")
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

async def delete_gift():
    try:
        async with async_session_maker() as session:
            stmt = select(Gift).where(Gift.name == 'Test Gift')
            result = await session.execute(stmt)
            gift = result.scalars().first()
            if gift:
                await session.delete(gift)
                await session.commit()
                print("Test gift deleted.")
            else:
                print("Test gift not found.")
    except SQLAlchemyError as e:
        print(f"Error deleting test gift: {e}")

async def main():
    await test_db_connection()
    user_id = await create_test_user()
    await check_test_user()
    await create_test_gift(user_id)  # Pass the actual user_id
    await check_gift()
    await delete_gift()
    await delete_test_user(user_id)  # Pass the actual user_id

if __name__ == "__main__":
    asyncio.run(main())
