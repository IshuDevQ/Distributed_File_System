from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session, joinedload
from pathlib import Path

from app.database import get_db
from app.models import FileMetadata, ChunkMetadata, ChunkReplica
from app.schemas import FileResponse
from app.services.chunker import chunk_bytes
from app.services.replication import replicate_chunk
from app.services.metadata import (
    create_file_metadata,
    create_chunk_metadata,
    create_replica_metadata,
)
from app.services.storage import read_chunk
from app.utils.hashing import sha256_bytes
from app.config import DOWNLOAD_DIR, CHUNK_SIZE
from app.cache.redis_cache import (
    cache,
    file_metadata_key,
    file_list_key,
    invalidate_file_cache,
)
from app.events.audit import emit_audit_event

router = APIRouter(prefix="/files", tags=["Files"])


def file_to_dict(file_metadata: FileMetadata) -> dict:
    return {
        "id": file_metadata.id,
        "filename": file_metadata.filename,
        "content_type": file_metadata.content_type,
        "size_bytes": file_metadata.size_bytes,
        "file_hash": file_metadata.file_hash,
        "total_chunks": file_metadata.total_chunks,
        "created_at": str(file_metadata.created_at),
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "chunk_hash": chunk.chunk_hash,
                "size_bytes": chunk.size_bytes,
                "replicas": [
                    {
                        "node_name": replica.node_name,
                        "path": replica.path
                    }
                    for replica in chunk.replicas
                ]
            }
            for chunk in file_metadata.chunks
        ]
    }


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_data = await uploaded_file.read()

    file_hash = sha256_bytes(file_data)
    total_chunks = (len(file_data) + CHUNK_SIZE - 1) // CHUNK_SIZE

    file_metadata = create_file_metadata(
        db=db,
        filename=uploaded_file.filename,
        content_type=uploaded_file.content_type,
        size_bytes=len(file_data),
        file_hash=file_hash,
        total_chunks=total_chunks
    )

    for chunk_index, chunk_data in chunk_bytes(file_data):
        chunk_hash = sha256_bytes(chunk_data)

        chunk_metadata = create_chunk_metadata(
            db=db,
            file_id=file_metadata.id,
            chunk_index=chunk_index,
            chunk_hash=chunk_hash,
            size_bytes=len(chunk_data)
        )

        replicas = replicate_chunk(
            file_id=file_metadata.id,
            chunk_index=chunk_index,
            chunk_data=chunk_data
        )

        for node_name, path in replicas:
            create_replica_metadata(
                db=db,
                chunk_id=chunk_metadata.id,
                node_name=node_name,
                path=path
            )

            emit_audit_event(
                db=db,
                event_type="chunk.replicated",
                entity_type="chunk",
                entity_id=str(chunk_metadata.id),
                message=f"Chunk replicated to {node_name}",
                payload={
                    "file_id": file_metadata.id,
                    "chunk_id": chunk_metadata.id,
                    "chunk_index": chunk_index,
                    "node_name": node_name,
                    "path": path
                }
            )

    invalidate_file_cache(file_metadata.id)

    emit_audit_event(
        db=db,
        event_type="file.uploaded",
        entity_type="file",
        entity_id=str(file_metadata.id),
        message=f"File uploaded: {uploaded_file.filename}",
        payload={
            "file_id": file_metadata.id,
            "filename": uploaded_file.filename,
            "size_bytes": len(file_data),
            "total_chunks": total_chunks
        }
    )

    return get_file_by_id(file_metadata.id, db)


@router.get("", response_model=list[FileResponse])
def list_files(db: Session = Depends(get_db)):
    cached = cache.get_json(file_list_key())

    if cached is not None:
        return cached

    files = (
        db.query(FileMetadata)
        .options(
            joinedload(FileMetadata.chunks)
            .joinedload(ChunkMetadata.replicas)
        )
        .all()
    )

    response = [file_to_dict(file_metadata) for file_metadata in files]

    cache.set_json(file_list_key(), response)

    return response


@router.get("/{file_id}", response_model=FileResponse)
def get_file_by_id(file_id: int, db: Session = Depends(get_db)):
    cached = cache.get_json(file_metadata_key(file_id))

    if cached is not None:
        return cached

    file_metadata = (
        db.query(FileMetadata)
        .options(
            joinedload(FileMetadata.chunks)
            .joinedload(ChunkMetadata.replicas)
        )
        .filter(FileMetadata.id == file_id)
        .first()
    )

    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")

    response = file_to_dict(file_metadata)
    cache.set_json(file_metadata_key(file_id), response)

    return response


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    file_metadata = (
        db.query(FileMetadata)
        .options(
            joinedload(FileMetadata.chunks)
            .joinedload(ChunkMetadata.replicas)
        )
        .filter(FileMetadata.id == file_id)
        .first()
    )

    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")

    for chunk in file_metadata.chunks:
        for replica in chunk.replicas:
            path = Path(replica.path)

            if path.exists():
                path.unlink()

    db.delete(file_metadata)
    db.commit()

    invalidate_file_cache(file_id)

    emit_audit_event(
        db=db,
        event_type="file.deleted",
        entity_type="file",
        entity_id=str(file_id),
        message=f"File deleted: {file_metadata.filename}",
        payload={
            "file_id": file_id,
            "filename": file_metadata.filename
        }
    )

    return {
        "message": "File deleted successfully",
        "file_id": file_id
    }


@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    file_metadata = (
        db.query(FileMetadata)
        .options(
            joinedload(FileMetadata.chunks)
            .joinedload(ChunkMetadata.replicas)
        )
        .filter(FileMetadata.id == file_id)
        .first()
    )

    if not file_metadata:
        raise HTTPException(status_code=404, detail="File not found")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    output_path = DOWNLOAD_DIR / file_metadata.filename

    chunks = sorted(
        file_metadata.chunks,
        key=lambda chunk: chunk.chunk_index
    )

    with open(output_path, "wb") as output_file:
        for chunk in chunks:
            chunk_data = None

            for replica in chunk.replicas:
                possible_data = read_chunk(replica.path)

                if possible_data is None:
                    continue

                if sha256_bytes(possible_data) == chunk.chunk_hash:
                    chunk_data = possible_data
                    break

            if chunk_data is None:
                raise HTTPException(
                    status_code=500,
                    detail=f"Chunk {chunk.chunk_index} is missing or corrupted"
                )

            output_file.write(chunk_data)

    reconstructed_hash = sha256_bytes(output_path.read_bytes())

    if reconstructed_hash != file_metadata.file_hash:
        raise HTTPException(
            status_code=500,
            detail="Downloaded file failed integrity check"
        )

    return FastAPIFileResponse(
        path=output_path,
        filename=file_metadata.filename,
        media_type=file_metadata.content_type or "application/octet-stream"
    )