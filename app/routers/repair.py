from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import ENABLE_ASYNC_REPAIR
from app.database import get_db
from app.models import RepairTaskStatus
from app.services.repair import (
    repair_under_replicated_chunks,
    find_under_replicated_chunks,
    create_repair_task_record,
)
from app.workers.tasks import repair_chunk_task

router = APIRouter(prefix="/repair", tags=["Repair"])


@router.post("/run")
def run_repair(db: Session = Depends(get_db)):
    if not ENABLE_ASYNC_REPAIR:
        return repair_under_replicated_chunks(db)

    chunks = find_under_replicated_chunks(db)

    queued_tasks = []

    for chunk in chunks:
        task_result = repair_chunk_task.delay(chunk.id)

        create_repair_task_record(
            db=db,
            chunk_id=chunk.id,
            celery_task_id=task_result.id
        )

        queued_tasks.append(
            {
                "chunk_id": chunk.id,
                "task_id": task_result.id,
                "status": "queued"
            }
        )

    return {
        "mode": "async",
        "queued_tasks": queued_tasks,
        "total_queued": len(queued_tasks)
    }


@router.get("/tasks")
def list_repair_tasks(db: Session = Depends(get_db)):
    tasks = (
        db.query(RepairTaskStatus)
        .order_by(RepairTaskStatus.created_at.desc())
        .all()
    )

    return [
        {
            "id": task.id,
            "task_id": task.task_id,
            "chunk_id": task.chunk_id,
            "status": task.status,
            "message": task.message,
            "retries": task.retries,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        for task in tasks
    ]