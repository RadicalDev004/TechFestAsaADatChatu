from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError  # <- import exceptions here
from passlib.context import CryptContext
from fastapi import Request
from .config import JWT_SECRET, JWT_ALG, JWT_EXPIRES_MIN

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
COOKIE_NAME = "access_token"

def get_current_session(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except ExpiredSignatureError:
        return None
    except JWTError:
        return None

    if not payload.get("isLogged"):
        return None

    # (Optional) extra check:
    if payload.get("exp") and datetime.now(timezone.utc).timestamp() > payload["exp"]:
        return None
    return payload

def hash_secret(raw: str) -> str:
    return pwd_ctx.hash(raw)

def verify_secret(raw: str, hashed: str) -> bool:
    return pwd_ctx.verify(raw, hashed)

def create_clinic_token(*, clinic_id: str, clinic_name: str, plan: str = "standard") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": f"clinic:{clinic_id}",
        "clinic_id": clinic_id,
        "clinic_name": clinic_name,
        "plan": plan,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_EXPIRES_MIN)).timestamp()),
        "isLogged": True,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
