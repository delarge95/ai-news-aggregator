// Tipos para el sistema de noticias
export interface NewsArticle {
  id: string;
  title: string;
  content: string;
  summary: string;
  url: string;
  source: string;
  author?: string;
  publishedAt: string;
  imageUrl?: string;
  tags: string[];
  category: string;
  
  // Metadatos de IA
  aiMetadata: {
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number; // 0-100
    keywords: string[];
    entities: {
      person?: string[];
      organization?: string[];
      location?: string[];
    };
    relevanceScore: number; // 0-100
    topic: string[];
    readability: number; // 0-100
    language: string;
  };
}

export interface NewsFilters {
  // Filtros de fecha
  dateRange?: {
    from: Date;
    to: Date;
  };
  
  // Filtros de fuente
  sources?: string[];
  
  // Filtros de sentimiento
  sentiment?: Array<'positive' | 'negative' | 'neutral'>;
  
  // Filtros de relevancia
  relevanceRange?: {
    min: number;
    max: number;
  };
  
  // Filtros de categoría
  categories?: string[];
  
  // Filtros de tags
  tags?: string[];
  
  // Filtros de autor
  authors?: string[];
  
  // Filtros de idioma
  languages?: string[];
}

export interface SortOption {
  field: 'publishedAt' | 'relevanceScore' | 'sentiment' | 'title' | 'source';
  direction: 'asc' | 'desc';
  label: string;
}

export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

export interface NewsSearchState {
  query: string;
  filters: NewsFilters;
  sort: SortOption;
  pagination: {
    page: number;
    limit: number;
  };
  isLoading: boolean;
  error?: string;
}

export interface AutocompleteSuggestion {
  value: string;
  label: string;
  type: 'source' | 'tag' | 'category' | 'keyword';
  count?: number;
}

export interface NewsState {
  articles: NewsArticle[];
  searchState: NewsSearchState;
  pagination: PaginationInfo;
  suggestions: AutocompleteSuggestion[];
  availableSources: string[];
  availableCategories: string[];
  availableTags: string[];
}

export type ViewMode = 'grid' | 'list';

export type FilterPanelState = {
  isOpen: boolean;
  activeTab: 'date' | 'source' | 'sentiment' | 'relevance' | 'category' | 'tags';
};