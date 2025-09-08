from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import decode_token

_bearer = HTTPBearer(auto_error=True)

def get_current_clinic(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    try:
        payload = decode_token(creds.credentials)
        clinic_id = payload.get("clinic_id")
        if not clinic_id:
            raise ValueError("missing clinic_id")
        return {
            "clinic_id": clinic_id,
            "clinic_name": payload.get("clinic_name"),
            "plan": payload.get("plan", "standard"),
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

