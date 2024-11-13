import asyncio
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text  # Import text from sqlalchemy
from app.dao.session_maker import async_session_maker
from app.giftme.models import User, Profile
from app.dao.dao import UserDAO

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

async def main():
    await test_db_connection()
    await create_test_user()

if __name__ == "__main__":
    asyncio.run(main())
