from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class FileMetadata(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String, nullable=False)
    total_chunks = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship(
        "ChunkMetadata",
        back_populates="file",
        cascade="all, delete-orphan"
    )


class ChunkMetadata(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)

    chunk_index = Column(Integer, nullable=False)
    chunk_hash = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)

    file = relationship("FileMetadata", back_populates="chunks")
    replicas = relationship(
        "ChunkReplica",
        back_populates="chunk",
        cascade="all, delete-orphan"
    )


class ChunkReplica(Base):
    __tablename__ = "chunk_replicas"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)

    node_name = Column(String, nullable=False)
    path = Column(String, nullable=False)

    chunk = relationship("ChunkMetadata", back_populates="replicas")


class RepairTaskStatus(Base):
    __tablename__ = "repair_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, nullable=True, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)
    status = Column(String, default="queued")
    message = Column(Text, nullable=True)
    retries = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)