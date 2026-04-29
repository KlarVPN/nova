import hashlib
import hmac
import json
import time
from urllib.parse import unquote, parse_qsl
from typing import Optional


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> Optional[dict]:
    """
    Validate Telegram WebApp initData and return parsed user dict, or None if invalid.
    """
    if not init_data:
        return None

    params = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = params.pop("hash", None)
    if not received_hash:
        return None

    # Check auth_date to prevent replay attacks
    auth_date = params.get("auth_date")
    if auth_date:
        try:
            age = int(time.time()) - int(auth_date)
            if age > max_age_seconds:
                return None
        except ValueError:
            return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    user_str = params.get("user")
    if not user_str:
        return None

    try:
        return json.loads(unquote(user_str))
    except (json.JSONDecodeError, ValueError):
        return None


def validate_login_widget_data(data: dict, bot_token: str, max_age_seconds: int = 86400) -> Optional[dict]:
    """Validate Telegram Login Widget payload and return user dict."""
    if not data or not isinstance(data, dict):
        return None

    received_hash = data.get("hash")
    if not received_hash or not isinstance(received_hash, str):
        return None

    auth_date = data.get("auth_date")
    if auth_date is None:
        return None

    try:
        age = int(time.time()) - int(auth_date)
        if age > max_age_seconds:
            return None
    except (ValueError, TypeError):
        return None

    check_data = {k: v for k, v in data.items() if k != "hash" and v is not None}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(check_data.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return None

    user_id = data.get("id")
    if user_id is None:
        return None

    try:
        parsed_id = int(user_id)
    except (TypeError, ValueError):
        return None

    return {
        "id": parsed_id,
        "first_name": str(data.get("first_name") or ""),
        "last_name": str(data.get("last_name") or "") or None,
        "username": str(data.get("username") or "") or None,
        "photo_url": str(data.get("photo_url") or "") or None,
    }
