/**
 * Tipos TypeScript para componentes de análisis
 */

export interface SentimentData {
  positive: number;
  negative: number;
  neutral: number;
  score: number;
  total_articles: number;
  sentiment_distribution: Record<string, number>;
}

export interface TopicData {
  name: string;
  count: number;
  sentiment: number;
  growth_rate: number;
  category?: string;
  relevance_score?: number;
}

export interface RelevanceScore {
  overall: number;
  credibility: number;
  engagement: number;
  quality: number;
  trends: number;
}

export interface AIInsight {
  id: string;
  type: 'sentiment' | 'trend' | 'anomaly' | 'prediction' | 'alert';
  title: string;
  description: string;
  confidence: number;
  impact: 'low' | 'medium' | 'high';
  timestamp: Date;
  related_data?: Record<string, unknown>;
}

export interface ComparisonData {
  period1: {
    label: string;
    start_date: Date;
    end_date: Date;
    metrics: Record<string, number>;
  };
  period2: {
    label: string;
    start_date: Date;
    end_date: Date;
    metrics: Record<string, number>;
  };
  changes: {
    metric: string;
    absolute_change: number;
    percentage_change: number;
    direction: 'up' | 'down' | 'stable';
  }[];
}

export interface WordCloudData {
  word: string;
  weight: number;
  sentiment: number;
  category?: string;
}

export interface AnalyticsFilters {
  date_from?: Date;
  date_to?: Date;
  granularity?: 'hourly' | 'daily' | 'weekly' | 'monthly';
  sources?: string[];
  topics?: string[];
}

export interface AnalyticsResponse {
  sentiment_analytics?: SentimentAnalytics;
  trend_analytics?: TrendAnalytics;
  source_analytics?: SourceAnalytics;
  engagement_analytics?: EngagementAnalytics;
  content_quality_analytics?: ContentQualityAnalytics;
  ai_processing_analytics?: AIProcessingAnalytics;
}

export interface SentimentAnalytics {
  total_articles: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  average_sentiment_score: number;
  sentiment_distribution: Record<string, number>;
  top_positive_articles: Array<Record<string, unknown>>;
  top_negative_articles: Array<Record<string, unknown>>;
  sentiment_trends: Array<Record<string, unknown>>;
}

export interface TrendAnalytics {
  trending_topics: Array<Record<string, unknown>>;
  topic_growth_rates: Record<string, number>;
  emerging_topics: Array<Record<string, unknown>>;
  declining_topics: Array<Record<string, unknown>>;
  topic_sentiment: Record<string, Record<string, number>>;
  seasonal_patterns: Array<Record<string, unknown>>;
  peak_activity_times: Array<Record<string, unknown>>;
}

export interface SourceAnalytics {
  source_performance: Array<Record<string, unknown>>;
  credibility_scores: Record<string, number>;
  bias_analysis: Record<string, number>;
  source_reliability: Record<string, Record<string, unknown>>;
  active_sources_count: number;
  top_sources_by_volume: Array<Record<string, unknown>>;
  top_sources_by_engagement: Array<Record<string, unknown>>;
  source_diversity_score: number;
}

export interface EngagementAnalytics {
  total_reads: number;
  unique_readers: number;
  average_reading_time: number;
  bounce_rate: number;
  most_read_articles: Array<Record<string, unknown>>;
  reading_patterns: Array<Record<string, unknown>>;
  peak_reading_hours: Array<Record<string, number>>;
  device_breakdown: Record<string, number>;
}

export interface ContentQualityAnalytics {
  average_content_length: number;
  quality_score_distribution: Record<string, number>;
  duplicate_articles_count: number;
  original_content_percentage: number;
  content_issues: Array<Record<string, unknown>>;
  linguistic_quality: Record<string, number>;
  readability_scores: Record<string, number>;
}

export interface AIProcessingAnalytics {
  total_processed_articles: number;
  average_processing_time: number;
  success_rate: number;
  model_performance: Record<string, Record<string, number>>;
  error_breakdown: Record<string, number>;
  processing_queue_size: number;
  processing_capacity: number;
  cost_analysis: Record<string, number>;
}

export interface ChartColors {
  positive: string;
  negative: string;
  neutral: string;
  primary: string;
  secondary: string;
  background: string;
  text: string;
}

export interface TooltipData {
  label: string;
  value: string | number;
  color?: string;
  context?: string;
}