// Componentes principales
export { default as NewsList } from './NewsList';
export { default as NewsCard } from './NewsCard';
export { default as SearchBar } from './SearchBar';
export { default as SortControls } from './SortControls';
export { default as AdvancedFilters } from './AdvancedFilters';
export { default as NewsFilters } from './NewsFilters';
export { default as NewsExample } from './NewsExample';

// Componentes de estado y UX
export { default as LoadingSkeleton, 
  NewsCardSkeleton,
  InitialLoadingSkeleton,
  LoadingMoreSkeleton,
  EmptySearchSkeleton,
  MobileFilterSkeleton 
} from './LoadingSkeleton';

export { 
  default as InfiniteScroll, 
  BatchInfiniteScroll, 
  HybridInfiniteScroll, 
  useInfiniteScrollState 
} from './InfiniteScroll';

export { 
  default as ErrorState, 
  NetworkErrorState, 
  EmptyState 
} from './ErrorState';

// Tipos y interfaces
export type {
  NewsArticle,
  NewsFilters,
  SortOption,
  PaginationInfo,
  NewsSearchState,
  AutocompleteSuggestion,
  NewsState,
  FilterPanelState,
} from './types';

// Constantes
export const DEFAULT_SORT_OPTIONS: SortOption[] = [
  { field: 'publishedAt', direction: 'desc', label: 'Fecha (más reciente)' },
  { field: 'publishedAt', direction: 'asc', label: 'Fecha (más antigua)' },
  { field: 'relevanceScore', direction: 'desc', label: 'Relevancia (mayor)' },
  { field: 'relevanceScore', direction: 'asc', label: 'Relevancia (menor)' },
  { field: 'title', direction: 'asc', label: 'Título (A-Z)' },
  { field: 'title', direction: 'desc', label: 'Título (Z-A)' },
  { field: 'source', direction: 'asc', label: 'Fuente (A-Z)' },
  { field: 'source', direction: 'desc', label: 'Fuente (Z-A)' },
];

export const DEFAULT_PAGINATION: PaginationInfo = {
  page: 1,
  limit: 20,
  total: 0,
  totalPages: 0,
  hasNext: false,
  hasPrevious: false,
};

export const DEFAULT_FILTERS: NewsFilters = {};

// Utilidades
export const createEmptyNewsState = (): NewsState => ({
  articles: [],
  searchState: {
    query: '',
    filters: DEFAULT_FILTERS,
    sort: DEFAULT_SORT_OPTIONS[0],
    pagination: {
      page: 1,
      limit: 20,
    },
    isLoading: false,
  },
  pagination: DEFAULT_PAGINATION,
  suggestions: [],
  availableSources: [],
  availableCategories: [],
  availableTags: [],
});