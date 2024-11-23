import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel
from app.dao.dao import ContactDAO, GiftDAO, GiftListDAO, PaymentDAO, UserDAO, UserListDAO
from app.twa.validation import TelegramWebAppValidator
from app.twa.auth import TWAAuthManager
from app.dao.session_maker import async_session_maker, connection
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from app.config import settings
from app.giftme.schemas import GiftCreate, GiftListCreate, GiftListResponse, GiftResponse, ProfilePydantic, UserFilterPydantic, UserPydantic
from app.utils.telegram_client import TelegramContactsService
from app.service.ContactService import ContactsService 
from app.utils.bot_instance import telegram_bot
from telethon import functions
from aiogram import types
from aiogram.types import Message

router = APIRouter(prefix="/twa", tags=["twa"])
templates = Jinja2Templates(directory="app/templates")

telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)
auth_manager = TWAAuthManager(settings.secret_key)

@router.get("/groups")
async def groups_page(request: Request):
    """Groups page"""
    user = request.state.user
    if not user:
        return RedirectResponse(url="/twa/error?message=User+not+found")

    try:
        async with async_session_maker() as session:
            user_list_dao = UserListDAO(session)
            user_lists = await user_list_dao.get_user_lists(user.id)
            
            return templates.TemplateResponse("pages/groups.html", {
                "request": request,
                "user": user,
                "user_lists": user_lists,
                "page_title": "Groups"
            })
            
    except Exception as e:
        logging.error(f"Error loading groups page: {e}")
        return RedirectResponse(url="/twa/error?message=Failed+to+load+groups")

@router.post("/api/groups", response_model=None)
async def create_user_list(request: Request, data: dict):
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            user_list_dao = UserListDAO(session)

            user_list_data = {
                "name": data["name"],
                "user_id": user_id
            }

            user_list = await user_list_dao.create_user_list(user_list_data)            

            return JSONResponse(status_code=200, content={"id": user_list.id})

    except Exception as e:
        logging.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/api/groups/{list_id}/toggle", response_model=None)
async def toggle_group_status(request: Request, list_id: int, data: dict):
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            user_list_dao = UserListDAO(session)
            success = await user_list_dao.toggle_member(list_id, data["is_active"])
            
            if not success:
                raise HTTPException(status_code=400, detail="Failed to update status")

            return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logging.error(f"Error toggling group status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def main_page(
    request: Request,
    startParam: Optional[str] = None,
    refresh_token: Optional[str] = None
):
    try:
        if not startParam or not refresh_token:
            return RedirectResponse(url="/twa/error?message=Missing+authentication+parameters")

        user_id = auth_manager.validate_token(startParam)

        async with async_session_maker() as session:
            user = await UserDAO.find_by_id(session, user_id)
            if not user:
                return RedirectResponse(url="/twa/error?message=User+not+found")

        bot_info = await telegram_bot.get_me()
        return templates.TemplateResponse("pages/index.html", {
            "request": request,
            "user": user,
            "bot_username": bot_info.username
        })

    except Exception as e:
        logging.error(f"Error in main_page: {e}")
        return RedirectResponse(url="/twa/error?message=Authentication+failed")

@router.get("/wishlist")
async def wishlist_page(
    request: Request,
    gift_id: Optional[int] = None
):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/twa/error?message=User+not+found")

    try:
        async with async_session_maker() as session:
            gift_list_dao = GiftListDAO(session)
            gift_lists = await gift_list_dao.get_giftlists_with_gifts(user.id)
            
            selected_gift = None
            selected_gift_lists = []
            
            if gift_id:
                gift_dao = GiftDAO(session)
                selected_gift = await gift_dao.get_gift_with_lists(gift_id, session)
                if selected_gift:
                    selected_gift_lists = [gift_list.id for gift_list in selected_gift.lists]
            
            context = {
                "request": request,
                "user": user,
                "gift_lists": gift_lists,
                "selected_gift": selected_gift,
                "selected_gift_lists": selected_gift_lists
            }
            
            return templates.TemplateResponse("pages/wishlist.html", context)

    except Exception as e:
        logging.error(f"Error in wishlist page: {e}")
        return RedirectResponse(url="/twa/error?message=Failed+to+load+wishlist")
    
@router.post("/api/giftlist/create", response_model=GiftListResponse)
async def create_gift_list(request: Request, gift_list: GiftListCreate):
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if gift_list.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot create list for another user")

        logging.info(f"Creating gift list: {gift_list.model_dump()}")

        async with async_session_maker() as session:
            gift_list_dao = GiftListDAO(session)
            new_list = await gift_list_dao.create_gift_list(gift_list.model_dump())
            
            if not new_list:
                raise HTTPException(status_code=500, detail="Failed to create gift list")
                
            return GiftListResponse(
                id=new_list.id,
                name=new_list.name,
                owner_id=new_list.owner_id
            )

    except Exception as e:
        logging.error(f"Error creating gift list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class GiftListToggleRequest(BaseModel):
    gift_id: int
    list_id: int
    action: str  # 'add' or 'remove'

@router.post("/api/giftlist/toggle", response_model=None)
async def toggle_gift_in_list(request: Request, toggle_data: GiftListToggleRequest):
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            gift_list_dao = GiftListDAO(session)
            
            if toggle_data.action == "add":
                success = await gift_list_dao.add_gift_to_list(toggle_data.list_id, toggle_data.gift_id)
            elif toggle_data.action == "remove":
                success = await gift_list_dao.remove_gift_from_list(toggle_data.list_id, toggle_data.gift_id)
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

            if not success:
                raise HTTPException(status_code=400, detail="Failed to update gift list")

            return JSONResponse(status_code=200, content={"status": "success"})

    except Exception as e:
        logging.error(f"Error toggling gift in list: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/gifts", response_model=GiftResponse)
async def create_gift(request: Request, gift_data: GiftCreate):
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if gift_data.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot create gift for another user")

        logging.info(f"Creating gift: {gift_data.model_dump()}")

        async with async_session_maker() as session:
            gift_dao = GiftDAO(session)
            new_gift = await gift_dao.create_gift(gift_data.model_dump())
            
            if not new_gift:
                raise HTTPException(status_code=500, detail="Failed to create gift")
                
            return GiftResponse(
                id=new_gift.id,
                name=new_gift.name,
                description=new_gift.description,
                price=new_gift.price,
                owner_id=new_gift.owner_id
            )

    except Exception as e:
        logging.error(f"Error creating gift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gifts")
async def gifts_page(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/twa/error?message=User+not+found")

    async with async_session_maker() as session:
        gift_dao = GiftDAO(session)
        gifts = await gift_dao.get_gifts_by_user_id(user.id)
        
        # Get bot information for sharing
        bot_info = await telegram_bot.get_me()
        
    return templates.TemplateResponse("pages/gifts.html", {
        "request": request,
        "user": user,
        "gifts": gifts,
        "page_title": "My Gifts",
        "bot_username": bot_info.username  # Add bot username to context
    })

@router.get("/groups")
async def groups(request: Request):
    """User's groups page"""
    user_id = request.state.user_id  # Retrieve user_id from middleware

    async with async_session_maker() as session:
        user = await UserDAO.find_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("pages/groups.html", {
        "request": request,
        "page_title": "Groups",
        "user_id": user_id,
        "user": user  # Pass the user object to the template
    })

@router.get("/contacts")
async def contacts_page(request: Request):
    """Contacts page route"""
    user = request.state.user
    if not user:
        return RedirectResponse(url="/twa/error?message=User+not+found")

    try:
        contacts_service = TelegramContactsService()
        await contacts_service.start()
        contacts = await contacts_service.get_saved_contacts()
        async with async_session_maker() as session:
            contact_dao = ContactDAO(session)
            contacts = await contact_dao.get_user_contacts(user.id)
            
            return templates.TemplateResponse(
                "pages/contacts.html",
                {"request": request, "user": user, "contacts": contacts}
            )
            
    except SQLAlchemyError as e:
        logging.error(f"Database error in contacts page: {e}")
        return RedirectResponse(url="/twa/error?message=Database+error")
    except Exception as e:
        logging.error(f"Error in contacts page: {e}")
        return RedirectResponse(url="/twa/error?message=Failed+to+load+contacts")
    
@router.post("/api/contacts/import", response_model=None)
async def import_contacts(request: Request):
    """Import contacts from phone contacts"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        data = await request.json()
        phone_contacts = data.get("contacts", [])

        async with async_session_maker() as session:
            # Import contacts via Telegram
            contacts_service = TelegramContactsService(TelegramContactsService.telegram_bot)
            result = await contacts_service.import_contacts(phone_contacts)

            # Save imported contacts to database
            contact_dao = ContactDAO(session)
            for user_info in result["imported_users"]:
                contact_data = {
                    "user_id": user_id,
                    "contact_telegram_id": user_info["telegram_id"],
                    "username": user_info["username"],
                    "first_name": user_info["first_name"],
                    "last_name": user_info["last_name"]
                }
                await contact_dao.add_contact(contact_data)

            return {
                "status": "success",
                "imported_count": len(result["imported_users"]),
                "retry_count": len(result["retry_contacts"])
            }

    except Exception as e:
        logging.error(f"Error importing contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/contacts", response_model=None)
async def add_contact(request: Request):
    """Add a contact"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        data = await request.json()
        telegram_id = data.get("telegram_id")
        if not telegram_id:
            raise HTTPException(status_code=400, detail="Missing telegram_id")

        async with async_session_maker() as session:
            contact_service = ContactsService(session)
            await contact_service.add_contact(user_id, telegram_id)
            return JSONResponse({"status": "success"})

    except Exception as e:
        logging.error(f"Error adding contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api/contacts/{contact_id}", response_model=None)
async def remove_contact(request: Request, contact_id: int):
    """Remove a contact"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            contact_service = ContactsService(session)
            success = await contact_service.remove_contact(user_id, contact_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="Contact not found")

            return JSONResponse({"status": "success"})

    except Exception as e:
        logging.error(f"Error removing contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/publish")
async def publish(request: Request):
    """Publishing page"""
    user_id = request.state.user_id  # Get user_id from middleware

    async with async_session_maker() as session:
        user = await UserDAO.find_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("pages/publish.html", {
        "request": request,
        "page_title": "To Publish",
        "user_id": user_id,
        "user": user  # Pass the user object to the template
    })

@router.get("/error")
async def error_page(request: Request, message: Optional[str] = Query(None)):
    """Error page route"""
    return templates.TemplateResponse("pages/error.html", {
        "request": request,
        "error_message": message or "An unknown error has occurred."
    })

@router.get("/api/contacts", response_model=None)
async def get_contacts(request: Request):
    """Get user contacts"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            user_dao = UserDAO(session)
            users = await user_dao.get_all_users()  
            contacts = [
                {"id": user.id, "username": user.username}
                for user in users
                if user.id != user_id
            ]
            return contacts

    except Exception as e:
        logging.error(f"Error getting contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/contacts/telegram", response_model=None)
async def get_telegram_contacts(request: Request):
    """Get user's Telegram contacts"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            user = await UserDAO.find_by_id(session, user_id)
            if not user or not user.telegram_id:
                raise HTTPException(status_code=400, detail="Telegram ID not found")

            # Получаем контакты пользователя через Telegram API
            # telegram_contacts = await get_telegram_user_contacts(user.telegram_id)
            
            # user_dao = UserDAO(session)
            # registered_users = await user_dao.get_users_by_telegram_ids(
            #     [contact['id'] for contact in telegram_contacts]
            # )
            
            # Создаем маппинг telegram_id -> user_id
            # user_mapping = {user.telegram_id: user.id for user in registered_users}
            
            # Добавляем user_id к контактам, если пользователь зарегистрирован
            # contacts_with_ids = [
            #     {**contact, 'id': user_mapping.get(contact['id'])}
            #     for contact in telegram_contacts
            #     if contact['id'] in user_mapping
            # ]
            
            return [{"id": 1, "username": "test"}]

    except Exception as e:
        logging.error(f"Error getting Telegram contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/groups/{list_id}/members", response_model=None)
async def add_list_member(list_id: int, data: dict, request: Request):
    """Add a member to a group"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with async_session_maker() as session:
            user_list_dao = UserListDAO(session)
            user_list_data = {
                "user_id": user_id,
                "added_user_id": data["user_id"],
                "gift_list_id": list_id,
                "name": "Member"  # You might want to customize this
            }
            await user_list_dao.add_user_to_list(user_list_data)
            return {"status": "success"}

    except Exception as e:
        logging.error(f"Error adding member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/contacts/saved", response_model=None)
async def get_saved_contacts(request: Request):
    """Get complete list of saved phone contacts"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        contacts_service = TelegramContactsService()
        # Use getSaved method from contacts functions
        saved_contacts = await contacts_service.client(functions.contacts.GetSavedRequest())

        # Format response
        contacts = []
        for contact in saved_contacts:
            contacts.append({
                "phone": contact.phone,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "date": contact.date
            })

        return {"contacts": contacts}
            
    except Exception as e:
        logging.error(f"Error getting saved contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/gifts/{gift_id}/pay")
async def initiate_payment(gift_id: int, request: Request):
    """Initiate Telegram Stars payment for a gift"""
    try:
        user = request.state.user
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

        async with async_session_maker() as session:
            gift_dao = GiftDAO(session)
            gift = await gift_dao.get_gift_by_id(gift_id)
            if not gift:
                raise HTTPException(status_code=404, detail="Gift not found")

            # Get payment data from request
            payload = await request.json()
            amount = float(payload.get('amount', 0))
            
            # Convert to Stars
            stars_amount = max(1, round(amount))
            amount_in_units = stars_amount * 100  # 1 Star = 100 units

            # Create Stars invoice
            try:
                result : Message = await telegram_bot.send_invoice(
                    chat_id=user.telegram_id,
                    title=f"🎁 {gift.name}",
                    description=f"Support gift: {gift.name} ({stars_amount} Stars)",
                    payload=str(gift_id),
                    provider_token="",  # Empty for Telegram Stars
                    currency="XTR",  # Telegram Stars currency
                    prices=[types.LabeledPrice(
                        label=f"Gift: {gift.name[:20]}",
                        amount=amount_in_units
                    )],
                    start_parameter=f"gift_{gift_id}",
                    need_shipping_address=False,
                    is_flexible=False
                )
                logging.info(f"Payment invoice sent: {result}")
                return {"status": "success", "message": "Payment invoice sent"}
                
            except Exception as e:
                logging.error(f"Error sending Stars invoice: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create Stars payment"
                )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Payment error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process payment request"
        )

@router.post("/api/gifts/{gift_id}/payment-callback")
async def payment_callback(
    gift_id: int,
    request: Request
):
    """Обработчик callback от Telegram после успешного платежа"""
    try:
        payment_data = await request.json()
        user_id = request.state.user_id
        
        async with async_session_maker() as session:
            # Проверяем существование подарка
            gift_dao = GiftDAO(session)
            gift = await gift_dao.get_gift_by_id(gift_id)
            
            if not gift:
                raise HTTPException(status_code=404, detail="Gift not found")

            # Обновляем сумму оплаты
            payment = {
                "user_id": user_id,
                "gift_id": gift_id,
                "amount": payment_data["amount"],
                "telegram_payment_charge_id": payment_data["telegram_payment_charge_id"]
            }
            
            payment_dao = PaymentDAO(session)
            await payment_dao.add_payment(payment)

            return JSONResponse({"status": "success"})

    except Exception as e:
        logging.error(f"Error processing payment callback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment")

# @router.get("/api/bot-info")
# async def get_bot_info():
#     """Get bot information"""
#     try:
#         bot_info = await telegram_bot.get_me()
#         return {"username": bot_info.username}
#     except Exception as e:
#         logging.error(f"Error getting bot info: {e}")
#         raise HTTPException(status_code=500, detail="Failed to get bot information")

class DirectAuthRequest(BaseModel):
    init_data: str
    return_url: str

@router.post("/api/auth/direct")
async def direct_auth(auth_request: DirectAuthRequest):
    """Direct authentication endpoint for WebApp"""
    try:
        if not auth_request.init_data:
            raise HTTPException(status_code=400, detail="No init_data provided")

        # Validate Telegram WebApp data
        try:
            validated_data = telegram_validator.validate_init_data(auth_request.init_data)
            user_telegram_id = validated_data["user"]["id"]
            logging.info(f"Validated user_telegram_id: {user_telegram_id}")
        except Exception as e:
            logging.error(f"Init data validation error: {e}")
            raise HTTPException(status_code=400, detail="Invalid init_data")
        
        async with async_session_maker() as session:
            # Find or create user
            filter_model = UserFilterPydantic(telegram_id=user_telegram_id)
            user = await UserDAO.find_one_or_none(session=session, filters=filter_model)
            
            if not user:
                # Create new user from Telegram data
                profile = ProfilePydantic(
                    first_name=validated_data["user"].get("first_name"),
                    last_name=validated_data["user"].get("last_name")
                )
                values = UserPydantic(
                    telegram_id=user_telegram_id,
                    username=validated_data["user"].get("username"),
                    profile=profile
                )
                user = await UserDAO.add(session=session, values=values)

            # Create tokens
            access_token = auth_manager.create_access_token(user.id)
            refresh_token = auth_manager.create_refresh_token(user.id)
            
            # Update refresh token in database
            await UserDAO.update_refresh_token(session, user.id, refresh_token)
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": {
                    "id": user.id,
                    "username": user.username
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Direct auth error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/public/gifts/{gift_id}")
async def public_gift_detail(request: Request, gift_id: int):
    try:
        async with async_session_maker() as session:
            gift_dao = GiftDAO(session)
            gift = await gift_dao.get_gift_by_id(gift_id)
            if not gift:
                raise HTTPException(status_code=404, detail="Gift not found")

            # Get bot information
            bot_info = await telegram_bot.get_me()

            # Pass 'user' from request state to the template
            return templates.TemplateResponse("pages/gift_detail.html", {
                "request": request,
                "gift": gift,
                "bot_username": bot_info.username,
                "user": request.state.user  # Add this line
            })
    except Exception as e:
        logging.error(f"Error fetching gift details: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/api/bot-info")
async def get_bot_info():
    """Get bot information"""
    try:
        bot_info = await telegram_bot.get_me()
        return {"username": bot_info.username}
    except Exception as e:
        logging.error(f"Error getting bot info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bot information")

@router.get("/api/auth/validate")
async def validate_auth(request: Request):
    """Validate authentication tokens"""
    try:
        user_id = request.state.user_id
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return {"status": "valid"}
    except Exception as e:
        logging.error(f"Auth validation error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication")
