"""
Redis client for caching, pub/sub, and session management
"""
import redis.asyncio as redis
from typing import Any, Optional, Dict, List, Callable
import json
import logging
from datetime import timedelta
from functools import wraps
import asyncio
import pickle

from core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client manager"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis = None
        self.pubsub = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._listener_task = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                settings.redis_url_with_password,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Connected to Redis")
            
            # Initialize pub/sub
            self.pubsub = self.redis.pubsub()
            self._listener_task = asyncio.create_task(self._pubsub_listener())
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def close(self):
        """Close Redis connection"""
        if self._listener_task:
            self._listener_task.cancel()
        
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis:
            await self.redis.close()
        
        logger.info("Closed Redis connection")
    
    # Cache Operations
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = await self.redis.get(key)
            if value:
                try:
                    # Try to deserialize JSON
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Return as string if not JSON
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration"""
        try:
            # Serialize to JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            if expire:
                await self.redis.setex(key, expire, value)
            else:
                await self.redis.set(key, value)
            
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key {key}: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiration on key {key}: {e}")
            return False
    
    # Hash Operations (for complex objects)
    
    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field"""
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            await self.redis.hset(name, key, value)
            return True
        except Exception as e:
            logger.error(f"Error setting hash {name}[{key}]: {e}")
            return False
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field"""
        try:
            value = await self.redis.hget(name, key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error getting hash {name}[{key}]: {e}")
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            data = await self.redis.hgetall(name)
            result = {}
            for key, value in data.items():
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            return result
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}
    
    # List Operations (for queues)
    
    async def lpush(self, key: str, *values) -> int:
        """Push values to list head"""
        try:
            serialized = [json.dumps(v) if not isinstance(v, str) else v for v in values]
            return await self.redis.lpush(key, *serialized)
        except Exception as e:
            logger.error(f"Error pushing to list {key}: {e}")
            return 0
    
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop value from list tail"""
        try:
            value = await self.redis.rpop(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Error popping from list {key}: {e}")
            return None
    
    # Pub/Sub Operations
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> int:
        """Publish message to channel"""
        try:
            return await self.redis.publish(channel, json.dumps(message))
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            return 0
    
    async def subscribe(self, channel: str, callback: Callable) -> bool:
        """Subscribe to channel with callback"""
        try:
            await self.pubsub.subscribe(channel)
            
            if channel not in self._subscribers:
                self._subscribers[channel] = []
            self._subscribers[channel].append(callback)
            
            logger.info(f"Subscribed to channel: {channel}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            return False
    
    async def unsubscribe(self, channel: str) -> bool:
        """Unsubscribe from channel"""
        try:
            await self.pubsub.unsubscribe(channel)
            if channel in self._subscribers:
                del self._subscribers[channel]
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from channel {channel}: {e}")
            return False
    
    async def _pubsub_listener(self):
        """Background task to listen for pub/sub messages"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    if channel in self._subscribers:
                        try:
                            data = json.loads(message["data"])
                            for callback in self._subscribers[channel]:
                                asyncio.create_task(callback(channel, data))
                        except Exception as e:
                            logger.error(f"Error processing message from {channel}: {e}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in pubsub listener: {e}")
    
    # Rate Limiting
    
    async def is_rate_limited(
        self,
        key: str,
        limit: int,
        window: int
    ) -> bool:
        """Check if rate limit exceeded"""
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window)
            return current > limit
        except Exception as e:
            logger.error(f"Error checking rate limit for {key}: {e}")
            return False
    
    # Session Management
    
    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        expire: int = 3600
    ) -> bool:
        """Store session data"""
        key = f"session:{session_id}"
        return await self.set(key, data, expire)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        key = f"session:{session_id}"
        return await self.delete(key)
    
    # Lock Implementation
    
    async def acquire_lock(
        self,
        key: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: int = 5
    ) -> bool:
        """Acquire distributed lock"""
        lock_key = f"lock:{key}"
        identifier = f"{id(self)}:{asyncio.get_event_loop().time()}"
        
        if blocking:
            end_time = asyncio.get_event_loop().time() + blocking_timeout
            while asyncio.get_event_loop().time() < end_time:
                if await self.redis.set(lock_key, identifier, nx=True, ex=timeout):
                    return True
                await asyncio.sleep(0.1)
            return False
        else:
            return await self.redis.set(lock_key, identifier, nx=True, ex=timeout)
    
    async def release_lock(self, key: str) -> bool:
        """Release distributed lock"""
        lock_key = f"lock:{key}"
        return await self.delete(lock_key)


# Cache decorator
def cached(
    expire: int = 300,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Simple key generation
                cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Get Redis client (assumes it's available in context)
            redis_client = getattr(wrapper, '_redis_client', None)
            if not redis_client:
                # Fallback: execute without caching
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cached_value = await redis_client.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await redis_client.set(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator


# Global Redis client instance
redis_client = RedisClient()