from hashlib import sha256
import hmac
import json
from urllib.parse import parse_qs, unquote
from fastapi import HTTPException
import logging
from pydantic import BaseModel, validator
from typing import Optional, Dict

class TelegramWebAppValidator:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        # Generate secret key from bot token
        secret = hmac.new(b"WebAppData", bot_token.encode(), sha256).digest()
        self.secret_key = hmac.new(b"WebAppData", secret, sha256).digest()

    def validate_init_data(self, init_data: str) -> Dict:
        """
        Validate Telegram WebApp init data
        Args:
            init_data: Raw init_data string from Telegram WebApp
        Returns:
            Dict: Validated and parsed data
        Raises:
            HTTPException if validation fails
        """
        try:
            logging.info(f"Validating init_data: {init_data}")

            # Parse init_data
            parsed_data = dict(parse_qs(init_data))
            data = {k: v[0] for k, v in parsed_data.items()}
            logging.debug(f"Parsed data: {data}")

            if 'hash' not in data:
                logging.error("Hash not found in init_data")
                raise HTTPException(status_code=401, detail="Hash not found")

            # Get hash from data
            hash_str = data.pop('hash')
            logging.debug(f"Extracted hash: {hash_str}")

            # Sort remaining data
            data_check_string = '\n'.join(
                f"{k}={v}" for k, v in sorted(data.items())
            )
            logging.debug(f"Data check string: {data_check_string}")

            # Compute HMAC SHA256
            secret_key = sha256(self.bot_token.encode()).digest()
            hash_check = hmac.new(secret_key, 
                                data_check_string.encode(), 
                                sha256).hexdigest()

            logging.debug(f"Computed hash: {hash_check}")

            if not hmac.compare_digest(hash_str, hash_check):
                logging.error("Invalid hash in init_data")
                raise HTTPException(status_code=401, detail="Invalid hash")

            # Parse user data if present
            if 'user' in data:
                try:
                    data['user'] = json.loads(data['user'])
                except json.JSONDecodeError:
                    logging.warning("Could not parse user data")

            return data

        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"Error validating init_data: {e}")
            raise HTTPException(status_code=400, detail="Invalid init_data")

    def extract_user_id(self, init_data: Dict) -> Optional[int]:
        """
        Extract user_id from validated init_data
        Args:
            init_data: Validated init_data dictionary
        Returns:
            Optional[int]: User ID if present, None otherwise
        """
        try:
            if 'user' in init_data and isinstance(init_data['user'], dict):
                return init_data['user'].get('id')
        except Exception as e:
            logging.error(f"Error extracting user_id: {e}")
        return None
