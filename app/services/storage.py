from pathlib import Path
from typing import Optional

from app.config import STORAGE_NODES
from app.utils.logger import get_logger

logger = get_logger(__name__)


def ensure_storage_nodes_exist() -> None:
    for node_path in STORAGE_NODES.values():
        node_path.mkdir(parents=True, exist_ok=True)


def get_chunk_path(node_name: str, file_id: int, chunk_index: int) -> Path:
    node_path = STORAGE_NODES[node_name]
    file_dir = node_path / f"file_{file_id}"
    file_dir.mkdir(parents=True, exist_ok=True)

    return file_dir / f"chunk_{chunk_index}.bin"


def store_chunk(
    node_name: str,
    file_id: int,
    chunk_index: int,
    chunk_data: bytes
) -> str:
    chunk_path = get_chunk_path(node_name, file_id, chunk_index)

    with open(chunk_path, "wb") as file:
        file.write(chunk_data)

    logger.info(
        f"Stored chunk {chunk_index} of file {file_id} on {node_name}"
    )

    return str(chunk_path)


def read_chunk(path: str) -> Optional[bytes]:
    chunk_path = Path(path)

    if not chunk_path.exists():
        return None

    with open(chunk_path, "rb") as file:
        return file.read()


def delete_chunk(path: str) -> None:
    chunk_path = Path(path)

    if chunk_path.exists():
        chunk_path.unlink()