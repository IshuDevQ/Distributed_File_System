from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.repair import repair_under_replicated_chunks

router = APIRouter(prefix="/repair", tags=["Repair"])


@router.post("/run")
def run_repair(db: Session = Depends(get_db)):
    return repair_under_replicated_chunks(db)