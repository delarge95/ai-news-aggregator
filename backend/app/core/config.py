"""
Configuration settings for AI News Aggregator
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI News Aggregator"
    VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database Configuration
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/ai_news_db",
        description="Database connection URL"
    )
    
    # Redis Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )
    
    # External API Keys
    NEWSAPI_KEY: Optional[str] = Field(default=None, description="NewsAPI.org API key")
    GUARDIAN_API_KEY: Optional[str] = Field(default=None, description="Guardian API key")
    NYTIMES_API_KEY: Optional[str] = Field(default=None, description="NY Times API key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    
    # AI Configuration
    OPENAI_MODEL: str = Field(default="gpt-3.5-turbo", description="OpenAI model to use")
    MAX_ARTICLES_PER_REQUEST: int = Field(default=50, description="Max articles per API request")
    AI_ANALYSIS_TIMEOUT: int = Field(default=30, description="AI analysis timeout in seconds")
    
    # Rate Limiting
    NEWS_API_RATE_LIMIT: int = Field(default=100, description="News API requests per hour")
    AI_API_RATE_LIMIT: int = Field(default=1000, description="AI API requests per hour")
    RATE_LIMIT_CONFIG: dict = Field(
        default={"max_requests": 1000, "time_window": 3600},
        description="Rate limit configuration as dictionary"
    )
    
    # Cache Configuration
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    ARTICLE_CACHE_TTL: int = Field(default=1800, description="Article cache TTL in seconds")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379", description="Celery result backend")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here", description="Application secret key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration time")
    
    # AI Monitoring Configuration
    AI_MONITORING_ENABLED: bool = Field(default=True, description="Enable AI monitoring")
    AI_MONITORING_RETENTION_DAYS: int = Field(default=30, description="Days to retain monitoring data")
    AI_MONITORING_MAX_HISTORY: int = Field(default=10000, description="Maximum number of tasks to keep in history")
    AI_MONITORING_ALERT_EMAIL: Optional[str] = Field(default=None, description="Email for critical alerts")
    AI_MONITORING_SLACK_WEBHOOK: Optional[str] = Field(default=None, description="Slack webhook for alerts")
    AI_MONITORING_DASHBOARD_ENABLED: bool = Field(default=True, description="Enable dashboard API endpoints")
    
    # Cost Thresholds
    AI_COST_DAILY_WARNING: float = Field(default=10.0, description="Daily cost warning threshold ($)")
    AI_COST_DAILY_CRITICAL: float = Field(default=25.0, description="Daily cost critical threshold ($)")
    AI_COST_TASK_WARNING: float = Field(default=0.5, description="Single task cost warning threshold ($)")
    AI_COST_TASK_CRITICAL: float = Field(default=1.0, description="Single task cost critical threshold ($)")
    
    # Performance Thresholds
    AI_LATENCY_WARNING: float = Field(default=30.0, description="Latency warning threshold (seconds)")
    AI_LATENCY_CRITICAL: float = Field(default=60.0, description="Latency critical threshold (seconds)")
    AI_ERROR_RATE_WARNING: float = Field(default=10.0, description="Error rate warning threshold (%)")
    AI_ERROR_RATE_CRITICAL: float = Field(default=20.0, description="Error rate critical threshold (%)")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance"""
    return settings