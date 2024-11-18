import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.dao.dao import UserDAO
from app.twa.validation import TelegramWebAppValidator
from app.twa.auth import TWAAuthManager
from app.dao.session_maker import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.config import settings
from app.giftme.models import User

router = APIRouter(prefix="/twa", tags=["twa"])
templates = Jinja2Templates(directory="app/templates")

telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)
auth_manager = TWAAuthManager(settings.secret_key)

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
    
    return templates.TemplateResponse("pages/gifts.html", {
        "request": request,
        "user_id": user_id,
        "user": user  # Pass the user object to the template
    })

async def get_current_user(request: Request) -> int:
    user_id = request.session.get("user_id")
    if not user_id:
        logging.warning(f"Unauthorized access to gifts page. user_id: {user_id}")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_id

@router.get("/groups")
async def groups(request: Request):
    """User's groups page"""
    user_id = request.state.user_id  # Get user_id from middleware
    
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
        "error_message": message or "An unknown error has occurred.",
        "user": None  # Pass None or handle accordingly if user is not required
    })
