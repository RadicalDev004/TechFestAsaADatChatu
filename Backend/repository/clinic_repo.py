from dataclasses import dataclass
from typing import Optional, Dict
import secrets
from ..core.security import hash_secret, verify_secret

@dataclass
class Clinic:
    id: str
    name: str
    secret_hash: str
    active: bool = True
    plan: str = "standard"


_CLINICS: Dict[str, Clinic] = {}

#testare
def _seed_demo():

    if "clinic_001" not in _CLINICS:
        _CLINICS["clinic_001"] = Clinic(
            id="clinic_001",
            name="LifeCare Demo",
            secret_hash=hash_secret("supersecret"),
            active=True,
            plan="standard",
        )
_seed_demo()


def create_clinic(name: str) -> tuple[Clinic, str]:

    clinic_id = f"clinic_{secrets.token_hex(4)}"
    clinic_secret = secrets.token_urlsafe(24)
    c = Clinic(id=clinic_id, name=name, secret_hash=hash_secret(clinic_secret))
    _CLINICS[clinic_id] = c
    return c, clinic_secret


def get_by_id(clinic_id: str) -> Optional[Clinic]:
    return _CLINICS.get(clinic_id)


def validate_credentials(clinic_id: str, clinic_secret: str) -> Optional[Clinic]:
    c = get_by_id(clinic_id)
    if not c or not c.active:
        return None
    return c if verify_secret(clinic_secret, c.secret_hash) else None