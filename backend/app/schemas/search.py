"""
Search schemas for AI News Aggregator
"""

import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Literal
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator, field_serializer
from pydantic.types import conlist


class SearchParams(BaseModel):
    """
    Basic search parameters
    """
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Results per page")
    sort_by: str = Field('relevance', regex='^(relevance|date|title|source)$', description="Sort field")
    sort_order: str = Field('desc', regex='^(asc|desc)$', description="Sort order")
    
    # Date filtering
    date_from: Optional[datetime] = Field(None, description="Start date filter")
    date_to: Optional[datetime] = Field(None, description="End date filter")
    
    # Source filtering
    sources: Optional[List[str]] = Field(None, description="Filter by source names or IDs")
    
    # Content filtering
    min_length: Optional[int] = Field(None, ge=0, description="Minimum content length")
    max_length: Optional[int] = Field(None, ge=0, description="Maximum content length")
    
    @validator('query')
    def validate_query(cls, v):
        """Clean and validate search query"""
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', v.strip())
        
        if len(cleaned) < 1:
            raise ValueError('Query cannot be empty')
        
        if len(cleaned) > 500:
            raise ValueError('Query cannot exceed 500 characters')
        
        return cleaned
    
    @validator('per_page')
    def validate_per_page(cls, v):
        """Validate per_page bounds"""
        if v > 100:
            raise ValueError('per_page cannot exceed 100')
        return v
    
    @validator('date_from', 'date_to')
    def validate_date_range(cls, v, values):
        """Validate date range consistency"""
        if v and v > datetime.now(timezone.utc):
            raise ValueError('Date cannot be in the future')
        
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValueError('date_from cannot be after date_to')
        
        return v
    
    @validator('min_length', 'max_length')
    def validate_length_range(cls, v, values):
        """Validate content length range"""
        min_length = values.get('min_length')
        max_length = values.get('max_length')
        
        if min_length is not None and max_length is not None:
            if min_length > max_length:
                raise ValueError('min_length cannot be greater than max_length')
        
        return v


class AdvancedSearchParams(SearchParams):
    """
    Advanced search parameters with additional filters
    """
    # AI analysis filters
    sentiment: Optional[str] = Field(None, regex='^(positive|negative|neutral)$', description="Sentiment filter")
    min_sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Minimum sentiment score")
    max_sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Maximum sentiment score")
    
    # Bias and relevance filters
    min_bias_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum bias score")
    max_bias_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum bias score")
    min_relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum relevance score")
    max_relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Maximum relevance score")
    
    # Topic filtering
    topics: Optional[List[str]] = Field(None, description="Filter by topics")
    exclude_topics: Optional[List[str]] = Field(None, description="Exclude topics")
    
    # Language filtering
    languages: Optional[List[str]] = Field(None, description="Filter by languages")
    
    # Processing status
    processing_status: Optional[str] = Field(None, regex='^(pending|processing|completed|failed|skipped)$', 
                                           description="Processing status filter")
    
    # Full-text search options
    search_in_content: bool = Field(True, description="Include content in search")
    search_in_summary: bool = Field(True, description="Include summary in search")
    search_in_title: bool = Field(True, description="Include title in search")
    
    # Fuzzy search
    fuzzy_search: bool = Field(False, description="Enable fuzzy search")
    fuzzy_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Fuzzy matching threshold")
    
    # Boolean operators
    use_boolean_operators: bool = Field(False, description="Enable boolean operators (AND, OR, NOT)")
    
    @validator('min_sentiment_score', 'max_sentiment_score')
    def validate_sentiment_range(cls, v, values):
        """Validate sentiment score range"""
        min_score = values.get('min_sentiment_score')
        max_score = values.get('max_sentiment_score')
        
        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise ValueError('min_sentiment_score cannot be greater than max_sentiment_score')
        
        return v
    
    @validator('min_bias_score', 'max_bias_score')
    def validate_bias_range(cls, v, values):
        """Validate bias score range"""
        min_score = values.get('min_bias_score')
        max_score = values.get('max_bias_score')
        
        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise ValueError('min_bias_score cannot be greater than max_bias_score')
        
        return v
    
    @validator('min_relevance_score', 'max_relevance_score')
    def validate_relevance_range(cls, v, values):
        """Validate relevance score range"""
        min_score = values.get('min_relevance_score')
        max_score = values.get('max_relevance_score')
        
        if min_score is not None and max_score is not None:
            if min_score > max_score:
                raise ValueError('min_relevance_score cannot be greater than max_relevance_score')
        
        return v
    
    @validator('topics', 'exclude_topics')
    def validate_topics(cls, v):
        """Validate topics list"""
        if v:
            for topic in v:
                if len(topic.strip()) == 0:
                    raise ValueError('Topics cannot be empty')
                if len(topic) > 50:
                    raise ValueError('Topics cannot exceed 50 characters')
            # Remove duplicates while preserving order
            return list(dict.fromkeys([topic.strip() for topic in v]))
        return v
    
    @validator('sources')
    def validate_sources(cls, v):
        """Validate sources list"""
        if v:
            # Check for duplicates
            if len(v) != len(set(v)):
                raise ValueError('Sources list cannot contain duplicates')
            # Check list size
            if len(v) > 50:
                raise ValueError('Cannot have more than 50 sources')
        return v
    
    @validator('fuzzy_threshold')
    def validate_fuzzy_threshold(cls, v):
        """Validate fuzzy search threshold"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('fuzzy_threshold must be between 0.0 and 1.0')
        return v
    
    @root_validator
    def validate_search_consistency(cls, values):
        """Validate overall search consistency"""
        # Check if at least one search field is enabled
        search_in_content = values.get('search_in_content', True)
        search_in_summary = values.get('search_in_summary', True)
        search_in_title = values.get('search_in_title', True)
        
        if not (search_in_content or search_in_summary or search_in_title):
            raise ValueError('At least one search field must be enabled')
        
        return values


class SearchFacet(BaseModel):
    """
    Search facet for filtering and grouping
    """
    name: str = Field(..., description="Facet name")
    values: List[Dict[str, Any]] = Field(..., description="Facet values with counts")
    total_values: int = Field(..., ge=0, description="Total number of unique values")
    selected_values: List[str] = Field(default_factory=list, description="Currently selected values")


class SearchHighlight(BaseModel):
    """
    Search result highlighting
    """
    title: Optional[List[str]] = Field(None, description="Title highlights")
    content: Optional[List[str]] = Field(None, description="Content highlights")
    summary: Optional[List[str]] = Field(None, description="Summary highlights")


class SearchResult(BaseModel):
    """
    Individual search result
    """
    id: UUID
    title: str
    url: str
    content: Optional[str] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    source_name: Optional[str] = None
    source_id: Optional[UUID] = None
    
    # Search relevance
    relevance_score: float = Field(ge=0.0, description="Search relevance score")
    matched_fields: List[str] = Field(default_factory=list, description="Fields that matched the query")
    
    # AI analysis scores
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    bias_score: Optional[float] = None
    relevance_score_ai: Optional[float] = None
    topic_tags: List[str] = Field(default_factory=list)
    
    # Highlighting
    highlights: Optional[SearchHighlight] = None
    
    # Metadata
    word_count: int = Field(ge=0, description="Number of words in content")
    reading_time: int = Field(ge=0, description="Estimated reading time in minutes")
    
    @field_serializer('published_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format"""
        if value is None:
            return None
        return value.isoformat()
    
    @validator('word_count', 'reading_time')
    def validate_metrics(cls, v):
        """Validate numerical metrics"""
        if v < 0:
            raise ValueError('Metrics cannot be negative')
        return v


class SearchResponse(BaseModel):
    """
    Search results response
    """
    query: str
    total_results: int = Field(ge=0, description="Total number of matching results")
    page: int = Field(ge=1, description="Current page")
    per_page: int = Field(ge=1, description="Results per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more results")
    has_prev: bool = Field(description="Whether there are previous results")
    
    # Results
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    
    # Facets for filtering
    facets: Dict[str, SearchFacet] = Field(default_factory=dict, description="Available facets")
    
    # Suggestions
    did_you_mean: Optional[List[str]] = Field(None, description="Query suggestions")
    related_queries: Optional[List[str]] = Field(None, description="Related search queries")
    
    # Search metadata
    search_time_ms: int = Field(ge=0, description="Search execution time in milliseconds")
    cached: bool = Field(False, description="Whether results were cached")
    processing_time_ms: int = Field(ge=0, description="Total processing time")
    
    @validator('per_page')
    def validate_per_page(cls, v):
        """Validate per_page bounds"""
        if v > 100:
            raise ValueError('per_page cannot exceed 100')
        return v
    
    @validator('total_pages')
    def validate_total_pages(cls, v, values):
        """Validate total pages calculation"""
        total_results = values.get('total_results', 0)
        per_page = values.get('per_page', 20)
        page = values.get('page', 1)
        
        if per_page > 0:
            calculated_pages = (total_results + per_page - 1) // per_page
            if v != calculated_pages:
                return calculated_pages
        
        return v
    
    @validator('has_next', 'has_prev')
    def validate_pagination_flags(cls, v, values):
        """Validate pagination flags"""
        total_pages = values.get('total_pages', 0)
        page = values.get('page', 1)
        
        if 'has_next' in values:
            values['has_next'] = page < total_pages
        if 'has_prev' in values:
            values['has_prev'] = page > 1
        
        return v


class SavedSearch(BaseModel):
    """
    Saved search configuration
    """
    id: UUID
    user_id: str
    name: str = Field(..., min_length=1, max_length=100, description="Search name")
    description: Optional[str] = Field(None, max_length=500, description="Search description")
    search_params: AdvancedSearchParams
    created_at: datetime
    last_run: Optional[datetime] = None
    run_count: int = Field(ge=0, default=0, description="Number of times searched")
    is_public: bool = Field(False, description="Whether search is publicly visible")
    
    # Alerts
    alert_enabled: bool = Field(False, description="Enable alerts for new results")
    alert_frequency: Optional[str] = Field(None, regex='^(realtime|hourly|daily|weekly)$', 
                                         description="Alert frequency")
    last_alert_sent: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @field_serializer('created_at', 'last_run', 'last_alert_sent')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format"""
        if value is None:
            return None
        return value.isoformat()


class SearchSuggestion(BaseModel):
    """
    Search suggestion with autocomplete
    """
    text: str = Field(..., description="Suggestion text")
    type: Literal['query', 'topic', 'source', 'person', 'location'] = Field(
        ..., description="Suggestion type"
    )
    count: Optional[int] = Field(None, ge=0, description="Number of results for this suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Suggestion confidence score")


class SearchAnalytics(BaseModel):
    """
    Search analytics and insights
    """
    total_searches: int = Field(ge=0, description="Total number of searches")
    unique_searchers: int = Field(ge=0, description="Number of unique searchers")
    average_results_per_search: float = Field(ge=0.0, description="Average results per search")
    popular_queries: List[Dict[str, Any]] = Field(default_factory=list, description="Most popular queries")
    zero_result_queries: List[str] = Field(default_factory=list, description="Queries with no results")
    
    # Search patterns
    search_trends: List[Dict[str, Any]] = Field(default_factory=list, description="Search trends over time")
    search_destination: Dict[str, int] = Field(default_factory=dict, description="Search result click-through rates")
    
    # Performance metrics
    average_search_time: float = Field(ge=0.0, description="Average search time in milliseconds")
    search_error_rate: float = Field(ge=0.0, le=1.0, description="Search error rate")
    
    # User behavior
    search_session_length: float = Field(ge=0.0, description="Average search session length")
    refinement_rate: float = Field(ge=0.0, le=1.0, description="Rate of query refinement")


# Utility functions for search
def parse_search_query(query: str) -> Dict[str, Any]:
    """
    Parse search query and extract components
    """
    parsed = {
        'original': query,
        'keywords': [],
        'phrases': [],
        'exclusions': [],
        'boost_terms': [],
        'fuzzy_terms': [],
        'boolean_operators': []
    }
    
    # Simple parsing - in production, use proper query parsers
    words = query.split()
    
    for word in words:
        if word.startswith('-') and len(word) > 1:
            parsed['exclusions'].append(word[1:])
        elif word.startswith('+') and len(word) > 1:
            parsed['boost_terms'].append(word[1:])
        elif word.startswith('~') and len(word) > 1:
            parsed['fuzzy_terms'].append(word[1:])
        elif word.upper() in ['AND', 'OR', 'NOT']:
            parsed['boolean_operators'].append(word.upper())
        else:
            parsed['keywords'].append(word)
    
    return parsed


def calculate_search_score(article: Dict[str, Any], query: str, weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate relevance score for search results
    """
    if weights is None:
        weights = {
            'title': 3.0,
            'summary': 2.0,
            'content': 1.0,
            'topic_tags': 1.5,
            'exact_match': 2.0
        }
    
    score = 0.0
    query_lower = query.lower()
    
    # Title matching
    title = article.get('title', '').lower()
    if title:
        if query_lower in title:
            score += weights['title']
        # Word-level matching
        title_words = set(title.split())
        query_words = set(query_lower.split())
        matches = len(title_words & query_words)
        score += (matches / len(query_words)) * weights['title'] * 0.5
    
    # Summary matching
    summary = article.get('summary', '').lower()
    if summary and query_lower in summary:
        score += weights['summary']
    
    # Content matching
    content = article.get('content', '').lower()
    if content and query_lower in content:
        score += weights['content']
    
    # Topic tags matching
    topic_tags = article.get('topic_tags', [])
    for tag in topic_tags:
        if isinstance(tag, str) and query_lower in tag.lower():
            score += weights['topic_tags']
    
    # Exact match boost
    if query_lower == title or query_lower == summary:
        score += weights['exact_match']
    
    return score


def extract_search_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text for search optimization
    """
    if not text:
        return []
    
    # Remove common words and extract meaningful terms
    stop_words = {
        'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
        'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 
        'did', 'man', 'way', 'what', 'when', 'will', 'with', 'your'
    }
    
    # Extract words with length >= 3
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Filter out stop words and count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:max_keywords]]


def build_search_index(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build search index for optimized searching
    """
    index = {
        'title_index': {},
        'content_index': {},
        'topic_index': {},
        'source_index': {},
        'date_index': {}
    }
    
    for article in articles:
        article_id = str(article.get('id', ''))
        
        # Title index
        title = article.get('title', '').lower()
        if title:
            for word in title.split():
                if word not in index['title_index']:
                    index['title_index'][word] = []
                index['title_index'][word].append(article_id)
        
        # Content index (simplified)
        content = article.get('content', '').lower()
        if content:
            # Index first 100 words only for performance
            content_words = content.split()[:100]
            for word in content_words:
                if word not in index['content_index']:
                    index['content_index'][word] = []
                index['content_index'][word].append(article_id)
        
        # Topic index
        topics = article.get('topic_tags', [])
        for topic in topics:
            if isinstance(topic, str):
                topic_lower = topic.lower()
                if topic_lower not in index['topic_index']:
                    index['topic_index'][topic_lower] = []
                index['topic_index'][topic_lower].append(article_id)
        
        # Source index
        source = article.get('source_name', '')
        if source:
            source_lower = source.lower()
            if source_lower not in index['source_index']:
                index['source_index'][source_lower] = []
            index['source_index'][source_lower].append(article_id)
        
        # Date index
        published_at = article.get('published_at')
        if published_at:
            date_str = published_at.strftime('%Y-%m-%d') if hasattr(published_at, 'strftime') else str(published_at)[:10]
            if date_str not in index['date_index']:
                index['date_index'][date_str] = []
            index['date_index'][date_str].append(article_id)
    
    return index