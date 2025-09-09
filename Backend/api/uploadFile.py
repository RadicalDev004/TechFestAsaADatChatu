from fastapi import APIRouter, UploadFile, File, HTTPException, status
from ..models.schemas import (
    ClinicRegisterRequest, ClinicRegisterResponse,
    ClinicTokenRequest, TokenResponse, ClinicPrincipal
)
from ..repository.clinic_repo import create_clinic, validate_credentials
from ..core.security import create_clinic_token
from ..core.deps import get_current_clinic
from Database.firebaseActions import upload_to_firebase, download_from_firebase, download_all_from_firebase

router = APIRouter(prefix = "/api", tags=["file-upload"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_to_firebase_placeholder(file: UploadFile = File(...)):
    """
    Placeholder endpoint that receives a file and will later
    stream it to Firebase Storage.

    For now, we just acknowledge receipt.
    """

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    upload_to_firebase("test_id", file)
    return {
        "status": "accepted",
        "message": "Upload route reachable; Firebase integration pending.",
        "filename": file.filename,
        "content_type": file.content_type,
    }


