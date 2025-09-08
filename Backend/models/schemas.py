from pydantic import BaseModel

class ClinicRegisterRequest(BaseModel):
    name: str

class ClinicRegisterResponse(BaseModel):
    clinic_id: str
    clinic_secret: str

class ClinicTokenRequest(BaseModel):
    clinic_id: str
    clinic_secret: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ClinicPrincipal(BaseModel):
    clinic_id: str
    clinic_name: str
    plan: str = "standard"