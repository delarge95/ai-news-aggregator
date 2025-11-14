"""
Cache and Rate Limiting Utilities

This module provides utility functions for common cache and rate limiting operations
in the AI News Aggregator application.
"""

import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from .redis_cache import get_cache_manager, RedisCacheManager
from .rate_limiter import get_rate_limit_manager, RateLimitConfig, RateLimitManager

logger = logging.getLogger(__name__)


class CacheUtils:
    """Utility class for common cache operations"""
    
    def __init__(self):
        self.cache_manager = None
    
    async def initialize(self):
        """Initialize cache manager"""
        self.cache_manager = await get_cache_manager()
    
    async def cache_news_articles(
        self, 
        query: str, 
        articles: List[Dict], 
        ttl: int = 900  # 15 minutes
    ) -> str:
        """
        Cache news articles search results
        
        Args:
            query: Search query
            articles: List of article dictionaries
            ttl: Cache TTL in seconds
            
        Returns:
            Cache key used
        """
        if not self.cache_manager:
            await self.initialize()
        
        # Create cache key based on query hash
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        cache_key = f"news:search:{query_hash}"
        
        # Prepare cache data
        cache_data = {
            'articles': articles,
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'count': len(articles)
        }
        
        # Cache the results
        await self.cache_manager.set(cache_key, cache_data, ttl=ttl)
        logger.info(f"Cached {len(articles)} articles for query: {query}")
        
        return cache_key
    
    async def get_cached_news_articles(self, query: str) -> Optional[Dict]:
        """
        Get cached news articles
        
        Args:
            query: Search query
            
        Returns:
            Cached articles data or None
        """
        if not self.cache_manager:
            await self.initialize()
        
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()
        cache_key = f"news:search:{query_hash}"
        
        cached_data = await self.cache_manager.get(cache_key)
        
        if cached_data:
            logger.info(f"Cache hit for query: {query}")
            # Add cache age information
            cache_timestamp = datetime.fromisoformat(cached_data['timestamp'])
            cache_age = datetime.now() - cache_timestamp
            cached_data['cache_age_seconds'] = cache_age.total_seconds()
        
        return cached_data
    
    async def cache_article_analysis(
        self, 
        article_id: str, 
        analysis: Dict, 
        ttl: int = 3600  # 1 hour
    ) -> bool:
        """
        Cache AI analysis of an article
        
        Args:
            article_id: Unique article identifier
            analysis: AI analysis results
            ttl: Cache TTL in seconds
            
        Returns:
            True if cached successfully
        """
        if not self.cache_manager:
            await self.initialize()
        
        cache_key = f"analysis:article:{article_id}"
        
        cache_data = {
            'analysis': analysis,
            'article_id': article_id,
            'timestamp': datetime.now().isoformat()
        }
        
        success = await self.cache_manager.set(cache_key, cache_data, ttl=ttl)
        
        if success:
            logger.info(f"Cached analysis for article: {article_id}")
        
        return success
    
    async def get_cached_article_analysis(self, article_id: str) -> Optional[Dict]:
        """
        Get cached article analysis
        
        Args:
            article_id: Unique article identifier
            
        Returns:
            Cached analysis or None
        """
        if not self.cache_manager:
            await self.initialize()
        
        cache_key = f"analysis:article:{article_id}"
        
        return await self.cache_manager.get(cache_key)
    
    async def invalidate_search_cache(self, query_pattern: str = None) -> int:
        """
        Invalidate search cache
        
        Args:
            query_pattern: Optional query pattern to match (if None, clears all search cache)
            
        Returns:
            Number of cache entries invalidated
        """
        if not self.cache_manager:
            await self.initialize()
        
        if query_pattern:
            pattern = f"news:search:*{query_pattern}*"
        else:
            pattern = "news:search:*"
        
        return await self.cache_manager.delete_pattern(pattern)
    
    async def cache_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict, 
        ttl: int = 86400  # 24 hours
    ) -> bool:
        """
        Cache user preferences
        
        Args:
            user_id: User identifier
            preferences: User preferences dictionary
            ttl: Cache TTL in seconds
            
        Returns:
            True if cached successfully
        """
        if not self.cache_manager:
            await self.initialize()
        
        cache_key = f"user:preferences:{user_id}"
        
        cache_data = {
            'preferences': preferences,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        return await self.cache_manager.set(cache_key, cache_data, ttl=ttl)
    
    async def get_user_preferences(self, user_id: str) -> Optional[Dict]:
        """
        Get cached user preferences
        
        Args:
            user_id: User identifier
            
        Returns:
            Cached preferences or None
        """
        if not self.cache_manager:
            await self.initialize()
        
        cache_key = f"user:preferences:{user_id}"
        
        return await self.cache_manager.get(cache_key)
    
    async def cache_api_response(
        self, 
        api_name: str, 
        endpoint: str, 
        response_data: Any, 
        ttl: int = 300  # 5 minutes
    ) -> str:
        """
        Cache external API response
        
        Args:
            api_name: Name of the API (newsapi, guardian, etc.)
            endpoint: API endpoint
            response_data: Response data to cache
            ttl: Cache TTL in seconds
            
        Returns:
            Cache key used
        """
        if not self.cache_manager:
            await self.initialize()
        
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        cache_key = f"api:{api_name}:{endpoint_hash}"
        
        cache_data = {
            'data': response_data,
            'api_name': api_name,
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat()
        }
        
        await self.cache_manager.set(cache_key, cache_data, ttl=ttl)
        return cache_key
    
    async def get_cached_api_response(
        self, 
        api_name: str, 
        endpoint: str
    ) -> Optional[Dict]:
        """
        Get cached API response
        
        Args:
            api_name: Name of the API
            endpoint: API endpoint
            
        Returns:
            Cached response data or None
        """
        if not self.cache_manager:
            await self.initialize()
        
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()
        cache_key = f"api:{api_name}:{endpoint_hash}"
        
        return await self.cache_manager.get(cache_key)


class RateLimitUtils:
    """Utility class for rate limiting operations"""
    
    def __init__(self):
        self.rate_limit_manager = None
    
    async def initialize(self):
        """Initialize rate limit manager"""
        self.rate_limit_manager = await get_rate_limit_manager()
    
    async def check_newsapi_limit(self) -> bool:
        """Check if NewsAPI request is within rate limit"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        return await self.rate_limit_manager.check_api_rate_limit('newsapi')
    
    async def check_ai_api_limit(self, api_name: str = 'openai') -> bool:
        """Check if AI API request is within rate limit"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        return await self.rate_limit_manager.check_api_rate_limit(api_name)
    
    async def check_ip_limit(self, ip_address: str, limit_type: str = 'default') -> bool:
        """Check IP-based rate limit"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        return await self.rate_limit_manager.check_ip_rate_limit(ip_address, limit_type)
    
    async def get_api_usage_stats(self, api_name: str) -> Dict:
        """Get usage statistics for an API"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        return await self.rate_limit_manager.get_api_rate_info(api_name)
    
    async def get_ip_usage_stats(self, ip_address: str) -> Dict:
        """Get usage statistics for an IP"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        return await self.rate_limit_manager.get_ip_rate_info(ip_address)
    
    async def reset_api_limit(self, api_name: str):
        """Reset rate limit for an API"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        await self.rate_limit_manager.reset_rate_limit(f"api:{api_name}", 'api')
    
    async def reset_ip_limit(self, ip_address: str):
        """Reset rate limit for an IP"""
        if not self.rate_limit_manager:
            await self.initialize()
        
        await self.rate_limit_manager.reset_rate_limit(f"ip:{ip_address}", 'ip')
    
    async def add_custom_api_limit(
        self, 
        api_name: str, 
        requests_per_hour: int, 
        burst_capacity: int = None,
        block_duration: int = 0
    ):
        """
        Add custom rate limit for API
        
        Args:
            api_name: API name
            requests_per_hour: Allowed requests per hour
            burst_capacity: Maximum burst capacity (defaults to requests_per_hour)
            block_duration: Block duration in seconds if exceeded
        """
        if not self.rate_limit_manager:
            await self.initialize()
        
        if burst_capacity is None:
            burst_capacity = requests_per_hour
        
        rate_config = RateLimitConfig(
            capacity=burst_capacity,
            refill_rate=requests_per_hour / 3600,  # Convert to tokens per second
            refill_interval=3600,
            block_duration=block_duration
        )
        
        self.rate_limit_manager.add_api_rate_limit(api_name, rate_config)
    
    async def add_custom_ip_limit(
        self, 
        ip_address: str, 
        requests_per_hour: int, 
        burst_capacity: int = None
    ):
        """
        Add custom rate limit for specific IP
        
        Args:
            ip_address: IP address
            requests_per_hour: Allowed requests per hour
            burst_capacity: Maximum burst capacity
        """
        if not self.rate_limit_manager:
            await self.initialize()
        
        if burst_capacity is None:
            burst_capacity = requests_per_hour
        
        rate_config = RateLimitConfig(
            capacity=burst_capacity,
            refill_rate=requests_per_hour / 3600,
            refill_interval=3600
        )
        
        self.rate_limit_manager.add_ip_rate_limit(ip_address, rate_config)


# Global utility instances
cache_utils = CacheUtils()
rate_limit_utils = RateLimitUtils()


async def get_cache_utils() -> CacheUtils:
    """Get global cache utilities instance"""
    if not cache_utils.cache_manager:
        await cache_utils.initialize()
    return cache_utils


async def get_rate_limit_utils() -> RateLimitUtils:
    """Get global rate limit utilities instance"""
    if not rate_limit_utils.rate_limit_manager:
        await rate_limit_utils.initialize()
    return rate_limit_utils


# Decorators for easy usage
def cache_result(ttl: int = 300, key_prefix: str = "function"):
    """
    Decorator to cache function results
    
    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            utils = await get_cache_utils()
            
            # Create cache key from function name and arguments
            args_str = json.dumps(args, sort_keys=True, default=str)
            kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
            key_data = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            cache_key = f"func_cache:{key_hash}"
            
            # Try to get from cache
            cached_result = await utils.cache_manager.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result['result']
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_data = {
                'result': result,
                'function': func.__name__,
                'timestamp': datetime.now().isoformat()
            }
            
            await utils.cache_manager.set(cache_key, cache_data, ttl=ttl)
            logger.debug(f"Cache miss for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator


def rate_limit_by_api(api_name: str, algorithm: str = 'token_bucket'):
    """
    Decorator to apply rate limiting by API
    
    Args:
        api_name: API name to limit
        algorithm: Rate limiting algorithm
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            utils = await get_rate_limit_utils()
            
            allowed = await utils.rate_limit_manager.check_api_rate_limit(api_name, algorithm)
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for API: {api_name}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator