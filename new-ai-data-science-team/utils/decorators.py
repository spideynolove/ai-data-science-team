import functools
import logging
import time
from typing import Callable, Any

def log_execution(logger: logging.Logger):
    """Decorator to log function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            logger.info(f"Executing {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                logger.info(f"Successfully executed {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

def retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry a function on failure"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

def timeout(seconds: float):
    """Decorator to add timeout to a function"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            import asyncio
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds} seconds")
        return wrapper
    return decorator

def cache_result(ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            from new_ai_data_science_team.data.storage.redis_client import RedisClient
            redis_client = RedisClient()
            
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached_result = await redis_client.get_value(cache_key)
            
            if cached_result:
                return cached_result
                
            result = await func(*args, **kwargs)
            await redis_client.set_value(cache_key, str(result), ttl=ttl)
            return result
        return wrapper
    return decorator
