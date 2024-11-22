import logging
from typing import Optional, List
from sqlalchemy import select, func, update as sa_update, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.dao.base import BaseDAO
from app.giftme.models import Contact, Gift, GiftList, Payment, User, Profile, UserList
from app.giftme.schemas import UserFilterPydantic, UserPydantic


class UserDAO(BaseDAO[User]):
    model = User

    @staticmethod
    async def find_one_or_none(session: AsyncSession, filters: UserFilterPydantic) -> Optional[User]:
        result = await session.execute(select(User).filter_by(**filters.dict()))
        user = result.scalars().first()
        # logging.info(f"UserDAO.find_one_or_none found user: {user.to_dict() if user else 'None'}")
        return user

    @classmethod
    async def update_username_age_by_id(cls, session: AsyncSession, data_id: int, username: str, age: int):
        user = await session.get(cls.model, data_id)
        user.username = username
        user.profile.age = age
        await session.flush()

    @classmethod
    async def add_user_with_profile(cls, session: AsyncSession, user_data: dict) -> User:
        """
        Добавляет пользователя и привязанный к нему профиль.

        Аргументы:
        - session: AsyncSession - асинхронная сессия базы данных
        - user_data: dict - словарь с данными пользователя и профиля

        Возвращает:
        - User - объект пользователя
        """
        # Создаем пользователя из переданных данных
        user = cls.model(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            telegram_id=user_data['telegram_id']
        )
        session.add(user)
        await session.flush()  # Чтобы получить user.id для профиля

        # Создаем профиль, привязанный к пользователю
        profile = Profile(
            user_id=user.id,
            first_name=user_data['first_name'],
            last_name=user_data.get('last_name'),
            date_of_birth=user_data.get('date_of_birth'),
            interests=user_data.get('interests'),
            contacts=user_data.get('contacts')
        )
        session.add(profile)

        # Один коммит для обеих операций
        await session.commit()

        return user  # Возвращаем объект пользователя

    async def get_all_users(self) -> List[User]:
        """Get all users"""
        query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_username_id(cls, session: AsyncSession):
        # Создаем запрос для выборки id и username всех пользователей
        query = select(cls.model.id, cls.model.username)  # Указываем конкретные колонки
        print(query)  # Выводим запрос для отладки
        result = await session.execute(query)  # Выполняем асинхронный запрос
        records = result.all()  # Получаем все результаты
        return records  # Возвращаем список записей

    @staticmethod
    async def add(session: AsyncSession, values: UserPydantic) -> UserPydantic:
        user = User(
            telegram_id=values.telegram_id,
            username=values.username,
            email=values.email,
            profile=Profile(
                first_name=values.profile.first_name,
                last_name=values.profile.last_name,
                date_of_birth=values.profile.date_of_birth,
                interests=values.profile.interests,
                contacts=values.profile.contacts,
            ) if values.profile else None
        )
        session.add(user)
        await session.flush()
        await session.commit()
        return UserPydantic.from_orm(user)  # Return Pydantic model

    async def create_user(self, user_data: dict) -> User:
        user = self.model(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            telegram_id=user_data["telegram_id"]
        )
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        stmt = select(self.model).where(self.model.username == username)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def delete_user(self, user_id: int):
        user = await self.session.get(self.model, user_id)
        if user:
            await self.session.delete(user)
            await self.session.commit()

    async def get_user_with_calendars(self, username: str) -> Optional[User]:
        stmt = select(self.model).where(self.model.username == username).options(
            selectinload(self.model.own_calendars),
            selectinload(self.model.calendars)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def find_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
    
    @staticmethod
    async def update_refresh_token(session: AsyncSession, user_id: int, new_refresh_token: str) -> None:
        await session.execute(
            sa_update(User)
            .where(User.id == user_id)
            .values(refresh_token=new_refresh_token)
        )
        await session.commit()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        return await self.session.get(User, user_id)

    async def get_users_by_telegram_ids(self, telegram_ids: List[int]) -> List[User]:
        """Get users by their Telegram IDs"""
        query = select(self.model).where(self.model.telegram_id.in_(telegram_ids))
        result = await self.session.execute(query)
        return result.scalars().all()

class ProfileDAO(BaseDAO[Profile]):
    model = Profile


class PaymentDAO(BaseDAO[Payment]):
    model = Payment


class GiftDAO(BaseDAO[Gift]):
    model = Gift

    async def create_gift(self, gift_data: dict) -> Gift:
        gift = self.model(**gift_data)
        self.session.add(gift)
        await self.session.commit()
        return gift

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
        return result.scalars().all()  # Return a list of gifts       

    async def get_gift_with_lists(self, gift_id: int, session: AsyncSession):
        """Get a gift with its associated lists"""
        try:
            query = (
                select(self.model)
                .options(selectinload(self.model.lists))
                .where(self.model.id == gift_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logging.error(f"Error getting gift with lists: {e}")
            raise

    async def get_gift_by_id(self, gift_id: int) -> Optional[Gift]:
        """Retrieve a gift by its ID"""
        try:
            stmt = select(self.model).where(self.model.id == gift_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logging.error(f"Error retrieving gift by ID: {e}")
            return None

    async def mark_gift_as_paid(self, gift_id: int):
        gift = await self.get_gift_by_id(gift_id)
        gift.is_paid = True
        self.session.add(gift)
        await self.session.commit()

class GiftListDAO(BaseDAO[GiftList]):
    model = GiftList

    async def create_gift_list(self, gift_list_data: dict) -> GiftList:
        gift_list = self.model(**gift_list_data)
        self.session.add(gift_list)
        await self.session.commit()
        return gift_list

    async def delete_gift_list(self, gift_list_id: int):
        gift_list = await self.session.get(self.model, gift_list_id)
        if gift_list:
            await self.session.delete(gift_list)
            await self.session.commit()

    async def add_gift_to_list(self, list_id: int, gift_id: int) -> bool:
        """Add a gift to a gift list"""
        try:
            gift_list = await self.session.get(self.model, list_id)
            gift = await self.session.get(Gift, gift_id)
            
            if not gift_list or not gift:
                return False
                
            if gift not in gift_list.gifts:
                gift_list.gifts.append(gift)
                await self.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding gift to list: {e}")
            await self.session.rollback()
            return False

    async def remove_gift_from_list(self, list_id: int, gift_id: int) -> bool:
        """Remove a gift from a gift list"""
        try:
            gift_list = await self.session.get(self.model, list_id)
            gift = await self.session.get(Gift, gift_id)
            
            if not gift_list or not gift:
                return False
                
            if gift in gift_list.gifts:
                gift_list.gifts.remove(gift)
                await self.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error removing gift from list: {e}")
            await self.session.rollback()
            return False
        
    async def get_giftlists_with_gifts(self, owner_id: int):
        """Get all gift lists with their associated gifts for a specific owner"""
        try:
            query = (
                select(self.model)
                .options(
                    selectinload(self.model.gifts)
                )
                .where(self.model.owner_id == owner_id)
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting gift lists with gifts: {e}")
            raise


class UserListDAO(BaseDAO[UserList]):
    model = UserList

    async def create_user_list(self, user_list_data: dict) -> UserList:
        """Create a new user list with just name and user_id"""
        try:
            user_list = self.model(
                name=user_list_data["name"],
                user_id=user_list_data["user_id"]
                # description=user_list_data.get("description"),  # Optional
                # gift_list_id=user_list_data.get("gift_list_id"),  # Optional
                # added_user_id=user_list_data.get("added_user_id")  # Optional
            )
            self.session.add(user_list)
            await self.session.commit()
            await self.session.refresh(user_list)
            return user_list
        except SQLAlchemyError as e:
            await self.session.rollback()
            logging.error(f"Error creating user list: {e}")
            raise
    
    async def add_user_to_list(self, user_list_data: dict) -> Optional[dict]:
        """
        Adds a user to a user list with name and description using ORM.
        """
        try:
            # Fetch the current maximum ID
            result = await self.session.execute(select(func.max(UserList.id)))
            max_id = result.scalar() or 0
            new_id = max_id + 1

            user_list = self.model(
                id=new_id,  # Explicitly set the ID
                user_id=user_list_data["user_id"],
                gift_list_id=user_list_data["gift_list_id"],
                added_user_id=user_list_data["added_user_id"],
                name=user_list_data["name"],
                description=user_list_data.get("description")
            )
            self.session.add(user_list)
            await self.session.flush()  
            await self.session.commit()
            return user_list.to_dict() if user_list else None
        except SQLAlchemyError as e:
            await self.session.rollback()
            print(f"Error adding user to list: {e}")
            raise

    async def remove_user_from_list(self, user_list_id: int):
        """
        Removes a UserList by its ID.
        """
        try:
            user_list = await self.session.get(self.model, user_list_id)
            if user_list:
                await self.session.delete(user_list)
                await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            print(f"Error removing user from list: {e}")
            raise

    async def update_user_list(self, user_list_id: int, name: str = None, description: str = None) -> dict:
        """
        Updates the name and/or description of a UserList by its ID.
        """
        try:
            user_list = await self.session.get(self.model, user_list_id)
            if user_list:
                if name is not None:
                    user_list.name = name
                if description is not None:
                    user_list.description = description
                await self.session.flush()
                await self.session.commit()
                return {"name": user_list.name, "description": user_list.description}
            return {}
        except SQLAlchemyError as e:
            await self.session.rollback()
            print(f"Error updating user list: {e}")
            raise

    async def get_user_list_by_id(self, user_list_id: int) -> Optional[dict]:
        """
        Retrieves a UserList by its ID.
        """
        return await self.find_one_or_none_by_id(user_list_id, self.session)

    async def get_user_lists(self, user_id: int) -> List[UserList]:
        """Get all user lists where user is owner"""
        try:
            query = (
                select(self.model)
                .where(self.model.user_id == user_id)
                .options(
                    selectinload(self.model.added_user),
                )
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting user lists: {e}")
            raise

    async def toggle_member(self, list_id: int, is_active: bool) -> bool:
        """Toggle member status in the list"""
        try:
            user_list = await self.session.get(self.model, list_id)
            if user_list:
                user_list.description = 'active' if is_active else 'inactive'
                await self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            logging.error(f"Error toggling member status: {e}")
            await self.session.rollback()
            return False

class ContactDAO(BaseDAO[Contact]):
    model = Contact

    async def get_user_contacts(self, user_id: int) -> List[Contact]:
        """Get user's contacts"""
        try:
            query = (
                select(self.model)
                .where(self.model.user_id == user_id)
                .options(selectinload(self.model.user))
            )
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting user contacts: {e}")
            raise

    async def add_contact(self, contact_data: dict) -> Optional[Contact]:
        """Add a new contact"""
        try:
            contact = self.model(**contact_data)
            self.session.add(contact)
            await self.session.commit()
            await self.session.refresh(contact)
            return contact
        except SQLAlchemyError as e:
            await self.session.rollback()
            logging.error(f"Error adding contact: {e}")
            raise

    async def remove_contact(self, user_id: int, contact_id: int) -> bool:
        """Remove contact if it belongs to user"""
        try:
            contact = await self.session.get(self.model, contact_id)
            if contact and contact.user_id == user_id:
                await self.session.delete(contact)
                await self.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            await self.session.rollback()
            logging.error(f"Error removing contact: {e}")
            raise

    async def get_contact_by_telegram_id(self, user_id: int, telegram_id: int) -> Optional[Contact]:
        """
        Найти контакт по Telegram ID
        
        Args:
            user_id: ID пользователя, которому принадлежит контакт
            telegram_id: Telegram ID искомого контакта
        """
        try:
            result = await self.session.execute(
                select(self.model).where(
                    and_(
                        self.model.user_id == user_id,
                        self.model.contact_telegram_id == telegram_id
                    )
                )
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logging.error(f"Error getting contact by telegram_id: {e}")
            raise
