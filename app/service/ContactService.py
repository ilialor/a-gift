from sqlalchemy.ext.asyncio import AsyncSession
from app.dao.dao import ContactDAO
from app.utils.telegram_client import TelegramContactsService
import logging

class ContactsService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._contact_dao = ContactDAO(session)
        
    async def import_contacts(self):
        """Import contacts from Telegram"""
        try:
            async with await TelegramContactsService.get_instance() as telegram:
                contacts = await telegram.get_saved_contacts()
                
            imported_contacts = []
            for contact in contacts:
                contact_obj = await self._contact_dao.add_contact({
                    "phone": contact["phone"],
                    "first_name": contact["first_name"], 
                    "last_name": contact["last_name"]
                })
                imported_contacts.append(contact_obj)
                
            return imported_contacts
                
        except Exception as e:
            logging.error(f"Error importing contacts: {e}")
            raise

# from typing import List, Optional
# from pydantic import BaseModel
# from sqlalchemy.ext.asyncio import AsyncSession
# from aiogram import Bot
# from app.giftme.models import Contact, User
# from app.dao.dao import UserDAO
# import logging
# from app.utils.bot_instance import telegram_bot

# class TelegramContact(BaseModel):
#     phone: str
#     first_name: str
#     last_name: Optional[str] = None
#     client_id: int
#     telegram_id: Optional[int] = None

# class ContactsService:
#     def __init__(self, session: AsyncSession):
#         self.bot = telegram_bot
#         self.session = session

#     @classmethod
#     async def create(cls, session: AsyncSession) -> 'ContactsService':
#         """Factory method to create ContactsService instance"""
#         return cls(session)

#     async def import_contacts(self, user_id: int, contacts: List[TelegramContact]) -> List[Contact]:
#         """
#         Import contacts using Telegram API and save to database
#         """
#         try:
#             # Prepare contacts for Telegram API
#             input_contacts = []
#             for idx, contact in enumerate(contacts):
#                 input_contacts.append({
#                     "phone": contact.phone,
#                     "first_name": contact.first_name,
#                     "last_name": contact.last_name or "",
#                     "client_id": idx  # Use index as client_id
#                 })

#             # Import contacts through Telegram API
#             result = await self.bot.get_contacts()
#             imported_contacts = []

#             # Process imported contacts
#             for imported in result.imported:
#                 contact_data = next(
#                     (c for c in contacts if c.client_id == imported.client_id),
#                     None
#                 )
#                 if contact_data:
#                     # Find user info from Telegram
#                     user_info = next(
#                         (u for u in result.users if u.id == imported.user_id),
#                         None
#                     )
#                     if user_info:
#                         contact = Contact(
#                             user_id=user_id,
#                             contact_telegram_id=imported.user_id,
#                             username=user_info.username,
#                             first_name=user_info.first_name,
#                             last_name=user_info.last_name
#                         )
#                         self.session.add(contact)
#                         imported_contacts.append(contact)

#             await self.session.commit()
#             return imported_contacts

#         except Exception as e:
#             logging.error(f"Error importing contacts: {e}")
#             await self.session.rollback()
#             raise

#     async def get_user_contacts(self, user_id: int) -> List[Contact]:
#         """
#         Get list of user's contacts
#         """
#         try:
#             user = await UserDAO.find_by_id(self.session, user_id)
#             if not user:
#                 raise ValueError("User not found")
                
#             return user.contacts

#         except Exception as e:
#             logging.error(f"Error getting contacts: {e}")
#             raise

#     async def add_contact(self, user_id: int, telegram_id: int) -> Contact:
#         """
#         Add a single contact by Telegram ID
#         """
#         try:
#             # Get user info from Telegram
#             user_info = await self.bot.get_chat(telegram_id)
            
#             contact = Contact(
#                 user_id=user_id,
#                 contact_telegram_id=telegram_id,
#                 username=user_info.username,
#                 first_name=user_info.first_name,
#                 last_name=user_info.last_name
#             )
            
#             self.session.add(contact)
#             await self.session.commit()
#             return contact

#         except Exception as e:
#             logging.error(f"Error adding contact: {e}")
#             await self.session.rollback()
#             raise

#     async def remove_contact(self, user_id: int, contact_id: int) -> bool:
#         """
#         Remove a contact
#         """
#         try:
#             contact = await self.session.get(Contact, contact_id)
#             if contact and contact.user_id == user_id:
#                 await self.session.delete(contact)
#                 await self.session.commit()
#                 return True
#             return False

#         except Exception as e:
#             logging.error(f"Error removing contact: {e}")
#             await self.session.rollback()
#             raise

#     async def sync_contacts(self, user_id: int) -> List[Contact]:
#         """
#         Sync contacts with Telegram
#         """
#         try:
#             # Get current contacts from Telegram
#             telegram_contacts = await self.bot.get_contacts()
            
#             # Get existing contacts from database
#             existing_contacts = await self.get_user_contacts(user_id)
#             existing_ids = {c.contact_telegram_id for c in existing_contacts}
            
#             # Add new contacts
#             new_contacts = []
#             for contact in telegram_contacts:
#                 if contact.id not in existing_ids:
#                     new_contact = Contact(
#                         user_id=user_id,
#                         contact_telegram_id=contact.id,
#                         username=contact.username,
#                         first_name=contact.first_name,
#                         last_name=contact.last_name
#                     )
#                     self.session.add(new_contact)
#                     new_contacts.append(new_contact)
            
#             await self.session.commit()
#             return existing_contacts + new_contacts

#         except Exception as e:
#             logging.error(f"Error syncing contacts: {e}")
#             await self.session.rollback()
#             raise
