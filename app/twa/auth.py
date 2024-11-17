from datetime import datetime
import jwt
from fastapi import HTTPException

class TWAAuthManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def create_token(self, user_id: int) -> str:
        """Create JWT token with user_id and timestamp"""
        payload = {
            "user_id": user_id,
            "created": datetime.utcnow().timestamp()
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def validate_token(self, token: str, max_age: int = 1800) -> int:
        """
        Validate token and return user_id
        max_age: maximum token age in seconds (default 30 min)
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            timestamp = payload.get('created', 0)
            
            # Check token age
            if datetime.utcnow().timestamp() - timestamp > max_age:
                raise HTTPException(status_code=401, detail="Token expired")
                
            return payload['user_id']
            
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
