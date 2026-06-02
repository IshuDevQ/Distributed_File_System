from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ReplicaResponse(BaseModel):
    node_name: str
    path: str

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: int
    chunk_index: int
    chunk_hash: str
    size_bytes: int
    replicas: List[ReplicaResponse]

    class Config:
        from_attributes = True


class FileResponse(BaseModel):
    id: int
    filename: str
    content_type: Optional[str]
    size_bytes: int
    file_hash: str
    total_chunks: int
    created_at: datetime
    chunks: List[ChunkResponse]

    class Config:
        from_attributes = True


class NodeHealthResponse(BaseModel):
    node_name: str
    path: str
    status: str