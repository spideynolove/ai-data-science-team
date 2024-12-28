import logging
import redis
from config import settings

class RedisClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = redis.Redis.from_url(settings.REDIS_URI)

    async def set_value(self, key: str, value: str, ttl: int = None) -> bool:
        """Set a value in Redis with optional TTL"""
        try:
            if ttl:
                return self.client.set(key, value, ex=ttl)
            return self.client.set(key, value)
        except redis.RedisError as e:
            self.logger.error(f"Redis set operation failed: {str(e)}")
            return False

    async def get_value(self, key: str) -> str:
        """Get a value from Redis"""
        try:
            value = self.client.get(key)
            return value.decode('utf-8') if value else None
        except redis.RedisError as e:
            self.logger.error(f"Redis get operation failed: {str(e)}")
            return None

    async def delete_key(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            return self.client.delete(key) > 0
        except redis.RedisError as e:
            self.logger.error(f"Redis delete operation failed: {str(e)}")
            return False

    async def increment(self, key: str) -> int:
        """Increment a value in Redis"""
        try:
            return self.client.incr(key)
        except redis.RedisError as e:
            self.logger.error(f"Redis increment operation failed: {str(e)}")
            return -1

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key"""
        try:
            return self.client.expire(key, ttl)
        except redis.RedisError as e:
            self.logger.error(f"Redis expire operation failed: {str(e)}")
            return False

    async def close(self):
        """Close Redis connection"""
        try:
            self.client.close()
            return True
        except redis.RedisError as e:
            self.logger.error(f"Failed to close Redis connection: {str(e)}")
            return False
