from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Annotated
from Backend.config.constants import MODEL_CONFIG, PROMPT_CONFIG, EXPLAIN_PROMPT
from Backend.services.chatbot_service import create_agent
from Database.db_history import (
    ensure_tables,
    create_conversation,
    list_conversations,
    get_conversation,
    delete_conversation,
    add_message,
    list_messages,
    title_from_text,
    rename_conversation,
)
from Backend.models.schemas import (
    ConversationOut,
    MessageIn,
    MessageOut,
    ConversationWithMessages,
)
from Backend.core.deps import get_current_clinic
from Backend.utils.tools import bots, is_image
from Database.firebaseActions import upload_to_firebase, download_from_firebase, download_all_from_firebase, delete_from_firebase, get_download_url


CurrentClinic = Annotated[dict, Depends(get_current_clinic)]
router = APIRouter(prefix = "/api", tags=["file-upload"])

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_to_firebase_placeholder(current: CurrentClinic, file: UploadFile = File(...)):
    """
    Placeholder endpoint that receives a file and will later
    stream it to Firebase Storage.

    For now, we just acknowledge receipt.
    """
    clinic_id = str(current["clinic_id"])

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    upload_to_firebase(clinic_id, file)
    return {
        "status": "accepted",
        "message": "Upload route reachable; Firebase integration pending.",
        "filename": file.filename,
        "content_type": file.content_type,
    }

@router.get("/download/{file_name}", status_code=200)
async def download_file_from_firebase(current: CurrentClinic, file_name: str):
    clinic_id = str(current["clinic_id"])
    local_path = f"/tmp/{file_name}"
    try:
        url = get_download_url(clinic_id, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download file: {e}")
    return {"status": "success", "message": f"{url}"}

@router.delete("/delete/{file_name}", status_code=204)
async def delete_file_from_firebase(current: CurrentClinic, file_name: str):
    clinic_id = str(current["clinic_id"])
    try:
        existed = delete_from_firebase(clinic_id, file_name)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file name")

    if not existed:
        raise HTTPException(status_code=404, detail="File not found")
    return  # 204 No Content



