from datetime import datetime

from sqlalchemy.orm import Session

from app.config import STORAGE_NODES, REPLICATION_FACTOR
from app.models import ChunkMetadata, ChunkReplica, RepairTaskStatus
from app.services.storage import read_chunk, store_chunk
from app.utils.hashing import sha256_bytes
from app.utils.logger import get_logger
from app.events.audit import emit_audit_event

logger = get_logger(__name__)


def get_alive_nodes() -> list[str]:
    alive_nodes = []

    for node_name, node_path in STORAGE_NODES.items():
        if node_path.exists() and node_path.is_dir():
            alive_nodes.append(node_name)

    return alive_nodes


def find_under_replicated_chunks(db: Session) -> list[ChunkMetadata]:
    under_replicated_chunks = []

    chunks = db.query(ChunkMetadata).all()

    for chunk in chunks:
        valid_replicas = []

        for replica in chunk.replicas:
            data = read_chunk(replica.path)

            if data is None:
                continue

            if sha256_bytes(data) == chunk.chunk_hash:
                valid_replicas.append(replica)

        if len(valid_replicas) < REPLICATION_FACTOR:
            under_replicated_chunks.append(chunk)

    return under_replicated_chunks


def create_repair_task_record(
    db: Session,
    chunk_id: int,
    celery_task_id: str | None = None
) -> RepairTaskStatus:
    task = RepairTaskStatus(
        chunk_id=chunk_id,
        task_id=celery_task_id,
        status="queued",
        message="Repair task queued",
        retries=0
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    emit_audit_event(
        db=db,
        event_type="chunk.repair.queued",
        entity_type="chunk",
        entity_id=str(chunk_id),
        message="Repair task queued",
        payload={"chunk_id": chunk_id}
    )

    return task


def update_repair_task_status(
    db: Session,
    chunk_id: int,
    status: str,
    message: str,
    task_id: str | None = None
) -> None:
    task = (
        db.query(RepairTaskStatus)
        .filter(RepairTaskStatus.chunk_id == chunk_id)
        .order_by(RepairTaskStatus.created_at.desc())
        .first()
    )

    if task is None:
        task = RepairTaskStatus(
            chunk_id=chunk_id,
            task_id=task_id,
            status=status,
            message=message,
            updated_at=datetime.utcnow()
        )
        db.add(task)
    else:
        task.status = status
        task.message = message
        task.updated_at = datetime.utcnow()

        if task_id is not None:
            task.task_id = task_id

    db.commit()


def repair_single_chunk(db: Session, chunk_id: int) -> dict:
    chunk = (
        db.query(ChunkMetadata)
        .filter(ChunkMetadata.id == chunk_id)
        .first()
    )

    if chunk is None:
        return {
            "chunk_id": chunk_id,
            "status": "failed",
            "message": "Chunk not found"
        }

    update_repair_task_status(
        db=db,
        chunk_id=chunk_id,
        status="running",
        message="Repair started"
    )

    emit_audit_event(
        db=db,
        event_type="chunk.repair.started",
        entity_type="chunk",
        entity_id=str(chunk_id),
        message="Repair started",
        payload={"chunk_id": chunk_id}
    )

    alive_nodes = get_alive_nodes()

    valid_replicas = []

    for replica in chunk.replicas:
        data = read_chunk(replica.path)

        if data is None:
            continue

        if sha256_bytes(data) == chunk.chunk_hash:
            valid_replicas.append(replica)

    if len(valid_replicas) >= REPLICATION_FACTOR:
        update_repair_task_status(
            db=db,
            chunk_id=chunk_id,
            status="skipped",
            message="Chunk already has enough valid replicas"
        )

        return {
            "chunk_id": chunk_id,
            "status": "skipped",
            "message": "Chunk already has enough valid replicas"
        }

    if not valid_replicas:
        update_repair_task_status(
            db=db,
            chunk_id=chunk_id,
            status="failed",
            message="No valid source replica found"
        )

        emit_audit_event(
            db=db,
            event_type="chunk.repair.failed",
            entity_type="chunk",
            entity_id=str(chunk_id),
            message="No valid source replica found",
            payload={"chunk_id": chunk_id}
        )

        return {
            "chunk_id": chunk_id,
            "status": "failed",
            "message": "No valid source replica found"
        }

    source_replica = valid_replicas[0]
    source_data = read_chunk(source_replica.path)

    existing_nodes = {replica.node_name for replica in valid_replicas}

    candidate_nodes = [
        node for node in alive_nodes
        if node not in existing_nodes
    ]

    repaired_nodes = []

    while len(valid_replicas) < REPLICATION_FACTOR and candidate_nodes:
        target_node = candidate_nodes.pop(0)

        new_path = store_chunk(
            node_name=target_node,
            file_id=chunk.file_id,
            chunk_index=chunk.chunk_index,
            chunk_data=source_data
        )

        new_replica = ChunkReplica(
            chunk_id=chunk.id,
            node_name=target_node,
            path=new_path
        )

        db.add(new_replica)
        db.commit()
        db.refresh(new_replica)

        valid_replicas.append(new_replica)
        repaired_nodes.append(target_node)

        emit_audit_event(
            db=db,
            event_type="chunk.replicated",
            entity_type="chunk",
            entity_id=str(chunk.id),
            message=f"Chunk replicated to {target_node}",
            payload={
                "chunk_id": chunk.id,
                "target_node": target_node,
                "path": new_path
            }
        )

    if len(valid_replicas) < REPLICATION_FACTOR:
        update_repair_task_status(
            db=db,
            chunk_id=chunk_id,
            status="partial",
            message="Repair partially completed"
        )

        return {
            "chunk_id": chunk_id,
            "status": "partial",
            "repaired_nodes": repaired_nodes
        }

    update_repair_task_status(
        db=db,
        chunk_id=chunk_id,
        status="completed",
        message="Repair completed successfully"
    )

    emit_audit_event(
        db=db,
        event_type="chunk.repair.completed",
        entity_type="chunk",
        entity_id=str(chunk_id),
        message="Repair completed successfully",
        payload={
            "chunk_id": chunk_id,
            "repaired_nodes": repaired_nodes
        }
    )

    logger.info(f"Repair completed for chunk {chunk_id}")

    return {
        "chunk_id": chunk_id,
        "status": "completed",
        "repaired_nodes": repaired_nodes
    }


def repair_under_replicated_chunks(db: Session) -> dict:
    repaired_chunks = []
    failed_chunks = []

    chunks = find_under_replicated_chunks(db)

    for chunk in chunks:
        result = repair_single_chunk(db, chunk.id)

        if result["status"] in {"completed", "skipped", "partial"}:
            repaired_chunks.append(result)
        else:
            failed_chunks.append(result)

    return {
        "mode": "sync",
        "repaired_chunks": repaired_chunks,
        "failed_chunks": failed_chunks
    }