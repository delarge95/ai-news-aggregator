/**
 * Provider de contexto para analytics
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { useAnalytics } from './useAnalytics';
import { AnalyticsFilters } from './types';

interface AnalyticsContextType {
  // Datos
  sentimentData: ReturnType<typeof useAnalytics>['getSentimentData'] | null;
  topicData: ReturnType<typeof useAnalytics>['getTopicData'];
  relevanceScore: ReturnType<typeof useAnalytics>['getRelevanceScore'] | null;
  aiInsights: ReturnType<typeof useAnalytics>['getAIInsights'];
  comparisonData: ReturnType<typeof useAnalytics>['getComparisonData'] | null;
  
  // Estado
  loading: boolean;
  error: string | null;
  
  // Filtros
  filters: AnalyticsFilters;
  updateFilters: (filters: Partial<AnalyticsFilters>) => void;
  
  // Acciones
  refetch: () => void;
}

const AnalyticsContext = createContext<AnalyticsContextType | undefined>(undefined);

export const useAnalyticsContext = () => {
  const context = useContext(AnalyticsContext);
  if (!context) {
    throw new Error('useAnalyticsContext must be used within an AnalyticsProvider');
  }
  return context;
};

interface AnalyticsProviderProps {
  children: ReactNode;
}

export const AnalyticsProvider: React.FC<AnalyticsProviderProps> = ({ children }) => {
  const [filters, setFilters] = useState<AnalyticsFilters>({
    granularity: 'daily',
    date_from: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 días atrás
    date_to: new Date()
  });

  const analytics = useAnalytics(filters);

  const updateFilters = (newFilters: Partial<AnalyticsFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const value: AnalyticsContextType = {
    // Datos
    sentimentData: analytics.getSentimentData(),
    topicData: analytics.getTopicData(),
    relevanceScore: analytics.getRelevanceScore(),
    aiInsights: analytics.getAIInsights(),
    comparisonData: analytics.getComparisonData(),
    
    // Estado
    loading: analytics.loading,
    error: analytics.error,
    
    // Filtros
    filters,
    updateFilters,
    
    // Acciones
    refetch: analytics.refetch
  };

  return (
    <AnalyticsContext.Provider value={value}>
      {children}
    </AnalyticsContext.Provider>
  );
};
