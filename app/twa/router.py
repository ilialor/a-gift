import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query, status, Header
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.dao.dao import GiftDAO, UserDAO
from app.twa.validation import TelegramWebAppValidator
from app.twa.auth import TWAAuthManager
from app.dao.session_maker import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.config import settings
from app.giftme.models import User
from pydantic import BaseModel, Field

router = APIRouter(prefix="/twa", tags=["twa"])
templates = Jinja2Templates(directory="app/templates")

telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)
auth_manager = TWAAuthManager(settings.secret_key)

class GiftCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)

@router.get("/")
async def main_page(request: Request):
    user_id = request.state.user_id  # Get user_id from middleware

    async with async_session_maker() as session:
        user = await UserDAO.find_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("pages/index.html", {
        "request": request,
        "user_id": user_id,
        "user": user  # Pass the user object to the template
    })

@router.get("/wishlist")
async def wishlist_page(request: Request):
    user_id = request.state.user_id  # Get user_id from middleware

    async with async_session_maker() as session:
        user = await UserDAO.find_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("pages/wishlist.html", {
        "request": request,
        "user_id": user_id,
        "user": user  # Pass the user object to the template
    })

@router.get("/gifts")
async def gifts_page(request: Request):
    user_id = request.state.user_id  # Get user_id from middleware

    async with async_session_maker() as session:
        user = await UserDAO.find_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        gifts_dao = GiftDAO(session)
        gifts = await gifts_dao.get_gifts_by_user_id(user_id)  # Fetch user's gifts

    return templates.TemplateResponse("pages/gifts.html", {
        "request": request,
        "user_id": user_id,
        "user": user,
        "gifts": gifts  # Pass gifts to the template
    })

# Enhance error handling and logging during gift creation

@router.post("/gifts", status_code=status.HTTP_201_CREATED)
async def create_gift(request: Request, gift: GiftCreate):
    try:
        user = request.state.user_id  # Ensure user is set by middleware
        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Create new gift associated with the user
        async with async_session_maker() as session:
            new_gift = await GiftDAO(session).create_gift(user_id=user, gift_data=gift)
            logging.info(f"app/twa/router.py: Gift created for user_id: {user}")
        
            return {"message": "Gift added successfully!", "gift": new_gift}
    except HTTPException as he:
        logging.error(f"app/twa/router.py: HTTPException - {he.detail}")
        raise he
    except Exception as e:
        logging.error(f"app/twa/router.py: Error creating gift: {e}")  # Log exception with details
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def get_current_user(request: Request) -> int:
    user_id = request.state.user_id
    if not user_id:
        user_id = request.session.get("user_id")
    if not user_id:
        logging.warning(f"Unauthorized access to gifts page. user_id: {user_id}")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id

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

