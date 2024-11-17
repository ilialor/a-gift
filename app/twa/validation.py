from hashlib import sha256
import hmac
import json
from urllib.parse import parse_qs, unquote
from fastapi import HTTPException

class TelegramWebAppValidator:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        # Generate secret key from bot token
        secret = hmac.new(b"WebAppData", bot_token.encode(), sha256).digest()
        self.secret_key = hmac.new(b"WebAppData", secret, sha256).digest()

    def validate_init_data(self, init_data: str) -> dict:
        """
        Validate Telegram WebApp init data
        Raises HTTPException if validation fails
        """
        try:
            # Parse init_data
            parsed_data = dict(parse_qs(init_data))
            data = {k: v[0] for k, v in parsed_data.items()}
            
            if 'hash' not in data:
                raise HTTPException(status_code=401, detail="Hash not found")

            # Get hash from data
            hash_str = data.pop('hash')
            
            # Sort remaining data
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(data.items())
            )
            
            # Generate secret key and calculate hash
            secret_key = self.secret_key
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                sha256
            ).hexdigest()
            
            # Validate hash
            if calculated_hash != hash_str:
                raise HTTPException(status_code=401, detail="Invalid hash")
            
            # Decode user data
            if 'user' in data:
                data['user'] = json.loads(unquote(data['user']))
                
            return data

        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Validation failed: {str(e)}")
