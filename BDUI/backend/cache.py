import redis
import json
import os
from typing import Any, Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class Cache:
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        try:
            value = redis_client.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    @staticmethod
    async def set(key: str, value: Any, ttl: int = 3600):
        try:
            redis_client.setex(key, ttl, json.dumps(value))
        except Exception:
            pass
    
    @staticmethod
    async def delete(key: str):
        try:
            redis_client.delete(key)
        except Exception:
            pass
    
    @staticmethod
    async def invalidate_pattern(pattern: str):
        try:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception:
            pass


cache = Cache()





