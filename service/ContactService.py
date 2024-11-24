from typing import List, Optional
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.giftme.models import Contact
from app.dao.contacts_dao import ContactDAO

class ContactService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._contact_dao = ContactDAO(session)

    async def get_user_contacts(self, user_id: int) -> List[Contact]:
        """Get user's contacts"""
        try:
            return await self._contact_dao.get_user_contacts(user_id)
        except SQLAlchemyError as e:
            logging.error(f"Error getting contacts: {e}")
            raise

    async def remove_contact(self, user_id: int, contact_id: int) -> bool:
        """Remove a contact"""
        try:
            return await self._contact_dao.remove_contact(user_id, contact_id)
        except SQLAlchemyError as e:
            logging.error(f"Error removing contact: {e}")
            raise

    async def add_contact(self, user_id: int, telegram_id: int) -> Optional[Contact]:
        """Add a contact"""
        try:
            return await self._contact_dao.add_contact(user_id, telegram_id)
        except SQLAlchemyError as e:
            logging.error(f"Error adding contact: {e}")
            raise
