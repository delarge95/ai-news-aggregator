"""
Pydantic schemas for AI News Aggregator
"""

from .article import (
    ArticleBase,
    ArticleCreate,
    ArticleUpdate,
    ArticleResponse,
    ArticleListResponse,
    ArticleAnalysisResponse
)
from .user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    UserPreferenceUpdate
)
from .analytics import (
    AnalyticsParams,
    AnalyticsResponse,
    SentimentAnalytics,
    TrendAnalytics,
    SourceAnalytics
)
from .search import (
    SearchParams,
    SearchResponse,
    AdvancedSearchParams,
    SearchFacet
)
from .pagination import (
    PaginationParams,
    Meta,
    PaginatedResponse
)

__all__ = [
    # Article schemas
    "ArticleBase",
    "ArticleCreate", 
    "ArticleUpdate",
    "ArticleResponse",
    "ArticleListResponse",
    "ArticleAnalysisResponse",
    
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin", 
    "UserResponse",
    "UserPreferenceUpdate",
    
    # Analytics schemas
    "AnalyticsParams",
    "AnalyticsResponse",
    "SentimentAnalytics",
    "TrendAnalytics",
    "SourceAnalytics",
    
    # Search schemas
    "SearchParams",
    "SearchResponse", 
    "AdvancedSearchParams",
    "SearchFacet",
    
    # Pagination schemas
    "PaginationParams",
    "Meta",
    "PaginatedResponse"
]