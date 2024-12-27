from typing import Dict, Any
import asyncio
from contextlib import asynccontextmanager
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import asyncpg
import redis
from redis.asyncio import Redis

from .settings import DATABASE_CONFIG

logger = logging.getLogger(__name__)

class DatabaseConnections:
    """
    Manages database connections for MongoDB, PostgreSQL, and Redis.
    Implements connection pooling and provides async context managers.
    """
    def __init__(self):
        self.mongo_client = None
        self.mongo_async_client = None
        self.postgres_pool = None
        self.redis_client = None
        self.redis_async_client = None
        
    async def init_connections(self):
        """Initialize all database connections."""
        await self.init_mongodb()
        await self.init_postgresql()
        await self.init_redis()
        logger.info("All database connections initialized")

    async def close_connections(self):
        """Close all database connections."""
        await self.close_mongodb()
        await self.close_postgresql()
        await self.close_redis()
        logger.info("All database connections closed")

    # MongoDB Configuration
    async def init_mongodb(self):
        """Initialize MongoDB connections (sync and async)."""
        try:
            # Sync client
            self.mongo_client = MongoClient(DATABASE_CONFIG['mongodb']['uri'])
            # Async client
            self.mongo_async_client = AsyncIOMotorClient(DATABASE_CONFIG['mongodb']['uri'])
            # Test connection
            await self.mongo_async_client.admin.command('ping')
            logger.info("MongoDB connection established")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def close_mongodb(self):
        """Close MongoDB connections."""
        if self.mongo_client:
            self.mongo_client.close()
        if self.mongo_async_client:
            self.mongo_async_client.close()
        logger.info("MongoDB connections closed")

    @asynccontextmanager
    async def mongodb_transaction(self):
        """Async context manager for MongoDB transactions."""
        async with await self.mongo_async_client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                except Exception as e:
                    await session.abort_transaction()
                    logger.error(f"MongoDB transaction failed: {str(e)}")
                    raise
                else:
                    await session.commit_transaction()

    # PostgreSQL Configuration
    async def init_postgresql(self):
        """Initialize PostgreSQL connection pool."""
        try:
            self.postgres_pool = await asyncpg.create_pool(
                DATABASE_CONFIG['postgresql']['uri'],
                min_size=5,
                max_size=20,
                command_timeout=60,
                max_queries=50000,
            )
            # Test connection
            async with self.postgres_pool.acquire() as conn:
                await conn.execute('SELECT 1')
            logger.info("PostgreSQL connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise

    async def close_postgresql(self):
        """Close PostgreSQL connection pool."""
        if self.postgres_pool:
            await self.postgres_pool.close()
        logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def postgresql_transaction(self):
        """Async context manager for PostgreSQL transactions."""
        async with self.postgres_pool.acquire() as connection:
            async with connection.transaction():
                try:
                    yield connection
                except Exception as e:
                    logger.error(f"PostgreSQL transaction failed: {str(e)}")
                    raise

    # Redis Configuration
    async def init_redis(self):
        """Initialize Redis connections (sync and async)."""
        try:
            # Sync client
            self.redis_client = redis.Redis.from_url(
                DATABASE_CONFIG['redis']['uri'],
                decode_responses=True
            )
            # Async client
            self.redis_async_client = Redis.from_url(
                DATABASE_CONFIG['redis']['uri'],
                decode_responses=True
            )
            # Test connection
            await self.redis_async_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise

    async def close_redis(self):
        """Close Redis connections."""
        if self.redis_client:
            self.redis_client.close()
        if self.redis_async_client:
            await self.redis_async_client.close()
        logger.info("Redis connections closed")

    @asynccontextmanager
    async def redis_pipeline(self):
        """Async context manager for Redis pipelines."""
        pipeline = self.redis_async_client.pipeline()
        try:
            yield pipeline
            await pipeline.execute()
        except Exception as e:
            logger.error(f"Redis pipeline failed: {str(e)}")
            raise

# Global database connections instance
db = DatabaseConnections()

async def initialize_databases():
    """Initialize all database connections."""
    await db.init_connections()

async def cleanup_databases():
    """Cleanup all database connections."""
    await db.close_connections()

# Utility functions for common database operations
async def health_check() -> Dict[str, Any]:
    """
    Perform health check on all database connections.
    Returns status of each database connection.
    """
    status = {
        'mongodb': False,
        'postgresql': False,
        'redis': False
    }
    
    try:
        # Check MongoDB
        await db.mongo_async_client.admin.command('ping')
        status['mongodb'] = True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")

    try:
        # Check PostgreSQL
        async with db.postgres_pool.acquire() as conn:
            await conn.execute('SELECT 1')
        status['postgresql'] = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")

    try:
        # Check Redis
        await db.redis_async_client.ping()
        status['redis'] = True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")

    return status
