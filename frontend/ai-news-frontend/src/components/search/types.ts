// Core types for the search system

export interface SearchState {
  query: string;
  isSearching: boolean;
  results: SearchResult[];
  totalResults: number;
  currentPage: number;
  hasMore: boolean;
  searchTime: number;
  error: string | null;
  filters: SearchFilters;
  sortBy: SortOption;
  suggestions: SearchSuggestion[];
  searchHistory: SearchHistoryItem[];
  savedSearches: SavedSearch[];
}

export interface SearchFilters {
  dateRange: {
    start: Date | null;
    end: Date | null;
  };
  sources: string[];
  categories: string[];
  authors: string[];
  language: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  minScore: number;
  maxScore: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  summary: string;
  url: string;
  imageUrl?: string;
  publishedAt: Date;
  source: {
    id: string;
    name: string;
    logo?: string;
  };
  author: string;
  category: string;
  tags: string[];
  sentiment: 'positive' | 'negative' | 'neutral';
  relevanceScore: number;
  aiInsights?: {
    keyTopics: string[];
    sentiment: string;
    confidence: number;
  };
  highlightedContent?: {
    title: string;
    content: string;
    matchedTerms: string[];
  };
}

export interface SearchSuggestion {
  id: string;
  text: string;
  type: 'query' | 'source' | 'category' | 'tag' | 'author';
  count: number;
  isRecent?: boolean;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  filters: SearchFilters;
  timestamp: Date;
  resultCount: number;
}

export interface SavedSearch {
  id: string;
  name: string;
  query: string;
  filters: SearchFilters;
  isPublic: boolean;
  createdAt: Date;
  lastUsed: Date;
  alertFrequency: 'immediate' | 'daily' | 'weekly' | 'never';
  emailNotifications: boolean;
}

export type SortOption = 
  | 'relevance' 
  | 'date_desc' 
  | 'date_asc' 
  | 'popularity' 
  | 'ai_score' 
  | 'author_az' 
  | 'source_az';

export interface AutocompleteOption {
  value: string;
  label: string;
  type: 'recent' | 'popular' | 'suggestion';
  count?: number;
}

export interface SearchAnalytics {
  totalSearches: number;
  popularQueries: Array<{ query: string; count: number }>;
  searchTrend: Array<{ date: string; searches: number }>;
  popularFilters: Array<{ filter: string; count: number }>;
}

export interface SearchContextType extends SearchState {
  search: (query: string, filters?: Partial<SearchFilters>) => Promise<void>;
  clearSearch: () => void;
  updateFilters: (filters: Partial<SearchFilters>) => void;
  loadMore: () => Promise<void>;
  saveSearch: (name: string, options?: Partial<SavedSearch>) => void;
  deleteSavedSearch: (id: string) => void;
  clearHistory: () => void;
  removeHistoryItem: (id: string) => void;
  getSuggestions: (query: string) => Promise<SearchSuggestion[]>;
  highlightTerms: (text: string, terms: string[]) => string;
}