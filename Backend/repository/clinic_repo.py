from dataclasses import dataclass
from typing import Optional
from Database.db_register import (
    register_clinic as db_register_clinic,
    authenticate as db_authenticate,
    get_clinic_name as db_get_clinic_name,
    ensure_table,
)


@dataclass
class Clinic:
    id: str
    name: str
    active: bool = True
    plan: str = "standard"


def create_clinic(name: str, password: str) -> Clinic:
    ensure_table()
    clinic_id = db_register_clinic(name=name, password_plain=password)
    return Clinic(id=clinic_id, name=name)



def validate_credentials(clinic_id: str, password: str) -> Optional[Clinic]:
    ensure_table()
    ok = db_authenticate(clinic_id, password)
    if not ok:
        return None
    name = db_get_clinic_name(clinic_id) or clinic_id
    return Clinic(id=clinic_id, name=name)