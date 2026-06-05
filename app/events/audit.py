import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.config import ENABLE_AUDIT_LOG
from app.models import AuditLog
from app.utils.logger import get_logger

logger = get_logger(__name__)


def emit_audit_event(
    db: Session,
    event_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    message: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None
) -> None:
    if not ENABLE_AUDIT_LOG:
        return

    try:
        audit_log = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            message=message,
            payload=json.dumps(payload or {}, default=str)
        )

        db.add(audit_log)
        db.commit()

        logger.info(f"Audit event emitted: {event_type}")

    except Exception as exc:
        db.rollback()
        logger.warning(f"Failed to emit audit event {event_type}: {exc}")