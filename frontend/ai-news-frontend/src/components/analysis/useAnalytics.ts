/**
 * Hook personalizado para integrar con endpoints de análisis
 */

import { useState, useEffect, useCallback } from 'react';
import { buildApiUrl } from '../../config/api';
import {
  AnalyticsResponse,
  AnalyticsFilters,
  SentimentData,
  TopicData,
  RelevanceScore,
  AIInsight,
  ComparisonData
} from './types';

interface UseAnalyticsReturn {
  data: AnalyticsResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
  getSentimentData: () => SentimentData | null;
  getTopicData: () => TopicData[];
  getRelevanceScore: () => RelevanceScore | null;
  getAIInsights: () => AIInsight[];
  getComparisonData: () => ComparisonData | null;
}

export const useAnalytics = (filters: AnalyticsFilters = {}): UseAnalyticsReturn => {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Construir query params
      const params = new URLSearchParams();
      
      if (filters.date_from) {
        params.append('date_from', filters.date_from.toISOString());
      }
      if (filters.date_to) {
        params.append('date_to', filters.date_to.toISOString());
      }
      if (filters.granularity) {
        params.append('granularity', filters.granularity);
      }
      if (filters.sources?.length) {
        params.append('sources', filters.sources.join(','));
      }
      if (filters.topics?.length) {
        params.append('topics', filters.topics.join(','));
      }

      const response = await fetch(buildApiUrl(`/analytics/comprehensive?${params.toString()}`));
      
      if (!response.ok) {
        throw new Error(`Error al obtener datos de análisis: ${response.status}`);
      }

      const result: AnalyticsResponse = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const getSentimentData = useCallback((): SentimentData | null => {
    if (!data?.sentiment_analytics) return null;

    const sentiment = data.sentiment_analytics;
    return {
      positive: sentiment.positive_count,
      negative: sentiment.negative_count,
      neutral: sentiment.neutral_count,
      score: sentiment.average_sentiment_score,
      total_articles: sentiment.total_articles,
      sentiment_distribution: sentiment.sentiment_distribution
    };
  }, [data]);

  const getTopicData = useCallback((): TopicData[] => {
    if (!data?.trend_analytics?.trending_topics) return [];

    return data.trend_analytics.trending_topics.map((topic: Record<string, unknown>) => ({
      name: topic.name as string || topic.topic as string || 'Sin nombre',
      count: (topic.count as number) || 0,
      sentiment: (topic.sentiment as number) || 0,
      growth_rate: (topic.growth_rate as number) || 0,
      category: topic.category as string,
      relevance_score: (topic.relevance_score as number) || 0
    }));
  }, [data]);

  const getRelevanceScore = useCallback((): RelevanceScore | null => {
    if (!data) return null;

    // Calcular scores de relevancia basados en múltiples métricas
    const sourceReliability = data.source_analytics?.source_diversity_score || 0;
    const engagementQuality = data.engagement_analytics ? 
      (1 - data.engagement_analytics.bounce_rate) * 100 : 0;
    const contentQuality = data.content_quality_analytics?.original_content_percentage || 0;
    const processingSuccess = data.ai_processing_analytics?.success_rate || 0;

    // Score de tendencias basado en la variabilidad de topics
    const trendScore = data.trend_analytics ? 75 : 50;

    return {
      overall: Math.round((sourceReliability + engagementQuality + contentQuality + processingSuccess + trendScore) / 5),
      credibility: Math.round(sourceReliability),
      engagement: Math.round(engagementQuality),
      quality: Math.round(contentQuality),
      trends: Math.round(trendScore)
    };
  }, [data]);

  const getAIInsights = useCallback((): AIInsight[] => {
    const insights: AIInsight[] = [];

    if (data?.sentiment_analytics) {
      const sentiment = data.sentiment_analytics;
      const avgSentiment = sentiment.average_sentiment_score;

      if (avgSentiment > 0.3) {
        insights.push({
          id: 'positive-sentiment',
          type: 'sentiment',
          title: 'Sentimiento Positivo Dominante',
          description: `El sentimiento promedio es ${(avgSentiment * 100).toFixed(1)}% positivo`,
          confidence: Math.abs(avgSentiment),
          impact: 'high',
          timestamp: new Date()
        });
      } else if (avgSentiment < -0.3) {
        insights.push({
          id: 'negative-sentiment',
          type: 'sentiment',
          title: 'Sentimiento Negativo Dominante',
          description: `El sentimiento promedio es ${Math.abs(avgSentiment * 100).toFixed(1)}% negativo`,
          confidence: Math.abs(avgSentiment),
          impact: 'high',
          timestamp: new Date()
        });
      }

      // Alertas por cambios significativos
      if (sentiment.positive_count > sentiment.negative_count * 2) {
        insights.push({
          id: 'sentiment-imbalance',
          type: 'anomaly',
          title: 'Desequilibrio de Sentimientos',
          description: 'Los artículos positivos duplican a los negativos',
          confidence: 0.8,
          impact: 'medium',
          timestamp: new Date()
        });
      }
    }

    if (data?.trend_analytics?.emerging_topics.length) {
      insights.push({
        id: 'emerging-topics',
        type: 'trend',
        title: 'Temas Emergentes Detectados',
        description: `${data.trend_analytics.emerging_topics.length} nuevos temas están ganando tracción`,
        confidence: 0.7,
        impact: 'medium',
        timestamp: new Date()
      });
    }

    if (data?.ai_processing_analytics) {
      const ai = data.ai_processing_analytics;
      if (ai.success_rate < 0.9) {
        insights.push({
          id: 'ai-processing-issues',
          type: 'alert',
          title: 'Problemas en Procesamiento IA',
          description: `Tasa de éxito del ${(ai.success_rate * 100).toFixed(1)}% - por debajo del objetivo`,
          confidence: 1.0 - ai.success_rate,
          impact: 'high',
          timestamp: new Date()
        });
      }
    }

    return insights;
  }, [data]);

  const getComparisonData = useCallback((): ComparisonData | null => {
    if (!data?.sentiment_analytics?.sentiment_trends.length) return null;

    const trends = data.sentiment_analytics.sentiment_trends;
    if (trends.length < 2) return null;

    const sortedTrends = trends
      .sort((a: Record<string, unknown>, b: Record<string, unknown>) => 
        new Date(a.date as string).getTime() - new Date(b.date as string).getTime()
      );

    const midPoint = Math.floor(sortedTrends.length / 2);
    const period1 = sortedTrends.slice(0, midPoint);
    const period2 = sortedTrends.slice(midPoint);

    const avgPeriod1 = period1.reduce((acc: Record<string, number>, item: Record<string, unknown>) => {
      Object.keys(item).forEach(key => {
        if (typeof item[key] === 'number') {
          acc[key] = (acc[key] || 0) + (item[key] as number);
        }
      });
      return acc;
    }, {});

    const avgPeriod2 = period2.reduce((acc: Record<string, number>, item: Record<string, unknown>) => {
      Object.keys(item).forEach(key => {
        if (typeof item[key] === 'number') {
          acc[key] = (acc[key] || 0) + (item[key] as number);
        }
      });
      return acc;
    }, {});

    const changes = Object.keys(avgPeriod1).map(metric => {
      const p1Value = avgPeriod1[metric] / period1.length;
      const p2Value = avgPeriod2[metric] / period2.length;
      const absoluteChange = p2Value - p1Value;
      const percentageChange = p1Value !== 0 ? (absoluteChange / p1Value) * 100 : 0;
      
      return {
        metric,
        absolute_change: absoluteChange,
        percentage_change: percentageChange,
        direction: Math.abs(percentageChange) < 1 ? 'stable' : 
                  percentageChange > 0 ? 'up' : 'down' as 'up' | 'down' | 'stable'
      };
    });

    return {
      period1: {
        label: 'Período Anterior',
        start_date: new Date(period1[0].date as string),
        end_date: new Date(period1[period1.length - 1].date as string),
        metrics: avgPeriod1
      },
      period2: {
        label: 'Período Actual',
        start_date: new Date(period2[0].date as string),
        end_date: new Date(period2[period2.length - 1].date as string),
        metrics: avgPeriod2
      },
      changes
    };
  }, [data]);

  return {
    data,
    loading,
    error,
    refetch: fetchAnalytics,
    getSentimentData,
    getTopicData,
    getRelevanceScore,
    getAIInsights,
    getComparisonData
  };
};
