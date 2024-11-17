import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query
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

telegram_validator = TelegramWebAppValidator(settings.bot_token)
auth_manager = TWAAuthManager(settings.secret_key)

@router.get("/")
async def index(
    request: Request,
    init_data: str = Query(None),
    start_param: str = Query(None),
    session: AsyncSession = Depends(async_session_maker)
):
    """Main TWA page with validation"""
    try:
        # Validate Telegram WebApp init data
        if not init_data:
            raise HTTPException(status_code=401, detail="No init data provided")
        
        # Validate Telegram data
        validated_data = telegram_validator.validate_init_data(init_data)
        user_data = validated_data.get('user')
        
        if not user_data:
            raise HTTPException(status_code=401, detail="No user data provided")

        if start_param:
            # Validate JWT token and get user_id
            user_id = auth_manager.validate_token(start_param)
            
            # Get user from database and verify telegram_id
            user = await UserDAO(session).get_user_by_id(user_id)
            if not user or user.telegram_id != user_data['id']:
                raise HTTPException(status_code=401, detail="User mismatch")
                
            request.state.user = user
    
    except HTTPException:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_message": "Invalid access. Please open through Telegram bot."
            }
        )
    
    return templates.TemplateResponse("pages/index.html", {"request": request})

@router.get("/wishlist")
async def wishlist(request: Request):
    """Your wishlist page"""
    return templates.TemplateResponse("pages/wishlist.html", {
        "request": request,
        "page_title": "My Wishlist"
    })

@router.get("/gifts")
async def gifts(request: Request):
    """Gift page"""
    logging.info(f"Received request for /gifts: method={request.method}, url={request.url}")
    logging.info(f"Request headers: {dict(request.headers)}")
    ser_id = request.session.get("user_id")
    logging.info(f"Getting user_id: {ser_id}")  

    current_user_id = await get_current_user(request)  
    logging.info(f"Accessing gifts page for user_id: {current_user_id}")  # Added logging
    return templates.TemplateResponse("pages/gifts.html", {
        "request": request,
        "page_title": "Gifts",
        "current_user_id": current_user_id  
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
    return templates.TemplateResponse("pages/groups.html", {
        "request": request,
        "page_title": "Groups"
    })

@router.get("/contacts")
async def contacts(request: Request):
    """Your contacts page"""
    return templates.TemplateResponse("pages/contacts.html", {
        "request": request,
        "page_title": "My Contacts"
    })

@router.get("/publish")
async def publish(request: Request):
    """Publishing page"""
    return templates.TemplateResponse("pages/publish.html", {
        "request": request,
        "page_title": "To Publish"
    })
