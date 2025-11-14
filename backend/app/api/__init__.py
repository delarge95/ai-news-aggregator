# API Router
from fastapi import APIRouter

from app.api.v1.endpoints import health, articles, analytics  # sources removed - file doesn't exist

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
# api_router.include_router(sources.router, prefix="/sources", tags=["sources"])  # File doesn't exist yet
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])