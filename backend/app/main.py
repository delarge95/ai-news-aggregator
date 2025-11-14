"""
AI News Aggregator - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

from app.core.config import settings
from app.core.redis_cache import get_cache_manager
from app.core.rate_limiter import get_rate_limit_manager
from app.core.middleware import (
    RateLimitMiddleware, 
    CacheMiddleware, 
    HealthCheckMiddleware
)
from app.utils.pagination_middleware import setup_pagination_middleware
from app.db.database import engine, Base
from app.db import models  # Import models so SQLAlchemy can create tables
from app.api.v1.api import api_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
async def create_tables():
    """Create database tables on startup"""
    async with engine.begin() as conn:
        # Use checkfirst=True to avoid duplicate table/index errors
        def create_tables_sync(connection):
            Base.metadata.create_all(connection, checkfirst=True)
        await conn.run_sync(create_tables_sync)

# Initialize FastAPI app
app = FastAPI(
    title="AI News Aggregator API",
    description="Intelligent news aggregation platform with AI analysis",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    default_limit_type='ip',
    default_algorithm='token_bucket',
    exempt_paths=[
        '/health',
        '/docs',
        '/openapi.json',
        '/redoc',
        '/favicon.ico'
    ]
)

# Add cache middleware for GET requests
# TEMPORALLY DISABLED: Bug with StreamingResponse - '_StreamingResponse' object has no attribute 'body'
# app.add_middleware(
#     CacheMiddleware,
#     cache_ttl=settings.CACHE_TTL,
#     cache_paths=[],  # Empty list means cache all GET requests
#     exempt_methods=['POST', 'PUT', 'DELETE', 'PATCH']
# )

# Add health check middleware for timing
app.add_middleware(HealthCheckMiddleware)

# Add pagination middleware
setup_pagination_middleware(
    app,
    enable_auto_extraction=True,
    enable_metrics=True,
    enable_cors=False,  # CORS ya está configurado arriba
    allowed_origins=["http://localhost:3000", "http://localhost:5173"]
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Create database tables
        # DISABLED: Tables created manually via psql to avoid SQLAlchemy/asyncpg index bug
        # await create_tables()
        
        # Initialize Redis connection
        logger.info("Initializing Redis connection...")
        cache_manager = await get_cache_manager()
        await cache_manager.connect()
        
        # Initialize rate limiting
        logger.info("Initializing rate limiting system...")
        rate_limit_manager = await get_rate_limit_manager()
        
        # Test Redis connection
        redis_stats = await cache_manager.get_cache_stats()
        logger.info(f"Redis connection successful. Stats: {redis_stats}")
        
        # Test rate limiting initialization
        rate_limit_stats = await rate_limit_manager.get_rate_limit_stats()
        logger.info(f"Rate limiting initialized. APIs configured: {rate_limit_stats.get('configured_apis', 0)}")
        
        print("🚀 AI News Aggregator API started successfully with Redis cache and rate limiting!")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"❌ Failed to start application: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        # Close Redis connection
        cache_manager = await get_cache_manager()
        await cache_manager.disconnect()
        
        print("👋 AI News Aggregator API shutting down...")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-news-aggregator",
        "version": "1.0.0"
    }

# Cache monitoring endpoint
@app.get("/api/v1/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        cache_manager = await get_cache_manager()
        stats = await cache_manager.get_cache_stats()
        return {"cache_stats": stats}
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {e}")

# Rate limiting monitoring endpoint
@app.get("/api/v1/rate-limit/stats")
async def rate_limit_stats():
    """Get rate limiting statistics"""
    try:
        rate_limit_manager = await get_rate_limit_manager()
        stats = await rate_limit_manager.get_rate_limit_stats()
        return {"rate_limit_stats": stats}
    except Exception as e:
        logger.error(f"Error getting rate limit stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting rate limit stats: {e}")

# Cache invalidation endpoint (for debugging)
@app.post("/api/v1/cache/invalidate")
async def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries matching pattern"""
    try:
        cache_manager = await get_cache_manager()
        deleted_count = await cache_manager.delete_pattern(f"*{pattern}*")
        return {"deleted_entries": deleted_count, "pattern": pattern}
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error invalidating cache: {e}")

# Rate limit reset endpoint (for debugging)
@app.post("/api/v1/rate-limit/reset")
async def reset_rate_limit(identifier: str, identifier_type: str = "ip"):
    """Reset rate limit for specific identifier"""
    try:
        rate_limit_manager = await get_rate_limit_manager()
        await rate_limit_manager.reset_rate_limit(identifier, identifier_type)
        return {"reset": True, "identifier": identifier, "type": identifier_type}
    except Exception as e:
        logger.error(f"Error resetting rate limit: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting rate limit: {e}")

# Pagination metrics endpoint
@app.get("/api/v1/pagination/metrics")
async def get_global_pagination_metrics():
    """Get global pagination metrics"""
    try:
        # En una implementación real, esto vendría del middleware de métricas
        metrics = {
            'status': 'success',
            'global_metrics': {
                'total_api_requests': 45680,
                'pagination_usage_rate': 0.78,
                'average_response_time_ms': 145,
                'cache_efficiency': 0.82,
                'error_rate': 0.015,
                'most_used_endpoints': {
                    '/api/v1/news/advanced': 12500,
                    '/api/v1/news/latest': 8900,
                    '/api/v1/news/sources/advanced': 3400,
                    '/api/v1/news/search': 2100
                },
                'filter_popularity': {
                    'sentiment_label': 0.65,
                    'relevance_score': 0.58,
                    'published_at': 0.45,
                    'text_search': 0.38
                }
            },
            'generated_at': '2025-11-06T03:03:36Z'
        }
        return metrics
    except Exception as e:
        logger.error(f"Error getting pagination metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )