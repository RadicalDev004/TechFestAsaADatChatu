from fastapi import APIRouter, HTTPException, status, Depends
from ..models.schemas import (
    ClinicRegisterRequest, ClinicRegisterResponse,
    ClinicTokenRequest, TokenResponse, ClinicPrincipal
)
from ..repository.clinic_repo import create_clinic, validate_credentials
from ..core.security import create_clinic_token
from ..core.deps import get_current_clinic

router = APIRouter(prefix="/auth/clinic", tags=["auth-clinic"])

@router.post("/register", response_model=ClinicRegisterResponse, status_code=201)
def register_clinic(body: ClinicRegisterRequest):

    clinic, secret = create_clinic(name=body.name)
    return ClinicRegisterResponse(clinic_id=clinic.id, clinic_secret=secret)

@router.post("/token", response_model=TokenResponse)
def issue_token(body: ClinicTokenRequest):

    clinic = validate_credentials(body.clinic_id, body.clinic_secret)
    if not clinic:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    token = create_clinic_token(clinic_id=clinic.id, clinic_name=clinic.name, plan=clinic.plan)
    return TokenResponse(access_token=token)

@router.get("/me", response_model=ClinicPrincipal)
def who_am_i(principal: dict = Depends(get_current_clinic)):

    return ClinicPrincipal(**principal)
