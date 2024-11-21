import logging
from fastapi import APIRouter, Request, HTTPException, Depends, Query, status
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
from app.auth.schemas import STokenRefreshRequest, STokenRefreshResponse
from app.auth.utils import create_access_token, create_refresh_token, validate_jwt_token
from app.dao.dao import UserDAO
from app.dao.session_maker import connection  

router = APIRouter(prefix="/twa", tags=["twa"])
templates = Jinja2Templates(directory="app/templates")

telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)
auth_manager = TWAAuthManager(settings.secret_key)

@router.get("/")
async def index(
    request: Request,
    init_data: str = Query(None),
    start_param: str = Query(None),
    refresh_token: str = Query(None),
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

    except HTTPException as he:
        logging.error(f"app/auth/router.py HTTPException: {he.detail}")
        return RedirectResponse(url="/twa/error?message=" + he.detail.replace(" ", "+"), status_code=he.status_code)
    except Exception as e:
        logging.error(f"app/auth/router.py Unexpected error: {e}")
        return RedirectResponse(url="/twa/error?message=Unexpected+error", status_code=500)

    return templates.TemplateResponse("pages/index.html", {
        "request": request,
        "user_id": user.id,
        "user": user
    })

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

@router.get("/error")
async def error_page(request: Request, message: Optional[str] = Query(None)):
    """Error page route"""
    return templates.TemplateResponse("pages/error.html", {
        "request": request,
        "error_message": message or "An unknown error has occurred."
    })

@router.post("/refresh", response_model=STokenRefreshResponse)
async def refresh_tokens(
    token_request: STokenRefreshRequest,
    session: AsyncSession = Depends(async_session_maker)
):
    user = await UserDAO.find_by_refresh_token(session, token_request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Генерация новых токенов
    new_access_token = create_access_token({"user_id": user.id})
    new_refresh_token = create_refresh_token(user.id)
    
    # Обновление refresh_token в базе данных
    await UserDAO.update_refresh_token(session, user.id, new_refresh_token)
    logging.info(f"app\\auth\\router.py: Refresh tokens issued for user_id: {user.id}")
    
    return STokenRefreshResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
