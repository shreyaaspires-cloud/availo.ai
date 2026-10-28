import json
import logging
from typing import Optional
from upstash_redis import Redis

from app.config import settings

logger = logging.getLogger(__name__)

redis_client: Optional[Redis] = None

try:
    if settings.UPSTASH_REDIS_URL and "dummy" not in settings.UPSTASH_REDIS_URL:
        redis_client = Redis(
            url=settings.UPSTASH_REDIS_URL,
            token=settings.UPSTASH_REDIS_TOKEN,
        )
except Exception as e:
    logger.warning("Upstash Redis connection failed, falling back to in-memory/noop: %s", e)
    redis_client = None

# Fallback local in-memory dict for development/demo when Upstash is not configured
_local_cache: dict[str, tuple[str, Optional[float]]] = {}


def cache_get(key: str) -> Optional[str]:
    if redis_client:
        try:
            return redis_client.get(key)
        except Exception:
            pass
    if key in _local_cache:
        val, _ = _local_cache[key]
        return val
    return None


def cache_set(key: str, value: str, ex: Optional[int] = None) -> bool:
    if redis_client:
        try:
            if ex:
                redis_client.setex(key, ex, value)
            else:
                redis_client.set(key, value)
            return True
        except Exception:
            pass
    _local_cache[key] = (value, None)
    return True


def cache_delete(key: str) -> bool:
    if redis_client:
        try:
            redis_client.delete(key)
            return True
        except Exception:
            pass
    _local_cache.pop(key, None)
    return True
