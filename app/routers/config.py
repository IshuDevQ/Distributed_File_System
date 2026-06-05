from fastapi import APIRouter

from app.config import (
    CHUNK_SIZE,
    REPLICATION_FACTOR,
    ENABLE_REDIS_CACHE,
    ENABLE_ASYNC_REPAIR,
    ENABLE_AUDIT_LOG,
    REPLICATION_STRATEGY,
    CANARY_PERCENTAGE,
    CACHE_TTL_SECONDS,
)

router = APIRouter(prefix="/config", tags=["Runtime Config"])


@router.get("")
def get_runtime_config():
    return {
        "chunk_size": CHUNK_SIZE,
        "replication_factor": REPLICATION_FACTOR,
        "enable_redis_cache": ENABLE_REDIS_CACHE,
        "enable_async_repair": ENABLE_ASYNC_REPAIR,
        "enable_audit_log": ENABLE_AUDIT_LOG,
        "replication_strategy": REPLICATION_STRATEGY,
        "canary_percentage": CANARY_PERCENTAGE,
        "cache_ttl_seconds": CACHE_TTL_SECONDS
    }