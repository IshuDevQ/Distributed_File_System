import json
from typing import Any, Optional

import redis

from app.config import REDIS_URL, CACHE_TTL_SECONDS, ENABLE_REDIS_CACHE
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    def __init__(self):
        self.enabled = ENABLE_REDIS_CACHE

        if not self.enabled:
            self.client = None
            return

        try:
            self.client = redis.Redis.from_url(
                REDIS_URL,
                decode_responses=True
            )
            self.client.ping()
            logger.info("Connected to Redis cache")
        except Exception as exc:
            logger.warning(f"Redis cache unavailable: {exc}")
            self.client = None
            self.enabled = False

    def get_json(self, key: str) -> Optional[Any]:
        if not self.enabled or self.client is None:
            return None

        try:
            value = self.client.get(key)

            if value is None:
                return None

            return json.loads(value)

        except Exception as exc:
            logger.warning(f"Redis GET failed for key={key}: {exc}")
            return None

    def set_json(
        self,
        key: str,
        value: Any,
        ttl: int = CACHE_TTL_SECONDS
    ) -> None:
        if not self.enabled or self.client is None:
            return

        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
        except Exception as exc:
            logger.warning(f"Redis SET failed for key={key}: {exc}")

    def delete(self, key: str) -> None:
        if not self.enabled or self.client is None:
            return

        try:
            self.client.delete(key)
        except Exception as exc:
            logger.warning(f"Redis DELETE failed for key={key}: {exc}")

    def delete_pattern(self, pattern: str) -> None:
        if not self.enabled or self.client is None:
            return

        try:
            keys = self.client.keys(pattern)

            if keys:
                self.client.delete(*keys)

        except Exception as exc:
            logger.warning(f"Redis DELETE PATTERN failed for {pattern}: {exc}")


cache = RedisCache()


def file_metadata_key(file_id: int) -> str:
    return f"file:metadata:{file_id}"


def file_list_key() -> str:
    return "file:list"


def node_health_key() -> str:
    return "nodes:health"


def chunk_locations_key(file_id: int) -> str:
    return f"file:chunks:{file_id}"


def invalidate_file_cache(file_id: int | None = None) -> None:
    cache.delete(file_list_key())

    if file_id is not None:
        cache.delete(file_metadata_key(file_id))
        cache.delete(chunk_locations_key(file_id))