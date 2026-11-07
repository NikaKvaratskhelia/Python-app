from datetime import datetime, timedelta, timezone
from core.config import settings
import jwt

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"


def create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=8)

    to_encode = {"sub": str(user_id), "username": username, "role": role, "exp": expire}

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
