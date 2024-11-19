from typing import Optional, List
from sqlalchemy import select, func, update as sa_update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.dao.base import BaseDAO
from app.giftme.models import Gift, GiftList, Payment, User, Profile, UserList
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

    @classmethod
    async def get_all_users(cls, session: AsyncSession):
        # Создаем запрос для выборки всех пользователей
        query = select(cls.model)

        # Выполняем запрос и получаем результат
        result = await session.execute(query)

        # Извлекаем записи как объекты модели
        records = result.scalars().all()

        # Возвращаем список всех пользователей
        return records

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


class UserListDAO(BaseDAO[UserList]):
    model = UserList

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
