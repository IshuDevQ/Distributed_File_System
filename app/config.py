from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = f"sqlite:///{BASE_DIR / 'metadata.db'}"

CHUNK_SIZE = 1024 * 1024  # 1 MB

REPLICATION_FACTOR = 2

STORAGE_NODES = {
    "node1": BASE_DIR / "storage_nodes" / "node1",
    "node2": BASE_DIR / "storage_nodes" / "node2",
    "node3": BASE_DIR / "storage_nodes" / "node3",
}

DOWNLOAD_DIR = BASE_DIR / "downloads"