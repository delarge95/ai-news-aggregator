import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Hook personalizado para búsquedas con debounce optimizado
 * @param delay - Tiempo de retraso en ms (por defecto 300ms)
 * @param maxWait - Tiempo máximo de espera en ms para ejecutar búsqueda forzada
 */
export const useDebouncedSearch = <T>(
  searchFunction: (query: string, ...args: any[]) => Promise<T> | void,
  delay: number = 300,
  maxWait: number = 2000
) => {
  const [query, setQuery] = useState<string>('');
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [lastSearchTime, setLastSearchTime] = useState<number>(0);
  
  const debounceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const maxWaitTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const searchPromiseRef = useRef<Promise<any> | null>(null);

  // Función para limpiar timeouts
  const clearTimeouts = useCallback(() => {
    if (debounceTimeoutRef.current) {
      clearTimeout(debounceTimeoutRef.current);
      debounceTimeoutRef.current = null;
    }
    if (maxWaitTimeoutRef.current) {
      clearTimeout(maxWaitTimeoutRef.current);
      maxWaitTimeoutRef.current = null;
    }
  }, []);

  // Función para cancelar la búsqueda anterior
  const cancelPreviousSearch = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (searchPromiseRef.current) {
      // No podemos cancelar promises en curso, pero marcamos que fueron cancelados
      searchPromiseRef.current = null;
    }
  }, []);

  // Función principal de búsqueda con debounce
  const debouncedSearch = useCallback(
    (searchQuery: string, ...args: any[]) => {
      const now = Date.now();
      setQuery(searchQuery);
      setLastSearchTime(now);

      // Limpiar timeouts anteriores
      clearTimeouts();
      cancelPreviousSearch();

      // Si la consulta está vacía, limpiar estado
      if (!searchQuery.trim()) {
        setIsSearching(false);
        return;
      }

      // Crear nuevo AbortController para esta búsqueda
      abortControllerRef.current = new AbortController();

      // Función para ejecutar la búsqueda
      const executeSearch = () => {
        setIsSearching(true);
        
        const searchPromise = searchFunction(searchQuery, ...args, {
          signal: abortControllerRef.current?.signal,
        });
        
        searchPromiseRef.current = searchPromise;

        if (searchPromise && typeof searchPromise.then === 'function') {
          return searchPromise
            .then(() => {
              if (searchPromiseRef.current === searchPromise) {
                setIsSearching(false);
              }
            })
            .catch((error) => {
              if (error.name === 'AbortError') {
                console.log('Búsqueda cancelada:', searchQuery);
                return;
              }
              console.error('Error en búsqueda:', error);
              setIsSearching(false);
            });
        } else {
          // Si no es una promesa, la búsqueda es síncrona
          setIsSearching(false);
        }
      };

      // Configurar timeout de debounce
      debounceTimeoutRef.current = setTimeout(executeSearch, delay);

      // Configurar timeout de máximo espera
      if (maxWait > delay) {
        maxWaitTimeoutRef.current = setTimeout(() => {
          if (Date.now() - now >= maxWait - delay) {
            executeSearch();
          }
        }, maxWait);
      }
    },
    [searchFunction, delay, maxWait, clearTimeouts, cancelPreviousSearch]
  );

  // Función para búsqueda inmediata (sin debounce)
  const immediateSearch = useCallback(
    (searchQuery: string, ...args: any[]) => {
      clearTimeouts();
      setQuery(searchQuery);
      
      if (!searchQuery.trim()) {
        setIsSearching(false);
        return;
      }

      cancelPreviousSearch();
      abortControllerRef.current = new AbortController();
      
      setIsSearching(true);
      const searchPromise = searchFunction(searchQuery, ...args, {
        signal: abortControllerRef.current?.signal,
      });
      
      searchPromiseRef.current = searchPromise;

      if (searchPromise && typeof searchPromise.then === 'function') {
        return searchPromise
          .then(() => {
            if (searchPromiseRef.current === searchPromise) {
              setIsSearching(false);
            }
          })
          .catch((error) => {
            if (error.name === 'AbortError') {
              return;
            }
            console.error('Error en búsqueda inmediata:', error);
            setIsSearching(false);
          });
      } else {
        setIsSearching(false);
      }
    },
    [searchFunction, clearTimeouts, cancelPreviousSearch]
  );

  // Función para limpiar la búsqueda
  const clearSearch = useCallback(() => {
    clearTimeouts();
    cancelPreviousSearch();
    setQuery('');
    setIsSearching(false);
  }, [clearTimeouts, cancelPreviousSearch]);

  // Función para obtener sugerencias con debounce
  const getSuggestions = useCallback(
    async (query: string, suggestionFunction: (q: string) => Promise<any[]>): Promise<any[]> => {
      if (query.length < 2) return [];
      
      try {
        const suggestions = await suggestionFunction(query);
        return suggestions;
      } catch (error) {
        console.error('Error obteniendo sugerencias:', error);
        return [];
      }
    },
    []
  );

  // Cleanup al desmontar el componente
  useEffect(() => {
    return () => {
      clearTimeouts();
      cancelPreviousSearch();
    };
  }, [clearTimeouts, cancelPreviousSearch]);

  // Estadísticas de la búsqueda actual
  const searchStats = {
    query,
    isSearching,
    lastSearchTime,
    hasQuery: query.length > 0,
    timeSinceLastSearch: Date.now() - lastSearchTime,
  };

  return {
    query,
    isSearching,
    searchStats,
    debouncedSearch,
    immediateSearch,
    clearSearch,
    getSuggestions,
    // Funciones de control
    cancel: cancelPreviousSearch,
    setQuery,
    setIsSearching,
  };
};