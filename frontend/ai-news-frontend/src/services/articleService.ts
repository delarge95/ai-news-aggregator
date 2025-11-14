/**
 * Article Service
 * Service for fetching articles from the AI News Aggregator API
 */

import { buildApiUrl } from "../config/api";

export interface Article {
  id: string;
  title: string;
  content?: string;
  summary?: string;
  url: string;
  published_at?: string;
  created_at?: string;
  updated_at?: string;
  author?: string;
  source_name?: string;
  source_url?: string;
  sentiment_score?: number;
  sentiment_label?: string;
  relevance_score?: number;
  topic_tags?: unknown;
}

export interface ArticlesResponse {
  articles: Article[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

class ArticleService {
  /**
   * Get articles with pagination
   * @param page - Page number (default: 1)
   * @param perPage - Items per page (default: 20)
   * @returns Promise with articles response
   */
  async getArticles(page: number = 1, perPage: number = 20): Promise<ArticlesResponse> {
    try {
      const response = await fetch(
        buildApiUrl(`/articles/articles?page=${page}&per_page=${perPage}`),
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching articles:', error);
      throw error;
    }
  }

  /**
   * Search articles
   * @param query - Search query
   * @param page - Page number (default: 1)
   * @param perPage - Items per page (default: 20)
   * @returns Promise with articles response
   */
  async searchArticles(
    query: string,
    page: number = 1,
    perPage: number = 20
  ): Promise<ArticlesResponse> {
    try {
      const params = new URLSearchParams({
        q: query,
        page: page.toString(),
        per_page: perPage.toString(),
      });

      const response = await fetch(
        buildApiUrl(`/articles/articles?${params.toString()}`),
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error searching articles:', error);
      throw error;
    }
  }
}

export const articleService = new ArticleService();
