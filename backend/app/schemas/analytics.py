"""
Analytics schemas for AI News Aggregator
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Literal
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, validator, root_validator, field_serializer
from pydantic.types import conlist


class AnalyticsParams(BaseModel):
    """
    Base parameters for analytics queries
    """
    date_from: Optional[datetime] = Field(None, description="Start date for analytics")
    date_to: Optional[datetime] = Field(None, description="End date for analytics")
    granularity: str = Field('daily', regex='^(hourly|daily|weekly|monthly)$', description="Time granularity")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    
    @validator('date_from', 'date_to')
    def validate_date_range(cls, v, values):
        """Validate date range"""
        if v and v > datetime.now(timezone.utc):
            raise ValueError('Date cannot be in the future')
        
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValueError('date_from cannot be after date_to')
        
        return v
    
    @validator('granularity')
    def validate_granularity_consistency(cls, v, values):
        """Validate granularity is appropriate for date range"""
        date_from = values.get('date_from')
        date_to = values.get('date_to')
        
        if date_from and date_to:
            date_diff = date_to - date_from
            days = date_diff.days
            
            if v == 'hourly' and days > 7:
                raise ValueError('Hourly granularity only available for ranges up to 7 days')
            elif v == 'daily' and days > 365:
                raise ValueError('Daily granularity only available for ranges up to 365 days')
            elif v == 'weekly' and days > 365 * 2:
                raise ValueError('Weekly granularity only available for ranges up to 2 years')
        
        return v


class SentimentAnalytics(BaseModel):
    """
    Sentiment analysis metrics
    """
    total_articles: int = Field(ge=0, description="Total articles analyzed")
    positive_count: int = Field(ge=0, description="Positive sentiment count")
    negative_count: int = Field(ge=0, description="Negative sentiment count")
    neutral_count: int = Field(ge=0, description="Neutral sentiment count")
    average_sentiment_score: float = Field(ge=-1.0, le=1.0, description="Average sentiment score")
    sentiment_distribution: Dict[str, float] = Field(description="Sentiment distribution percentages")
    top_positive_articles: List[Dict[str, Any]] = Field(default_factory=list, description="Top positive articles")
    top_negative_articles: List[Dict[str, Any]] = Field(default_factory=list, description="Top negative articles")
    sentiment_trends: List[Dict[str, Any]] = Field(default_factory=list, description="Sentiment trends over time")
    
    @validator('sentiment_distribution')
    def validate_sentiment_distribution(cls, v):
        """Validate sentiment distribution sums to 100%"""
        if v:
            total_percentage = sum(v.values())
            if abs(total_percentage - 100.0) > 0.1:  # Allow small rounding errors
                raise ValueError('Sentiment distribution must sum to 100%')
        return v
    
    @validator('positive_count', 'negative_count', 'neutral_count')
    def validate_counts_consistency(cls, v, values):
        """Validate counts are consistent with total"""
        total = values.get('total_articles', 0)
        if v > total:
            raise ValueError('Individual count cannot exceed total articles')
        return v


class TrendAnalytics(BaseModel):
    """
    Trend analysis metrics
    """
    trending_topics: List[Dict[str, Any]] = Field(default_factory=list, description="Currently trending topics")
    topic_growth_rates: Dict[str, float] = Field(default_factory=dict, description="Topic growth rates")
    emerging_topics: List[Dict[str, Any]] = Field(default_factory=list, description="Emerging topics")
    declining_topics: List[Dict[str, Any]] = Field(default_factory=list, description="Declining topics")
    topic_sentiment: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Topic sentiment breakdown")
    seasonal_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Seasonal topic patterns")
    peak_activity_times: List[Dict[str, Any]] = Field(default_factory=list, description="Peak activity time analysis")


class SourceAnalytics(BaseModel):
    """
    News source analysis metrics
    """
    source_performance: List[Dict[str, Any]] = Field(default_factory=list, description="Source performance metrics")
    credibility_scores: Dict[str, float] = Field(default_factory=dict, description="Source credibility scores")
    bias_analysis: Dict[str, float] = Field(default_factory=dict, description="Source bias analysis")
    source_reliability: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Source reliability metrics")
    active_sources_count: int = Field(ge=0, description="Number of active sources")
    top_sources_by_volume: List[Dict[str, Any]] = Field(default_factory=list, description="Top sources by article volume")
    top_sources_by_engagement: List[Dict[str, Any]] = Field(default_factory=list, description="Top sources by engagement")
    source_diversity_score: float = Field(ge=0.0, le=1.0, description="Source diversity score")
    
    @validator('source_diversity_score')
    def validate_diversity_score(cls, v):
        """Validate diversity score is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Diversity score must be between 0.0 and 1.0')
        return v


class EngagementAnalytics(BaseModel):
    """
    User engagement metrics
    """
    total_reads: int = Field(ge=0, description="Total article reads")
    unique_readers: int = Field(ge=0, description="Unique readers count")
    average_reading_time: float = Field(ge=0.0, description="Average reading time in minutes")
    bounce_rate: float = Field(ge=0.0, le=1.0, description="Bounce rate percentage")
    most_read_articles: List[Dict[str, Any]] = Field(default_factory=list, description="Most read articles")
    reading_patterns: List[Dict[str, Any]] = Field(default_factory=list, description="Reading pattern analysis")
    peak_reading_hours: List[Dict[str, int]] = Field(default_factory=list, description="Peak reading hours")
    device_breakdown: Dict[str, int] = Field(default_factory=dict, description="Device usage breakdown")
    
    @validator('bounce_rate')
    def validate_bounce_rate(cls, v):
        """Validate bounce rate is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Bounce rate must be between 0.0 and 1.0')
        return v


class ContentQualityAnalytics(BaseModel):
    """
    Content quality metrics
    """
    average_content_length: float = Field(ge=0.0, description="Average article length")
    quality_score_distribution: Dict[str, int] = Field(default_factory=dict, description="Quality score distribution")
    duplicate_articles_count: int = Field(ge=0, description="Number of duplicate articles detected")
    original_content_percentage: float = Field(ge=0.0, le=100.0, description="Percentage of original content")
    content_issues: List[Dict[str, Any]] = Field(default_factory=list, description="Content quality issues")
    linguistic_quality: Dict[str, float] = Field(default_factory=dict, description="Linguistic quality metrics")
    readability_scores: Dict[str, float] = Field(default_factory=dict, description="Readability scores by source")


class AIProcessingAnalytics(BaseModel):
    """
    AI processing performance metrics
    """
    total_processed_articles: int = Field(ge=0, description="Total articles processed by AI")
    average_processing_time: float = Field(ge=0.0, description="Average processing time in seconds")
    success_rate: float = Field(ge=0.0, le=1.0, description="AI processing success rate")
    model_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Performance by AI model")
    error_breakdown: Dict[str, int] = Field(default_factory=dict, description="Error type breakdown")
    processing_queue_size: int = Field(ge=0, description="Current queue size")
    processing_capacity: int = Field(ge=0, description="Processing capacity")
    cost_analysis: Dict[str, float] = Field(default_factory=dict, description="AI processing cost analysis")
    
    @validator('success_rate')
    def validate_success_rate(cls, v):
        """Validate success rate is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Success rate must be between 0.0 and 1.0')
        return v


class AnalyticsResponse(BaseModel):
    """
    Comprehensive analytics response
    """
    query_params: AnalyticsParams
    generated_at: datetime
    data_summary: Dict[str, Any] = Field(description="High-level data summary")
    
    # Analytics components
    sentiment_analytics: Optional[SentimentAnalytics] = None
    trend_analytics: Optional[TrendAnalytics] = None
    source_analytics: Optional[SourceAnalytics] = None
    engagement_analytics: Optional[EngagementAnalytics] = None
    content_quality_analytics: Optional[ContentQualityAnalytics] = None
    ai_processing_analytics: Optional[AIProcessingAnalytics] = None
    
    # Metadata
    total_data_points: int = Field(ge=0, description="Total data points in response")
    computation_time_ms: int = Field(ge=0, description="Computation time in milliseconds")
    cache_hit: bool = Field(False, description="Whether response was served from cache")
    data_freshness: Optional[str] = Field(None, description="Data freshness information")
    
    @validator('total_data_points')
    def validate_data_points(cls, v, values):
        """Validate total data points"""
        # Count data points from various analytics components
        count = 0
        
        for key in ['sentiment_analytics', 'trend_analytics', 'source_analytics', 
                   'engagement_analytics', 'content_quality_analytics', 'ai_processing_analytics']:
            if values.get(key):
                count += 1
        
        if v != count:
            # Update total_data_points to match actual count
            return count
        return v
    
    @field_serializer('generated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format"""
        return value.isoformat()


class ComparisonAnalytics(BaseModel):
    """
    Analytics for comparing different time periods or segments
    """
    comparison_type: Literal['time_periods', 'sources', 'topics', 'custom'] = Field(
        ..., description="Type of comparison being made"
    )
    baseline_period: Dict[str, Any] = Field(description="Baseline period configuration")
    comparison_period: Dict[str, Any] = Field(description="Comparison period configuration")
    
    # Metrics comparisons
    metric_changes: Dict[str, Dict[str, float]] = Field(description="Metric changes between periods")
    significant_differences: List[Dict[str, Any]] = Field(default_factory=list, description="Statistically significant differences")
    trends_comparison: List[Dict[str, Any]] = Field(default_factory=list, description="Trend comparisons")
    
    # Recommendations
    insights: List[str] = Field(default_factory=list, description="Key insights from comparison")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")


class RealTimeAnalytics(BaseModel):
    """
    Real-time analytics for dashboard
    """
    current_active_users: int = Field(ge=0, description="Currently active users")
    articles_processed_today: int = Field(ge=0, description="Articles processed today")
    current_queue_size: int = Field(ge=0, description="Current processing queue size")
    system_health_score: float = Field(ge=0.0, le=1.0, description="Overall system health score")
    
    # Recent activity
    recent_articles: List[Dict[str, Any]] = Field(default_factory=list, description="Recently processed articles")
    trending_now: List[Dict[str, Any]] = Field(default_factory=list, description="Trending topics right now")
    system_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Active system alerts")
    
    # Performance metrics
    response_time_avg: float = Field(ge=0.0, description="Average API response time")
    error_rate: float = Field(ge=0.0, le=1.0, description="Current error rate")
    throughput: float = Field(ge=0.0, description="Current system throughput")
    
    @validator('system_health_score', 'error_rate')
    def validate_scores(cls, v):
        """Validate scores are between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v


class PredictiveAnalytics(BaseModel):
    """
    Predictive analytics for forecasting
    """
    forecast_horizon_days: int = Field(ge=1, le=90, description="Forecast horizon in days")
    predicted_metrics: Dict[str, List[Dict[str, Any]]] = Field(description="Predicted metrics over time")
    confidence_intervals: Dict[str, Dict[str, float]] = Field(description="Confidence intervals for predictions")
    trend_projections: List[Dict[str, Any]] = Field(default_factory=list, description="Trend projections")
    
    # Model information
    model_used: str = Field(description="AI model used for predictions")
    model_accuracy: float = Field(ge=0.0, le=1.0, description="Model historical accuracy")
    last_updated: datetime = Field(description="When predictions were last updated")
    
    # Risk factors
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list, description="Identified risk factors")
    scenarios: List[Dict[str, Any]] = Field(default_factory=list, description="Different scenario projections")
    
    @validator('model_accuracy')
    def validate_accuracy(cls, v):
        """Validate model accuracy is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Model accuracy must be between 0.0 and 1.0')
        return v
    
    @field_serializer('last_updated')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format"""
        return value.isoformat()


# Utility functions for analytics
def calculate_growth_rate(current_value: float, previous_value: float) -> float:
    """Calculate growth rate as percentage"""
    if previous_value == 0:
        return float('inf') if current_value > 0 else 0.0
    
    return ((current_value - previous_value) / previous_value) * 100


def calculate_percentage_change(old_value: float, new_value: float) -> Dict[str, float]:
    """Calculate detailed percentage change metrics"""
    if old_value == 0:
        if new_value == 0:
            return {
                'percentage_change': 0.0,
                'absolute_change': 0.0,
                'is_increase': False,
                'is_decrease': False
            }
        else:
            return {
                'percentage_change': float('inf'),
                'absolute_change': new_value,
                'is_increase': True,
                'is_decrease': False
            }
    
    percentage_change = ((new_value - old_value) / old_value) * 100
    
    return {
        'percentage_change': percentage_change,
        'absolute_change': new_value - old_value,
        'is_increase': new_value > old_value,
        'is_decrease': new_value < old_value
    }


def detect_anomalies(data: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detect anomalies in time series data using z-score
    Returns indices of anomalous data points
    """
    if len(data) < 3:
        return []
    
    import statistics
    
    mean = statistics.mean(data)
    std_dev = statistics.stdev(data)
    
    if std_dev == 0:
        return []
    
    anomalies = []
    for i, value in enumerate(data):
        z_score = abs((value - mean) / std_dev)
        if z_score > threshold:
            anomalies.append(i)
    
    return anomalies


def calculate_moving_average(data: List[float], window: int) -> List[float]:
    """Calculate moving average for time series data"""
    if len(data) < window or window <= 0:
        return data
    
    moving_averages = []
    for i in range(len(data) - window + 1):
        window_data = data[i:i + window]
        moving_averages.append(sum(window_data) / window)
    
    return moving_averages