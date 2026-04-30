from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

_ALGORITHM = "HS256"
_TTL_DAYS = 1


def create_jwt(user_id: int, secret: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=_TTL_DAYS),
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def verify_jwt(token: str, secret: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM])
        return int(payload["sub"])
    except Exception:
        return None
