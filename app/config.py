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

# Redis / cache config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = os.getenv(
    "REDIS_URL",
    f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
)

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", 300))

# Feature flags
ENABLE_REDIS_CACHE = os.getenv("ENABLE_REDIS_CACHE", "true").lower() == "true"
ENABLE_ASYNC_REPAIR = os.getenv("ENABLE_ASYNC_REPAIR", "true").lower() == "true"
ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"

# Canary-style replication strategy
# Supported values: round_robin, reverse_round_robin
REPLICATION_STRATEGY = os.getenv("REPLICATION_STRATEGY", "round_robin")

# Percentage of requests/chunks routed to new strategy
CANARY_PERCENTAGE = int(os.getenv("CANARY_PERCENTAGE", 0))