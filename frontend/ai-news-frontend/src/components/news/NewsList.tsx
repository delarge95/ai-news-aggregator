import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Grid3X3, 
  List, 
  RefreshCw, 
  AlertCircle, 
  ChevronLeft, 
  ChevronRight,
  Loader2,
  Search,
  Filter,
  SortAsc
} from 'lucide-react';
import { useIsMobile } from '@/hooks/use-mobile';
import NewsCard from './NewsCard';
import SearchBar from './SearchBar';
import SortControls from './SortControls';
import AdvancedFilters from './AdvancedFilters';
import { 
  NewsArticle, 
  NewsFilters, 
  SortOption, 
  PaginationInfo, 
  AutocompleteSuggestion, 
  FilterPanelState,
  ViewMode 
} from './types';

interface NewsListProps {
  // Datos
  articles: NewsArticle[];
  isLoading: boolean;
  error?: string;
  pagination: PaginationInfo;
  
  // Opciones de vista
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  
  // Búsqueda y filtros
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearchSubmit: (query: string) => void;
  filters: NewsFilters;
  onFiltersChange: (filters: NewsFilters) => void;
  suggestions: AutocompleteSuggestion[];
  onSuggestionSelect: (suggestion: AutocompleteSuggestion) => void;
  
  // Ordenamiento
  sortOption: SortOption;
  onSortChange: (sort: SortOption) => void;
  
  // Panel de filtros
  filterPanelState: FilterPanelState;
  onFilterPanelStateChange: (state: FilterPanelState) => void;
  
  // Opciones disponibles para filtros
  availableSources: string[];
  availableCategories: string[];
  availableTags: string[];
  
  // Acciones
  onLoadMore: () => void;
  onRefresh: () => void;
  onArticleClick?: (article: NewsArticle) => void;
  
  // Configuración
  enableInfiniteScroll?: boolean;
  enableFilters?: boolean;
  enableSearch?: boolean;
  enableSort?: boolean;
  
  className?: string;
}

const NewsList: React.FC<NewsListProps> = ({
  articles,
  isLoading,
  error,
  pagination,
  viewMode,
  onViewModeChange,
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  filters,
  onFiltersChange,
  suggestions,
  onSuggestionSelect,
  sortOption,
  onSortChange,
  filterPanelState,
  onFilterPanelStateChange,
  availableSources,
  availableCategories,
  availableTags,
  onLoadMore,
  onRefresh,
  onArticleClick,
  enableInfiniteScroll = true,
  enableFilters = true,
  enableSearch = true,
  enableSort = true,
  className = "",
}) => {
  const isMobile = useIsMobile();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showFilters, setShowFilters] = useState(!isMobile);
  const sentinelRef = useRef<HTMLDivElement>(null);
  
  // Mock data para búsquedas recientes y populares
  const recentSearches = ['inteligencia artificial', 'machine learning', 'chatgpt'];
  const popularSearches = ['IA', 'OpenAI', 'Google', 'Microsoft', 'Tesla'];

  // Configurar infinite scroll
  useEffect(() => {
    if (!enableInfiniteScroll) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && !isLoading && pagination.hasNext) {
          onLoadMore();
        }
      },
      { threshold: 0.1 }
    );

    const currentSentinel = sentinelRef.current;
    if (currentSentinel) {
      observer.observe(currentSentinel);
    }

    return () => {
      if (currentSentinel) {
        observer.unobserve(currentSentinel);
      }
    };
  }, [enableInfiniteScroll, isLoading, pagination.hasNext, onLoadMore]);

  // Manejar refresh
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await onRefresh();
    setIsRefreshing(false);
  }, [onRefresh]);

  // Cambiar página manualmente
  const changePage = (direction: 'prev' | 'next') => {
    const newPage = direction === 'prev' ? pagination.page - 1 : pagination.page + 1;
    if (direction === 'prev' && pagination.hasPrevious) {
      // Implementar cambio de página manual si no hay infinite scroll
    } else if (direction === 'next' && pagination.hasNext) {
      // Implementar cambio de página manual si no hay infinite scroll
    }
  };

  // Toggle filtros en móvil
  const toggleFilters = () => {
    onFilterPanelStateChange({
      ...filterPanelState,
      isOpen: !filterPanelState.isOpen
    });
  };

  // Generar números de página para paginación manual
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, pagination.page - Math.floor(maxVisible / 2));
    let end = Math.min(pagination.totalPages, start + maxVisible - 1);
    
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }
    
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  if (error) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
        <div className="text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Error al cargar noticias
          </h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={handleRefresh} variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reintentar
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex h-full ${className}`}>
      {/* Panel de filtros lateral */}
      {enableFilters && showFilters && (
        <AdvancedFilters
          filters={filters}
          onFiltersChange={onFiltersChange}
          availableSources={availableSources}
          availableCategories={availableCategories}
          availableTags={availableTags}
          panelState={filterPanelState}
          onPanelStateChange={onFilterPanelStateChange}
        />
      )}

      {/* Contenido principal */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header con controles */}
        <div className="sticky top-0 z-30 bg-white border-b border-gray-200 px-4 py-3 space-y-4">
          {/* Barra de búsqueda */}
          {enableSearch && (
            <SearchBar
              value={searchQuery}
              onChange={onSearchChange}
              onSubmit={onSearchSubmit}
              suggestions={suggestions}
              onSuggestionSelect={onSuggestionSelect}
              isLoading={isLoading}
              recentSearches={recentSearches}
              popularSearches={popularSearches}
            />
          )}

          {/* Controles de vista y filtros */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Toggle filtros en móvil */}
              {enableFilters && (
                <Button
                  variant={showFilters ? "default" : "outline"}
                  size="sm"
                  onClick={toggleFilters}
                  className="lg:hidden"
                >
                  <Filter className="h-4 w-4" />
                </Button>
              )}

              {/* Toggle vista grid/lista */}
              <div className="flex items-center bg-gray-100 rounded-lg p-1">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => onViewModeChange('grid')}
                  className="h-8"
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => onViewModeChange('list')}
                  className="h-8"
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Controles de ordenamiento */}
              {enableSort && (
                <SortControls
                  currentSort={sortOption}
                  onSortChange={onSortChange}
                />
              )}

              {/* Botón refresh */}
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>

          {/* Contadores y estado */}
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center gap-4">
              <span>
                {pagination.total} noticias encontradas
              </span>
              {articles.length > 0 && (
                <span>
                  Mostrando {Math.min(articles.length, pagination.limit)} de {pagination.total}
                </span>
              )}
            </div>
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center gap-2 text-blue-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Cargando...</span>
              </div>
            )}
          </div>
        </div>

        {/* Contenido de noticias */}
        <ScrollArea className="flex-1">
          <div className="p-4">
            {articles.length === 0 && !isLoading ? (
              <div className="text-center py-12">
                <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  No se encontraron noticias
                </h3>
                <p className="text-gray-600 mb-4">
                  Intenta ajustar tus filtros o términos de búsqueda
                </p>
                {enableFilters && (
                  <Button onClick={toggleFilters} variant="outline">
                    <Filter className="h-4 w-4 mr-2" />
                    Mostrar filtros
                  </Button>
                )}
              </div>
            ) : (
              <>
                {/* Grid/Lista de noticias */}
                <div className={
                  viewMode === 'grid' 
                    ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6'
                    : 'space-y-4'
                }>
                  {articles.map((article) => (
                    <NewsCard
                      key={article.id}
                      article={article}
                      viewMode={viewMode}
                      onClick={onArticleClick}
                    />
                  ))}
                </div>

                {/* Loading más contenido */}
                {isLoading && articles.length > 0 && (
                  <div className="flex justify-center py-8">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Cargando más noticias...</span>
                    </div>
                  </div>
                )}

                {/* Sentinel para infinite scroll */}
                {enableInfiniteScroll && pagination.hasNext && (
                  <div ref={sentinelRef} className="h-1" />
                )}

                {/* Paginación manual (si no hay infinite scroll) */}
                {!enableInfiniteScroll && pagination.totalPages > 1 && (
                  <div className="flex justify-center items-center gap-2 mt-8">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => changePage('prev')}
                      disabled={!pagination.hasPrevious}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Anterior
                    </Button>

                    {getPageNumbers().map((page) => (
                      <Button
                        key={page}
                        variant={page === pagination.page ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          // Implementar cambio de página
                        }}
                      >
                        {page}
                      </Button>
                    ))}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => changePage('next')}
                      disabled={!pagination.hasNext}
                    >
                      Siguiente
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}

                {/* Estado final */}
                {!isLoading && !pagination.hasNext && (
                  <div className="text-center py-8 text-gray-600">
                    <p>Has llegado al final de las noticias</p>
                  </div>
                )}
              </>
            )}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
};

export default NewsList;