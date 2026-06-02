from sqlalchemy.orm import Session

from app.models import FileMetadata, ChunkMetadata, ChunkReplica


def create_file_metadata(
    db: Session,
    filename: str,
    content_type: str | None,
    size_bytes: int,
    file_hash: str,
    total_chunks: int
) -> FileMetadata:
    file_metadata = FileMetadata(
        filename=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        file_hash=file_hash,
        total_chunks=total_chunks
    )

    db.add(file_metadata)
    db.commit()
    db.refresh(file_metadata)

    return file_metadata


def create_chunk_metadata(
    db: Session,
    file_id: int,
    chunk_index: int,
    chunk_hash: str,
    size_bytes: int
) -> ChunkMetadata:
    chunk_metadata = ChunkMetadata(
        file_id=file_id,
        chunk_index=chunk_index,
        chunk_hash=chunk_hash,
        size_bytes=size_bytes
    )

    db.add(chunk_metadata)
    db.commit()
    db.refresh(chunk_metadata)

    return chunk_metadata


def create_replica_metadata(
    db: Session,
    chunk_id: int,
    node_name: str,
    path: str
) -> ChunkReplica:
    replica = ChunkReplica(
        chunk_id=chunk_id,
        node_name=node_name,
        path=path
    )

    db.add(replica)
    db.commit()
    db.refresh(replica)

    return replica