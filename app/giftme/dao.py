from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.giftme.models import User, Profile, Gift, Payment, GiftList, UserList
import logging


class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none(cls, session: AsyncSession, filters: BaseModel):
        filter_dict = filters.model_dump(exclude_unset=True)
        try:
            query = select(cls.model).filter_by(**filter_dict)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise

    @classmethod
    async def add(cls, session: AsyncSession, values: BaseModel):
        values_dict = values.model_dump(exclude_unset=True)
        new_instance = cls.model(**values_dict)
        session.add(new_instance)
        try:
            await session.commit()
            return new_instance
        except SQLAlchemyError:
            await session.rollback()
            raise


class UserDAO(BaseDAO):
    model = User

    @classmethod
    async def get_user_with_profile(cls, session: AsyncSession, user_id: int):
        try:
            query = select(cls.model).options(selectinload(cls.model.profile)).where(cls.model.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError:
            raise


class ProfileDAO(BaseDAO):
    model = Profile


class GiftDAO(BaseDAO):
    model = Gift

    @classmethod
    async def get_gifts_by_owner(cls, session: AsyncSession, owner_id: int):
        try:
            query = select(cls.model).where(cls.model.owner_id == owner_id)
            result = await session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError:
            raise

    async def create_gift(self, gift_data: dict):
        logging.info(f"app\giftme\dao.py: Creating gift with data: {gift_data}")  # Log gift data
        gift = Gift(**gift_data)
        self.session.add(gift)
        await self.session.commit()
        await self.session.refresh(gift)
        logging.info(f"app\giftme\dao.py: Gift created with id: {gift.id}")  # Log gift ID
        return gift


class PaymentDAO(BaseDAO):
    model = Payment

    @classmethod
    async def get_payments_by_user(cls, session: AsyncSession, user_id: int):
        try:
            query = select(cls.model).where(cls.model.user_id == user_id)
            result = await session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError:
            raise


class GiftListDAO(BaseDAO):
    model = GiftList

    @classmethod
    async def get_giftlists_with_gifts(cls, session: AsyncSession, owner_id: int):
        try:
            query = select(cls.model).options(selectinload(cls.model.gifts)).where(cls.model.owner_id == owner_id)
            result = await session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError:
            raise


class UserListDAO(BaseDAO):
    model = UserList
