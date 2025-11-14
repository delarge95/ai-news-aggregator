import { useCallback, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { SearchFilters, SortOption } from '../components/search/types';

/**
 * Hook personalizado para manejo de estado URL en búsquedas
 * Sincroniza los parámetros de búsqueda con la URL y mantiene el estado
 */
export const useSearchURL = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // Parsear parámetros de URL
  const urlState = useMemo(() => {
    const query = searchParams.get('q') || '';
    const page = parseInt(searchParams.get('page') || '1');
    const sort = (searchParams.get('sort') as SortOption) || 'relevance';
    const lang = searchParams.get('lang') || 'all';
    
    // Parsear filtros de fecha
    const dateStart = searchParams.get('date_start');
    const dateEnd = searchParams.get('date_end');
    
    // Parsear arrays
    const sources = searchParams.get('sources')?.split(',').filter(Boolean) || [];
    const categories = searchParams.get('categories')?.split(',').filter(Boolean) || [];
    const authors = searchParams.get('authors')?.split(',').filter(Boolean) || [];
    
    // Parsear rangos
    const minScore = parseInt(searchParams.get('min_score') || '0');
    const maxScore = parseInt(searchParams.get('max_score') || '100');

    return {
      query,
      page,
      sort,
      language: lang,
      filters: {
        dateRange: {
          start: dateStart ? new Date(dateStart) : null,
          end: dateEnd ? new Date(dateEnd) : null,
        },
        sources,
        categories,
        authors,
        language: lang,
        sortBy: sort,
        sortOrder: 'desc' as const,
        minScore,
        maxScore,
      },
    };
  }, [searchParams]);

  // Actualizar URL con nuevos parámetros
  const updateURL = useCallback((
    updates: Partial<{
      query: string;
      page: number;
      sort: SortOption;
      language: string;
      filters: Partial<SearchFilters>;
    }>
  ) => {
    const newParams = new URLSearchParams(searchParams);

    // Actualizar query
    if (updates.query !== undefined) {
      if (updates.query) {
        newParams.set('q', updates.query);
      } else {
        newParams.delete('q');
      }
    }

    // Actualizar página
    if (updates.page !== undefined) {
      if (updates.page > 1) {
        newParams.set('page', updates.page.toString());
      } else {
        newParams.delete('page');
      }
    }

    // Actualizar ordenamiento
    if (updates.sort !== undefined) {
      if (updates.sort !== 'relevance') {
        newParams.set('sort', updates.sort);
      } else {
        newParams.delete('sort');
      }
    }

    // Actualizar idioma
    if (updates.language !== undefined) {
      if (updates.language !== 'all') {
        newParams.set('lang', updates.language);
      } else {
        newParams.delete('lang');
      }
    }

    // Actualizar filtros
    if (updates.filters) {
      const filters = updates.filters;

      // Filtros de fecha
      if (filters.dateRange) {
        if (filters.dateRange.start) {
          newParams.set('date_start', filters.dateRange.start.toISOString());
        } else {
          newParams.delete('date_start');
        }

        if (filters.dateRange.end) {
          newParams.set('date_end', filters.dateRange.end.toISOString());
        } else {
          newParams.delete('date_end');
        }
      }

      // Arrays de filtros
      if (filters.sources !== undefined) {
        if (filters.sources.length > 0) {
          newParams.set('sources', filters.sources.join(','));
        } else {
          newParams.delete('sources');
        }
      }

      if (filters.categories !== undefined) {
        if (filters.categories.length > 0) {
          newParams.set('categories', filters.categories.join(','));
        } else {
          newParams.delete('categories');
        }
      }

      if (filters.authors !== undefined) {
        if (filters.authors.length > 0) {
          newParams.set('authors', filters.authors.join(','));
        } else {
          newParams.delete('authors');
        }
      }

      // Rangos de puntuación
      if (filters.minScore !== undefined) {
        if (filters.minScore > 0) {
          newParams.set('min_score', filters.minScore.toString());
        } else {
          newParams.delete('min_score');
        }
      }

      if (filters.maxScore !== undefined) {
        if (filters.maxScore < 100) {
          newParams.set('max_score', filters.maxScore.toString());
        } else {
          newParams.delete('max_score');
        }
      }

      // Idioma en filtros
      if (filters.language !== undefined) {
        if (filters.language !== 'all') {
          newParams.set('lang', filters.language);
        } else {
          newParams.delete('lang');
        }
      }

      // Ordenamiento en filtros
      if (filters.sortBy !== undefined) {
        if (filters.sortBy !== 'relevance') {
          newParams.set('sort', filters.sortBy);
        } else {
          newParams.delete('sort');
        }
      }
    }

    // Navegar con nuevos parámetros
    navigate(
      { search: newParams.toString() },
      { 
        replace: true,
        preventScrollReset: false,
      }
    );
  }, [searchParams, navigate]);

  // Funciones específicas para operaciones comunes
  const setQuery = useCallback((query: string) => {
    updateURL({ query });
  }, [updateURL]);

  const setPage = useCallback((page: number) => {
    updateURL({ page });
  }, [updateURL]);

  const setSort = useCallback((sort: SortOption) => {
    updateURL({ sort });
  }, [updateURL]);

  const setLanguage = useCallback((language: string) => {
    updateURL({ language });
  }, [updateURL]);

  const setFilters = useCallback((filters: Partial<SearchFilters>) => {
    updateURL({ filters });
  }, [updateURL]);

  // Funciones para navegar entre páginas
  const nextPage = useCallback(() => {
    setPage(urlState.page + 1);
  }, [urlState.page, setPage]);

  const previousPage = useCallback(() => {
    if (urlState.page > 1) {
      setPage(urlState.page - 1);
    }
  }, [urlState.page, setPage]);

  // Función para limpiar todos los filtros
  const clearFilters = useCallback(() => {
    const newParams = new URLSearchParams();
    const query = urlState.query;
    
    if (query) {
      newParams.set('q', query);
    }

    navigate(
      { search: newParams.toString() },
      { replace: true }
    );
  }, [navigate, urlState.query]);

  // Función para compartir URL actual
  const getShareableURL = useCallback(() => {
    return window.location.href;
  }, []);

  // Función para obtener parámetros serializados para API
  const getAPIFilters = useCallback(() => {
    const apiFilters: any = {};

    // Idioma
    if (urlState.language !== 'all') {
      apiFilters.language = urlState.language;
    }

    // Fechas
    if (urlState.filters.dateRange.start) {
      apiFilters.date_start = urlState.filters.dateRange.start.toISOString();
    }
    if (urlState.filters.dateRange.end) {
      apiFilters.date_end = urlState.filters.dateRange.end.toISOString();
    }

    // Arrays
    if (urlState.filters.sources.length > 0) {
      apiFilters.sources = urlState.filters.sources;
    }
    if (urlState.filters.categories.length > 0) {
      apiFilters.categories = urlState.filters.categories;
    }
    if (urlState.filters.authors.length > 0) {
      apiFilters.authors = urlState.filters.authors;
    }

    // Rangos
    if (urlState.filters.minScore > 0) {
      apiFilters.min_score = urlState.filters.minScore;
    }
    if (urlState.filters.maxScore < 100) {
      apiFilters.max_score = urlState.filters.maxScore;
    }

    return apiFilters;
  }, [urlState]);

  // Detectar si hay filtros activos
  const hasActiveFilters = useMemo(() => {
    const filters = urlState.filters;
    return !!(
      filters.dateRange.start ||
      filters.sources.length > 0 ||
      filters.categories.length > 0 ||
      filters.authors.length > 0 ||
      filters.language !== 'all' ||
      filters.minScore > 0 ||
      filters.maxScore < 100
    );
  }, [urlState.filters]);

  // Obtener conteo de filtros activos
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    const filters = urlState.filters;
    
    if (filters.dateRange.start) count++;
    if (filters.sources.length > 0) count++;
    if (filters.categories.length > 0) count++;
    if (filters.authors.length > 0) count++;
    if (filters.language !== 'all') count++;
    if (filters.minScore > 0) count++;
    if (filters.maxScore < 100) count++;
    
    return count;
  }, [urlState.filters]);

  return {
    // Estado actual
    urlState,
    hasActiveFilters,
    activeFiltersCount,

    // Actualizaciones
    updateURL,
    setQuery,
    setPage,
    setSort,
    setLanguage,
    setFilters,

    // Navegación
    nextPage,
    previousPage,
    clearFilters,

    // Utilidades
    getShareableURL,
    getAPIFilters,
  };
};