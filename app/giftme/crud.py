from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database import connection, async_session_maker
from models import Gift, Payment, GiftList, UserList, User  # Updated imports
from sqlalchemy.orm import selectinload

@connection
async def add_gift(name: str, description: str, price: float, owner_id: int, *, session: AsyncSession) -> int:
    gift = Gift(name=name, description=description, price=price, owner_id=owner_id)
    session.add(gift)
    await session.commit()
    return gift.id

@connection
async def add_user_to_list(user_id: int, list_id: int, related_user_id: int, *, session: AsyncSession) -> None:
    entry = UserList(user_id=user_id, list_id=list_id, related_user_id=related_user_id)  
    session.add(entry)
    await session.commit()

@connection
async def delete_user(user_id: int, *, session: AsyncSession) -> None:
    try:
        user = await session.get(User, user_id)
        if user:
            await session.delete(user)
            await session.commit()
            print(f'Deleted user with ID {user_id} and cascaded profile.')
        else:
            print(f'User with ID {user_id} does not exist.')
    except Exception as e:
        await session.rollback()
        raise e

@connection
async def create_main_user(username: str, email: str, password: str, *, session: AsyncSession) -> int:
    try:
        main_user = User(username=username, email=email, password=password)
        session.add(main_user)
        await session.flush()
        await session.refresh(main_user)
        await session.commit()
        return main_user.id
    except Exception as e:
        await session.rollback()
        raise e

@connection
async def add_gift_to_list(gift_id: int, list_id: int, *, session: AsyncSession) -> None:
    gift_list = await session.get(GiftList, list_id)
    if gift_list:
        gift = await session.get(Gift, gift_id)
        if gift and gift not in gift_list.gifts:
            gift_list.gifts.append(gift)
            await session.commit()

@connection
async def send_gift_list(list_id: int, *, session: AsyncSession) -> list:
    gift_list = await session.get(GiftList, list_id)  # Updated class name
    if gift_list:
        return [gift.to_dict() for gift in gift_list.gifts]
    return []

@connection
async def process_payment(user_id: int, amount: float, *, session: AsyncSession) -> int:
    payment = Payment(user_id=user_id, amount=amount)
    session.add(payment)
    await session.commit()
    return payment.id

async def teardown():
    # Remove test users, profiles, gifts, lists, and payments
    async with async_session_maker() as session:
        try:
            # Delete from gift_list_gift first due to foreign key constraints
            await session.execute(
                text("DELETE FROM gift_list_gift WHERE giftlist_id IN (SELECT id FROM giftlists WHERE name LIKE 'list_%');")
            )
        except Exception as e:
            print(f"Skipping deletion from gift_list_gift table: {e}")

        try:
            await session.execute(
                text("DELETE FROM giftlists WHERE name LIKE 'list_%';")
            )
        except Exception as e:
            print(f"Skipping deletion from giftlists table: {e}")

        try:
            await session.execute(
                text("DELETE FROM gifts WHERE name = 'Test Gift';")
            )
        except Exception as e:
            print(f"Skipping deletion from Gift table: {e}")

        try:
            await session.execute(
                text("DELETE FROM payments WHERE amount = 100;")
            )
        except Exception as e:
            print(f"Skipping deletion from Payment table: {e}")
        
        try:
            await session.execute(
                text("DELETE FROM users WHERE username LIKE 'test_%' OR username LIKE 'main_%' OR username LIKE 'user_for_%' OR username LIKE 'delete_%';")
            )
        except Exception as e:
            print(f"Skipping deletion from User table: {e}")

        await session.commit()
