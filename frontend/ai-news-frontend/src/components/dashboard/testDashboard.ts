import { dashboardService } from '../services/dashboardService';

// Mock data para testing
const mockDashboardMetrics = {
  total_articles: 12543,
  active_sources: 127,
  average_sentiment: 0.67,
  articles_today: 89,
  articles_this_week: 456,
  articles_this_month: 1876,
  sentiment_distribution: {
    positive: 0.45,
    neutral: 0.35,
    negative: 0.20
  },
  top_sources: [
    { name: 'Reuters', count: 1234, percentage: 9.8 },
    { name: 'BBC News', count: 987, percentage: 7.9 },
    { name: 'CNN', count: 856, percentage: 6.8 },
    { name: 'The Guardian', count: 743, percentage: 5.9 },
    { name: 'AP News', count: 654, percentage: 5.2 }
  ],
  sentiment_trend: [
    { date: '2025-11-01', sentiment_score: 0.72, article_count: 45 },
    { date: '2025-11-02', sentiment_score: 0.68, article_count: 52 },
    { date: '2025-11-03', sentiment_score: 0.75, article_count: 38 },
    { date: '2025-11-04', sentiment_score: 0.63, article_count: 67 },
    { date: '2025-11-05', sentiment_score: 0.67, article_count: 89 },
    { date: '2025-11-06', sentiment_score: 0.71, article_count: 34 }
  ],
  categories_distribution: [
    { category: 'Technology', count: 3456, percentage: 27.6 },
    { category: 'Politics', count: 2987, percentage: 23.8 },
    { category: 'Business', count: 2345, percentage: 18.7 },
    { category: 'Health', count: 1876, percentage: 15.0 },
    { category: 'Sports', count: 1234, percentage: 9.8 },
    { category: 'Entertainment', count: 645, percentage: 5.1 }
  ],
  hourly_activity: Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    count: Math.floor(Math.random() * 100) + 10
  }))
};

const mockLiveStats = {
  current_articles: 12543,
  sources_online: 127,
  average_processing_time: 2.3,
  last_update: new Date().toISOString()
};

// Override fetch for testing
const originalFetch = global.fetch;
global.fetch = async (url: string) => {
  console.log(`🧪 Test: Fetching ${url}`);
  
  if (url.includes('/analytics/dashboard')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics)
    } as Response);
  }
  
  if (url.includes('/analytics/stats')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockLiveStats)
    } as Response);
  }
  
  // Fallback to original fetch
  return originalFetch(url);
};

export const testDashboardService = {
  async testDashboardMetrics() {
    try {
      console.log('🧪 Testing getDashboardMetrics...');
      const metrics = await dashboardService.getDashboardMetrics();
      console.log('✅ Dashboard metrics loaded:', {
        total_articles: metrics.total_articles,
        active_sources: metrics.active_sources,
        average_sentiment: metrics.average_sentiment
      });
      return metrics;
    } catch (error) {
      console.error('❌ Error testing dashboard metrics:', error);
      throw error;
    }
  },

  async testLiveStats() {
    try {
      console.log('🧪 Testing getLiveStats...');
      const stats = await dashboardService.getLiveStats();
      console.log('✅ Live stats loaded:', {
        current_articles: stats.current_articles,
        sources_online: stats.sources_online,
        average_processing_time: stats.average_processing_time
      });
      return stats;
    } catch (error) {
      console.error('❌ Error testing live stats:', error);
      throw error;
    }
  },

  async testAllEndpoints() {
    console.log('🧪 Starting dashboard service tests...');
    
    try {
      const [metrics, stats] = await Promise.all([
        this.testDashboardMetrics(),
        this.testLiveStats()
      ]);
      
      console.log('✅ All dashboard tests passed!');
      console.log('📊 Test Summary:', {
        dashboard_metrics_loaded: !!metrics,
        live_stats_loaded: !!stats,
        total_articles: metrics.total_articles,
        active_sources: metrics.active_sources,
        current_articles: stats.current_articles,
        sources_online: stats.sources_online
      });
      
      return { metrics, stats };
    } catch (error) {
      console.error('❌ Dashboard tests failed:', error);
      throw error;
    }
  }
};

// Auto-run tests if this file is executed directly
if (typeof window !== 'undefined') {
  (window as any).testDashboard = testDashboardService;
}