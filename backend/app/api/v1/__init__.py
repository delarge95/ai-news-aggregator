"""
API endpoint files
"""

# Import all endpoint routers here
from .endpoints.health import router as health_router
from .endpoints.articles import router as articles_router
# from .endpoints.sources import router as sources_router  # File doesn't exist yet
from .endpoints.analytics import router as analytics_router

# Export router for API inclusion
from .endpoints.health import router
from .endpoints.articles import router
# from .endpoints.sources import router  # File doesn't exist yet
from .endpoints.analytics import router