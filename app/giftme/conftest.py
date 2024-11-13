# from typing import AsyncGenerator
# import uuid  # Add this import at the top
# import pytest
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.giftme.database import async_session_maker
# from models import GiftList

# @pytest.fixture
# async def session() -> AsyncGenerator[AsyncSession, None]:
#     async with async_session_maker() as session:
#         yield session

# @pytest.fixture
# async def user(session: AsyncSession) -> dict[str, int]:
#     username = f'test_user_{uuid.uuid4()}'
#     email = f'test_{uuid.uuid4()}@email.com'
#     password = 'password'
#     main_user_id = await create_main_user(
#         username=username,
#         email=email,
#         password=password,
#         session=session
#     )
#     return {'user_id': main_user_id}

# @pytest.fixture
# async def gift(session: AsyncSession, user: dict[str, int]) -> int:
#     gift_id = await add_gift(
#         name='Test Gift',
#         description='A gift for testing purposes',
#         price=50.0,
#         owner_id=user['user_id'],
#         session=session
#     )
#     return gift_id

# @pytest.fixture
# async def giftlist(session: AsyncSession, user: dict[str, int]) -> int:
#     gift_list = GiftList(name=f'list_{uuid.uuid4()}', owner_id=user['user_id'])
#     session.add(gift_list)
#     await session.commit()
#     return gift_list.id
