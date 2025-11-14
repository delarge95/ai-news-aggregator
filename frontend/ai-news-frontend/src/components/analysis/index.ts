/**
 * Índice de exportación para componentes de análisis
 */

// Componentes principales
export { SentimentChart } from './SentimentChart';
export { default as SentimentChartComponent } from './SentimentChart';

export { TopicAnalysis } from './TopicAnalysis';
export { default as TopicAnalysisComponent } from './TopicAnalysis';

export { RelevanceScoreComponent } from './RelevanceScore';
export { default as RelevanceScore } from './RelevanceScore';

export { AIInsights } from './AIInsights';
export { default as AIInsightsComponent } from './AIInsights';

export { ComparisonChart } from './ComparisonChart';
export { default as ComparisonChartComponent } from './ComparisonChart';

// Dashboard y Provider
export { AnalyticsDashboard } from './AnalyticsDashboard';
export { AnalyticsProvider, useAnalyticsContext } from './AnalyticsProvider';

// Hooks
export { useAnalytics } from './useAnalytics';

// Utilidades
export * from './utils';
export * from './types';
