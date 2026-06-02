from sqlalchemy.orm import Session

from app.config import STORAGE_NODES, REPLICATION_FACTOR
from app.models import ChunkMetadata, ChunkReplica
from app.services.storage import read_chunk, store_chunk
from app.utils.hashing import sha256_bytes
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_alive_nodes() -> list[str]:
    alive_nodes = []

    for node_name, node_path in STORAGE_NODES.items():
        if node_path.exists() and node_path.is_dir():
            alive_nodes.append(node_name)

    return alive_nodes


def repair_under_replicated_chunks(db: Session) -> dict:
    alive_nodes = get_alive_nodes()

    repaired_chunks = []
    failed_chunks = []

    chunks = db.query(ChunkMetadata).all()

    for chunk in chunks:
        valid_replicas = []

        for replica in chunk.replicas:
            data = read_chunk(replica.path)

            if data is None:
                continue

            if sha256_bytes(data) == chunk.chunk_hash:
                valid_replicas.append(replica)

        if len(valid_replicas) >= REPLICATION_FACTOR:
            continue

        if not valid_replicas:
            failed_chunks.append(
                {
                    "chunk_id": chunk.id,
                    "reason": "No valid source replica found"
                }
            )
            continue

        source_replica = valid_replicas[0]
        source_data = read_chunk(source_replica.path)

        existing_nodes = {replica.node_name for replica in valid_replicas}

        candidate_nodes = [
            node for node in alive_nodes
            if node not in existing_nodes
        ]

        while (
            len(valid_replicas) < REPLICATION_FACTOR
            and candidate_nodes
        ):
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

            repaired_chunks.append(
                {
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "new_node": target_node
                }
            )

            logger.info(
                f"Repaired chunk {chunk.id} on node {target_node}"
            )

    return {
        "repaired_chunks": repaired_chunks,
        "failed_chunks": failed_chunks
    }