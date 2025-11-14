import { DashboardMetrics, LiveStats } from '../types/dashboard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class DashboardService {
  private async fetchAPI<T>(endpoint: string): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  }

  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.fetchAPI<DashboardMetrics>('/analytics/dashboard');
  }

  async getLiveStats(): Promise<LiveStats> {
    return this.fetchAPI<LiveStats>('/analytics/stats');
  }

  async getTotalArticles(): Promise<{ total: number }> {
    return this.fetchAPI<{ total: number }>('/analytics/total-articles');
  }

  async getActiveSources(): Promise<{ active: number }> {
    return this.fetchAPI<{ active: number }>('/analytics/active-sources');
  }

  async getAverageSentiment(): Promise<{ average: number }> {
    return this.fetchAPI<{ average: number }>('/analytics/average-sentiment');
  }

  async getSentimentDistribution(): Promise<{ positive: number; neutral: number; negative: number }> {
    return this.fetchAPI<{ positive: number; neutral: number; negative: number }>('/analytics/sentiment-distribution');
  }
}

export const dashboardService = new DashboardService();