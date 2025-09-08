from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from .config import JWT_SECRET, JWT_ALG, JWT_EXPIRES_MIN

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

