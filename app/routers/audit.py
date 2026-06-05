import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get("")
def list_audit_logs(db: Session = Depends(get_db), limit: int = 100):
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    response = []

    for log in logs:
        try:
            payload = json.loads(log.payload or "{}")
        except Exception:
            payload = {}

        response.append(
            {
                "id": log.id,
                "event_type": log.event_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "message": log.message,
                "payload": payload,
                "created_at": log.created_at
            }
        )

    return response