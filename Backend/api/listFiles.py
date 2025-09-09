# Backend/routers/whatever_module.py  (the same file where your router is defined)
from fastapi import HTTPException, Response, Depends,APIRouter
from typing import Annotated, Dict, List, Optional
from datetime import timedelta

from Backend.core.deps import get_current_clinic
from Database.firebaseActions import list_files_from_firebase  # adjust path if needed

CurrentClinic = Annotated[dict, Depends(get_current_clinic)]
router = APIRouter(prefix="/api", tags=["list files"])

@router.get("/listFiles", status_code=200)
def list_files(current: CurrentClinic) -> Dict[str, List[Dict[str, str]]]:
    clinic_id = str(current["clinic_id"])
    try:
        names = list_files_from_firebase(clinic_id)  # e.g. ["4d2464/clinic=sons.csv", "4d2464/report.csv"]
        files = [
            {
                "path": n,              # full Firebase path
                "name": n.split("/")[-1]  # just the last element after "/"
            }
            for n in names
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {e}")

    return {"files": files}