from sqlalchemy.ext.asyncio import AsyncSession
from database import connection
from models import Gift, UserListEntry, User

@connection
async def add_gift(name: str, description: str, price: float, owner_id: int, session: AsyncSession) -> int:
    gift = Gift(name=name, description=description, price=price, owner_id=owner_id)
    session.add(gift)
    await session.commit()
    return gift.id

@connection
async def add_user_to_list(user_id: int, list_id: int, related_user_id: int, session: AsyncSession) -> None:
    entry = UserListEntry(user_id=user_id, list_id=list_id, related_user_id=related_user_id)
    session.add(entry)
    await session.commit()

@connection
async def delete_user(user_id: int, session: AsyncSession) -> None:
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
