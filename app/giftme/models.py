from typing import List
from sqlalchemy import ARRAY, JSON, ForeignKey, Integer, String, Table, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from database import Base, uniq_str_an
from enums import GenderEnum, ProfessionEnum  # Updated import

class Profile(Base):
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    age: Mapped[int | None]
    gender: Mapped[GenderEnum]
    profession: Mapped[ProfessionEnum] = mapped_column(
        default=ProfessionEnum.DEVELOPER,
        server_default=text("'UNEMPLOYED'")
    )
    interests: Mapped[List[str] | None] = mapped_column(ARRAY(String))
    contacts: Mapped[dict | None] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    user: Mapped['User'] = relationship('User', back_populates='profile')

class UserList(Base):
    name: Mapped[str] = mapped_column(unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    owner: Mapped['User'] = relationship('User', back_populates='lists')
    entries: Mapped[List['UserListEntry']] = relationship('UserListEntry', back_populates='list')

class UserListEntry(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey('userlists.id'), primary_key=True)
    related_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    related_user: Mapped['User'] = relationship('User', foreign_keys=[related_user_id])
    list: Mapped['UserList'] = relationship('UserList', back_populates='entries')

class User(Base):
    username: Mapped[uniq_str_an]
    email: Mapped[uniq_str_an]
    password: Mapped[str]
    profile: Mapped['Profile'] = relationship(
        'Profile',
        back_populates='user',
        uselist=False,
        lazy="joined",
        cascade='all, delete, delete-orphan'  # Added cascade options
    )
    
    lists: Mapped[List['UserList']] = relationship('UserList', back_populates='owner', cascade='all, delete')
    payments: Mapped[list['Payment']] = relationship('Payment', back_populates='user')

class Gift(Base):
    name: Mapped[str]
    description: Mapped[str]
    price: Mapped[float]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    owner: Mapped['User'] = relationship('User')

class Payment(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    amount: Mapped[float]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    user: Mapped['User'] = relationship('User', back_populates='payments')
