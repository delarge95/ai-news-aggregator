"""
Article schemas for AI News Aggregator
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, validator, root_validator, field_serializer
from pydantic.types import conlist


class ArticleBase(BaseModel):
    """
    Base schema for articles with common fields
    """
    title: str = Field(..., min_length=5, max_length=500, description="Article title")
    content: Optional[str] = Field(None, description="Article full content")
    summary: Optional[str] = Field(None, max_length=2000, description="Article summary")
    url: str = Field(..., min_length=10, max_length=1000, description="Article URL")
    source_id: Optional[UUID] = Field(None, description="Source ID")
    
    # Optional fields with validation
    published_at: Optional[datetime] = Field(None, description="Publication date")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title content"""
        if v.strip() != v:
            raise ValueError('Title cannot have leading/trailing whitespace')
        if len(v.split()) < 2:
            raise ValueError('Title must have at least 2 words')
        return v.strip()
    
    @validator('published_at')
    def validate_published_date(cls, v):
        """Validate published date is not in the future"""
        if v and v > datetime.now(timezone.utc):
            raise ValueError('Published date cannot be in the future')
        return v


class ArticleCreate(ArticleBase):
    """
    Schema for creating a new article
    """
    # AI analysis fields - optional on creation
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Sentiment score (-1.0 to 1.0)")
    sentiment_label: Optional[str] = Field(None, regex='^(positive|negative|neutral)$', description="Sentiment label")
    bias_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Bias score (0.0 to 1.0)")
    topic_tags: Optional[List[str]] = Field(default_factory=list, description="Topic tags")
    relevance_score: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Relevance score")
    
    @validator('topic_tags')
    def validate_topic_tags(cls, v):
        """Validate topic tags"""
        if v:
            for tag in v:
                if len(tag.strip()) == 0:
                    raise ValueError('Topic tags cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Topic tags cannot exceed 50 characters')
            # Remove duplicates while preserving order
            return list(dict.fromkeys([tag.strip() for tag in v]))
        return v
    
    @validator('sentiment_label')
    def validate_sentiment_consistency(cls, v, values):
        """Ensure sentiment score and label are consistent"""
        sentiment_score = values.get('sentiment_score')
        if sentiment_score is not None and v:
            expected_label = cls._get_sentiment_label(sentiment_score)
            if v != expected_label:
                raise ValueError(f'Sentiment label "{v}" inconsistent with score {sentiment_score}')
        return v
    
    @classmethod
    def _get_sentiment_label(cls, score: float) -> str:
        """Determine sentiment label from score"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'


class ArticleUpdate(BaseModel):
    """
    Schema for updating an existing article
    """
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = Field(None, max_length=2000)
    
    # AI analysis fields
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_label: Optional[str] = Field(None, regex='^(positive|negative|neutral)$')
    bias_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    topic_tags: Optional[List[str]] = None
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    @validator('title')
    def validate_title(cls, v):
        """Validate title content"""
        if v is not None:
            if v.strip() != v:
                raise ValueError('Title cannot have leading/trailing whitespace')
            if len(v.split()) < 2:
                raise ValueError('Title must have at least 2 words')
            return v.strip()
        return v
    
    @validator('topic_tags')
    def validate_topic_tags(cls, v):
        """Validate topic tags"""
        if v is not None:
            for tag in v:
                if len(tag.strip()) == 0:
                    raise ValueError('Topic tags cannot be empty')
                if len(tag) > 50:
                    raise ValueError('Topic tags cannot exceed 50 characters')
            # Remove duplicates while preserving order
            return list(dict.fromkeys([tag.strip() for tag in v]))
        return v


class ArticleResponse(ArticleBase):
    """
    Schema for article responses
    """
    id: UUID
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    ai_processed_at: Optional[datetime] = None
    processing_status: str
    
    # AI analysis fields
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    bias_score: Optional[float] = None
    topic_tags: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    
    # Source information
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_api_name: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @field_serializer('created_at', 'updated_at', 'published_at', 'processed_at', 'ai_processed_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime objects to ISO format"""
        if value is None:
            return None
        return value.isoformat()


class ArticleAnalysisResponse(BaseModel):
    """
    Schema for article analysis results
    """
    id: UUID
    article_id: UUID
    analysis_type: str
    analysis_data: Dict[str, Any]
    model_used: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    processed_at: datetime
    
    class Config:
        from_attributes = True
    
    @field_serializer('processed_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format"""
        return value.isoformat()


class ArticleListResponse(BaseModel):
    """
    Schema for paginated article list responses
    """
    articles: List[ArticleResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
    
    @validator('per_page')
    def validate_per_page(cls, v):
        """Validate per_page is within reasonable bounds"""
        if v < 1:
            raise ValueError('per_page must be at least 1')
        if v > 100:
            raise ValueError('per_page cannot exceed 100')
        return v
    
    @root_validator
    def calculate_pages(cls, values):
        """Calculate total pages"""
        total = values.get('total', 0)
        per_page = values.get('per_page', 10)
        page = values.get('page', 1)
        
        if per_page > 0:
            pages = (total + per_page - 1) // per_page
            values['pages'] = pages
            values['has_next'] = page < pages
            values['has_prev'] = page > 1
        else:
            values['pages'] = 0
            values['has_next'] = False
            values['has_prev'] = False
        
        return values


# Utility functions for article validation
def validate_article_content(content: str) -> Dict[str, Any]:
    """
    Validate article content and return validation results
    """
    validation_result = {
        'is_valid': True,
        'warnings': [],
        'errors': []
    }
    
    if not content or len(content.strip()) == 0:
        validation_result['errors'].append('Content cannot be empty')
        validation_result['is_valid'] = False
        return validation_result
    
    content_length = len(content)
    if content_length < 100:
        validation_result['warnings'].append('Content is very short (< 100 characters)')
    elif content_length > 50000:
        validation_result['warnings'].append('Content is very long (> 50,000 characters)')
    
    # Check for potential issues
    words = content.split()
    if len(words) < 20:
        validation_result['warnings'].append('Content has fewer than 20 words')
    
    return validation_result


def calculate_reading_time(content: str) -> int:
    """
    Calculate estimated reading time in minutes
    Assumes average reading speed of 200 words per minute
    """
    if not content:
        return 0
    
    words = len(content.split())
    return max(1, round(words / 200))


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract potential keywords from text
    Simple implementation - in production, use NLP libraries
    """
    if not text:
        return []
    
    # Simple keyword extraction based on word frequency
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    word_freq = {}
    
    for word in words:
        # Filter out common words
        if word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'what', 'when', 'will', 'with', 'your']:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]