from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from app.twa.auth import TWAAuthManager
from app.twa.validation import TelegramWebAppValidator
from app.config import settings
import logging
from app.dao.database import async_session_maker
from app.auth.utils import validate_jwt_token  
from app.dao.dao import UserDAO

templates = Jinja2Templates(directory="app/templates")

class TelegramWebAppMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_manager = TWAAuthManager(settings.secret_key)
        self.telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith('/twa/'):
            # Exclude the error page from authentication checks
            if request.url.path.startswith('/twa/error'):
                return await call_next(request)
            
            # Get init data and start param from query params
            init_data = request.query_params.get('initData')
            start_param = request.query_params.get('tgWebAppStartParam')
            refresh_token = request.query_params.get('refresh_token')
            
            logging.info(f"app\middleware\auth.py Processing request to {request.url.path}")
            logging.info(f"app\middleware\auth.py Init data present: {bool(init_data)}")
            logging.info(f"app\middleware\auth.py Start param present: {bool(start_param)}")
            logging.info(f"app\middleware\auth.py Refresh token present: {bool(refresh_token)}")

            if not init_data and not start_param:
                logging.warning("app\middleware\auth.py Missing initData or tgWebAppStartParam")
                return RedirectResponse(url="/twa/error?message=Missing+authentication+parameters", status_code=400)
            
            try:
                if init_data:
                    # Telegram WebApp data validation
                    validated_data = self.telegram_validator.validate_init_data(init_data)
                    user_data = validated_data.get('user')
                    
                    if not user_data:
                        raise ValueError("No user data in init_data")

                    request.state.telegram_user = user_data
                
                if start_param:
                    # JWT token validation
                    user_id = self.auth_manager.validate_token(start_param)
                    if not user_id:
                        raise ValueError("Invalid JWT token")
                    
                    # Check if user exists
                    async with async_session_maker() as session:
                        user = await UserDAO.find_by_id(session, user_id)
                        if not user:
                            raise ValueError("User not found")
                        
                        # Update refresh_token if necessary
                        new_refresh_token = self.auth_manager.create_refresh_token(user_id)
                        await UserDAO.update_refresh_token(session, user_id, new_refresh_token)
                    
                    request.state.user_id = user_id

                logging.info(f"app\middleware\auth.py Successfully authenticated user_id: {request.state.user_id}")

                # Check if tokens are already present to avoid redirect loop
                if not (start_param and refresh_token):
                    # Redirect to URL with updated tokens
                    new_url = f"{request.url.path}?tgWebAppStartParam={start_param}&refresh_token={new_refresh_token}"
                    if init_data:
                        new_url += f"&initData={init_data}"
                    return RedirectResponse(url=new_url, status_code=302)

            except Exception as e:
                logging.error(f"app\middleware\auth.py Authentication error: {str(e)}")
                return RedirectResponse(url="/twa/error?message=Authentication+failed", status_code=401)

        response = await call_next(request)
        return response
