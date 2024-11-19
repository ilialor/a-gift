from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import HTTPException

class TWAAuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.access_token_expires = timedelta(minutes=30)
        self.refresh_token_expires = timedelta(days=7)
        self.refresh_threshold = timedelta(minutes=5)  # Refresh token if less than 5 minutes left

    def create_token(self, user_id: int) -> str:
        """Create JWT token with user_id and timestamp"""
        payload = {
            "user_id": user_id,
            "created": datetime.now(timezone.utc).timestamp()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token with user_id and expiration"""
        expires = datetime.utcnow() + self.access_token_expires
        payload = {
            "user_id": user_id,
            "type": "access",
            "exp": expires
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def create_refresh_token(self, user_id: int) -> str:
        """Create JWT refresh token with user_id and expiration"""
        expires = datetime.utcnow() + self.refresh_token_expires
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": expires
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def validate_token(self, token: str, token_type: str = "access") -> int:
        """Validate JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            if payload.get("type") != token_type:
                raise HTTPException(status_code=401, detail="Invalid token type")
            return payload.get("user_id")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def should_refresh_token(self, token: str) -> bool:
        """Check if token should be refreshed based on expiration time"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            exp = datetime.fromtimestamp(payload["exp"])
            now = datetime.utcnow()
            return (exp - now) < self.refresh_threshold
        except JWTError:
            return True
