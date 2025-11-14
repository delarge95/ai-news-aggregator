import {
  SearchResult,
  SearchSuggestion,
  SearchFilters,
  SortOption,
} from '../components/search/types';

interface SearchRequest {
  query: string;
  filters: SearchFilters;
  page: number;
  sortBy: SortOption;
  signal?: AbortSignal;
}

interface SearchResponse {
  results: SearchResult[];
  totalResults: number;
  hasMore: boolean;
  searchTime: number;
  facets?: {
    sources: Array<{ name: string; count: number }>;
    categories: Array<{ name: string; count: number }>;
    authors: Array<{ name: string; count: number }>;
  };
}

class SearchAPIService {
  private baseURL = 'http://localhost:8000/api/v1';

  async search(params: SearchRequest): Promise<SearchResponse> {
    const { query, filters, page, sortBy, signal } = params;
    
    const searchParams = new URLSearchParams({
      q: query,
      page: page.toString(),
      sort: sortBy,
      ...this.filtersToParams(filters),
    });

    try {
      const response = await fetch(`${this.baseURL}/search?${searchParams}`, {
        signal,
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        results: data.results || [],
        totalResults: data.total || 0,
        hasMore: data.has_more || false,
        searchTime: data.search_time || 0,
        facets: data.facets,
      };
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw error;
      }
      
      // Mock data for development
      return this.getMockSearchResults(query, page);
    }
  }

  async getSuggestions(query: string): Promise<SearchSuggestion[]> {
    if (query.length < 2) return [];

    try {
      const response = await fetch(`${this.baseURL}/search/suggestions?q=${encodeURIComponent(query)}`);
      
      if (!response.ok) {
        throw new Error('Suggestions request failed');
      }

      const data = await response.json();
      return data.suggestions || [];
    } catch (error) {
      // Mock suggestions for development
      return this.getMockSuggestions(query);
    }
  }

  async getTrendingSearches(): Promise<SearchSuggestion[]> {
    try {
      const response = await fetch(`${this.baseURL}/search/trending`);
      
      if (!response.ok) {
        throw new Error('Trending searches request failed');
      }

      const data = await response.json();
      return data.trending || [];
    } catch (error) {
      // Mock trending searches
      return this.getMockTrendingSearches();
    }
  }

  private filtersToParams(filters: SearchFilters): Record<string, string> {
    const params: Record<string, string> = {};

    if (filters.language !== 'all') {
      params.language = filters.language;
    }

    if (filters.dateRange.start) {
      params.date_start = filters.dateRange.start.toISOString();
    }

    if (filters.dateRange.end) {
      params.date_end = filters.dateRange.end.toISOString();
    }

    if (filters.sources.length > 0) {
      params.sources = filters.sources.join(',');
    }

    if (filters.categories.length > 0) {
      params.categories = filters.categories.join(',');
    }

    if (filters.authors.length > 0) {
      params.authors = filters.authors.join(',');
    }

    if (filters.minScore > 0) {
      params.min_score = filters.minScore.toString();
    }

    if (filters.maxScore < 100) {
      params.max_score = filters.maxScore.toString();
    }

    if (filters.sortOrder !== 'desc') {
      params.sort_order = filters.sortOrder;
    }

    return params;
  }

  // Mock data for development
  private getMockSearchResults(query: string, page: number): SearchResponse {
    const mockResults: SearchResult[] = Array.from({ length: 10 }, (_, i) => ({
      id: `${page}-${i}`,
      title: `${query} - Artículo ${i + 1} - Página ${page}`,
      content: `Este es un contenido de ejemplo sobre ${query}. Contiene información relevante y actualizada sobre el tema que estás buscando. Lorem ipsum dolor sit amet, consectetur adipiscing elit.`,
      summary: `Resumen del artículo sobre ${query}...`,
      url: `https://example.com/article-${page}-${i}`,
      imageUrl: `https://picsum.photos/400/200?random=${page}-${i}`,
      publishedAt: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000),
      source: {
        id: `source-${i % 3}`,
        name: ['BBC News', 'CNN', 'Reuters'][i % 3] || 'Unknown',
        logo: `https://picsum.photos/32/32?random=${i}`,
      },
      author: `Autor ${i + 1}`,
      category: ['Tecnología', 'Salud', 'Negocios', 'Deportes'][i % 4] || 'General',
      tags: [query, 'IA', 'Machine Learning', 'Noticia'],
      sentiment: ['positive', 'negative', 'neutral'][Math.floor(Math.random() * 3)] as any,
      relevanceScore: Math.floor(Math.random() * 100),
      aiInsights: {
        keyTopics: [query, 'inteligencia artificial', 'tecnología'],
        sentiment: ['positive', 'negative', 'neutral'][Math.floor(Math.random() * 3)],
        confidence: Math.floor(Math.random() * 100),
      },
      highlightedContent: {
        title: `<mark>${query}</mark> - Artículo ${i + 1}`,
        content: `Este es un contenido de ejemplo sobre <mark>${query}</mark>.`,
        matchedTerms: [query],
      },
    }));

    return {
      results: mockResults,
      totalResults: 156,
      hasMore: page < 3,
      searchTime: Math.random() * 500 + 100,
      facets: {
        sources: [
          { name: 'BBC News', count: 45 },
          { name: 'CNN', count: 32 },
          { name: 'Reuters', count: 28 },
          { name: 'Associated Press', count: 23 },
        ],
        categories: [
          { name: 'Tecnología', count: 67 },
          { name: 'Salud', count: 34 },
          { name: 'Negocios', count: 28 },
          { name: 'Deportes', count: 27 },
        ],
        authors: [
          { name: 'Juan Pérez', count: 12 },
          { name: 'María García', count: 8 },
          { name: 'Carlos López', count: 6 },
        ],
      },
    };
  }

  private getMockSuggestions(query: string): SearchSuggestion[] {
    const baseSuggestions = [
      'inteligencia artificial',
      'machine learning',
      'deep learning',
      'redes neuronales',
      'procesamiento de lenguaje natural',
      'visión por computadora',
    ];

    return baseSuggestions
      .filter(suggestion => suggestion.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 5)
      .map((suggestion, i) => ({
        id: `suggestion-${i}`,
        text: suggestion,
        type: 'query' as const,
        count: Math.floor(Math.random() * 100) + 1,
      }));
  }

  private getMockTrendingSearches(): SearchSuggestion[] {
    const trending = [
      'ChatGPT',
      'OpenAI',
      'GPT-4',
      'inteligencia artificial',
      'machine learning',
      'IA generativa',
    ];

    return trending.map((trend, i) => ({
      id: `trending-${i}`,
      text: trend,
      type: 'query' as const,
      count: Math.floor(Math.random() * 500) + 100,
      isRecent: true,
    }));
  }
}

export const searchAPI = new SearchAPIService();