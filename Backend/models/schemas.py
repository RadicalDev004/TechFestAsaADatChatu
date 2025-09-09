from pydantic import BaseModel

class ClinicRegisterRequest(BaseModel):
    name: str
    password: str

class ClinicRegisterResponse(BaseModel):
    clinic_id: str
    name: str

class ClinicTokenRequest(BaseModel):
    clinic_id: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ClinicPrincipal(BaseModel):
    clinic_id: str
    clinic_name: str
    plan: str = "standard"
