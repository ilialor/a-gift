import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from pydantic import BaseModel, Field
from app.dao.dao import GiftDAO, GiftListDAO, UserDAO
from app.twa.validation import TelegramWebAppValidator
from app.twa.auth import TWAAuthManager
from app.dao.session_maker import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.config import settings
from app.giftme.models import Gift, User
from app.giftme.schemas import GiftCreate, GiftResponse

router = APIRouter(prefix="/twa", tags=["twa"])
templates = Jinja2Templates(directory="app/templates")

telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)
auth_manager = TWAAuthManager(settings.secret_key)

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
                # Get the actual Gift model instance instead of dict
                selected_gift = await session.get(Gift, gift_id)
                if selected_gift:
                    # Get the list IDs that contain this gift
                    selected_gift_lists = [gift_list.id for gift_list in selected_gift.lists]
            
            return templates.TemplateResponse("pages/wishlist.html", {
                "request": request,
                "user": user,
                "gift_lists": gift_lists,
                "selected_gift": selected_gift,
                "selected_gift_lists": selected_gift_lists
            })
    except Exception as e:
        logging.error(f"Error in wishlist page: {e}")
        return RedirectResponse(url="/twa/error?message=Failed+to+load+wishlist")

@router.post("/api/giftlist/toggle")
async def toggle_gift_in_list(request: Request):
    try:
        data = await request.json()
        gift_id = data.get("gift_id")
        list_id = data.get("list_id")
        action = data.get("action")
        
        if not all([gift_id, list_id, action]) or action not in ["add", "remove"]:
            raise HTTPException(status_code=400, detail="Invalid request data")

        async with async_session_maker() as session:
            gift_list_dao = GiftListDAO(session)
            
            if action == "add":
                success = await gift_list_dao.add_gift_to_list(list_id, gift_id)
            else:
                success = await gift_list_dao.remove_gift_from_list(list_id, gift_id)

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

