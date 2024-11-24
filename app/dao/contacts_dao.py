from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.giftme.models import Contact
from app.dao.base import BaseDAO
import logging

class ContactDAO(BaseDAO[Contact]):
    model = Contact
    
    async def add_contact(self, contact_data: dict) -> Contact:
        """Add a new contact"""
        try:
            contact = Contact(**contact_data)
            self.session.add(contact)
            await self.session.commit()
            await self.session.refresh(contact)
            return contact
        except SQLAlchemyError as e:
            await self.session.rollback()
            logging.error(f"Error adding contact: {e}")
            raise
    
    async def get_user_contacts(self, user_id: int):
        """Get user's contacts"""
        try:
            query = select(self.model).where(self.model.user_id == user_id)
            result = await self.session.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logging.error(f"Error getting contacts: {e}")
            raise
