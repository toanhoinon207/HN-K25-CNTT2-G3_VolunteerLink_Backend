from datetime import datetime, timedelta, timezone
import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt
from app.core.config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict, expires_minutes: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes = expires_minutes)
    payload["exp"] = expire
    payload["type"] = "access"
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm = settings.JWT_ALGORITHM)

def create_refresh_token(data: dict, expires_days: int = settings.REFRESH_TOKEN_EXPIRE_DAYS):
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days = expires_days)
    payload["exp"] = expire
    payload["type"] = "refresh"
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm = settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms = [settings.JWT_ALGORITHM],
            options = {"require_exp": True, "require_sub": True}
        )

        if payload.get("type") != "access":
            raise ValueError("TOKEN_INVALID")
        return payload

    except ExpiredSignatureError:
        raise ValueError("TOKEN_EXPIRED")

    except JWTError:
        raise ValueError("TOKEN_INVALID")


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require_exp": True, "require_sub": True}
        )

        if payload.get("type") != "refresh":
            raise ValueError("TOKEN_INVALID")

        return payload

    except ExpiredSignatureError:
        raise ValueError("TOKEN_EXPIRED")

    except JWTError:
        raise ValueError("TOKEN_INVALID")
