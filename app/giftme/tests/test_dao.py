import unittest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from pydantic import BaseModel
from app.giftme.dao import (
    UserDAO,
    ProfileDAO,
    GiftDAO,
    PaymentDAO,
    GiftListDAO,
    UserListDAO
)
from app.giftme.models import User, Profile, Gift, Payment, GiftList, UserList
from app.dao.database import Base, engine
from app.giftme.schemas import UserPydantic, ProfilePydantic, UsernameIdPydantic
from app.dao.session_maker import async_session_maker

class AsyncTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Use the existing engine and async_session_maker from database.py
        self.engine = engine
        self.async_session = async_session_maker
        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        # Drop all tables and dispose engine
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

class TestUserDAO(AsyncTestCase):
    async def test_db_connection(self):
        # Use the real database connection
        async with async_session_maker() as session:
            # Test database connection
            result = await session.execute(text("SELECT 1"))
            self.assertEqual(result.scalar_one(), 1)
            # Retrieve and print all users
            users = await session.execute(select(User))
            users_list = users.scalars().all()
            print("All users:", users_list)
            res2 = await session.execute(select(User))
            print(res2.scalars().all())
            self.assertEqual(res2.scalars().all(), [])
            
    async def test_remove_all_users(self):
        async with self.async_session() as session:
            await session.execute(text("DELETE FROM users"))
            await session.commit()
            users = await UserDAO.get_all_users(session)
            self.assertEqual(users, [])

    async def test_add_user(self):
        # Test adding a new user
        async with self.async_session() as session:
            user_data = UserPydantic(
                username="testuser3",
                email="testuser3@example.com",
                password="securepassword"
            )
            user = await UserDAO.add(session, user_data)
            self.assertIsNotNone(user.id)
            self.assertEqual(user.username, "testuser3")

    async def test_find_one_or_none_user(self):
        # Test finding a user by filters
        async with self.async_session() as session:
            user_data = UserPydantic(
                username="testuser4",
                email="testuser4@example.com",
                password="securepassword"
            )
            await UserDAO.add(session, user_data)
            filters = UserPydantic(username="testuser4")
            user = await UserDAO.find_one_or_none(session, filters)
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "testuser4@example.com")
    
    # async def test_get_top_scores(self):
    #     # Test retrieving top scores
    #     async with self.async_session() as session:
    #         users = [
    #             User(username="user1", email="user1@example.com", password="pass1", best_score=100),
    #             User(username="user2", email="user2@example.com", password="pass2", best_score=200),
    #             User(username="user3", email="user3@example.com", password="pass3", best_score=150),
    #         ]
    #         session.add_all(users)
    #         await session.commit()

    #         top_scores = await UserDAO.get_top_scores(session, limit=2)
    #         self.assertEqual(len(top_scores), 2)
    #         self.assertEqual(top_scores[0]['best_score'], 200)
    #         self.assertEqual(top_scores[1]['best_score'], 150)
    
    # async def test_get_user_rank(self):
    #     # Test retrieving a user's rank
    #     async with self.async_session() as session:
    #         users = [
    #             User(username="user1", email="user1@example.com", password="pass1", best_score=100),
    #             User(username="user2", email="user2@example.com", password="pass2", best_score=200),
    #             User(username="user3", email="user3@example.com", password="pass3", best_score=150),
    #         ]
    #         session.add_all(users)
    #         await session.commit()

    #         user = await UserDAO.find_one_or_none(session, BaseModel(username="user3"))
    #         self.assertIsNotNone(user)

    #         rank = await UserDAO.get_user_rank(session, user.telegram_id)
    #         self.assertEqual(rank['rank'], 2)
    #         self.assertEqual(rank['best_score'], 150)

# class TestProfileDAO(AsyncTestCase):
#     async def test_add_profile(self):
#         # Test adding a new profile
#         async with self.async_session() as session:
#             user = User(username="profileuser", email="profileuser@example.com", password="pass123")
#             session.add(user)
#             await session.commit()

#             profile_data = ProfilePydantic(
#                 first_name="Profile",
#                 last_name="User",
#                 age=30
#             )
#             profile = await ProfileDAO.add(session, profile_data)
#             self.assertIsNotNone(profile.id)
#             self.assertEqual(profile.first_name, "Profile")
    
    # async def test_find_one_or_none_profile(self):
    #     # Test finding a profile by user_id
    #     async with self.async_session() as session:
    #         user = User(username="profileuser", email="profileuser@example.com", password="pass123")
    #         session.add(user)
    #         await session.commit()

    #         profile_data = BaseModel(
    #             first_name="Profile",
    #             last_name="User",
    #             age=30
    #         )
    #         await ProfileDAO.add(session, profile_data)

    #         filters = BaseModel(user_id=user.id)
    #         profile = await ProfileDAO.find_one_or_none(session, filters)
    #         self.assertIsNotNone(profile)
    #         self.assertEqual(profile.last_name, "User")

# class TestGiftDAO(AsyncTestCase):
#     async def test_add_gift(self):
#         # Test adding a new gift
#         async with self.async_session() as session:
#             gift_data = BaseModel(
#                 name="Teddy Bear",
#                 description="A soft teddy bear",
#                 price=25.99,
#                 owner_id=1
#             )
#             gift = await GiftDAO.add(session, gift_data)
#             self.assertIsNotNone(gift.id)
#             self.assertEqual(gift.name, "Teddy Bear")
    
#     async def test_get_gifts_by_owner(self):
#         # Test retrieving gifts by owner_id
#         async with self.async_session() as session:
#             gifts = [
#                 Gift(name="Teddy Bear", description="A soft teddy bear", price=25.99, owner_id=1),
#                 Gift(name="Chocolate Box", description="Assorted chocolates", price=15.99, owner_id=1),
#                 Gift(name="Flower Bouquet", description="Fresh flowers", price=20.99, owner_id=2),
#             ]
#             session.add_all(gifts)
#             await session.commit()

#             owner_gifts = await GiftDAO.get_gifts_by_owner(session, owner_id=1)
#             self.assertEqual(len(owner_gifts), 2)
#             self.assertTrue(all(g.owner_id == 1 for g in owner_gifts))

# class TestPaymentDAO(AsyncTestCase):
#     async def test_add_payment(self):
#         # Test adding a new payment
#         async with self.async_session() as session:
#             payment_data = BaseModel(
#                 user_id=1,
#                 amount=50.0
#             )
#             payment = await PaymentDAO.add(session, payment_data)
#             self.assertIsNotNone(payment.id)
#             self.assertEqual(payment.amount, 50.0)
    
#     async def test_get_payments_by_user(self):
#         # Test retrieving payments by user_id
#         async with self.async_session() as session:
#             payments = [
#                 Payment(user_id=1, amount=50.0),
#                 Payment(user_id=1, amount=75.0),
#                 Payment(user_id=2, amount=20.0),
#             ]
#             session.add_all(payments)
#             await session.commit()

#             user_payments = await PaymentDAO.get_payments_by_user(session, user_id=1)
#             self.assertEqual(len(user_payments), 2)
#             self.assertTrue(all(p.user_id == 1 for p in user_payments))

# class TestGiftListDAO(AsyncTestCase):
#     async def test_add_giftlist(self):
#         # Test adding a new gift list
#         async with self.async_session() as session:
#             giftlist_data = BaseModel(
#                 name="Birthday Gifts",
#                 owner_id=1
#             )
#             giftlist = await GiftListDAO.add(session, giftlist_data)
#             self.assertIsNotNone(giftlist.id)
#             self.assertEqual(giftlist.name, "Birthday Gifts")
    
#     async def test_get_giftlists_with_gifts(self):
#         # Test retrieving gift lists with associated gifts
#         async with self.async_session() as session:
#             giftlist = GiftList(name="Birthday Gifts", owner_id=1)
#             gifts = [
#                 Gift(name="Teddy Bear", description="A soft teddy bear", price=25.99, owner_id=1),
#                 Gift(name="Chocolate Box", description="Assorted chocolates", price=15.99, owner_id=1),
#             ]
#             giftlist.gifts.extend(gifts)
#             session.add(giftlist)
#             await session.commit()

#             giftlists_with_gifts = await GiftListDAO.get_giftlists_with_gifts(session, owner_id=1)
#             self.assertEqual(len(giftlists_with_gifts), 1)
#             self.assertEqual(giftlists_with_gifts[0].name, "Birthday Gifts")
#             self.assertEqual(len(giftlists_with_gifts[0].gifts), 2)

# class TestUserListDAO(AsyncTestCase):
#     async def test_add_user_to_list(self):
#         # Test adding a user to a gift list
#         async with self.async_session() as session:
#             user = User(username="user1", email="user1@example.com", password="pass1")
#             giftlist = GiftList(name="Holiday Gifts", owner_id=1)
#             session.add_all([user, giftlist])
#             await session.commit()

#             userlist_data = BaseModel(
#                 user_id=user.id,
#                 list_id=giftlist.id,
#                 related_user_id=2
#             )
#             await UserListDAO.add(session, userlist_data)

#             userlist = await UserListDAO.find_one_or_none(
#                 session,
#                 BaseModel(user_id=user.id, list_id=giftlist.id)
#             )
#             self.assertIsNotNone(userlist)
#             self.assertEqual(userlist.related_user_id, 2)

# class TestDatabaseCleanup(AsyncTestCase):
#     async def test_cleanup(self):
#         # Ensure the database is clean after tests
#         async with self.async_session() as session:
#             await session.execute(text("DELETE FROM users"))
#             await session.execute(text("DELETE FROM profiles"))
#             await session.execute(text("DELETE FROM gifts"))
#             await session.execute(text("DELETE FROM payments"))
#             await session.execute(text("DELETE FROM giftlists"))
#             await session.execute(text("DELETE FROM userlists"))
#             await session.commit()

#             # Verify all tables are empty
#             users = await session.execute(select(User))
#             self.assertEqual(len(users.scalars().all()), 0)
#             profiles = await session.execute(select(Profile))
#             self.assertEqual(len(profiles.scalars().all()), 0)
#             gifts = await session.execute(select(Gift))
#             self.assertEqual(len(gifts.scalars().all()), 0)
#             payments = await session.execute(select(Payment))
#             self.assertEqual(len(payments.scalars().all()), 0)
#             giftlists = await session.execute(select(GiftList))
#             self.assertEqual(len(giftlists.scalars().all()), 0)
#             userlists = await session.execute(select(UserList))
#             self.assertEqual(len(userlists.scalars().all()), 0)

if __name__ == "__main__":
    unittest.main()
