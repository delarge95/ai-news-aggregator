import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { SearchInterface } from '../components/search';
import { SearchDemo } from '../pages/SearchDemo';
import { Home } from '../pages/Home';
import { News } from '../pages/News';
import { Profile } from '../pages/Profile';
import { NotFound } from '../pages/NotFound';
import { Layout } from '../components/layout/Layout';

/**
 * Configuración de rutas del sistema
 * Ejemplo de cómo integrar el sistema de búsqueda con React Router
 */

export const AppRoutes: React.FC = () => {
  return (
    <Router>
      <Layout>
        <Routes>
          {/* Página principal */}
          <Route path="/" element={<Home />} />
          
          {/* Página de noticias con sistema de búsqueda integrado */}
          <Route 
            path="/news" 
            element={
              <NewsSearchPage />
            } 
          />
          
          {/* Demo del sistema de búsqueda completo */}
          <Route 
            path="/search-demo" 
            element={
              <div className="min-h-screen bg-background">
                <SearchDemo />
              </div>
            } 
          />
          
          {/* Página de perfil */}
          <Route path="/profile" element={<Profile />} />
          
          {/* Redirecciones para compatibilidad */}
          <Route 
            path="/search" 
            element={<Navigate to="/news" replace />} 
          />
          <Route 
            path="/buscar" 
            element={<Navigate to="/news" replace />} 
          />
          
          {/* Página 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </Router>
  );
};

/**
 * Componente específico para la página de noticias con búsqueda
 * Demostración de integración completa del sistema de búsqueda
 */
const NewsSearchPage: React.FC = () => {
  const handleArticleClick = (article: any) => {
    // Abrir artículo en nueva pestaña
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  const handleSearch = (query: string) => {
    console.log('Búsqueda realizada:', query);
    // Aquí podrías enviar eventos de analytics
    // analytics.track('search_performed', { query, timestamp: new Date() });
  };

  const handleFilterChange = (filters: any) => {
    console.log('Filtros modificados:', filters);
    // Aquí podrías enviar eventos de analytics
    // analytics.track('filters_applied', { filters, timestamp: new Date() });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header específico para noticias */}
      <header className="bg-white dark:bg-gray-900 border-b">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Noticias con IA
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Búsqueda inteligente en miles de artículos de noticias
              </p>
            </div>
            <div className="hidden md:flex items-center gap-4">
              <div className="text-right">
                <div className="text-sm text-gray-500">Motor de búsqueda</div>
                <div className="text-xs text-blue-600 font-medium">Potenciado por IA</div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Sistema de búsqueda principal */}
      <main className="py-8">
        <SearchInterface
          showSavedSearches={true}
          showHistory={true}
          showFilters={true}
          initialQuery=""
          onArticleClick={handleArticleClick}
          className="max-w-none"
        />
      </main>

      {/* Footer informativo */}
      <footer className="bg-gray-50 dark:bg-gray-900 border-t mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <h3 className="font-semibold mb-4">Sobre la búsqueda</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Nuestro sistema de búsqueda utiliza inteligencia artificial para 
                encontrar las noticias más relevantes para ti.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Características</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Búsqueda en tiempo real</li>
                <li>• Filtros avanzados</li>
                <li>• Análisis de sentimientos</li>
                <li>• Insights de IA</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Datos</h3>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>• Miles de fuentes</li>
                <li>• Actualización constante</li>
                <li>• Categorías variadas</li>
                <li>• Múltiples idiomas</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Estado del sistema</h3>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Sistema activo</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">IA funcionando</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-gray-600 dark:text-gray-400">Filtros activos</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

/**
 * Hook para configurar rutas de búsqueda específicas
 * Útil para componentes que necesitan navegación programática
 */
export const useSearchNavigation = () => {
  const navigate = useSearchNavigationHelper();

  const goToSearch = React.useCallback((query?: string, filters?: any) => {
    const params = new URLSearchParams();
    
    if (query) {
      params.set('q', query);
    }
    
    if (filters) {
      if (filters.category) {
        params.set('category', filters.category);
      }
      if (filters.language && filters.language !== 'all') {
        params.set('lang', filters.language);
      }
      if (filters.dateRange?.start) {
        params.set('date_start', filters.dateRange.start.toISOString());
      }
    }

    navigate(`/news?${params.toString()}`);
  }, [navigate]);

  const goToSearchWithSavedFilters = React.useCallback((savedSearch: any) => {
    goToSearch(savedSearch.query, savedSearch.filters);
  }, [goToSearch]);

  return {
    goToSearch,
    goToSearchWithSavedFilters,
  };
};

/**
 * Helper para navegación
 */
const useSearchNavigationHelper = () => {
  const navigate = React.useCallback((path: string) => {
    // Aquí implementarías la navegación real
    // Por ejemplo con useNavigate de React Router
    window.location.href = path;
  }, []);

  return navigate;
};

/**
 * Componente para breadcrumbs de búsqueda
 */
export const SearchBreadcrumbs: React.FC<{
  query?: string;
  filters?: any;
  onClearSearch?: () => void;
}> = ({ query, filters, onClearSearch }) => {
  const breadcrumbItems = [];

  if (query) {
    breadcrumbItems.push({
      label: `Búsqueda: "${query}"`,
      href: `/news?q=${encodeURIComponent(query)}`
    });
  }

  if (filters) {
    const activeFilters = [];
    if (filters.category) activeFilters.push(filters.category);
    if (filters.language && filters.language !== 'all') activeFilters.push(`Idioma: ${filters.language}`);
    
    if (activeFilters.length > 0) {
      breadcrumbItems.push({
        label: `Filtros: ${activeFilters.join(', ')}`,
        href: '#'
      });
    }
  }

  if (breadcrumbItems.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
      <a href="/news" className="hover:text-blue-600">Noticias</a>
      {breadcrumbItems.map((item, index) => (
        <React.Fragment key={index}>
          <span>/</span>
          <span className={index === breadcrumbItems.length - 1 ? 'text-gray-900 dark:text-white' : ''}>
            {item.label}
          </span>
        </React.Fragment>
      ))}
      {onClearSearch && (
        <button
          onClick={onClearSearch}
          className="ml-4 text-xs text-red-600 hover:text-red-800"
        >
          Limpiar búsqueda
        </button>
      )}
    </nav>
  );
};