from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.twa.auth import TWAAuthManager
from app.twa.validation import TelegramWebAppValidator
from app.config import settings
from app.dao.dao import UserDAO
from app.dao.session_maker import async_session_maker
import logging

class TelegramWebAppMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_manager = TWAAuthManager(settings.secret_key)
        self.telegram_validator = TelegramWebAppValidator(settings.BOT_TOKEN)

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith('/twa/'):
            # Allow unauthenticated access to the index page
            if request.url.path in ['/twa/', '/twa/index']:
                request.state.user = None
                return await call_next(request)
            # Skip auth check for error page and public gift detail
            if request.url.path in ['/twa/error'] or request.url.path.startswith('/twa/public/gifts/'):
                request.state.user = None
                return await call_next(request)

            # Get auth parameters from query params or headers
            start_param = (
                request.query_params.get('startParam') or 
                request.headers.get('X-Start-Param')
            )
            refresh_token = (
                request.query_params.get('refresh_token') or 
                request.headers.get('X-Refresh-Token')
            )
            init_data = (
                request.query_params.get('initData') or 
                request.headers.get('X-Init-Data')
            )

            logging.info(f"Processing request to {request.url.path}")
            logging.info(f"Start param present: {bool(start_param)}")
            logging.info(f"Refresh token present: {bool(refresh_token)}")
            logging.info(f"Init data present: {bool(init_data)}")
            logging.info(f"Method: {request.method}")
            # logging.info(f"Headers: {dict(request.headers)}")

            if not start_param or not refresh_token:
                # Check if it's an API request
                if request.url.path.startswith('/twa/api/'):
                    raise HTTPException(status_code=401, detail="Unauthorized")
                request.state.user = None
                return RedirectResponse(url="/twa/error?message=Missing+authentication+parameters")

            try:
                # Validate Telegram data if present
                if init_data:
                    try:
                        validated_data = self.telegram_validator.validate_init_data(init_data)
                        request.state.telegram_data = validated_data
                        logging.info(f"Validated Telegram data: {validated_data}")
                    except Exception as e:
                        logging.error(f"Telegram data validation failed: {e}")
                        return RedirectResponse(url="/twa/error?message=Invalid+Telegram+data")

                # Validate the token
                user_id = self.auth_manager.validate_token(start_param)

                # Get user from database
                async with async_session_maker() as session:
                    user = await UserDAO(session).get_user_by_id(user_id)

                if not user:
                    logging.warning(f"User not found for user_id: {user_id}")
                    request.state.user = None
                    return RedirectResponse(url="/twa/error?message=User+not+found")

                # Store user info in request state
                request.state.user = user
                request.state.user_id = user.id

                # Handle token refresh if needed
                if self.auth_manager.should_refresh_token(start_param):
                    new_access_token = self.auth_manager.create_access_token(user.id)
                    response = await call_next(request)
                    response.headers['X-New-Access-Token'] = new_access_token
                    response.headers['Access-Control-Expose-Headers'] = 'X-New-Access-Token'
                    return response

                # Process the request with auth data
                response = await call_next(request)
                
                # Add CORS headers for API requests
                if request.url.path.startswith('/twa/api/'):
                    response.headers['Access-Control-Allow-Headers'] = 'X-Start-Param, X-Refresh-Token, X-Init-Data'
                    response.headers['Access-Control-Allow-Origin'] = '*'
                
                return response

            except Exception as e:
                logging.error(f"Exception during authentication: {str(e)}")
                logging.error(f"Request path: {request.url.path}")
                logging.error(f"Request method: {request.method}")
                request.state.user = None
                
                # Return JSON response for API requests
                if request.url.path.startswith('/twa/api/'):
                    raise HTTPException(status_code=401, detail="Authentication failed")
                
                return RedirectResponse(url="/twa/error?message=Authentication+failed")

        return await call_next(request)
