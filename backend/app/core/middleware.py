"""
FastAPI Middleware for Rate Limiting and Caching

This module provides middleware components for integrating rate limiting
and caching functionality with FastAPI applications.
"""

import asyncio
import time
from typing import Callable, Dict, Optional, Union, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException
import logging

from .redis_cache import get_cache_manager, RedisCacheManager
from .rate_limiter import get_rate_limit_manager, RateLimitConfig

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic rate limiting
    """
    
    def __init__(
        self,
        app,
        default_limit_type: str = 'ip',
        default_algorithm: str = 'token_bucket',
        exempt_paths: list = None
    ):
        """
        Initialize rate limit middleware
        
        Args:
            app: FastAPI application
            default_limit_type: Default limit type ('ip', 'api', 'user')
            default_algorithm: Algorithm to use ('token_bucket', 'sliding_window')
            exempt_paths: List of exempt paths (no rate limiting)
        """
        super().__init__(app)
        self.default_limit_type = default_limit_type
        self.default_algorithm = default_algorithm
        self.exempt_paths = exempt_paths or [
            '/health',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/favicon.ico'
        ]
        self.rate_limit_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the rate limit manager"""
        if not self._initialized:
            self.rate_limit_manager = await get_rate_limit_manager()
            self._initialized = True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply rate limiting"""
        await self.initialize()
        
        # Check if path is exempt
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip rate limiting for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        try:
            # Determine limit type and identifier
            limit_type, identifier = await self._get_limit_type_and_identifier(request)
            
            if not await self._check_rate_limit(limit_type, identifier):
                return await self._create_rate_limit_response(request, limit_type, identifier)
            
            # Proceed with request
            response = await call_next(request)
            
            # Add rate limit headers to response
            await self._add_rate_limit_headers(response, limit_type, identifier)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            # In case of error, allow the request but log the issue
            return await call_next(request)
    
    async def _get_limit_type_and_identifier(self, request: Request) -> tuple:
        """Determine rate limit type and identifier from request"""
        
        # Check for custom rate limit headers
        custom_limit_type = request.headers.get('X-RateLimit-Type')
        custom_identifier = request.headers.get('X-RateLimit-Identifier')
        
        if custom_limit_type and custom_identifier:
            return custom_limit_type, custom_identifier
        
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return 'api', f"api:{api_key}"
        
        # Default to IP-based limiting
        client_ip = self._get_client_ip(request)
        return 'ip', f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (for proxies/load balancers)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Get the first IP in the list
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(self, limit_type: str, identifier: str) -> bool:
        """Check if request is within rate limit"""
        
        if limit_type == 'api':
            # Extract API name from identifier
            api_name = identifier.replace('api:', '') if identifier.startswith('api:') else 'general'
            return await self.rate_limit_manager.check_api_rate_limit(api_name, self.default_algorithm)
        
        elif limit_type == 'ip':
            # Extract IP from identifier
            ip_address = identifier.replace('ip:', '') if identifier.startswith('ip:') else 'default'
            return await self.rate_limit_manager.check_ip_rate_limit(ip_address, 'default', self.default_algorithm)
        
        elif limit_type == 'user':
            # This would need custom logic based on your authentication system
            return True  # Placeholder
        
        else:
            logger.warning(f"Unknown rate limit type: {limit_type}")
            return True  # Allow request if type is unknown
    
    async def _create_rate_limit_response(self, request: Request, limit_type: str, identifier: str) -> Response:
        """Create rate limit exceeded response"""
        
        # Get rate limit info for response headers
        if limit_type == 'api':
            api_name = identifier.replace('api:', '') if identifier.startswith('api:') else 'general'
            rate_info = await self.rate_limit_manager.get_api_rate_info(api_name)
        elif limit_type == 'ip':
            ip_address = identifier.replace('ip:', '') if identifier.startswith('ip:') else 'default'
            rate_info = await self.rate_limit_manager.get_ip_rate_info(ip_address, 'default')
        else:
            rate_info = {}
        
        # Create response headers
        headers = {
            'X-RateLimit-Type': limit_type,
            'X-RateLimit-Identifier': identifier,
            'Retry-After': str(int(rate_info.get('reset_time', time.time()) - time.time())) if rate_info else '60'
        }
        
        if rate_info:
            headers.update({
                'X-RateLimit-Limit': str(rate_info.get('capacity', 0)),
                'X-RateLimit-Remaining': str(rate_info.get('remaining', 0)),
                'X-RateLimit-Reset': str(int(rate_info.get('reset_time', 0)))
            })
        
        return JSONResponse(
            status_code=429,
            content={
                'error': 'Rate limit exceeded',
                'message': f'Requests exceeded for {limit_type}: {identifier}',
                'retry_after': headers['Retry-After']
            },
            headers=headers
        )
    
    async def _add_rate_limit_headers(self, response: Response, limit_type: str, identifier: str):
        """Add rate limit headers to response"""
        
        try:
            if limit_type == 'api':
                api_name = identifier.replace('api:', '') if identifier.startswith('api:') else 'general'
                rate_info = await self.rate_limit_manager.get_api_rate_info(api_name)
            elif limit_type == 'ip':
                ip_address = identifier.replace('ip:', '') if identifier.startswith('ip:') else 'default'
                rate_info = await self.rate_limit_manager.get_ip_rate_info(ip_address, 'default')
            else:
                rate_info = {}
            
            if rate_info:
                response.headers['X-RateLimit-Limit'] = str(rate_info.get('capacity', 0))
                response.headers['X-RateLimit-Remaining'] = str(rate_info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(int(rate_info.get('reset_time', 0)))
            
            response.headers['X-RateLimit-Type'] = limit_type
            
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")


class CacheMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic caching
    """
    
    def __init__(
        self,
        app,
        cache_ttl: int = 300,  # 5 minutes default
        cache_paths: list = None,
        exempt_methods: list = None
    ):
        """
        Initialize cache middleware
        
        Args:
            app: FastAPI application
            cache_ttl: Default cache TTL in seconds
            cache_paths: List of paths to cache (empty list = cache all GET requests)
            exempt_methods: HTTP methods to exempt from caching
        """
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cache_paths = cache_paths or []
        self.exempt_methods = exempt_methods or ['POST', 'PUT', 'DELETE', 'PATCH']
        self.cache_manager = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the cache manager"""
        if not self._initialized:
            self.cache_manager = await get_cache_manager()
            self._initialized = True
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching support"""
        await self.initialize()
        
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if path should be cached
        if self.cache_paths and request.url.path not in self.cache_paths:
            return await call_next(request)
        
        # Create cache key
        cache_key = await self._create_cache_key(request)
        
        try:
            # Try to get from cache first
            cached_response = await self.cache_manager.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {request.url.path}")
                return Response(
                    content=cached_response['content'],
                    status_code=cached_response['status_code'],
                    headers=cached_response['headers'],
                    media_type=cached_response['media_type']
                )
            
            # Not in cache, process request
            logger.debug(f"Cache miss for {request.url.path}")
            response = await call_next(request)
            
            # Cache the response (only for successful responses)
            if response.status_code < 400:
                await self._cache_response(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Cache middleware error: {e}")
            return await call_next(request)
    
    async def _create_cache_key(self, request: Request) -> str:
        """Create cache key from request"""
        # Include method, path, and query parameters
        query_params = sorted(request.query_params.items())
        key_data = f"{request.method}:{request.url.path}"
        
        if query_params:
            key_data += "?" + "&".join([f"{k}={v}" for k, v in query_params])
        
        # Create hash-like key (Redis doesn't support all characters)
        import hashlib
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"http_cache:{key_hash}"
    
    async def _cache_response(self, cache_key: str, response: Response):
        """Cache response data"""
        try:
            # Read response body for caching
            response_body = response.body
            
            cache_data = {
                'content': response_body.decode() if response_body else '',
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'media_type': response.media_type
            }
            
            await self.cache_manager.set(cache_key, cache_data, ttl=self.cache_ttl)
            logger.debug(f"Response cached for key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware for health checks and system monitoring
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.start_time = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add timing and health check headers"""
        request_start_time = time.time()
        
        response = await call_next(request)
        
        # Add custom headers
        response.headers['X-Response-Time'] = str(time.time() - request_start_time)
        response.headers['X-Uptime'] = str(time.time() - self.start_time)
        
        return response