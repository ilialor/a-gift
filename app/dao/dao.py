from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.base import BaseDAO
from app.giftme.models import Gift, GiftList, Payment, User, Profile, UserList


class UserDAO(BaseDAO[User]):
    model = User

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
            age=user_data.get('age'),
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

    async def add_user_to_list(self, user_list_data: dict) -> UserList:
        user_list = self.model(**user_list_data)
        self.session.add(user_list)
        await self.session.commit()
        return user_list

    async def remove_user_from_list(self, user_list_data: dict):
        stmt = select(self.model).where(
            self.model.user_id == user_list_data["user_id"],
            self.model.list_id == user_list_data["list_id"],
            self.model.related_user_id == user_list_data["related_user_id"]
        )
        result = await self.session.execute(stmt)
        user_list = result.scalars().first()
        if user_list:
            await self.session.delete(user_list)
            await self.session.commit()
