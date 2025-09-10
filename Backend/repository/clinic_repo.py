from dataclasses import dataclass
from typing import Optional
from Database.db_register import Clinic


@dataclass
class Clinic:
    id: str
    name: str
    active: bool = True
    plan: str = "standard"



def validate_credentials(clinic_id: str, password: str) -> Optional[Clinic]:
    ok = Clinic.authenticate(clinic_id, password)
    if not ok:
        return None
    name = Clinic.get_clinic_name(clinic_id) or clinic_id
    return Clinic(id=clinic_id, name=name)