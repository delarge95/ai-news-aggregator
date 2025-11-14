"""
Rate Limiting System using Token Bucket Algorithm

This module provides comprehensive rate limiting functionality including:
- Token bucket algorithm implementation
- Rate limiting by API and IP
- Configurable rate limits per service
- Sliding window rate limiting
- Integration with Redis for distributed rate limiting
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime, timedelta

from .redis_cache import RedisCacheManager, get_cache_manager

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    capacity: int
    refill_rate: float
    refill_interval: float
    block_duration: int = 0  # 0 means no blocking
    
    @property
    def requests_per_minute(self) -> float:
        """Calculate requests per minute"""
        return (self.refill_rate * 60) if self.refill_rate > 0 else 0
    
    @property
    def requests_per_hour(self) -> float:
        """Calculate requests per hour"""
        return (self.refill_rate * 3600) if self.refill_rate > 0 else 0


class RateLimiter(ABC):
    """Abstract base class for rate limiters"""
    
    @abstractmethod
    async def check_rate_limit(self, identifier: str, limit_config: RateLimitConfig) -> bool:
        """Check if request is within rate limit"""
        pass
    
    @abstractmethod
    async def get_remaining_tokens(self, identifier: str, limit_config: RateLimitConfig) -> int:
        """Get remaining tokens"""
        pass


class TokenBucketRateLimiter(RateLimiter):
    """
    Token Bucket Rate Limiter implementation
    
    The token bucket algorithm works as follows:
    1. A bucket has a fixed capacity
    2. Tokens are added to the bucket at a fixed refill rate
    3. Each request consumes one token
    4. If no tokens are available, the request is rejected
    5. The bucket cannot exceed its capacity
    """
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager
        
    async def check_rate_limit(self, identifier: str, limit_config: RateLimitConfig) -> bool:
        """
        Check if request is within rate limit using token bucket algorithm
        
        Args:
            identifier: Unique identifier (IP, API key, etc.)
            limit_config: Rate limit configuration
            
        Returns:
            True if request is allowed, False if rate limited
        """
        try:
            now = time.time()
            bucket_key = f"rate_limit:bucket:{identifier}"
            last_refill_key = f"rate_limit:last_refill:{identifier}"
            
            # Get current state from Redis
            async with self.cache.redis.pipeline() as pipe:
                pipe.get(bucket_key)
                pipe.get(last_refill_key)
                pipe.get(f"rate_limit:blocked_until:{identifier}")
                
                results = await pipe.execute()
                current_tokens_str, last_refill_str, blocked_until_str = results
                
                # Check if user is currently blocked
                if blocked_until_str:
                    blocked_until = float(blocked_until_str)
                    if now < blocked_until:
                        logger.warning(f"Rate limit: Identifier {identifier} is blocked until {blocked_until}")
                        return False
                    else:
                        # Clear expired block
                        await self.cache.delete(f"rate_limit:blocked_until:{identifier}")
            
            # Calculate tokens to add based on time passed
            current_tokens = float(current_tokens_str) if current_tokens_str is not None else float(limit_config.capacity)
            last_refill = float(last_refill_str) if last_refill_str is not None else now
            
            # Time elapsed since last refill
            time_elapsed = now - last_refill
            
            # Calculate new tokens (cannot exceed capacity)
            tokens_to_add = time_elapsed * limit_config.refill_rate
            new_tokens = min(float(limit_config.capacity), current_tokens + tokens_to_add)
            
            # Check if we have at least 1 token
            if new_tokens < 1.0:
                if limit_config.block_duration > 0:
                    # Block the identifier for the specified duration
                    blocked_until = now + limit_config.block_duration
                    await self.cache.redis.setex(
                        f"rate_limit:blocked_until:{identifier}",
                        limit_config.block_duration,
                        str(blocked_until)
                    )
                    logger.warning(f"Rate limit: Identifier {identifier} blocked for {limit_config.block_duration}s")
                return False
            
            # Consume one token
            new_tokens -= 1.0
            
            # Update bucket state in Redis
            async with self.cache.redis.pipeline() as pipe:
                pipe.setex(bucket_key, 3600, str(new_tokens))  # Store for 1 hour
                pipe.setex(last_refill_key, 3600, str(now))
                
                await pipe.execute()
            
            logger.debug(f"Rate limit: Identifier {identifier} allowed, {new_tokens:.2f} tokens remaining")
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error for {identifier}: {e}")
            # In case of error, allow the request but log the issue
            return True
    
    async def get_remaining_tokens(self, identifier: str, limit_config: RateLimitConfig) -> int:
        """Get remaining tokens for identifier"""
        try:
            now = time.time()
            bucket_key = f"rate_limit:bucket:{identifier}"
            last_refill_key = f"rate_limit:last_refill:{identifier}"
            
            async with self.cache.redis.pipeline() as pipe:
                pipe.get(bucket_key)
                pipe.get(last_refill_key)
                
                results = await pipe.execute()
                current_tokens_str, last_refill_str = results
                
                current_tokens = float(current_tokens_str) if current_tokens_str is not None else float(limit_config.capacity)
                last_refill = float(last_refill_str) if last_refill_str is not None else now
                
                time_elapsed = now - last_refill
                tokens_to_add = time_elapsed * limit_config.refill_rate
                new_tokens = min(float(limit_config.capacity), current_tokens + tokens_to_add)
                
                return max(0, int(new_tokens))
                
        except Exception as e:
            logger.error(f"Error getting remaining tokens for {identifier}: {e}")
            return limit_config.capacity
    
    async def get_rate_limit_info(self, identifier: str, limit_config: RateLimitConfig) -> Dict:
        """Get detailed rate limit information"""
        try:
            remaining_tokens = await self.get_remaining_tokens(identifier, limit_config)
            reset_time = time.time() + (1 / limit_config.refill_rate) if limit_config.refill_rate > 0 else 0
            
            return {
                'capacity': limit_config.capacity,
                'remaining': remaining_tokens,
                'reset_time': reset_time,
                'requests_per_minute': limit_config.requests_per_minute,
                'requests_per_hour': limit_config.requests_per_hour
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info for {identifier}: {e}")
            return {}


class SlidingWindowRateLimiter(RateLimiter):
    """
    Sliding Window Rate Limiter implementation
    
    Tracks requests in a sliding time window for more precise rate limiting
    """
    
    def __init__(self, cache_manager: RedisCacheManager):
        self.cache = cache_manager
    
    async def check_rate_limit(self, identifier: str, limit_config: RateLimitConfig) -> bool:
        """Check rate limit using sliding window algorithm"""
        try:
            window_size = 60  # 1 minute window
            now = time.time()
            window_start = now - window_size
            window_key = f"rate_limit:window:{identifier}:{int(window_start // window_size)}"
            
            # Get all request timestamps in current window
            pattern = f"rate_limit:window:{identifier}:*"
            keys = await self.cache.redis.keys(pattern)
            
            total_requests = 0
            current_window_requests = 0
            
            if keys:
                values = await self.cache.redis.mget(keys)
                for key, value in zip(keys, values):
                    if value:
                        timestamps = value.split(',')
                        for timestamp_str in timestamps:
                            if timestamp_str:
                                timestamp = float(timestamp_str)
                                if timestamp >= window_start:
                                    total_requests += 1
                                    if key == window_key:
                                        current_window_requests += 1
            
            # Check if we're at or below capacity
            if total_requests < limit_config.capacity:
                # Add current request
                if current_window_requests == 0:
                    await self.cache.redis.setex(window_key, window_size + 10, str(now))
                else:
                    await self.cache.redis.setex(
                        window_key, 
                        window_size + 10, 
                        f"{current_window_requests},{now}"
                    )
                
                logger.debug(f"Rate limit: Sliding window for {identifier} allowed")
                return True
            else:
                logger.warning(f"Rate limit: Sliding window for {identifier} exceeded")
                return False
                
        except Exception as e:
            logger.error(f"Sliding window rate limit error for {identifier}: {e}")
            return True
    
    async def get_remaining_tokens(self, identifier: str, limit_config: RateLimitConfig) -> int:
        """Get remaining tokens in sliding window"""
        try:
            window_size = 60
            now = time.time()
            window_start = now - window_size
            
            pattern = f"rate_limit:window:{identifier}:*"
            keys = await self.cache.redis.keys(pattern)
            
            if not keys:
                return limit_config.capacity
            
            values = await self.cache.redis.mget(keys)
            total_requests = 0
            
            for key, value in zip(keys, values):
                if value:
                    timestamps = value.split(',')
                    for timestamp_str in timestamps:
                        if timestamp_str:
                            timestamp = float(timestamp_str)
                            if timestamp >= window_start:
                                total_requests += 1
            
            return max(0, limit_config.capacity - total_requests)
            
        except Exception as e:
            logger.error(f"Error getting sliding window tokens for {identifier}: {e}")
            return limit_config.capacity


class RateLimitManager:
    """
    Centralized rate limit management system
    """
    
    def __init__(self):
        self.cache_manager = None
        self.token_bucket_limiter = None
        self.sliding_window_limiter = None
        self._api_limits = {}
        self._ip_limits = {}
    
    async def initialize(self, cache_manager: RedisCacheManager):
        """Initialize rate limiter with cache manager"""
        self.cache_manager = cache_manager
        self.token_bucket_limiter = TokenBucketRateLimiter(cache_manager)
        self.sliding_window_limiter = SlidingWindowRateLimiter(cache_manager)
        
        # Configure default rate limits
        await self._setup_default_limits()
    
    async def _setup_default_limits(self):
        """Setup default rate limits for different APIs and IP addresses"""
        # API-specific rate limits
        self._api_limits = {
            'newsapi': RateLimitConfig(
                capacity=100,  # Max burst requests
                refill_rate=100/3600,  # 100 requests per hour
                refill_interval=3600,
                block_duration=300  # 5 minute block if exceeded
            ),
            'guardian': RateLimitConfig(
                capacity=50,  # Max burst requests
                refill_rate=50/3600,  # 50 requests per hour
                refill_interval=3600,
                block_duration=600  # 10 minute block if exceeded
            ),
            'nytimes': RateLimitConfig(
                capacity=50,  # Max burst requests
                refill_rate=50/3600,  # 50 requests per hour
                refill_interval=3600,
                block_duration=300  # 5 minute block if exceeded
            ),
            'openai': RateLimitConfig(
                capacity=60,  # Max burst requests
                refill_rate=60/3600,  # 60 requests per hour
                refill_interval=3600,
                block_duration=1800  # 30 minute block if exceeded
            ),
            'general': RateLimitConfig(
                capacity=1000,  # Max burst requests
                refill_rate=1000/3600,  # 1000 requests per hour
                refill_interval=3600
            )
        }
        
        # IP-based rate limits
        self._ip_limits = {
            'default': RateLimitConfig(
                capacity=100,  # Max 100 requests burst
                refill_rate=100/3600,  # 100 requests per hour
                refill_interval=3600,
                block_duration=1800  # 30 minute block if exceeded
            ),
            'premium': RateLimitConfig(
                capacity=500,  # Max 500 requests burst
                refill_rate=500/3600,  # 500 requests per hour
                refill_interval=3600
            )
        }
    
    async def check_api_rate_limit(self, api_name: str, use_algorithm: str = 'token_bucket') -> bool:
        """
        Check rate limit for API usage
        
        Args:
            api_name: Name of the API (newsapi, guardian, openai, etc.)
            use_algorithm: Algorithm to use ('token_bucket' or 'sliding_window')
            
        Returns:
            True if request is allowed
        """
        if not self.cache_manager:
            raise RuntimeError("Rate limit manager not initialized")
        
        # Get API configuration
        api_config = self._api_limits.get(api_name, self._api_limits['general'])
        
        # Use API name as identifier
        if use_algorithm == 'token_bucket':
            return await self.token_bucket_limiter.check_rate_limit(f"api:{api_name}", api_config)
        else:
            return await self.sliding_window_limiter.check_rate_limit(f"api:{api_name}", api_config)
    
    async def check_ip_rate_limit(
        self, 
        ip_address: str, 
        limit_type: str = 'default',
        use_algorithm: str = 'token_bucket'
    ) -> bool:
        """
        Check rate limit for IP address
        
        Args:
            ip_address: Client IP address
            limit_type: Type of limit ('default' or 'premium')
            use_algorithm: Algorithm to use
            
        Returns:
            True if request is allowed
        """
        if not self.cache_manager:
            raise RuntimeError("Rate limit manager not initialized")
        
        ip_config = self._ip_limits.get(limit_type, self._ip_limits['default'])
        ip_identifier = f"ip:{ip_address}"
        
        if use_algorithm == 'token_bucket':
            return await self.token_bucket_limiter.check_rate_limit(ip_identifier, ip_config)
        else:
            return await self.sliding_window_limiter.check_rate_limit(ip_identifier, ip_config)
    
    async def check_user_rate_limit(
        self, 
        user_id: str, 
        limit_config: RateLimitConfig,
        use_algorithm: str = 'token_bucket'
    ) -> bool:
        """
        Check rate limit for specific user
        
        Args:
            user_id: User identifier
            limit_config: Custom rate limit configuration
            use_algorithm: Algorithm to use
            
        Returns:
            True if request is allowed
        """
        if not self.cache_manager:
            raise RuntimeError("Rate limit manager not initialized")
        
        user_identifier = f"user:{user_id}"
        
        if use_algorithm == 'token_bucket':
            return await self.token_bucket_limiter.check_rate_limit(user_identifier, limit_config)
        else:
            return await self.sliding_window_limiter.check_rate_limit(user_identifier, limit_config)
    
    async def get_api_rate_info(self, api_name: str) -> Dict:
        """Get rate limit information for API"""
        if not self.cache_manager:
            raise RuntimeError("Rate limit manager not initialized")
        
        api_config = self._api_limits.get(api_name, self._api_limits['general'])
        return await self.token_bucket_limiter.get_rate_limit_info(f"api:{api_name}", api_config)
    
    async def get_ip_rate_info(self, ip_address: str, limit_type: str = 'default') -> Dict:
        """Get rate limit information for IP"""
        if not self.cache_manager:
            raise RuntimeError("Rate limit manager not initialized")
        
        ip_config = self._ip_limits.get(limit_type, self._ip_limits['default'])
        return await self.token_bucket_limiter.get_rate_limit_info(f"ip:{ip_address}", ip_config)
    
    async def reset_rate_limit(self, identifier: str, identifier_type: str = 'ip'):
        """Reset rate limit for a specific identifier"""
        try:
            if not self.cache_manager:
                return
            
            pattern = f"rate_limit:*:{identifier}"
            await self.cache_manager.delete_pattern(pattern)
            logger.info(f"Rate limit reset for {identifier_type}:{identifier}")
            
        except Exception as e:
            logger.error(f"Error resetting rate limit for {identifier}: {e}")
    
    def add_api_rate_limit(self, api_name: str, rate_config: RateLimitConfig):
        """Add custom rate limit for API"""
        self._api_limits[api_name] = rate_config
        logger.info(f"Added custom rate limit for API: {api_name}")
    
    def add_ip_rate_limit(self, ip_address: str, rate_config: RateLimitConfig):
        """Add custom rate limit for specific IP"""
        self._ip_limits[ip_address] = rate_config
        logger.info(f"Added custom rate limit for IP: {ip_address}")
    
    async def get_rate_limit_stats(self) -> Dict:
        """Get overall rate limiting statistics"""
        try:
            if not self.cache_manager:
                return {}
            
            stats = await self.cache_manager.get_cache_stats()
            stats['rate_limit_stats'] = {
                'configured_apis': len(self._api_limits),
                'configured_ips': len(self._ip_limits),
                'api_limits': {name: config.__dict__ for name, config in self._api_limits.items()},
                'ip_limits': {name: config.__dict__ for name, config in self._ip_limits.items()}
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {}


# Global rate limit manager instance
rate_limit_manager = RateLimitManager()


async def get_rate_limit_manager() -> RateLimitManager:
    """Get global rate limit manager instance"""
    if not rate_limit_manager.cache_manager:
        cache_manager = await get_cache_manager()
        await rate_limit_manager.initialize(cache_manager)
    return rate_limit_manager


# Decorator for easy rate limiting
def rate_limit(limit_type: str = 'api', identifier: str = None, algorithm: str = 'token_bucket'):
    """
    Decorator for automatic rate limiting
    
    Args:
        limit_type: Type of limit ('api', 'ip', or 'user')
        identifier: Custom identifier (defaults to request context)
        algorithm: Rate limiting algorithm to use
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = await get_rate_limit_manager()
            
            if limit_type == 'api':
                api_name = identifier or 'general'
                allowed = await manager.check_api_rate_limit(api_name, algorithm)
            elif limit_type == 'ip':
                # This would need to be adapted based on your request handling
                allowed = True  # Placeholder - would need actual IP extraction
            elif limit_type == 'user':
                # This would need to be adapted based on your user handling
                allowed = True  # Placeholder - would need actual user ID
            else:
                allowed = True
            
            if not allowed:
                raise Exception(f"Rate limit exceeded for {limit_type}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator