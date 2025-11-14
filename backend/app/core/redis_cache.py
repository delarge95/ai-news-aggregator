"""
Redis Cache Management System

This module provides comprehensive Redis cache functionality including:
- Basic cache operations (get, set, delete)
- TTL management
- Cache invalidation strategies
- Connection pooling and error handling
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from .config import settings

logger = logging.getLogger(__name__)


class RedisCacheManager:
    """
    Redis cache manager with comprehensive functionality for AI News Aggregator
    """
    
    def __init__(self, redis_url: str = None, decode_responses: bool = True):
        """
        Initialize Redis cache manager
        
        Args:
            redis_url: Redis connection URL
            decode_responses: Whether to decode responses automatically
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.decode_responses = decode_responses
        self._connection_pool = None
        self._redis_client = None
        
    async def connect(self) -> None:
        """Establish Redis connection with connection pooling"""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                decode_responses=self.decode_responses,
                max_connections=20,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
            self._redis_client = redis.Redis(
                connection_pool=self._connection_pool,
                encoding='utf-8' if self.decode_responses else None,
                decode_responses=self.decode_responses
            )
            
            # Test connection
            await self._redis_client.ping()
            logger.info("Redis cache connection established successfully")
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Redis connection and cleanup"""
        if self._redis_client:
            await self._redis_client.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        logger.info("Redis cache connection closed")
    
    @property
    def redis(self) -> redis.Redis:
        """Get Redis client instance"""
        if not self._redis_client:
            raise RuntimeError("Redis connection not established. Call connect() first.")
        return self._redis_client
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.redis.get(key)
            if value is None:
                logger.debug(f"Cache miss for key: {key}")
                return None
            
            logger.debug(f"Cache hit for key: {key}")
            
            # Try to deserialize JSON, fallback to raw string
            try:
                return json.loads(value) if isinstance(value, str) else value
            except json.JSONDecodeError:
                return value
                
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use default TTL from settings if not specified
            if ttl is None:
                ttl = settings.CACHE_TTL
            
            # Serialize value
            serialized_value = value
            if not isinstance(value, str):
                serialized_value = json.dumps(value, default=str)
            
            result = await self.redis.set(key, serialized_value, ex=ttl, nx=nx, xx=xx)
            
            if result:
                logger.debug(f"Cache set successful for key: {key} (TTL: {ttl}s)")
            else:
                logger.debug(f"Cache set failed for key: {key} (nx={nx}, xx={xx})")
            
            return bool(result)
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """
        Delete key(s) from cache
        
        Args:
            *keys: One or more keys to delete
            
        Returns:
            Number of keys deleted
        """
        try:
            if not keys:
                return 0
                
            result = await self.redis.delete(*keys)
            logger.debug(f"Cache delete: {result} keys deleted: {keys}")
            return result
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis delete error for keys {keys}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(await self.redis.exists(key))
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key"""
        try:
            return bool(await self.redis.expire(key, ttl))
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis expire error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for a key"""
        try:
            ttl = await self.redis.ttl(key)
            return ttl if ttl != -2 else -1  # -2 = key doesn't exist, -1 = no TTL
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis ttl error for key {key}: {e}")
            return -1
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric value"""
        try:
            return await self.redis.incrby(key, amount)
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis increment error for key {key}: {e}")
            return None
    
    async def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement numeric value"""
        try:
            return await self.redis.decrby(key, amount)
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis decrement error for key {key}: {e}")
            return None
    
    # Cache Invalidation Strategies
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., "articles:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted_count = await self.redis.delete(*keys)
                logger.info(f"Cache invalidation: {deleted_count} keys deleted for pattern {pattern}")
                return deleted_count
            return 0
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis delete pattern error for {pattern}: {e}")
            return 0
    
    async def invalidate_by_prefix(self, prefix: str) -> int:
        """
        Invalidate cache entries by prefix
        
        Args:
            prefix: Key prefix (e.g., "articles:", "news:")
            
        Returns:
            Number of keys deleted
        """
        pattern = f"{prefix}*"
        return await self.delete_pattern(pattern)
    
    async def clear_namespace(self, namespace: str) -> int:
        """
        Clear all cache entries in a namespace
        
        Args:
            namespace: Namespace identifier
            
        Returns:
            Number of keys deleted
        """
        pattern = f"{namespace}:*"
        return await self.delete_pattern(pattern)
    
    async def batch_set(self, items: Dict[str, tuple]) -> int:
        """
        Batch set multiple key-value pairs
        
        Args:
            items: Dictionary with keys as keys and tuples of (value, ttl) as values
            
        Returns:
            Number of items successfully set
        """
        if not items:
            return 0
            
        try:
            pipeline = self.redis.pipeline()
            success_count = 0
            
            for key, (value, ttl) in items.items():
                serialized_value = value
                if not isinstance(value, str):
                    serialized_value = json.dumps(value, default=str)
                
                if ttl:
                    pipeline.setex(key, ttl, serialized_value)
                else:
                    pipeline.set(key, serialized_value)
                success_count += 1
            
            await pipeline.execute()
            logger.info(f"Batch cache set: {success_count} items cached")
            return success_count
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis batch set error: {e}")
            return 0
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """
        Batch get multiple keys
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary with key-value pairs for found keys
        """
        if not keys:
            return {}
            
        try:
            values = await self.redis.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value) if isinstance(value, str) else value
                    except json.JSONDecodeError:
                        result[key] = value
            
            logger.debug(f"Batch cache get: {len(result)}/{len(keys)} keys found")
            return result
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis batch get error: {e}")
            return {}
    
    # Specialized cache methods for AI News Aggregator
    
    async def cache_article(self, article_id: str, article_data: Dict, ttl: int = None) -> bool:
        """Cache individual article data"""
        if ttl is None:
            ttl = settings.ARTICLE_CACHE_TTL
        key = f"article:{article_id}"
        return await self.set(key, article_data, ttl=ttl)
    
    async def get_cached_article(self, article_id: str) -> Optional[Dict]:
        """Get cached article data"""
        key = f"article:{article_id}"
        return await self.get(key)
    
    async def cache_search_results(self, query_hash: str, results: List[Dict], ttl: int = 900) -> bool:
        """Cache search results (15 minutes default TTL)"""
        key = f"search:{query_hash}"
        return await self.set(key, results, ttl=ttl)
    
    async def get_cached_search_results(self, query_hash: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        key = f"search:{query_hash}"
        return await self.get(key)
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a specific user"""
        return await self.invalidate_by_prefix(f"user:{user_id}")
    
    async def invalidate_articles_cache(self) -> int:
        """Invalidate all articles cache"""
        return await self.clear_namespace("article")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = await self.redis.info()
            return {
                'connected_clients': info.get('connected_clients'),
                'used_memory': info.get('used_memory'),
                'used_memory_human': info.get('used_memory_human'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'total_commands_processed': info.get('total_commands_processed'),
                'uptime_in_seconds': info.get('uptime_in_seconds')
            }
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.error(f"Redis stats error: {e}")
            return {}


# Global cache manager instance
cache_manager = RedisCacheManager()


async def get_cache_manager() -> RedisCacheManager:
    """Get global cache manager instance"""
    if not cache_manager._redis_client:
        await cache_manager.connect()
    return cache_manager


# Alias for backward compatibility
get_cache = get_cache_manager
get_redis_client = get_cache_manager