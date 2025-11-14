import React, { useState } from 'react';
import { Search, Filter, History, Bookmark, Settings, X, RotateCcw } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from '../ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { SearchBar } from './SearchBar';
import { SearchFilters } from './SearchFilters';
import { SearchResults } from './SearchResults';
import { SearchHistory } from './SearchHistory';
import { SavedSearches } from './SavedSearches';
import { SearchSkeleton } from './SearchSkeleton';
import { useSearch } from './useSearch';
import { SearchFilters as SearchFiltersType } from './types';
import { cn } from '../../lib/utils';

interface SearchInterfaceProps {
  className?: string;
  showSavedSearches?: boolean;
  showHistory?: boolean;
  showFilters?: boolean;
  initialQuery?: string;
  onArticleClick?: (article: any) => void;
}

export const SearchInterface: React.FC<SearchInterfaceProps> = ({
  className,
  showSavedSearches = true,
  showHistory = true,
  showFilters = true,
  initialQuery = '',
  onArticleClick,
}) => {
  const [showFiltersDialog, setShowFiltersDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('search');
  
  const {
    query,
    isSearching,
    results,
    totalResults,
    currentPage,
    hasMore,
    searchTime,
    error,
    filters,
    sortBy,
    suggestions,
    searchHistory,
    savedSearches,
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
  } = useSearch();

  const [searchTerm, setSearchTerm] = useState(initialQuery);

  React.useEffect(() => {
    if (initialQuery) {
      setSearchTerm(initialQuery);
      search(initialQuery);
    }
  }, [initialQuery, search]);

  const handleSearch = (newQuery: string) => {
    if (newQuery.trim()) {
      search(newQuery.trim());
    }
  };

  const handleFilterChange = (newFilters: Partial<SearchFiltersType>) => {
    updateFilters(newFilters);
  };

  const handleClearFilters = () => {
    updateFilters({
      dateRange: { start: null, end: null },
      sources: [],
      categories: [],
      authors: [],
      language: 'all',
      minScore: 0,
      maxScore: 100,
    });
  };

  const handleLoadSuggestions = async (query: string) => {
    await getSuggestions(query);
  };

  const handleLoadHistoryItem = (historyItem: any) => {
    setSearchTerm(historyItem.query);
    search(historyItem.query, historyItem.filters);
  };

  const handleLoadSavedSearch = (savedSearch: any) => {
    setSearchTerm(savedSearch.query);
    search(savedSearch.query, savedSearch.filters);
  };

  const activeFiltersCount = React.useMemo(() => {
    let count = 0;
    if (filters.dateRange.start) count++;
    if (filters.sources.length > 0) count++;
    if (filters.categories.length > 0) count++;
    if (filters.authors.length > 0) count++;
    if (filters.language !== 'all') count++;
    if (filters.minScore > 0 || filters.maxScore < 100) count++;
    return count;
  }, [filters]);

  const hasActiveSearch = query.length > 0 || results.length > 0 || isSearching;

  return (
    <div className={cn("w-full max-w-6xl mx-auto", className)}>
      {/* Search Header */}
      <div className="sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
        <div className="container mx-auto px-4 py-4">
          {/* Search Bar */}
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <SearchBar
                value={searchTerm}
                onChange={setSearchTerm}
                onSearch={handleSearch}
                suggestions={suggestions}
                onGetSuggestions={handleLoadSuggestions}
                placeholder="Buscar noticias, temas, autores..."
                disabled={isSearching}
              />
            </div>

            {/* Filter Button */}
            {showFilters && (
              <Sheet open={showFiltersDialog} onOpenChange={setShowFiltersDialog}>
                <SheetTrigger asChild>
                  <Button variant="outline" className="relative">
                    <Filter className="w-4 h-4 mr-2" />
                    Filtros
                    {activeFiltersCount > 0 && (
                      <Badge 
                        variant="destructive" 
                        className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 text-xs flex items-center justify-center"
                      >
                        {activeFiltersCount}
                      </Badge>
                    )}
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-96 overflow-y-auto">
                  <SheetHeader>
                    <SheetTitle>Filtros de búsqueda</SheetTitle>
                    <SheetDescription>
                      Refina tus resultados con filtros avanzados
                    </SheetDescription>
                  </SheetHeader>
                  <div className="mt-6">
                    <SearchFilters
                      filters={filters}
                      onFiltersChange={handleFilterChange}
                      onClearFilters={handleClearFilters}
                      onSaveFilterPreset={(name, searchFilters) => {
                        const savedSearch: SavedSearch = {
                          id: crypto.randomUUID(),
                          name,
                          query: state.query,
                          filters: searchFilters,
                          isPublic: false,
                          createdAt: new Date(),
                          lastUsed: new Date(),
                          alertFrequency: 'never',
                          emailNotifications: false,
                        };
                        saveSearch(savedSearch.name, savedSearch);
                      }}
                      onLoadFilterPreset={(presetId) => {
                        const savedSearch = state.savedSearches.find(s => s.id === presetId);
                        if (savedSearch) {
                          handleFilterChange(savedSearch.filters);
                        }
                      }}
                      filterPresets={state.savedSearches}
                      isPersistent={true}
                      showSavePreset={true}
                      showLoadPreset={true}
                    />
                  </div>
                </SheetContent>
              </Sheet>
            )}

            {/* History and Saved Searches */}
            {(showHistory || showSavedSearches) && (
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="ghost">
                    <History className="w-4 h-4 mr-2" />
                    Historial
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Búsquedas recientes</DialogTitle>
                    <DialogDescription>
                      Accede a tus búsquedas anteriores y búsquedas guardadas
                    </DialogDescription>
                  </DialogHeader>
                  
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="search">Historial</TabsTrigger>
                      <TabsTrigger value="saved">Guardadas</TabsTrigger>
                    </TabsList>
                    
                    <TabsContent value="search" className="mt-4">
                      <SearchHistory
                        history={searchHistory}
                        onSelectItem={handleLoadHistoryItem}
                        onClearHistory={clearHistory}
                        onRemoveItem={removeHistoryItem}
                      />
                    </TabsContent>
                    
                    <TabsContent value="saved" className="mt-4">
                      <SavedSearches
                        savedSearches={savedSearches}
                        onSelectSearch={handleLoadSavedSearch}
                        onDeleteSearch={deleteSavedSearch}
                      />
                    </TabsContent>
                  </Tabs>
                </DialogContent>
              </Dialog>
            )}

            {/* Clear Search */}
            {hasActiveSearch && (
              <Button variant="ghost" onClick={clearSearch}>
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Search Stats */}
          {hasActiveSearch && (
            <div className="flex items-center gap-4 mt-4 text-sm text-muted-foreground">
              {query && (
                <>
                  <span>
                    Búsqueda: "<strong>{query}</strong>"
                  </span>
                  <span>•</span>
                </>
              )}
              
              {!isSearching && results.length > 0 && (
                <>
                  <span>
                    {totalResults.toLocaleString()} resultados
                  </span>
                  <span>•</span>
                  <span>
                    {searchTime}ms
                  </span>
                  <span>•</span>
                </>
              )}
              
              {activeFiltersCount > 0 && (
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {activeFiltersCount} filtros activos
                  </Badge>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={handleClearFilters}
                    className="h-6 px-2 text-xs"
                  >
                    <RotateCcw className="w-3 h-3 mr-1" />
                    Limpiar
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Search Results */}
      <div className="container mx-auto px-4 py-6">
        {isSearching && results.length === 0 && (
          <SearchSkeleton count={6} />
        )}

        {error && (
          <Card className="border-destructive">
            <CardContent className="pt-6">
              <div className="text-center">
                <p className="text-destructive font-medium">Error en la búsqueda</p>
                <p className="text-muted-foreground mt-1">{error}</p>
                <Button 
                  variant="outline" 
                  onClick={() => search(query, filters)}
                  className="mt-4"
                >
                  Intentar de nuevo
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {results.length > 0 && (
          <SearchResults
            results={results}
            isLoading={isSearching && hasMore}
            hasMore={hasMore}
            onLoadMore={loadMore}
            highlightTerms={highlightTerms}
            searchQuery={query}
            onSaveArticle={(article) => {
              // TODO: Implement save article functionality
              console.log('Save article:', article.id);
            }}
            onShareArticle={(article) => {
              // TODO: Implement share article functionality
              console.log('Share article:', article.id);
            }}
            onLikeArticle={(article) => {
              // TODO: Implement like article functionality
              console.log('Like article:', article.id);
            }}
            onViewArticle={onArticleClick}
          />
        )}

        {/* Empty State */}
        {!isSearching && results.length === 0 && query && !error && (
          <div className="text-center py-12">
            <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              No se encontraron resultados
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Prueba con diferentes términos de búsqueda o ajusta los filtros
            </p>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Sugerencias:</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {['inteligencia artificial', 'tecnología', 'ciencia', 'salud'].map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="outline"
                    size="sm"
                    onClick={() => handleSearch(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Welcome State */}
        {!query && !isSearching && results.length === 0 && (
          <div className="text-center py-16">
            <div className="max-w-2xl mx-auto">
              <Search className="w-16 h-16 text-gray-400 mx-auto mb-6" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                Encuentra las últimas noticias
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-8">
                Busca en miles de artículos de noticias con nuestro motor de búsqueda inteligente 
                potenciado por IA. Encuentra exactamente lo que buscas con filtros avanzados y 
                análisis de sentimientos.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                <Card>
                  <CardHeader>
                    <Search className="w-8 h-8 text-blue-600 mb-2" />
                    <CardTitle className="text-base">Búsqueda inteligente</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Autocompletado, sugerencias y búsqueda semántica
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <Filter className="w-8 h-8 text-green-600 mb-2" />
                    <CardTitle className="text-base">Filtros avanzados</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Por fecha, fuente, categoría y mucho más
                    </p>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader>
                    <Settings className="w-8 h-8 text-purple-600 mb-2" />
                    <CardTitle className="text-base">Análisis de IA</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Insights de IA y análisis de sentimientos
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};