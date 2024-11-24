from typing import List, Optional
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

class GiftDAO(BaseDAO[Gift]):
    model = Gift

    async def create_gift(self, gift_data: dict) -> Gift:
        """Create a new gift"""
        try:
            logging.info(f"Creating gift with data: {gift_data}")
            gift = Gift(**gift_data)
            self.session.add(gift)
            await self.session.commit()
            await self.session.refresh(gift)
            logging.info(f"Created gift with id: {gift.id}")
            return gift
        except Exception as e:
            logging.error(f"Error creating gift: {e}")
            await self.session.rollback()
            raise

    async def get_gift_by_name(self, name: str) -> Optional[Gift]:
        stmt = select(self.model).where(self.model.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_gift(self, gift_id: int):
        gift = await self.session.get(self.model, gift_id)
        if gift:
            await self.session.delete(gift)
            await self.session.commit()

    async def get_gifts_by_user_id(self, user_id: int) -> List[Gift]:
        stmt = select(self.model).where(self.model.owner_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    


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
