import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    str(BASE_DIR / "metadata.db")
)

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024 * 1024))

REPLICATION_FACTOR = int(os.getenv("REPLICATION_FACTOR", 2))

STORAGE_BASE_DIR = Path(
    os.getenv("STORAGE_BASE_DIR", str(BASE_DIR / "storage_nodes"))
)

STORAGE_NODES = {
    "node1": STORAGE_BASE_DIR / "node1",
    "node2": STORAGE_BASE_DIR / "node2",
    "node3": STORAGE_BASE_DIR / "node3",
}

DOWNLOAD_DIR = Path(
    os.getenv("DOWNLOAD_DIR", str(BASE_DIR / "downloads"))
)