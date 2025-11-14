"""
Database models for AI News Aggregator
"""

import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, 
    Float, JSON, ForeignKey, Index, UniqueConstraint, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import Base from database module to ensure single Base instance
from app.db.database import Base


class ProcessingStatus(PyEnum):
    """Estados de procesamiento de IA para artículos"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AnalysisTaskStatus(PyEnum):
    """Estados de tareas de análisis asíncronas"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Source(Base):
    """News sources table"""
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    url = Column(String(500), nullable=False)
    api_name = Column(String(100), nullable=False)  # 'newsapi', 'guardian', 'nytimes'
    # api_source_id = Column(String(255))  # ID específico de cada API - COMENTADO: no existe en BD
    country = Column(String(100))
    language = Column(String(10), default='en')
    credibility_score = Column(Float, default=0.0)
    # is_active = Column(Boolean, default=True)  # COMENTADO: no existe en BD
    rate_limit_per_hour = Column(Integer, default=100)
    # rate_limit_info = Column(JSON)  # COMENTADO: no existe en BD
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    articles = relationship("Article", back_populates="source")


class Article(Base):
    """Articles table"""
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    url = Column(String(1000), unique=True, nullable=False)
    published_at = Column(DateTime)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Duplicate Detection Fields
    duplicate_group_id = Column(UUID(as_uuid=True))  # Para tracking de duplicados
    content_hash = Column(String(64))  # Hash del contenido para detección de duplicados (SHA-256)
    cache_expires_at = Column(DateTime)  # Para cache management
    
    # AI Analysis Fields
    sentiment_score = Column(Float)  # -1.0 to 1.0
    sentiment_label = Column(String(20))  # 'positive', 'negative', 'neutral'
    bias_score = Column(Float)  # 0.0 to 1.0
    topic_tags = Column(JSON)  # Array of topic tags
    relevance_score = Column(Float, default=0.0)  # 0.0 to 1.0
    summary = Column(Text)  # AI-generated summary of the article
    processed_at = Column(DateTime)  # General processing timestamp
    ai_processed_at = Column(DateTime)  # Specific AI processing timestamp
    # processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)  # ⚠️ ENUM no existe en DB
    processing_status = Column(String(20), default='pending')  # ✅ Usamos String por ahora
    
    # Relationships
    source = relationship("Source", back_populates="articles")
    analysis_results = relationship("ArticleAnalysis", back_populates="article")
    
    # Unique constraint for duplicate tracking
    __table_args__ = (
        Index('idx_articles_duplicate_group_hash', 'duplicate_group_id', 'content_hash'),
        Index('idx_articles_sentiment_score', 'sentiment_score'),
        Index('idx_articles_sentiment_label', 'sentiment_label'),
        Index('idx_articles_ai_processed_at', 'ai_processed_at'),
        Index('idx_articles_processing_status', 'processing_status'),
    )


class ArticleAnalysis(Base):
    """Article analysis results cache table"""
    __tablename__ = "article_analysis"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # 'summary', 'sentiment', 'bias', 'topics'
    analysis_data = Column(JSON)  # Store analysis results as JSON
    model_used = Column(String(100))
    confidence_score = Column(Float)  # 0.0 to 1.0
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    article = relationship("Article", back_populates="analysis_results")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('article_id', 'analysis_type', name='_article_analysis_type_uc'),
    )


class User(Base):
    """User authentication table"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(String(20), default='user')  # 'user', 'admin', 'moderator'
    avatar_url = Column(String(500))
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    preferences = relationship("UserPreference", back_populates="user", uselist=False)
    bookmarks = relationship("UserBookmark", back_populates="user", cascade="all, delete-orphan")


class UserPreference(Base):
    """User preferences table"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    preferred_sources = Column(JSON)  # Array of source IDs
    blocked_sources = Column(JSON)  # Array of source IDs
    preferred_topics = Column(JSON)  # Array of topic strings
    ignored_topics = Column(JSON)  # Array of topic strings
    sentiment_preference = Column(String(20), default='all')  # 'positive', 'negative', 'neutral', 'all'
    reading_level = Column(String(20), default='mixed')  # 'simple', 'mixed', 'complex'
    notification_frequency = Column(String(20), default='daily')  # 'realtime', 'hourly', 'daily', 'weekly'
    language = Column(String(10), default='es')  # Idioma preferido del usuario
    timezone = Column(String(50), default='UTC')  # Zona horaria del usuario
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")


class UserBookmark(Base):
    """User saved articles/bookmarks table"""
    __tablename__ = "user_bookmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    notes = Column(Text)  # Notas personales del usuario
    tags = Column(JSON)  # Tags asignados por el usuario
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="bookmarks")
    article = relationship("Article")
    
    # Unique constraint to prevent duplicate bookmarks
    __table_args__ = (
        UniqueConstraint('user_id', 'article_id', name='_user_article_bookmark_uc'),
    )


class TrendingTopic(Base):
    """Trending topics cache table"""
    __tablename__ = "trending_topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic = Column(String(255), nullable=False)
    topic_category = Column(String(100))  # 'politics', 'technology', 'health', etc.
    trend_score = Column(Float, default=0.0)  # Calculated trending score
    article_count = Column(Integer, default=0)
    sources_count = Column(Integer, default=0)
    time_period = Column(String(20), default='24h')  # '1h', '6h', '24h', '7d'
    date_recorded = Column(DateTime, default=datetime.utcnow)
    trend_metadata = Column(JSON)  # Additional trend metadata
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_trending_topic_date', 'date_recorded'),
        Index('idx_trending_topic_category', 'topic_category'),
        Index('idx_trending_topic_score', 'trend_score'),
    )


class AnalysisTask(Base):
    """Async AI analysis tasks tracking table"""
    __tablename__ = "analysis_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), nullable=False)  # 'sentiment', 'summary', 'topics', 'relevance'
    task_name = Column(String(255), nullable=False)  # Descriptive task name
    article_id = Column(UUID(as_uuid=True), ForeignKey("articles.id"), nullable=True)  # Puede ser None para tareas generales
    source_article_url = Column(String(1000))  # URL del artículo fuente para debugging
    
    # Task execution details
    status = Column(Enum(AnalysisTaskStatus), default=AnalysisTaskStatus.PENDING, nullable=False)
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # AI model information
    model_name = Column(String(100))
    model_version = Column(String(50))
    input_data = Column(JSON)  # Input parameters for the analysis
    output_data = Column(JSON)  # Results from the analysis
    
    # Timing information
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_duration_ms = Column(Integer)  # Duration in milliseconds
    
    # Error handling
    error_message = Column(Text)
    error_code = Column(String(50))
    stack_trace = Column(Text)
    
    # Metadata
    worker_id = Column(String(100))  # ID of the worker that processed the task
    task_metadata = Column(JSON)  # Additional task metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    article = relationship("Article")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analysis_tasks_status', 'status'),
        Index('idx_analysis_tasks_task_type', 'task_type'),
        Index('idx_analysis_tasks_scheduled_at', 'scheduled_at'),
        Index('idx_analysis_tasks_priority', 'priority'),
        Index('idx_analysis_tasks_article_id', 'article_id'),
        Index('idx_analysis_tasks_worker_id', 'worker_id'),
        Index('idx_analysis_tasks_status_priority', 'status', 'priority'),
    )


# Database indexes for performance
Index('idx_articles_source_id', Article.source_id)
Index('idx_articles_published_at', Article.published_at)
Index('idx_articles_url', Article.url)
Index('idx_articles_processed_at', Article.processed_at)
Index('idx_articles_ai_processed_at', Article.ai_processed_at)
Index('idx_articles_relevance_score', Article.relevance_score)
Index('idx_articles_duplicate_group_id', Article.duplicate_group_id)
Index('idx_articles_content_hash', Article.content_hash)
Index('idx_articles_cache_expires_at', Article.cache_expires_at)
Index('idx_sources_api_name', Source.api_name)
# Index('idx_sources_api_source_id', Source.api_source_id)  # COMENTADO: columna no existe en BD
# Index('idx_sources_is_active', Source.is_active)  # COMENTADO: columna no existe en BD
Index('idx_article_analysis_article_id', ArticleAnalysis.article_id)
Index('idx_article_analysis_type', ArticleAnalysis.analysis_type)
Index('idx_analysis_tasks_status', AnalysisTask.status)
Index('idx_analysis_tasks_task_type', AnalysisTask.task_type)
Index('idx_analysis_tasks_scheduled_at', AnalysisTask.scheduled_at)
Index('idx_analysis_tasks_article_id', AnalysisTask.article_id)