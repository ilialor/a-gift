from telethon import TelegramClient, functions
import asyncio
import logging
import os
from app.config import settings

class TelegramContactsService:
    _instance = None
    _client = None
    _lock = asyncio.Lock()

    def __init__(self):
        if not TelegramContactsService._client:
            session_file = os.path.join('sessions', 'telegram_session')
            os.makedirs('sessions', exist_ok=True)
            
            self.client = TelegramClient(
                session_file,
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH
            )
            TelegramContactsService._client = self.client
        else:
            self.client = TelegramContactsService._client

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
                    await cls._instance.start()
        return cls._instance

    async def start(self):
        if not self.client.is_connected():
            await self.client.connect()
            if not await self.client.is_user_authorized():
                phone = settings.TELEGRAM_PHONE
                await self.client.send_code_request(phone)
                code = input('Enter the code you received: ')  # Для первого запуска
                await self.client.sign_in(phone, code)

    async def get_saved_contacts(self):
        try:
            if not self.client.is_connected():
                await self.start()
                
            result = await self.client(functions.contacts.GetSavedRequest())
            return [
                {
                    "phone": contact.phone,
                    "first_name": contact.first_name,
                    "last_name": contact.last_name,
                    "date": contact.date.isoformat() if contact.date else None
                }
                for contact in result
            ]
        except Exception as e:
            logging.error(f"Error getting saved contacts: {e}")
            raise

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        pass


# import logging
# from typing import List, Dict, Any
# import asyncio
# from aiogram import Bot
# from app.auth.router import contacts
# from app.config import settings
# from telethon import TelegramClient, functions, types
# from app.utils.bot_instance import telegram_bot

# class TelegramContactsService:
#     def __init__(self):
#         self.client = TelegramClient(
#             'giftme_bot',
#             settings.TELEGRAM_API_ID,
#             settings.TELEGRAM_API_HASH
#         )
#         self.bot = telegram_bot
#         asyncio.create_task(self.init_bot())

#     async def init_bot(self):
#         try:
#             if not self.client.is_connected():
#                 await self.client.connect()
#             if not await self.client.is_user_authorized():
#                 await self.client.start(bot_token=settings.BOT_TOKEN)
#             logging.info("Bot initialized")
#         except Exception as e:
#             logging.error(f"Failed to initialize bot: {e}")
#             raise

#     async def import_contacts(self, phone_contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """Import phone contacts using Telegram API"""
#         try:
#             formatted_contacts = [{
#                 "client_id": i,
#                 "phone": contact["phone"],
#                 "first_name": contact["first_name"],
#                 "last_name": contact.get("last_name", "")
#             } for i, contact in enumerate(phone_contacts)]

#             result = await self.client.invoke(
#                 contacts.ImportContactsRequest(contacts=formatted_contacts)
#             )

#             imported_users = []
#             for imported in result.imported:
#                 user_info = next(
#                     (u for u in result.users if u.id == imported.user_id), 
#                     None
#                 )
#                 if user_info:
#                     imported_users.append({
#                         "telegram_id": imported.user_id,
#                         "username": getattr(user_info, 'username', None),
#                         "first_name": user_info.first_name,
#                         "last_name": getattr(user_info, 'last_name', None)
#                     })

#             return {
#                 "imported_users": imported_users,
#                 "retry_contacts": result.retry_contacts
#             }

#         except Exception as e:
#             logging.error(f"Error importing contacts: {e}")
#             raise

#     async def get_contacts(self) -> Dict[str, Any]:
#         """Get all contacts using Telegram API"""
#         try:
#             result = await self.client(functions.contacts.GetContactsRequest(hash=0))
#             contacts = []
            
#             for user in result.users:
#                 if hasattr(user, 'contact') and user.contact:
#                     contacts.append({
#                         "id": user.id,
#                         "username": user.username,
#                         "first_name": user.first_name,
#                         "last_name": user.last_name,
#                         "phone": user.phone
#                     })
            
#             return {"contacts": contacts}

#         except Exception as e:
#             logging.error(f"Error getting contacts: {e}")
#             raise

#     async def get_saved_contacts(self) -> List[Dict[str, Any]]:
#         """Get saved phone contacts"""
#         try:
#             result = await self.client(functions.contacts.GetSavedRequest())
#             return [
#                 {
#                     "phone": contact.phone,
#                     "first_name": contact.first_name,
#                     "last_name": contact.last_name,
#                     "date": contact.date
#                 }
#                 for contact in result
#             ]
#         except Exception as e:
#             logging.error(f"Error getting saved contacts: {e}")
#             raise

# async def get_telegram_user_info(user_telegram_id: int):
#     """Get user info using Bot API"""
#     try:
#         user = await telegram_bot.get_chat(user_telegram_id)
#         return {
#             'id': user.id,
#             'username': user.username,
#             'first_name': user.first_name,
#             'last_name': user.last_name
#         }
#     except Exception as e:
#         logging.error(f"Error getting user info: {e}")
#         return None




