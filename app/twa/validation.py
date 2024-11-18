from hashlib import sha256
import hmac
import json
from urllib.parse import parse_qs, unquote
from fastapi import HTTPException
import logging

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
            logging.info(f"app\twa\validation.py: Validating init_data: {init_data}")  # Log incoming init_data

            # Parse init_data
            parsed_data = dict(parse_qs(init_data))
            data = {k: v[0] for k, v in parsed_data.items()}
            logging.debug(f"app\twa\validation.py: Parsed data: {data}")  # Log parsed data

            if 'hash' not in data:
                logging.error("app\twa\validation.py: Hash not found in init_data")
                raise HTTPException(status_code=401, detail="Hash not found")

            # Get hash from data
            hash_str = data.pop('hash')
            logging.debug(f"app\twa\validation.py: Extracted hash: {hash_str}")

            # Sort remaining data
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(data.items())
            )
            logging.debug(f"app\twa\validation.py: Data check string: {data_check_string}")

            # Generate secret key and calculate hash
            secret_key = self.secret_key
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                sha256
            ).hexdigest()
            logging.debug(f"app\twa\validation.py: Calculated hash: {calculated_hash}")

            # Validate hash
            if calculated_hash != hash_str:
                logging.error("app\twa\validation.py: Calculated hash does not match provided hash")
                raise HTTPException(status_code=401, detail="Invalid hash")

            # Decode user data
            if 'user' in data:
                data['user'] = json.loads(unquote(data['user']))
                logging.debug(f"app\twa\validation.py: Decoded user data: {data['user']}")
                
            logging.info("app\twa\validation.py: Init data validation successful")
            return data

        except Exception as e:
            logging.error(f"app\twa\validation.py: Validation failed: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Validation failed: {str(e)}")
