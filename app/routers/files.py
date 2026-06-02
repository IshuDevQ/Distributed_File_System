from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session, joinedload
from pathlib import Path

from app.database import get_db
from app.models import FileMetadata, ChunkMetadata
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
from app.config import DOWNLOAD_DIR

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/upload", response_model=FileResponse)
async def upload_file(
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_data = await uploaded_file.read()

    file_hash = sha256_bytes(file_data)
    total_chunks = (len(file_data) + 1024 * 1024 - 1) // (1024 * 1024)

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

    return get_file_by_id(file_metadata.id, db)


@router.get("", response_model=list[FileResponse])
def list_files(db: Session = Depends(get_db)):
    return (
        db.query(FileMetadata)
        .options(
            joinedload(FileMetadata.chunks)
            .joinedload(ChunkMetadata.replicas)
        )
        .all()
    )


@router.get("/{file_id}", response_model=FileResponse)
def get_file_by_id(file_id: int, db: Session = Depends(get_db)):
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

    return file_metadata


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