import React, { useState, useCallback } from 'react';
import { SearchInterface } from '../components/search';
import { SearchResult } from '../components/search/types';

export default function SearchPage() {
  const [selectedArticle, setSelectedArticle] = useState<SearchResult | null>(null);

  const handleArticleClick = useCallback((article: SearchResult) => {
    setSelectedArticle(article);
    // Aquí podrías navegar a una página de detalle del artículo
    console.log('Article clicked:', article);
  }, []);

  const handleSearch = useCallback((query: string) => {
    console.log('Searching for:', query);
    // Aquí podrías enviar eventos de analytics
  }, []);

  const handleFilterChange = useCallback((filters: any) => {
    console.log('Filters changed:', filters);
    // Aquí podrías enviar eventos de analytics
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Búsqueda de Noticias IA</h1>
          <p className="text-muted-foreground">
            Encuentra las últimas noticias con nuestro motor de búsqueda inteligente
          </p>
        </div>
      </header>
      
      {/* Main Search Interface */}
      <main className="container mx-auto px-4 py-8">
        <SearchInterface 
          showSavedSearches={true}
          showHistory={true}
          showFilters={true}
          initialQuery=""
          onArticleClick={handleArticleClick}
        />
      </main>

      {/* Footer con información adicional */}
      <footer className="border-t mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-semibold mb-4">Características</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Búsqueda inteligente con IA</li>
                <li>• Filtros avanzados persistentes</li>
                <li>• Historial de búsquedas</li>
                <li>• Búsquedas guardadas</li>
                <li>• Análisis de sentimientos</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Tecnologías</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• React + TypeScript</li>
                <li>• Tailwind CSS</li>
                <li>• React Router</li>
                <li>• LocalStorage</li>
                <li>• Debounced search</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold mb-4">Estado del Sistema</h3>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Sistema de búsqueda activo</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Filtros persistentes</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>URL state management</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Loading skeletons</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}