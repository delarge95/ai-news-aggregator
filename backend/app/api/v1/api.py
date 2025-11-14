from fastapi import APIRouter
from app.api.v1.endpoints import health, news, ai_analysis, ai_test, ai_monitor, users, analytics, articles, search

api_router = APIRouter()

# Include all API routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(ai_analysis.router, prefix="/ai-analysis", tags=["ai-analysis"])
api_router.include_router(ai_test.router, prefix="/ai-analysis/test", tags=["ai-test"])
api_router.include_router(ai_monitor.router, prefix="/monitor", tags=["monitor"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])