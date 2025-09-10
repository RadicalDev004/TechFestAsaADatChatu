# Backend/routers/whatever_module.py  (the same file where your router is defined)
from fastapi import HTTPException, Response, Depends,APIRouter
from typing import Annotated, Dict, List, Optional
from datetime import datetime
from datetime import timedelta
from pydantic import BaseModel

from Backend.core.deps import get_current_clinic
from Database.firebaseActions import list_files_from_firebase  # adjust path if needed

CurrentClinic = Annotated[dict, Depends(get_current_clinic)]
router = APIRouter(prefix="/api", tags=["list files"])

class FileItem(BaseModel):
    path: str
    name: str
    size: Optional[str] = None
    updated: Optional[str] = None

class ListFilesResponse(BaseModel):
    files: List[FileItem]

@router.get("/listFiles", status_code=200)
def list_files(current: CurrentClinic) -> ListFilesResponse:
    clinic_id = str(current["clinic_id"])
    try:
        names = list_files_from_firebase(clinic_id) 
        files = [
            FileItem(
                path=n["name"],
                name=n["name"].split("/")[-1],
                size=human_readable_size(n.get("size")),
                updated=n.get("updated").strftime("%d/%m/%Y %H:%M") if n.get("updated") else None
            )
            for n in names
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")
    print({"files": files})
    return {"files": files}

def human_readable_size(size_in_bytes: int) -> str:
    if size_in_bytes is None:
        return None

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.2f} PB"
