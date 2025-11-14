import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { debounce } from 'lodash';
import { 
  SearchState, 
  SearchFilters, 
  SearchResult, 
  SearchSuggestion,
  SearchHistoryItem,
  SavedSearch,
  SortOption 
} from './types';
import { searchAPI } from '../../services/searchAPI';
import { storageService } from '../../services/storageService';
import { useDebouncedSearch } from '../../hooks/useDebouncedSearch';
import { useSearchURL } from '../../hooks/useSearchURL';

const DEFAULT_FILTERS: SearchFilters = {
  dateRange: {
    start: null,
    end: null,
  },
  sources: [],
  categories: [],
  authors: [],
  language: 'all',
  sortBy: 'relevance',
  sortOrder: 'desc',
  minScore: 0,
  maxScore: 100,
};

export const useSearch = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [state, setState] = useState<SearchState>({
    query: searchParams.get('q') || '',
    isSearching: false,
    results: [],
    totalResults: 0,
    currentPage: 1,
    hasMore: false,
    searchTime: 0,
    error: null,
    filters: DEFAULT_FILTERS,
    sortBy: 'relevance',
    suggestions: [],
    searchHistory: [],
    savedSearches: [],
  });

  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load search history and saved searches from localStorage
  useEffect(() => {
    const history = storageService.getSearchHistory();
    const savedSearches = storageService.getSavedSearches();
    setState(prev => ({
      ...prev,
      searchHistory: history,
      savedSearches,
    }));
  }, []);

  // Update URL when search state changes
  useEffect(() => {
    const params = new URLSearchParams();
    if (state.query) params.set('q', state.query);
    if (state.currentPage > 1) params.set('page', state.currentPage.toString());
    if (state.sortBy !== 'relevance') params.set('sort', state.sortBy);
    if (state.filters.language !== 'all') params.set('lang', state.filters.language);
    
    setSearchParams(params, { replace: true });
  }, [state.query, state.currentPage, state.sortBy, state.filters.language, setSearchParams]);

  // Debounced search function
  const debouncedSearch = useCallback(
    debounce(async (query: string, filters: SearchFilters, page: number) => {
      if (!query.trim()) {
        setState(prev => ({ ...prev, results: [], totalResults: 0, hasMore: false }));
        return;
      }

      setState(prev => ({ ...prev, isSearching: true, error: null }));

      // Cancel previous request if exists
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      
      const startTime = Date.now();

      try {
        const response = await searchAPI.search({
          query,
          filters,
          page,
          sortBy: state.sortBy,
          signal: abortControllerRef.current.signal,
        });

        const searchTime = Date.now() - startTime;

        setState(prev => {
          const newResults = page === 1 ? response.results : [...prev.results, ...response.results];
          const updatedHistory = updateSearchHistory(prev.searchHistory, query, filters, response.totalResults);

          return {
            ...prev,
            query,
            results: newResults,
            totalResults: response.totalResults,
            currentPage: page,
            hasMore: response.hasMore,
            searchTime,
            isSearching: false,
            error: null,
            searchHistory: updatedHistory,
            filters,
          };
        });

        // Save to localStorage
        storageService.saveSearchHistory(updateSearchHistory(state.searchHistory, query, filters, response.totalResults));
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          return; // Ignore aborted requests
        }

        setState(prev => ({
          ...prev,
          isSearching: false,
          error: error instanceof Error ? error.message : 'Error during search',
        }));
      }
    }, 300),
    [state.sortBy]
  );

  // Search function
  const search = useCallback(async (query: string, filters?: Partial<SearchFilters>) => {
    const mergedFilters = { ...state.filters, ...filters };
    setState(prev => ({ ...prev, currentPage: 1 }));
    debouncedSearch(query, mergedFilters, 1);
  }, [debouncedSearch, state.filters]);

  // Load more results
  const loadMore = useCallback(async () => {
    if (!state.hasMore || state.isSearching) return;

    const nextPage = state.currentPage + 1;
    debouncedSearch(state.query, state.filters, nextPage);
    setState(prev => ({ ...prev, currentPage: nextPage }));
  }, [debouncedSearch, state.hasMore, state.isSearching, state.currentPage, state.query, state.filters]);

  // Clear search
  const clearSearch = useCallback(() => {
    setState(prev => ({
      ...prev,
      query: '',
      results: [],
      totalResults: 0,
      currentPage: 1,
      hasMore: false,
      error: null,
      isSearching: false,
    }));
    setSearchParams({});
  }, [setSearchParams]);

  // Update filters
  const updateFilters = useCallback((newFilters: Partial<SearchFilters>) => {
    const updatedFilters = { ...state.filters, ...newFilters };
    setState(prev => ({ ...prev, filters: updatedFilters }));
    
    // Re-run search with new filters
    if (state.query) {
      debouncedSearch(state.query, updatedFilters, 1);
    }
  }, [state.filters, state.query, debouncedSearch]);

  // Save search
  const saveSearch = useCallback((name: string, options?: Partial<SavedSearch>) => {
    const savedSearch: SavedSearch = {
      id: crypto.randomUUID(),
      name,
      query: state.query,
      filters: state.filters,
      isPublic: false,
      createdAt: new Date(),
      lastUsed: new Date(),
      alertFrequency: 'never',
      emailNotifications: false,
      ...options,
    };

    const updatedSavedSearches = [...state.savedSearches, savedSearch];
    setState(prev => ({
      ...prev,
      savedSearches: updatedSavedSearches,
    }));

    storageService.saveSavedSearches(updatedSavedSearches);
  }, [state.query, state.filters, state.savedSearches]);

  // Delete saved search
  const deleteSavedSearch = useCallback((id: string) => {
    const updatedSavedSearches = state.savedSearches.filter(s => s.id !== id);
    setState(prev => ({
      ...prev,
      savedSearches: updatedSavedSearches,
    }));
    storageService.saveSavedSearches(updatedSavedSearches);
  }, [state.savedSearches]);

  // Clear search history
  const clearHistory = useCallback(() => {
    setState(prev => ({ ...prev, searchHistory: [] }));
    storageService.clearSearchHistory();
  }, []);

  // Remove history item
  const removeHistoryItem = useCallback((id: string) => {
    const updatedHistory = state.searchHistory.filter(h => h.id !== id);
    setState(prev => ({ ...prev, searchHistory: updatedHistory }));
    storageService.saveSearchHistory(updatedHistory);
  }, [state.searchHistory]);

  // Get suggestions
  const getSuggestions = useCallback(async (query: string): Promise<SearchSuggestion[]> => {
    try {
      const suggestions = await searchAPI.getSuggestions(query);
      return suggestions;
    } catch {
      return [];
    }
  }, []);

  // Highlight terms in text
  const highlightTerms = useCallback((text: string, terms: string[]): string => {
    if (!terms.length) return text;
    
    const regex = new RegExp(`(${terms.map(term => escapeRegExp(term)).join('|')})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800">$1</mark>');
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    ...state,
    search,
    clearSearch,
    updateFilters,
    loadMore,
    saveSearch,
    deleteSavedSearch,
    clearHistory,
    removeHistoryItem,
    getSuggestions,
    highlightTerms,
  };
};

// Helper functions
const escapeRegExp = (string: string): string => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
};

const updateSearchHistory = (
  currentHistory: SearchHistoryItem[],
  query: string,
  filters: SearchFilters,
  resultCount: number
): SearchHistoryItem[] => {
  const newItem: SearchHistoryItem = {
    id: crypto.randomUUID(),
    query,
    filters,
    timestamp: new Date(),
    resultCount,
  };

  // Remove existing entry for the same query
  const filteredHistory = currentHistory.filter(h => h.query !== query);
  
  // Add new item at the beginning
  const updatedHistory = [newItem, ...filteredHistory];
  
  // Keep only last 50 searches
  return updatedHistory.slice(0, 50);
};