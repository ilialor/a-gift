from typing import List, Optional
from sqlalchemy import ARRAY, JSON, ForeignKey, Integer, String, Table, Enum, Text, UniqueConstraint, text, Column, DateTime, BigInteger, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.dao.database import Base, uniq_str_an, array_or_none_an

from enum import Enum as PyEnum

class User(Base):
    username: Mapped[uniq_str_an]
    email: Mapped[Optional[uniq_str_an]] = mapped_column(unique=True, nullable=True)
    password: Mapped[Optional[uniq_str_an]] = mapped_column(unique=False, nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String, nullable=True)
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
    groups: Mapped[List['UserList']] = relationship(
        'UserList',
        back_populates='owner',
        foreign_keys='UserList.user_id'  
    )
    own_calendars: Mapped[List['Calendar']] = relationship(
        'Calendar',
        back_populates='owner'
    )
    calendars: Mapped[List['Calendar']] = relationship(
        'Calendar',
        secondary='calendar_participants',
        back_populates='participants'
    )
    contacts: Mapped[List["Contact"]] = relationship(
        "Contact",
        back_populates="user",
        cascade="all, delete-orphan"
    )

class Profile(Base):
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  
    interests: Mapped[array_or_none_an]
    contacts: Mapped[dict | None] = mapped_column(JSON)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    user: Mapped['User'] = relationship('User', back_populates='profile')

class GiftList(Base):
    name: Mapped[str] = mapped_column(unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    owner: Mapped['User'] = relationship('User', back_populates='lists')
    groups: Mapped[List['UserList']] = relationship('UserList', back_populates='gift_list')
    gifts: Mapped[List['Gift']] = relationship(
        'Gift',
        secondary='gift_list_gift',
        back_populates='lists',
        lazy='selectin'  # Set lazy loading strategy for async
    )

class UserList(Base):
    __tablename__ = 'userlists'

    name: Mapped[str] = mapped_column(String(), nullable=False)
    description: Mapped[str | None] = mapped_column(String(), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    gift_list_id: Mapped[int | None] = mapped_column(ForeignKey('giftlists.id', ondelete='CASCADE'), nullable=True)
    added_user_id: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    added_user = relationship('User', foreign_keys=[added_user_id])
    gift_list = relationship('GiftList', back_populates='groups')
    owner = relationship(
        'User',
        foreign_keys=[user_id],
        back_populates='groups'
    )

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
    payments: Mapped[List['Payment']] = relationship('Payment', back_populates='gift')
    events: Mapped[List['Calendar']] = relationship(
        'Calendar',
        secondary='calendar_gift',
        back_populates='gifts',
        lazy='selectin'
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
    gift_id: Mapped[int] = mapped_column(ForeignKey('gifts.id'), nullable=False)
    gift: Mapped['Gift'] = relationship('Gift', back_populates='payments')

# Association table for GiftList and Gift
gift_list_gift = Table(
    'gift_list_gift',
    Base.metadata,
    Column('giftlist_id', ForeignKey('giftlists.id', ondelete='CASCADE'), primary_key=True),
    Column('gift_id', ForeignKey('gifts.id', ondelete='CASCADE'), primary_key=True)
)


class EventTypeEnum(str, PyEnum):
    BIRTHDAY = "birthday"
    PERSONAL = "personal"  # личные праздники (годовщины и т.д.)
    PROFESSIONAL = "professional"  # профессиональные праздники
    NATIONAL = "national"  # государственные праздники
    RELIGIOUS = "religious"  # религиозные праздники
    CULTURAL = "cultural"  # культурные события
    REMINDER = "reminder"  # напоминания о подарках
    OTHER = "other"

class RecurrenceTypeEnum(str, PyEnum):
    NONE = "none"  # однократное событие
    YEARLY = "yearly"  # ежегодное
    MONTHLY = "monthly"  # ежемесячное
    WEEKLY = "weekly"  # еженедельное
    CUSTOM = "custom"  # пользовательская периодичность

# Define the association table for Calendar and User
calendar_participants = Table(
    'calendar_participants',
    Base.metadata,
    Column('calendar_id', ForeignKey('calendar_events.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
)

class Calendar(Base):
    """
    Модель календаря для отслеживания праздников и событий, связанных с подарками
    """
    __tablename__ = 'calendar_events'

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[EventTypeEnum] = mapped_column(Enum(EventTypeEnum), default=EventTypeEnum.BIRTHDAY, nullable=False)
    
    # Дата и время события
    start_date: Mapped[datetime] = mapped_column(nullable=False)
    end_date: Mapped[datetime | None]
    
    # Повторение события
    recurrence_type: Mapped[RecurrenceTypeEnum] = mapped_column(
        Enum(RecurrenceTypeEnum), 
        nullable=False, 
        default=RecurrenceTypeEnum.NONE
    )
    recurrence_rule: Mapped[dict | None] = mapped_column(
        JSON,  # Для хранения сложных правил повторения
        comment='JSON with recurrence rules (intervals, exclusions, etc.)'
    )
    
    # Связь с пользователем
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    owner: Mapped['User'] = relationship('User', back_populates='own_calendars')
    
    # Участники события (для групповых праздников)
    participants: Mapped[List['User']] = relationship(
        'User',
        secondary='calendar_participants',
        back_populates='calendars'
    )
    
    # Теги для фильтрации и группировки
    tags: Mapped[array_or_none_an]
    
    # Настройки напоминаний
    reminder_days: Mapped[List[int] | None] = mapped_column(
        ARRAY(Integer), 
        comment='Days before event to send reminders'
    )
    
    # Бюджет на подарки
    budget: Mapped[float | None]
    currency: Mapped[str | None] = mapped_column(String(3))  # ISO 4217 код валюты
    
    # Связанные подарки
    gifts: Mapped[List['Gift']] = relationship(
        'Gift',
        secondary='calendar_gift',
        back_populates='events',
        lazy='selectin'
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type.value,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "recurrence_type": self.recurrence_type.value,
            "recurrence_rule": self.recurrence_rule,
            "owner_id": self.owner_id,
            "participant_ids": self.participants,
            "tags": self.tags,
            "reminder_days": self.reminder_days,
            "budget": self.budget,
            "currency": self.currency,
        }

# Таблица связи календаря и подарков
calendar_gift = Table(
    'calendar_gift',
    Base.metadata,
    Column('calendar_id', ForeignKey('calendar_events.id', ondelete='CASCADE'), primary_key=True),
    Column('gift_id', ForeignKey('gifts.id', ondelete='CASCADE'), primary_key=True)
)

class Contact(Base):    
    """Модель для хранения контактов пользователя"""
    __tablename__ = 'contacts'

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    contact_telegram_id: Mapped[int] = mapped_column(BigInteger)
    username: Mapped[str | None]
    first_name: Mapped[str]
    last_name: Mapped[str | None]

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="contacts", foreign_keys=[user_id])

    __table_args__ = (
        UniqueConstraint('user_id', 'contact_telegram_id', name='uq_user_contact'),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "contact_telegram_id": self.contact_telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
