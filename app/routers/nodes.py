from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import STORAGE_NODES
from app.schemas import NodeHealthResponse
from app.cache.redis_cache import cache, node_health_key
from app.events.audit import emit_audit_event
from app.database import get_db

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.get("/health", response_model=list[NodeHealthResponse])
def check_nodes_health(db: Session = Depends(get_db)):
    cached = cache.get_json(node_health_key())

    if cached is not None:
        return cached

    health_status = []

    for node_name, node_path in STORAGE_NODES.items():
        if node_path.exists() and node_path.is_dir():
            status = "alive"
        else:
            status = "dead"

            emit_audit_event(
                db=db,
                event_type="node.failed",
                entity_type="node",
                entity_id=node_name,
                message=f"Storage node failed: {node_name}",
                payload={
                    "node_name": node_name,
                    "path": str(node_path)
                }
            )

        health_status.append(
            {
                "node_name": node_name,
                "path": str(node_path),
                "status": status
            }
        )

    cache.set_json(node_health_key(), health_status)

    return health_status