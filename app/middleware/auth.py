from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
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

    async def __call__(self, request: Request, call_next):
        try:
            if request.url.path.startswith('/twa/'):
                # Get all possible auth parameters
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

                logging.info(f"Auth parameters: start_param={bool(start_param)}, refresh_token={bool(refresh_token)}, init_data={bool(init_data)}")

                try:
                    # Try to authenticate user
                    user = None

                    # First try token authentication
                    if start_param and refresh_token:
                        try:
                            user_id = self.auth_manager.validate_token(start_param)
                            async with async_session_maker() as session:
                                user = await UserDAO(session).get_user_by_id(user_id)
                        except Exception as e:
                            logging.error(f"Token validation failed: {e}")

                    # If token auth failed but we have init_data, try Telegram validation
                    if not user and init_data:
                        try:
                            validated_data = self.telegram_validator.validate_init_data(init_data)
                            user_telegram_id = validated_data["user"]["id"]
                            
                            async with async_session_maker() as session:
                                from app.giftme.schemas import UserFilterPydantic
                                filter_model = UserFilterPydantic(telegram_id=user_telegram_id)
                                user = await UserDAO.find_one_or_none(session=session, filters=filter_model)

                                # Create user if not exists
                                if not user:
                                    from app.giftme.schemas import UserCreate, ProfilePydantic
                                    profile = ProfilePydantic(
                                        first_name=validated_data["user"].get("first_name"),
                                        last_name=validated_data["user"].get("last_name")
                                    )

                                    values = UserCreate(
                                        telegram_id=user_telegram_id,
                                        username=validated_data["user"].get("username"),
                                        profile=profile
                                    )
                                    user = await UserDAO.add(session=session, values=values)

                                    # Create new tokens
                                    access_token = self.auth_manager.create_access_token(user.id)
                                    refresh_token = self.auth_manager.create_refresh_token(user.id)
                                    await UserDAO.update_refresh_token(session, user.id, refresh_token)

                        except Exception as e:
                            logging.error(f"Telegram validation failed: {e}")

                    # Set user in request state
                    request.state.user = user
                    if user:
                        request.state.user_id = user.id
                        logging.info(f"User authenticated: {user.id}")

                    # Process the request
                    response = await call_next(request)

                    # Add CORS headers for API requests
                    if request.url.path.startswith('/twa/api/'):
                        response.headers['Access-Control-Allow-Headers'] = 'X-Start-Param, X-Refresh-Token, X-Init-Data'
                        response.headers['Access-Control-Allow-Origin'] = '*'

                    return response

                except Exception as e:
                    logging.error(f"Auth middleware error: {e}")
                    if request.url.path.startswith('/twa/api/'):
                        return JSONResponse(
                            status_code=401,
                            content={"detail": "Authentication failed"}
                        )
                    return RedirectResponse(url="/twa/error?message=Authentication+failed")

            # For non-TWA routes
            return await call_next(request)
        except Exception as e:
            logging.error(f"Auth middleware error: {e}")
            # Вместо редиректа, просто пропускаем запрос дальше
            return await call_next(request)
