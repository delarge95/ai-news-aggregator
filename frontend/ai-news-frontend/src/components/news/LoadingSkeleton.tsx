import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface LoadingSkeletonProps {
  count?: number;
  viewMode?: 'grid' | 'list';
  showFilters?: boolean;
  className?: string;
}

// Skeleton para tarjeta de noticia en vista de lista
const NewsCardListSkeleton: React.FC = () => (
  <Card className="w-full">
    <CardContent className="p-6">
      <div className="flex gap-6">
        {/* Imagen skeleton */}
        <div className="flex-shrink-0">
          <Skeleton className="w-32 h-24 rounded-lg" />
        </div>
        
        {/* Contenido skeleton */}
        <div className="flex-1 min-w-0 space-y-3">
          {/* Título */}
          <div className="space-y-2">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-6 w-1/2" />
          </div>

          {/* Metadatos principales */}
          <div className="flex gap-4">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-5 w-16" />
          </div>

          {/* Metadatos de IA */}
          <div className="flex gap-3">
            <Skeleton className="h-6 w-16 rounded-full" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-4 rounded" />
              <Skeleton className="h-2 w-16" />
              <Skeleton className="h-4 w-8" />
            </div>
            <div className="flex items-center gap-1">
              <Skeleton className="h-4 w-4 rounded" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>

          {/* Resumen */}
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-5/6" />
          </div>

          {/* Tags */}
          <div className="flex gap-1">
            <Skeleton className="h-5 w-16" />
            <Skeleton className="h-5 w-12" />
            <Skeleton className="h-5 w-14" />
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
);

// Skeleton para tarjeta de noticia en vista de grid
const NewsCardGridSkeleton: React.FC = () => (
  <Card className="w-full">
    {/* Imagen skeleton */}
    <div className="relative h-48 overflow-hidden rounded-t-lg">
      <Skeleton className="w-full h-full" />
    </div>

    <CardContent className="p-4 space-y-3">
      {/* Título */}
      <div className="space-y-2">
        <Skeleton className="h-5 w-full" />
        <Skeleton className="h-5 w-3/4" />
      </div>

      {/* Metadatos de IA grid */}
      <div className="grid grid-cols-2 gap-2">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className="h-4 w-12" />
        </div>
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className="h-2 w-12" />
        </div>
      </div>

      {/* Información básica */}
      <div className="space-y-2">
        <div className="flex items-center gap-1">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="flex items-center gap-1">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className="h-4 w-20" />
        </div>
        <div className="flex items-center gap-1">
          <Skeleton className="h-5 w-16" />
        </div>
      </div>

      {/* Resumen */}
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>

      {/* Tags */}
      <div className="flex gap-1">
        <Skeleton className="h-5 w-12" />
        <Skeleton className="h-5 w-16" />
      </div>
    </CardContent>
  </Card>
);

// Skeleton para el panel de filtros
const FilterPanelSkeleton: React.FC = () => (
  <div className="w-80 border-r bg-gray-50/50 h-full">
    {/* Header skeleton */}
    <div className="flex items-center justify-between p-4 border-b">
      <div className="flex items-center gap-2">
        <Skeleton className="h-5 w-5" />
        <Skeleton className="h-5 w-16" />
        <Skeleton className="h-5 w-6 rounded-full" />
      </div>
      <Skeleton className="h-8 w-16" />
    </div>

    {/* Content skeleton */}
    <div className="p-4 space-y-4">
      {/* Tabs skeleton */}
      <div className="flex gap-1">
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-8 w-16" />
        <Skeleton className="h-8 w-20" />
      </div>

      {/* Filter sections skeleton */}
      <div className="space-y-4">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>

        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-2">
              <Skeleton className="h-4 w-4 rounded" />
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-full" />
        </div>
      </div>
    </div>
  </div>
);

// Skeleton para la barra de búsqueda
const SearchBarSkeleton: React.FC = () => (
  <div className="relative w-full max-w-2xl">
    <div className="relative flex items-center">
      <div className="relative flex-1">
        <Skeleton className="pl-10 h-12 w-full rounded-md" />
      </div>
      <Skeleton className="ml-2 h-12 w-20 rounded-md" />
    </div>
  </div>
);

// Skeleton para controles de ordenamiento
const SortControlsSkeleton: React.FC = () => (
  <div className="flex items-center gap-2">
    <Skeleton className="h-10 w-32" />
    <Skeleton className="h-10 w-10" />
  </div>
);

// Skeleton principal para la lista de noticias
const NewsListSkeleton: React.FC<LoadingSkeletonProps> = ({
  count = 6,
  viewMode = 'grid',
  showFilters = true,
  className = "",
}) => {
  return (
    <div className={`flex h-full ${className}`}>
      {/* Panel de filtros skeleton */}
      {showFilters && <FilterPanelSkeleton />}

      {/* Contenido principal skeleton */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header skeleton */}
        <div className="sticky top-0 z-30 bg-white border-b border-gray-200 px-4 py-3 space-y-4">
          <SearchBarSkeleton />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Skeleton className="h-10 w-24" />
              <div className="flex items-center bg-gray-100 rounded-lg p-1">
                <Skeleton className="h-8 w-8 rounded" />
                <Skeleton className="h-8 w-8 rounded" />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <SortControlsSkeleton />
              <Skeleton className="h-10 w-10" />
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>

        {/* Contenido skeleton */}
        <div className="flex-1">
          <div className="p-4">
            <div className={
              viewMode === 'grid' 
                ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6'
                : 'space-y-4'
            }>
              {Array.from({ length: count }).map((_, index) => (
                <div key={index}>
                  {viewMode === 'grid' ? (
                    <NewsCardGridSkeleton />
                  ) : (
                    <NewsCardListSkeleton />
                  )}
                </div>
              ))}
            </div>

            {/* Loading more indicator skeleton */}
            <div className="flex justify-center py-8">
              <div className="flex items-center gap-2 text-gray-600">
                <Skeleton className="h-5 w-5 rounded" />
                <Skeleton className="h-4 w-32" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Skeleton compacto para tarjetas individuales
export const NewsCardSkeleton: React.FC<{ viewMode?: 'grid' | 'list' }> = ({ 
  viewMode = 'grid' 
}) => {
  return viewMode === 'grid' ? <NewsCardGridSkeleton /> : <NewsCardListSkeleton />;
};

// Skeleton para el estado de carga inicial
export const InitialLoadingSkeleton: React.FC = () => (
  <div className="flex items-center justify-center h-64">
    <div className="text-center space-y-4">
      <div className="animate-pulse">
        <Skeleton className="h-12 w-12 rounded-full mx-auto" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-6 w-48 mx-auto" />
        <Skeleton className="h-4 w-32 mx-auto" />
      </div>
    </div>
  </div>
);

// Skeleton para el estado de "cargando más"
export const LoadingMoreSkeleton: React.FC = () => (
  <div className="flex justify-center py-8">
    <div className="flex items-center gap-2 text-gray-600">
      <div className="animate-spin">
        <Skeleton className="h-5 w-5 rounded-full" />
      </div>
      <Skeleton className="h-4 w-32" />
    </div>
  </div>
);

// Skeleton para el estado vacío con búsqueda
export const EmptySearchSkeleton: React.FC = () => (
  <div className="text-center py-12">
    <div className="space-y-4">
      <Skeleton className="h-12 w-12 rounded-full mx-auto" />
      <div className="space-y-2">
        <Skeleton className="h-6 w-64 mx-auto" />
        <Skeleton className="h-4 w-48 mx-auto" />
      </div>
      <Skeleton className="h-10 w-32 mx-auto" />
    </div>
  </div>
);

// Skeleton para el panel de filtros en móvil
export const MobileFilterSkeleton: React.FC = () => (
  <div className="fixed top-4 right-4 z-40">
    <Skeleton className="h-10 w-24 rounded-md" />
  </div>
);

export default NewsListSkeleton;