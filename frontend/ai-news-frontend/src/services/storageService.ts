import {
  SearchHistoryItem,
  SavedSearch,
} from '../components/search/types';

const STORAGE_KEYS = {
  SEARCH_HISTORY: 'ai-news-search-history',
  SAVED_SEARCHES: 'ai-news-saved-searches',
  USER_PREFERENCES: 'ai-news-user-preferences',
};

export class StorageService {
  // Search History
  getSearchHistory(): SearchHistoryItem[] {
    try {
      const history = localStorage.getItem(STORAGE_KEYS.SEARCH_HISTORY);
      if (!history) return [];

      const parsed = JSON.parse(history);
      return parsed.map((item: any) => ({
        ...item,
        timestamp: new Date(item.timestamp),
        filters: {
          ...item.filters,
          dateRange: {
            start: item.filters.dateRange.start ? new Date(item.filters.dateRange.start) : null,
            end: item.filters.dateRange.end ? new Date(item.filters.dateRange.end) : null,
          },
        },
      }));
    } catch (error) {
      console.error('Error loading search history:', error);
      return [];
    }
  }

  saveSearchHistory(history: SearchHistoryItem[]): void {
    try {
      localStorage.setItem(STORAGE_KEYS.SEARCH_HISTORY, JSON.stringify(history));
    } catch (error) {
      console.error('Error saving search history:', error);
    }
  }

  clearSearchHistory(): void {
    try {
      localStorage.removeItem(STORAGE_KEYS.SEARCH_HISTORY);
    } catch (error) {
      console.error('Error clearing search history:', error);
    }
  }

  // Saved Searches
  getSavedSearches(): SavedSearch[] {
    try {
      const searches = localStorage.getItem(STORAGE_KEYS.SAVED_SEARCHES);
      if (!searches) return [];

      const parsed = JSON.parse(searches);
      return parsed.map((search: any) => ({
        ...search,
        createdAt: new Date(search.createdAt),
        lastUsed: new Date(search.lastUsed),
        filters: {
          ...search.filters,
          dateRange: {
            start: search.filters.dateRange.start ? new Date(search.filters.dateRange.start) : null,
            end: search.filters.dateRange.end ? new Date(search.filters.dateRange.end) : null,
          },
        },
      }));
    } catch (error) {
      console.error('Error loading saved searches:', error);
      return [];
    }
  }

  saveSavedSearches(searches: SavedSearch[]): void {
    try {
      localStorage.setItem(STORAGE_KEYS.SAVED_SEARCHES, JSON.stringify(searches));
    } catch (error) {
      console.error('Error saving searches:', error);
    }
  }

  getSavedSearch(id: string): SavedSearch | null {
    const searches = this.getSavedSearches();
    return searches.find(search => search.id === id) || null;
  }

  updateSavedSearch(id: string, updates: Partial<SavedSearch>): void {
    const searches = this.getSavedSearches();
    const index = searches.findIndex(search => search.id === id);
    
    if (index !== -1) {
      searches[index] = { ...searches[index], ...updates };
      this.saveSavedSearches(searches);
    }
  }

  deleteSavedSearch(id: string): void {
    const searches = this.getSavedSearches();
    const filtered = searches.filter(search => search.id !== id);
    this.saveSavedSearches(filtered);
  }

  // User Preferences
  getUserPreferences(): Record<string, any> {
    try {
      const preferences = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return preferences ? JSON.parse(preferences) : {};
    } catch (error) {
      console.error('Error loading user preferences:', error);
      return {};
    }
  }

  saveUserPreferences(preferences: Record<string, any>): void {
    try {
      localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(preferences));
    } catch (error) {
      console.error('Error saving user preferences:', error);
    }
  }

  getUserPreference(key: string, defaultValue?: any): any {
    const preferences = this.getUserPreferences();
    return preferences[key] ?? defaultValue;
  }

  setUserPreference(key: string, value: any): void {
    const preferences = this.getUserPreferences();
    preferences[key] = value;
    this.saveUserPreferences(preferences);
  }

  // Cleanup old data
  cleanupOldData(): void {
    try {
      this.cleanupOldHistory();
      this.cleanupOldSavedSearches();
    } catch (error) {
      console.error('Error cleaning up old data:', error);
    }
  }

  private cleanupOldHistory(): void {
    const history = this.getSearchHistory();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const filtered = history.filter(item => item.timestamp > thirtyDaysAgo);
    this.saveSearchHistory(filtered);
  }

  private cleanupOldSavedSearches(): void {
    const searches = this.getSavedSearches();
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

    const filtered = searches.filter(search => search.lastUsed > sixMonthsAgo);
    this.saveSavedSearches(filtered);
  }

  // Export/Import functionality
  exportUserData(): string {
    const data = {
      searchHistory: this.getSearchHistory(),
      savedSearches: this.getSavedSearches(),
      preferences: this.getUserPreferences(),
      exportedAt: new Date().toISOString(),
    };

    return JSON.stringify(data, null, 2);
  }

  importUserData(jsonData: string): boolean {
    try {
      const data = JSON.parse(jsonData);
      
      if (data.searchHistory) {
        this.saveSearchHistory(data.searchHistory);
      }
      
      if (data.savedSearches) {
        this.saveSavedSearches(data.savedSearches);
      }
      
      if (data.preferences) {
        this.saveUserPreferences(data.preferences);
      }

      return true;
    } catch (error) {
      console.error('Error importing user data:', error);
      return false;
    }
  }

  clearAllUserData(): void {
    try {
      localStorage.removeItem(STORAGE_KEYS.SEARCH_HISTORY);
      localStorage.removeItem(STORAGE_KEYS.SAVED_SEARCHES);
      localStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES);
    } catch (error) {
      console.error('Error clearing all user data:', error);
    }
  }
}

export const storageService = new StorageService();