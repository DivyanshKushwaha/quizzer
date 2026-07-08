import redis
import json
from typing import Any, Optional
from config import Configs
from core.logger.logging_tool import get_logger

config = Configs()
logger = get_logger(name="Redis Utils", feature="database/redis/redis_utils.py")

# Initialize Redis client
_redis_client = None

def get_redis_client():
    """Get or create Redis client singleton"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=config.REDIS_HOST,
            port=int(config.REDIS_PORT),
            db=int(config.REDIS_DB),
            decode_responses=True
        )
    return _redis_client

def get_cache(key: str) -> Optional[Any]:
    """Get cached data by key"""
    try:
        data = get_redis_client().get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Error getting cache key {key}: {e}")
        return None

def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set cache data with optional TTL (None = no expiration)"""
    try:
        if ttl is None:
            get_redis_client().set(key, json.dumps(value))
        else:
            get_redis_client().setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Error setting cache key {key}: {e}")
        return False

def delete_cache(key: str) -> bool:
    """Delete cache by key"""
    try:
        return bool(get_redis_client().delete(key))
    except Exception as e:
        logger.error(f"Error deleting cache key {key}: {e}")
        return False

def delete_cache_pattern(pattern: str) -> int:
    """Delete all keys matching pattern"""
    try:
        keys = get_redis_client().keys(pattern)
        return get_redis_client().delete(*keys) if keys else 0
    except Exception as e:
        logger.error(f"Error deleting cache pattern {pattern}: {e}")
        return 0

