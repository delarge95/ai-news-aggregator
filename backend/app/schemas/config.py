"""
Configuration settings for Pydantic schemas
"""

from typing import Dict, Any, Optional
from pydantic import BaseSettings


class SchemaSettings(BaseSettings):
    """
    Settings specific to schema validation and serialization
    """
    
    # Validation settings
    MAX_TITLE_LENGTH: int = 500
    MAX_CONTENT_LENGTH: int = 100000
    MAX_SUMMARY_LENGTH: int = 2000
    MAX_TOPIC_LENGTH: int = 50
    MAX_TOPICS_PER_ITEM: int = 20
    MAX_SOURCES_PER_USER: int = 50
    
    # Performance settings
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    MAX_CURSOR_LIMIT: int = 100
    DEFAULT_SEARCH_LIMIT: int = 20
    MAX_SEARCH_LIMIT: int = 100
    
    # Date settings
    MAX_FUTURE_DATE_DAYS: int = 1  # Allow 1 day in future for processing delays
    DEFAULT_TIMEZONE: str = "UTC"
    
    # Score ranges
    SENTIMENT_SCORE_MIN: float = -1.0
    SENTIMENT_SCORE_MAX: float = 1.0
    BIAS_SCORE_MIN: float = 0.0
    BIAS_SCORE_MAX: float = 1.0
    RELEVANCE_SCORE_MIN: float = 0.0
    RELEVANCE_SCORE_MAX: float = 1.0
    CONFIDENCE_SCORE_MIN: float = 0.0
    CONFIDENCE_SCORE_MAX: float = 1.0
    
    # Search settings
    FUZZY_SEARCH_THRESHOLD_DEFAULT: float = 0.7
    MIN_QUERY_LENGTH: int = 1
    MAX_QUERY_LENGTH: int = 500
    MAX_SEARCH_RESULTS: int = 1000
    
    # Content settings
    MIN_ARTICLE_LENGTH: int = 100
    MAX_ARTICLE_LENGTH: int = 50000
    AVERAGE_READING_SPEED: int = 200  # words per minute
    
    # User settings
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 50
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128
    FULL_NAME_MAX_LENGTH: int = 100
    
    # Analytics settings
    MAX_ANALYTICS_POINTS: int = 10000
    DEFAULT_ANALYTICS_LIMIT: int = 100
    MAX_ANALYTICS_GRANULARITY_DAYS: Dict[str, int] = {
        "hourly": 7,
        "daily": 365,
        "weekly": 730,
        "monthly": 3650
    }
    
    # Caching settings
    ENABLE_SCHEMA_CACHING: bool = True
    SCHEMA_CACHE_TTL: int = 3600  # 1 hour
    
    # Validation strictness
    STRICT_EMAIL_VALIDATION: bool = True
    STRICT_URL_VALIDATION: bool = True
    STRICT_DATE_VALIDATION: bool = True
    ALLOW_PARTIAL_UPDATES: bool = True
    
    # Serialization settings
    DATETIMESerialization_FORMAT: str = "iso"
    DECIMAL_PRECISION: int = 4
    ENUM_SERIALIZATION: str = "value"  # "value" or "name"
    
    # Error handling
    DETAILED_VALIDATION_ERRORS: bool = True
    INCLUDE_ERROR_CONTEXTS: bool = True
    VALIDATION_ERROR_STATUS_CODE: int = 422
    
    class Config:
        env_prefix = "SCHEMA_"
        case_sensitive = False


# Global settings instance
schema_settings = SchemaSettings()


# Validation constants
VALIDATION_CONSTANTS = {
    # Regex patterns
    EMAIL_PATTERN: r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    URL_PATTERN: r'^https?://(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?(?:/?|[/?]\S+)$',
    USERNAME_PATTERN: r'^[a-zA-Z0-9_-]+$',
    
    # Common values
    SENTIMENT_LABELS: ["positive", "negative", "neutral"],
    SENTIMENT_PREFERENCES: ["positive", "negative", "neutral", "all"],
    READING_LEVELS: ["simple", "mixed", "complex"],
    NOTIFICATION_FREQUENCIES: ["realtime", "hourly", "daily", "weekly"],
    PROCESSING_STATUSES: ["pending", "processing", "completed", "failed", "skipped"],
    SORT_ORDERS: ["asc", "desc"],
    SORT_FIELDS_ARTICLES: ["relevance", "date", "title", "source"],
    SORT_FIELDS_GENERAL: ["created_at", "updated_at", "name", "title"],
    
    # Date formats
    SUPPORTED_DATE_FORMATS: [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f"
    ],
    
    # Stop words for text processing
    ENGLISH_STOP_WORDS: {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy',
        'did', 'man', 'way', 'what', 'when', 'will', 'with', 'your', 'from',
        'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time'
    },
    
    # Common weak passwords
    COMMON_PASSWORDS: [
        'password', '123456', 'qwerty', 'abc123', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', 'dragon',
        '1234567890', '123456789', 'password1', '12345',
        'iloveyou', '1234', '111111', '123123', 'qwerty123'
    ],
    
    # Content quality thresholds
    MIN_CONTENT_QUALITY_SCORE: 0.5,
    MIN_LINGUISTIC_QUALITY_SCORE: 0.3,
    MIN_READABILITY_SCORE: 0.4,
    
    # Performance thresholds
    MAX_PROCESSING_TIME_MS: 5000,
    MAX_CACHE_HIT_RATIO: 0.95,
    MIN_SUCCESS_RATE: 0.90
}


# Utility functions for schema configuration
def get_validation_config(schema_type: str) -> Dict[str, Any]:
    """
    Get validation configuration for specific schema type
    """
    configs = {
        "article": {
            "title_min_length": 5,
            "title_max_length": schema_settings.MAX_TITLE_LENGTH,
            "content_max_length": schema_settings.MAX_CONTENT_LENGTH,
            "summary_max_length": schema_settings.MAX_SUMMARY_LENGTH,
            "url_max_length": 1000,
            "published_date_future_limit": schema_settings.MAX_FUTURE_DATE_DAYS
        },
        "user": {
            "email_strict": schema_settings.STRICT_EMAIL_VALIDATION,
            "username_min_length": schema_settings.USERNAME_MIN_LENGTH,
            "username_max_length": schema_settings.USERNAME_MAX_LENGTH,
            "password_min_length": schema_settings.PASSWORD_MIN_LENGTH,
            "password_max_length": schema_settings.PASSWORD_MAX_LENGTH,
            "full_name_max_length": schema_settings.FULL_NAME_MAX_LENGTH,
            "max_sources": schema_settings.MAX_SOURCES_PER_USER
        },
        "search": {
            "query_min_length": schema_settings.MIN_QUERY_LENGTH,
            "query_max_length": schema_settings.MAX_QUERY_LENGTH,
            "per_page_max": schema_settings.MAX_SEARCH_LIMIT,
            "fuzzy_threshold_default": schema_settings.FUZZY_SEARCH_THRESHOLD_DEFAULT
        },
        "pagination": {
            "page_max": 10000,
            "per_page_max": schema_settings.MAX_PAGE_SIZE,
            "cursor_limit_max": schema_settings.MAX_CURSOR_LIMIT
        },
        "analytics": {
            "granularity_limits": schema_settings.MAX_ANALYTICS_GRANULARITY_DAYS,
            "max_points": schema_settings.MAX_ANALYTICS_POINTS,
            "default_limit": schema_settings.DEFAULT_ANALYTICS_LIMIT
        }
    }
    
    return configs.get(schema_type, {})


def get_score_ranges() -> Dict[str, Dict[str, float]]:
    """
    Get valid score ranges for all metric types
    """
    return {
        "sentiment": {
            "min": schema_settings.SENTIMENT_SCORE_MIN,
            "max": schema_settings.SENTIMENT_SCORE_MAX,
            "default": 0.0
        },
        "bias": {
            "min": schema_settings.BIAS_SCORE_MIN,
            "max": schema_settings.BIAS_SCORE_MAX,
            "default": 0.0
        },
        "relevance": {
            "min": schema_settings.RELEVANCE_SCORE_MIN,
            "max": schema_settings.RELEVANCE_SCORE_MAX,
            "default": 0.0
        },
        "confidence": {
            "min": schema_settings.CONFIDENCE_SCORE_MIN,
            "max": schema_settings.CONFIDENCE_SCORE_MAX,
            "default": 1.0
        }
    }


def get_date_validation_config() -> Dict[str, Any]:
    """
    Get date validation configuration
    """
    return {
        "timezone": schema_settings.DEFAULT_TIMEZONE,
        "future_limit_days": schema_settings.MAX_FUTURE_DATE_DAYS,
        "supported_formats": VALIDATION_CONSTANTS["SUPPORTED_DATE_FORMATS"],
        "strict_validation": schema_settings.STRICT_DATE_VALIDATION
    }


def get_performance_config() -> Dict[str, Any]:
    """
    Get performance-related configuration
    """
    return {
        "default_page_size": schema_settings.DEFAULT_PAGE_SIZE,
        "max_page_size": schema_settings.MAX_PAGE_SIZE,
        "default_search_limit": schema_settings.DEFAULT_SEARCH_LIMIT,
        "max_search_limit": schema_settings.MAX_SEARCH_LIMIT,
        "schema_caching": schema_settings.ENABLE_SCHEMA_CACHING,
        "cache_ttl": schema_settings.SCHEMA_CACHE_TTL,
        "max_processing_time_ms": VALIDATION_CONSTANTS["MAX_PROCESSING_TIME_MS"]
    }