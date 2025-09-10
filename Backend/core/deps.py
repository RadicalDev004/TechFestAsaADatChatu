from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import decode_token
from Database.db_register import Clinic
_bearer = HTTPBearer(auto_error=True)

def get_current_clinic(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    try:
        payload = decode_token(creds.credentials)
        clinic_email = payload.get("clinic_email")
        clinic_id = Clinic.get_clinic_id_by_email(clinic_email)
        if not clinic_email:
            raise ValueError("missing clinic_id")
        return {
            "clinic_id": clinic_id,
            "clinic_name": payload.get("clinic_name")
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

