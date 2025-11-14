// Export all search components
export { SearchInterface } from './SearchInterface';
export { SearchBar } from './SearchBar';
export { SearchFilters } from './SearchFilters';
export { SearchResults } from './SearchResults';
export { SavedSearches } from './SavedSearches';
export { SearchHistory } from './SearchHistory';
export { SearchSkeleton } from './SearchSkeleton';

// Export hook personalizado
export { useTextHighlighting, HighlightedText, MatchStats } from './useTextHighlighting';

// Types
export type { SearchState } from './types';
export type { SearchFilters } from './types';
export type { SearchResult } from './types';
export type { SearchSuggestion } from './types';
export type { SearchHistoryItem } from './types';
export type { SavedSearch } from './types';