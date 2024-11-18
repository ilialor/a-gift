from datetime import datetime, timedelta, timezone  # Added timezone
from jose import jwt, JWTError
from fastapi import HTTPException
import logging

class TWAAuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.access_token_expires = timedelta(minutes=30)
        self.refresh_token_expires = timedelta(days=7)

    def create_token(self, user_id: int) -> str:
        """Create JWT token with user_id and timestamp"""
        payload = {
            "user_id": user_id,
            "created": datetime.now(timezone.utc).timestamp()  # Updated utcnow to now(timezone.utc)
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token with user_id and expiration"""
        expire = datetime.now(timezone.utc) + self.access_token_expires  # Updated utcnow to now(timezone.utc)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token with user_id and expiration"""
        expire = datetime.now(timezone.utc) + self.refresh_token_expires  # Updated utcnow to now(timezone.utc)
        payload = {
            "user_id": user_id,
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def validate_token(self, token: str, token_type: str = "access") -> int:
        """
        Validate token and return user_id
        token_type: 'access' or 'refresh'
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if payload.get("type") != token_type:
                logging.error(f"app\twa\auth.py TWAAuthManager: Invalid token type. Expected {token_type}, got {payload.get('type')}")
                raise JWTError("Invalid token type")
            logging.info(f"app\twa\auth.py TWAAuthManager: Token valid for user_id: {payload['user_id']}")
            return payload['user_id']
        except JWTError as e:
            logging.error(f"app\twa\auth.py TWAAuthManager: Invalid token. Error: {str(e)}")
            raise HTTPException(status_code=401, detail="Invalid token")
