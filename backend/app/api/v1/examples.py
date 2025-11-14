"""
Example usage of cache and rate limiting systems

This module demonstrates how to use the cache and rate limiting systems
in FastAPI endpoints and background tasks.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Dict, Optional
import logging

from app.core.utils import get_cache_utils, get_rate_limit_utils, cache_result, rate_limit_by_api
from app.core.redis_cache import get_cache_manager
from app.core.rate_limit import get_rate_limit_manager

logger = logging.getLogger(__name__)

# Create example router
example_router = APIRouter(prefix="/examples", tags=["examples"])


@example_router.get("/cache-demo")
@cache_result(ttl=300, key_prefix="demo")
async def cache_demo_endpoint(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Demo endpoint showing cache functionality
    
    This endpoint demonstrates:
    - Automatic caching of results
    - Cache hit/miss logging
    - TTL management
    """
    # Simulate expensive operation
    await asyncio.sleep(2)
    
    # Simulated results
    results = {
        "query": query,
        "page": page,
        "results": f"Sample results for {query}",
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Generated results for query: {query}, page: {page}")
    return results


@example_router.get("/rate-limit-demo")
@rate_limit_by_api('general')
async def rate_limit_demo_endpoint(
    request: Request,
    action: str = Query(..., description="Action to perform")
):
    """
    Demo endpoint showing rate limiting
    
    This endpoint demonstrates:
    - Automatic rate limiting by API
    - Rate limit headers in response
    - Custom rate limit configurations
    """
    # Get rate limit info from headers
    remaining_tokens = request.headers.get('X-RateLimit-Remaining')
    reset_time = request.headers.get('X-RateLimit-Reset')
    
    result = {
        "action": action,
        "status": "success",
        "rate_limit_info": {
            "remaining": remaining_tokens,
            "reset_time": reset_time
        }
    }
    
    logger.info(f"Rate limit demo: {action}")
    return result


@example_router.get("/manual-cache-demo")
async def manual_cache_demo(
    search_term: str = Query(..., description="Search term to cache"),
    use_cache: bool = Query(True, description="Whether to use cache")
):
    """
    Demo endpoint showing manual cache usage
    
    This endpoint demonstrates:
    - Manual cache operations
    - Cache utility functions
    - Cache invalidation
    """
    cache_utils = await get_cache_utils()
    
    if use_cache:
        # Try to get from cache first
        cached_result = await cache_utils.get_cached_news_articles(search_term)
        if cached_result:
            logger.info(f"Cache hit for manual demo: {search_term}")
            return {
                "search_term": search_term,
                "results": cached_result['articles'],
                "cache_hit": True,
                "cache_age_seconds": cached_result.get('cache_age_seconds', 0)
            }
    
    # Simulate API call
    await asyncio.sleep(1)
    results = {
        "articles": [
            {
                "title": f"Sample article for {search_term}",
                "content": "This is a sample article content...",
                "url": f"https://example.com/article/{search_term}"
            }
        ],
        "total": 1
    }
    
    # Cache the results
    cache_key = await cache_utils.cache_news_articles(search_term, results['articles'])
    
    return {
        "search_term": search_term,
        "results": results,
        "cache_hit": False,
        "cache_key": cache_key
    }


@example_router.get("/news-search")
@cache_result(ttl=900, key_prefix="news_search")
@rate_limit_by_api('newsapi')
async def news_search_endpoint(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="News category"),
    language: str = Query("en", description="Language code"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    News search endpoint with full cache and rate limiting integration
    
    This endpoint demonstrates:
    - Combined cache and rate limiting
    - API-specific rate limiting
    - Caching with custom TTL
    - Error handling
    """
    rate_limit_utils = await get_rate_limit_utils()
    
    # Check rate limit before proceeding
    within_limit = await rate_limit_utils.check_newsapi_limit()
    if not within_limit:
        raise HTTPException(
            status_code=429,
            detail="News API rate limit exceeded. Please try again later."
        )
    
    # Check cache first
    cache_utils = await get_cache_utils()
    
    # Create search query hash for cache
    cache_data = {
        "query": query,
        "category": category,
        "language": language,
        "page": page,
        "page_size": page_size
    }
    
    # Try cache
    cached_results = await cache_utils.get_cached_news_articles(str(cache_data))
    if cached_results:
        logger.info(f"Cache hit for news search: {query}")
        return {
            "query": query,
            "category": category,
            "language": language,
            "articles": cached_results['articles'],
            "cache_hit": True,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": len(cached_results['articles'])
            }
        }
    
    # Simulate external API call
    logger.info(f"Making NewsAPI call for: {query}")
    await asyncio.sleep(1)
    
    # Simulated API response
    articles = [
        {
            "id": f"article_{i}",
            "title": f"News article {i} about {query}",
            "description": f"This is a sample news article about {query}...",
            "content": f"Full content of the article about {query}...",
            "url": f"https://news.example.com/article_{i}",
            "published_at": datetime.now().isoformat(),
            "source": "Sample News",
            "category": category or "general"
        }
        for i in range(1, page_size + 1)
    ]
    
    # Cache the results
    await cache_utils.cache_news_articles(str(cache_data), articles)
    
    return {
        "query": query,
        "category": category,
        "language": language,
        "articles": articles,
        "cache_hit": False,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": len(articles)
        }
    }


@example_router.post("/cache-invalidate")
async def invalidate_cache_endpoint(
    pattern: str = Query(..., description="Cache pattern to invalidate")
):
    """
    Endpoint to manually invalidate cache
    
    This endpoint demonstrates:
    - Manual cache invalidation
    - Pattern-based cache clearing
    - Cache statistics
    """
    cache_utils = await get_cache_utils()
    
    # Invalidate cache
    deleted_count = await cache_utils.invalidate_search_cache(pattern)
    
    # Get cache stats
    cache_manager = await get_cache_manager()
    stats = await cache_manager.get_cache_stats()
    
    return {
        "pattern": pattern,
        "deleted_entries": deleted_count,
        "cache_stats": stats
    }


@example_router.get("/rate-limit-info")
async def rate_limit_info_endpoint():
    """
    Endpoint to get rate limiting information
    
    This endpoint demonstrates:
    - Rate limit monitoring
    - API usage statistics
    - System status
    """
    rate_limit_utils = await get_rate_limit_utils()
    
    # Get stats for different APIs
    newsapi_stats = await rate_limit_utils.get_api_usage_stats('newsapi')
    openai_stats = await rate_limit_utils.get_api_usage_stats('openai')
    
    # Get rate limit manager stats
    rate_limit_manager = await get_rate_limit_manager()
    global_stats = await rate_limit_manager.get_rate_limit_stats()
    
    return {
        "api_stats": {
            "newsapi": newsapi_stats,
            "openai": openai_stats
        },
        "global_stats": global_stats
    }


@example_router.post("/add-custom-limit")
async def add_custom_limit_endpoint(
    api_name: str = Query(..., description="API name"),
    requests_per_hour: int = Query(..., description="Requests per hour"),
    burst_capacity: Optional[int] = Query(None, description="Burst capacity"),
    block_duration: int = Query(300, description="Block duration in seconds")
):
    """
    Endpoint to add custom rate limits
    
    This endpoint demonstrates:
    - Dynamic rate limit configuration
    - Custom API limits
    - Rate limit management
    """
    rate_limit_utils = await get_rate_limit_utils()
    
    # Add custom limit
    await rate_limit_utils.add_custom_api_limit(
        api_name=api_name,
        requests_per_hour=requests_per_hour,
        burst_capacity=burst_capacity,
        block_duration=block_duration
    )
    
    return {
        "api_name": api_name,
        "requests_per_hour": requests_per_hour,
        "burst_capacity": burst_capacity,
        "block_duration": block_duration,
        "status": "configured"
    }


# Background task example
@example_router.post("/background-task-demo")
async def background_task_demo():
    """
    Demo endpoint showing background task with cache integration
    """
    async def process_with_cache():
        """Background task that processes data with caching"""
        cache_utils = await get_cache_utils()
        
        # Simulate long-running process
        await asyncio.sleep(5)
        
        # Cache results
        background_results = {
            "task_id": "background_task_123",
            "status": "completed",
            "processed_items": 100,
            "timestamp": datetime.now().isoformat()
        }
        
        await cache_utils.cache_news_articles("background_task", [background_results])
        logger.info("Background task completed and cached")
    
    # Start background task
    import asyncio
    asyncio.create_task(process_with_cache())
    
    return {
        "message": "Background task started",
        "task_id": "background_task_123"
    }


# Helper function for asyncio
import asyncio
from datetime import datetime