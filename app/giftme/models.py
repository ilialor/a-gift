from typing import List
from sqlalchemy import ARRAY, JSON, ForeignKey, Integer, String, Table, Enum, text, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from database import Base, uniq_str_an

class User(Base):
    username: Mapped[uniq_str_an]
    email: Mapped[uniq_str_an]
    password: Mapped[str]
    profile: Mapped['Profile'] = relationship(
        'Profile',
        back_populates='user',
        uselist=False,
        lazy="joined",
        cascade='all, delete, delete-orphan'  
    )    
    lists: Mapped[List['GiftList']] = relationship('GiftList', back_populates='owner', cascade='all, delete')  # Updated reference
    payments: Mapped[list['Payment']] = relationship(
        'Payment', 
        back_populates='user',
        cascade='all, delete-orphan'  
    )

class Profile(Base):
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    age: Mapped[int | None]
    interests: Mapped[List[str] | None] = mapped_column(ARRAY(String))
    contacts: Mapped[dict | None] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    user: Mapped['User'] = relationship('User', back_populates='profile')

class GiftList(Base):
    name: Mapped[str] = mapped_column(unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    owner: Mapped['User'] = relationship('User', back_populates='lists')
    entries: Mapped[List['UserList']] = relationship('UserList', back_populates='list')
    gifts: Mapped[List['Gift']] = relationship(
        'Gift',
        secondary='gift_list_gift',
        back_populates='lists',
        lazy='selectin'  # Set lazy loading strategy for async
    )

class UserList(Base):  
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey('giftlists.id'), primary_key=True)  # Updated reference
    related_user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    related_user: Mapped['User'] = relationship('User', foreign_keys=[related_user_id])
    list: Mapped['GiftList'] = relationship('GiftList', back_populates='entries')  # Updated reference

class Gift(Base):
    name: Mapped[str]
    description: Mapped[str]
    price: Mapped[float]
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    owner: Mapped['User'] = relationship('User')
    lists: Mapped[List['GiftList']] = relationship(
        'GiftList',
        secondary='gift_list_gift',
        back_populates='gifts',
        lazy='selectin'  # Set lazy loading strategy for async
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "owner_id": self.owner_id,
        }

class Payment(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    amount: Mapped[float]
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    user: Mapped['User'] = relationship('User', back_populates='payments')

# Association table for GiftList and Gift
gift_list_gift = Table(
    'gift_list_gift',
    Base.metadata,
    Column('giftlist_id', ForeignKey('giftlists.id', ondelete='CASCADE'), primary_key=True),
    Column('gift_id', ForeignKey('gifts.id', ondelete='CASCADE'), primary_key=True)
)
