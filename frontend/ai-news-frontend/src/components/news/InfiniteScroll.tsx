import React, { useEffect, useRef, useCallback } from 'react';
import { useInView } from 'react-intersection-observer';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  ChevronDown, 
  Loader2, 
  RefreshCw, 
  AlertCircle,
  Repeat as InfiniteIcon
} from 'lucide-react';

interface InfiniteScrollProps {
  // Función para cargar más datos
  loadMore: () => void;
  
  // Estados
  isLoading: boolean;
  hasNextPage: boolean;
  error?: string | null;
  
  // Configuración
  rootMargin?: string;
  threshold?: number | number[];
  disabled?: boolean;
  
  // Componentes personalizados
  loadingComponent?: React.ReactNode;
  endComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  
  // Estilos y clases
  className?: string;
  loadingClassName?: string;
  errorClassName?: string;
  endClassName?: string;
  
  // Callbacks
  onRetry?: () => void;
  onRefresh?: () => void;
}

// Componente de carga por defecto
const DefaultLoadingComponent: React.FC = () => (
  <div className="flex justify-center py-8">
    <div className="flex items-center gap-3 text-gray-600">
      <Loader2 className="h-5 w-5 animate-spin" />
      <span>Cargando más noticias...</span>
    </div>
  </div>
);

// Componente de error por defecto
const DefaultErrorComponent: React.FC<{ 
  error: string; 
  onRetry?: () => void;
  onRefresh?: () => void;
}> = ({ error, onRetry, onRefresh }) => (
  <div className="flex flex-col items-center justify-center py-8 text-center">
    <AlertCircle className="h-8 w-8 text-red-500 mb-3" />
    <p className="text-gray-700 mb-3">{error}</p>
    <div className="flex gap-2">
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Reintentar
        </Button>
      )}
      {onRefresh && (
        <Button variant="outline" size="sm" onClick={onRefresh}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Recargar todo
        </Button>
      )}
    </div>
  </div>
);

// Componente de fin por defecto
const DefaultEndComponent: React.FC = () => (
  <div className="text-center py-8 text-gray-600">
    <InfiniteIcon className="h-6 w-6 mx-auto mb-2 opacity-50" />
    <p>Has llegado al final de las noticias</p>
  </div>
);

// Componente de sentinel invisible para detectar el scroll
const ScrollSentinel: React.FC<{ 
  hasNextPage: boolean; 
  isLoading: boolean; 
  disabled: boolean;
  rootMargin?: string;
  threshold?: number | number[];
}> = ({ hasNextPage, isLoading, disabled, rootMargin, threshold }) => {
  const { ref, inView } = useInView({
    threshold: threshold ?? 0.1,
    rootMargin: rootMargin ?? '100px',
    skip: disabled || !hasNextPage || isLoading,
  });

  useEffect(() => {
    // El useInView hook manejará automáticamente la detección
    // La función loadMore se llamará desde el componente padre
  }, [inView, hasNextPage, isLoading, disabled]);

  return (
    <div
      ref={ref}
      className="h-1 w-full"
      style={{ minHeight: '1px' }}
    />
  );
};

// Componente de paginación manual como fallback
const ManualPagination: React.FC<{
  hasNextPage: boolean;
  isLoading: boolean;
  onLoadMore: () => void;
  className?: string;
}> = ({ hasNextPage, isLoading, onLoadMore, className }) => (
  <div className={`flex justify-center py-6 ${className || ''}`}>
    <Button
      onClick={onLoadMore}
      disabled={!hasNextPage || isLoading}
      variant="outline"
      className="flex items-center gap-2"
    >
      {isLoading ? (
        <>
          <Loader2 className="h-4 w-4 animate-spin" />
          Cargando...
        </>
      ) : (
        <>
          <ChevronDown className="h-4 w-4" />
          Cargar más
        </>
      )}
    </Button>
  </div>
);

// Hook personalizado para infinite scroll
const useInfiniteScroll = (
  loadMore: () => void,
  hasNextPage: boolean,
  isLoading: boolean,
  disabled: boolean = false
) => {
  const { ref, inView } = useInView({
    threshold: 0.1,
    rootMargin: '100px',
    skip: disabled || !hasNextPage || isLoading,
  });

  useEffect(() => {
    if (inView && hasNextPage && !isLoading && !disabled) {
      loadMore();
    }
  }, [inView, hasNextPage, isLoading, disabled, loadMore]);

  return ref;
};

// Componente principal InfiniteScroll
const InfiniteScroll: React.FC<InfiniteScrollProps> = ({
  loadMore,
  isLoading,
  hasNextPage,
  error = null,
  rootMargin = '100px',
  threshold = 0.1,
  disabled = false,
  loadingComponent,
  endComponent,
  errorComponent,
  emptyComponent,
  className,
  loadingClassName,
  errorClassName,
  endClassName,
  onRetry,
  onRefresh,
}) => {
  const sentinelRef = useInfiniteScroll(loadMore, hasNextPage, isLoading, disabled);

  // Si hay un error, mostrar componente de error
  if (error && errorComponent === undefined) {
    return (
      <div className={errorClassName}>
        <DefaultErrorComponent 
          error={error} 
          onRetry={onRetry}
          onRefresh={onRefresh}
        />
      </div>
    );
  }

  if (error && errorComponent) {
    return <div className={errorClassName}>{errorComponent}</div>;
  }

  // Si se deshabilita el scroll infinito, no mostrar sentinel
  if (disabled) {
    return null;
  }

  return (
    <div className={className}>
      {/* Componente de carga mientras se obtienen datos iniciales */}
      {isLoading && !hasNextPage && !loadingComponent && (
        <div className={loadingClassName}>
          <DefaultLoadingComponent />
        </div>
      )}

      {/* Componente de carga personalizado */}
      {isLoading && !hasNextPage && loadingComponent && (
        <div className={loadingClassName}>
          {loadingComponent}
        </div>
      )}

      {/* Sentinel para detectar scroll */}
      {hasNextPage && (
        <ScrollSentinel
          hasNextPage={hasNextPage}
          isLoading={isLoading}
          disabled={disabled}
          rootMargin={rootMargin}
          threshold={threshold}
        />
      )}

      {/* Componente de fin cuando no hay más datos */}
      {!hasNextPage && !isLoading && !error && (
        <div className={endClassName}>
          {endComponent || <DefaultEndComponent />}
        </div>
      )}

      {/* Indicador de carga adicional cuando ya hay datos */}
      {isLoading && hasNextPage && (
        <div className={loadingClassName}>
          {loadingComponent || <DefaultLoadingComponent />}
        </div>
      )}
    </div>
  );
};

// Componente de carga por lotes para mejor rendimiento
export const BatchInfiniteScroll: React.FC<InfiniteScrollProps & {
  batchSize?: number;
  batchDelay?: number;
}> = ({
  loadMore,
  isLoading,
  hasNextPage,
  error = null,
  batchSize = 10,
  batchDelay = 100,
  disabled = false,
  ...props
}) => {
  const [batchCount, setBatchCount] = React.useState(0);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const handleLoadMore = useCallback(() => {
    if (disabled || isLoading || !hasNextPage) return;

    // Cargar en lotes
    for (let i = 0; i < batchSize; i++) {
      setTimeout(() => {
        loadMore();
      }, i * batchDelay);
    }

    setBatchCount(prev => prev + batchSize);
  }, [loadMore, isLoading, hasNextPage, disabled, batchSize, batchDelay]);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <InfiniteScroll
      {...props}
      loadMore={handleLoadMore}
      isLoading={isLoading}
      hasNextPage={hasNextPage}
      error={error}
      disabled={disabled}
    />
  );
};

// Componente de scroll con paginación manual como fallback
export const HybridInfiniteScroll: React.FC<InfiniteScrollProps & {
  enableManualFallback?: boolean;
  manualPageSize?: number;
}> = ({
  enableManualFallback = true,
  manualPageSize = 10,
  loadMore,
  isLoading,
  hasNextPage,
  error,
  disabled,
  ...props
}) => {
  const [manualMode, setManualMode] = React.useState(false);
  const [loadedItems, setLoadedItems] = React.useState(0);

  const handleLoadMore = useCallback(() => {
    if (manualMode) return;
    loadMore();
  }, [loadMore, manualMode]);

  const handleManualLoadMore = useCallback(() => {
    loadMore();
    setLoadedItems(prev => prev + manualPageSize);
  }, [loadMore, manualPageSize]);

  // Auto-switch a modo manual si falla el infinite scroll
  useEffect(() => {
    if (enableManualFallback && !hasNextPage && loadedItems > 0 && !isLoading) {
      setManualMode(true);
    }
  }, [hasNextPage, loadedItems, isLoading, enableManualFallback]);

  if (manualMode && enableManualFallback) {
    return (
      <>
        <InfiniteScroll
          {...props}
          loadMore={handleManualLoadMore}
          isLoading={isLoading}
          hasNextPage={hasNextPage}
          error={error}
          disabled={true} // Deshabilitar infinite scroll en modo manual
          loadingComponent={
            <ManualPagination
              hasNextPage={hasNextPage}
              isLoading={isLoading}
              onLoadMore={handleManualLoadMore}
            />
          }
        />
      </>
    );
  }

  return (
    <InfiniteScroll
      {...props}
      loadMore={handleLoadMore}
      isLoading={isLoading}
      hasNextPage={hasNextPage}
      error={error}
      disabled={disabled}
    />
  );
};

// Hook para manejar el estado del infinite scroll
export const useInfiniteScrollState = () => {
  const [state, setState] = React.useState({
    isLoading: false,
    hasNextPage: true,
    error: null as string | null,
    loadedCount: 0,
  });

  const updateState = React.useCallback((updates: Partial<typeof state>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  const reset = React.useCallback(() => {
    setState({
      isLoading: false,
      hasNextPage: true,
      error: null,
      loadedCount: 0,
    });
  }, []);

  return {
    ...state,
    updateState,
    reset,
  };
};

export default InfiniteScroll;