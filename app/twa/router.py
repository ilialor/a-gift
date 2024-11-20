import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from pydantic import BaseModel, Field
from app.dao.dao import GiftDAO, GiftListDAO, UserDAO, UserListDAO
from app.twa.validation import TelegramWebAppValidator
from app.twa.auth import TWAAuthManager
from app.dao.session_maker import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.config import settings
from app.giftme.models import Gift, User
from app.giftme.schemas import GiftCreate, GiftListCreate, GiftListResponse, GiftResponse

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

@router.post("/api/groups")
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

@router.patch("/api/groups/{list_id}/toggle")
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

        return templates.TemplateResponse("pages/index.html", {
            "request": request,
            "user": user
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

@router.post("/api/giftlist/toggle")
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
        
    return templates.TemplateResponse("pages/gifts.html", {
        "request": request,
        "user": user,
        "gifts": gifts,
        "page_title": "My Gifts"
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
async def contacts(request: Request):
    """Your contacts page"""
    user_id = request.state.user_id  # Get user_id from middleware

    async with async_session_maker() as session:
        user = await UserDAO.find_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("pages/contacts.html", {
        "request": request,
        "page_title": "My Contacts",
        "user_id": user_id,
        "user": user  # Pass the user object to the template
    })

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

