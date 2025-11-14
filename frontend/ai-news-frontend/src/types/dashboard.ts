export interface DashboardMetrics {
  total_articles: number;
  active_sources: number;
  average_sentiment: number;
  articles_today: number;
  articles_this_week: number;
  articles_this_month: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  top_sources: Array<{
    name: string;
    count: number;
    percentage: number;
  }>;
  sentiment_trend: Array<{
    date: string;
    sentiment_score: number;
    article_count: number;
  }>;
  categories_distribution: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  hourly_activity: Array<{
    hour: number;
    count: number;
  }>;
}

export interface LiveStats {
  current_articles: number;
  sources_online: number;
  average_processing_time: number;
  last_update: string;
}

export interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: React.ReactNode;
  description?: string;
}

export interface KPIWidgetProps {
  title: string;
  value: number;
  target?: number;
  unit?: string;
  trend: Array<{ date: string; value: number }>;
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}

export interface ChartDataPoint {
  name: string;
  value: number;
  percentage?: number;
}