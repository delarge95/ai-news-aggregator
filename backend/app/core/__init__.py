"""
Core functionality modules for AI News Aggregator

This module provides essential backend services including:
- Configuration management
- Redis caching system
- Rate limiting with token bucket algorithm
- FastAPI middleware integration
- Utility functions for cache and rate limiting operations
"""

from .config import settings
from .redis_cache import (
    RedisCacheManager,
    cache_manager,
    get_cache_manager
)
from .rate_limiter import (
    RateLimitManager,
    RateLimitConfig,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    rate_limit,
    rate_limit_manager,
    get_rate_limit_manager
)
from .middleware import (
    RateLimitMiddleware,
    CacheMiddleware,
    HealthCheckMiddleware
)
from .utils import (
    CacheUtils,
    RateLimitUtils,
    cache_utils,
    rate_limit_utils,
    get_cache_utils,
    get_rate_limit_utils,
    cache_result,
    rate_limit_by_api
)

__all__ = [
    # Configuration
    "settings",
    
    # Redis Cache
    "RedisCacheManager",
    "cache_manager", 
    "get_cache_manager",
    
    # Rate Limiting
    "RateLimitManager",
    "RateLimitConfig",
    "TokenBucketRateLimiter", 
    "SlidingWindowRateLimiter",
    "rate_limit",
    "rate_limit_manager",
    "get_rate_limit_manager",
    
    # Middleware
    "RateLimitMiddleware",
    "CacheMiddleware",
    "HealthCheckMiddleware",
    
    # Utilities
    "CacheUtils",
    "RateLimitUtils",
    "cache_utils",
    "rate_limit_utils",
    "get_cache_utils",
    "get_rate_limit_utils",
    "cache_result",
    "rate_limit_by_api"
]