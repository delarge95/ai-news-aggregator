import React, { useState, useEffect, useCallback } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { 
  NewsList, 
  NewsArticle, 
  NewsFilters, 
  SortOption, 
  PaginationInfo, 
  AutocompleteSuggestion,
  FilterPanelState,
  DEFAULT_SORT_OPTIONS,
  LoadingSkeleton,
  InfiniteScroll,
  ErrorState,
  EmptyState
} from './index';

// Mock data mejorado para demostración
const mockArticles: NewsArticle[] = [
  {
    id: '1',
    title: 'Avances Revolucionarios en Inteligencia Artificial Transforman la Industria Tech Global',
    content: 'Las últimas innovaciones en IA están revolucionando cómo las empresas operan en el siglo XXI...',
    summary: 'Las empresas tecnológicas están implementando soluciones de IA para mejorar la eficiencia operativa y reducir costos.',
    url: 'https://example.com/news/1',
    source: 'TechCrunch',
    author: 'Juan Pérez',
    publishedAt: '2025-11-06T10:30:00Z',
    imageUrl: 'https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800',
    tags: ['IA', 'tecnología', 'innovación', 'empresas'],
    category: 'Tecnología',
    aiMetadata: {
      sentiment: 'positive',
      confidence: 85,
      keywords: ['inteligencia artificial', 'industria', 'tecnología', 'eficiencia'],
      entities: {
        organization: ['TechCrunch', 'Microsoft', 'Google'],
        person: ['Juan Pérez', 'Satya Nadella'],
        location: ['Silicon Valley']
      },
      relevanceScore: 92,
      topic: ['Inteligencia Artificial', 'Tecnología', 'Negocios'],
      readability: 78,
      language: 'es'
    }
  },
  {
    id: '2',
    title: 'Nuevos Desarrollos en Machine Learning Automático Alcanzan Precisión Record',
    content: 'Los algoritmos de ML automático están alcanzando nuevos niveles de precisión en tareas complejas...',
    summary: 'Investigadores de universidades prestigiosas presentan avances significativos en aprendizaje automático.',
    url: 'https://example.com/news/2',
    source: 'MIT Technology Review',
    author: 'María García',
    publishedAt: '2025-11-06T09:15:00Z',
    imageUrl: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800',
    tags: ['machine learning', 'investigación', 'algoritmos', 'precisión'],
    category: 'Investigación',
    aiMetadata: {
      sentiment: 'neutral',
      confidence: 76,
      keywords: ['machine learning', 'algoritmos', 'precisión', 'investigación'],
      entities: {
        organization: ['MIT Technology Review', 'Stanford University'],
        person: ['María García', 'Andrew Ng']
      },
      relevanceScore: 88,
      topic: ['Machine Learning', 'Investigación', 'Ciencia'],
      readability: 82,
      language: 'es'
    }
  },
  {
    id: '3',
    title: 'OpenAI Anuncia Capacidades Revolucionarias en GPT-5 para Generación de Texto',
    content: 'La última versión de GPT promete revolucionar la generación de texto con capacidades sin precedentes...',
    summary: 'OpenAI presenta innovaciones en su modelo de lenguaje más avanzado con capacidades multimodales.',
    url: 'https://example.com/news/3',
    source: 'The Verge',
    author: 'Carlos López',
    publishedAt: '2025-11-06T08:00:00Z',
    tags: ['OpenAI', 'GPT', 'texto', 'multimodal'],
    category: 'Tecnología',
    aiMetadata: {
      sentiment: 'positive',
      confidence: 91,
      keywords: ['OpenAI', 'GPT', 'generación de texto', 'multimodal'],
      entities: {
        organization: ['OpenAI', 'The Verge'],
        person: ['Carlos López', 'Sam Altman']
      },
      relevanceScore: 95,
      topic: ['OpenAI', 'GPT', 'IA Generativa'],
      readability: 85,
      language: 'es'
    }
  },
  {
    id: '4',
    title: 'Startups de IA Reciben Inversión Récord de $2.5 Billones en 2024',
    content: 'El ecosistema de startups de inteligencia artificial continúa expandiéndose con inversiones históricas...',
    summary: 'Los inversores muestran confianza creciente en el potencial de la IA para transformar múltiples industrias.',
    url: 'https://example.com/news/4',
    source: 'Forbes',
    author: 'Ana Martín',
    publishedAt: '2025-11-06T07:45:00Z',
    tags: ['startups', 'inversión', 'IA', 'ecosistema'],
    category: 'Negocios',
    aiMetadata: {
      sentiment: 'positive',
      confidence: 89,
      keywords: ['startups', 'inversión', 'IA', 'ecosistema'],
      entities: {
        organization: ['Forbes', 'Sequoia Capital'],
        person: ['Ana Martín']
      },
      relevanceScore: 87,
      topic: ['Inversión', 'Startups', 'IA'],
      readability: 79,
      language: 'es'
    }
  },
  {
    id: '5',
    title: 'Problemas Éticos en IA: Expertos Advierten sobre Sesgos Algorítmicos',
    content: 'Investigadores señalan la importancia de abordar los sesgos en sistemas de inteligencia artificial...',
    summary: 'La comunidad científica insta a desarrollar frameworks éticos más robustos para el desarrollo de IA.',
    url: 'https://example.com/news/5',
    source: 'Nature',
    author: 'Dr. Roberto Silva',
    publishedAt: '2025-11-06T06:30:00Z',
    tags: ['ética', 'sesgos', 'algoritmos', 'responsabilidad'],
    category: 'Ciencia',
    aiMetadata: {
      sentiment: 'negative',
      confidence: 72,
      keywords: ['ética', 'sesgos', 'algoritmos', 'responsabilidad'],
      entities: {
        organization: ['Nature', 'AI Ethics Institute'],
        person: ['Dr. Roberto Silva']
      },
      relevanceScore: 84,
      topic: ['Ética IA', 'Sesgos', 'Responsabilidad'],
      readability: 88,
      language: 'es'
    }
  }
];

const mockSuggestions: AutocompleteSuggestion[] = [
  { value: 'inteligencia artificial', label: 'Inteligencia Artificial', type: 'keyword', count: 45 },
  { value: 'machine learning', label: 'Machine Learning', type: 'keyword', count: 32 },
  { value: 'OpenAI', label: 'OpenAI', type: 'source', count: 28 },
  { value: 'ChatGPT', label: 'ChatGPT', type: 'keyword', count: 22 },
  { value: 'tecnología', label: 'Tecnología', type: 'category', count: 67 },
  { value: 'GPT-5', label: 'GPT-5', type: 'keyword', count: 15 },
  { value: 'ética IA', label: 'Ética en IA', type: 'topic', count: 12 },
  { value: 'startups', label: 'Startups', type: 'category', count: 18 }
];

const mockSources = ['TechCrunch', 'MIT Technology Review', 'The Verge', 'Wired', 'Ars Technica', 'Forbes', 'Nature', 'Science'];
const mockCategories = ['Tecnología', 'Investigación', 'Ciencia', 'Negocios', 'Salud', 'Educación'];
const mockTags = ['IA', 'machine learning', 'investigación', 'algoritmos', 'tecnología', 'innovación', 'OpenAI', 'GPT', 'ética', 'startups', 'inversión', 'sesgos'];

const NewsExample: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>();
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    limit: 20,
    total: mockArticles.length,
    totalPages: Math.ceil(mockArticles.length / 20),
    hasNext: false,
    hasPrevious: false,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<NewsFilters>({});
  const [sortOption, setSortOption] = useState<SortOption>(DEFAULT_SORT_OPTIONS[0]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [suggestions] = useState<AutocompleteSuggestion[]>(mockSuggestions);
  const [filterPanelState, setFilterPanelState] = useState<FilterPanelState>({
    isOpen: false,
    activeTab: 'date'
  });

  // Simular carga inicial
  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      setArticles(mockArticles);
      setIsLoading(false);
    }, 1500);
  }, []);

  // Filtrar artículos
  const filteredArticles = articles.filter(article => {
    // Filtro de búsqueda
    if (searchQuery && !article.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !article.summary.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase())) &&
        !article.aiMetadata.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()))) {
      return false;
    }

    // Filtros de sentimiento
    if (filters.sentiment && filters.sentiment.length > 0) {
      if (!filters.sentiment.includes(article.aiMetadata.sentiment)) {
        return false;
      }
    }

    // Filtros de fuentes
    if (filters.sources && filters.sources.length > 0) {
      if (!filters.sources.includes(article.source)) {
        return false;
      }
    }

    // Filtros de relevancia
    if (filters.relevanceRange) {
      const score = article.aiMetadata.relevanceScore;
      if (score < filters.relevanceRange.min || score > filters.relevanceRange.max) {
        return false;
      }
    }

    // Filtros de categoría
    if (filters.categories && filters.categories.length > 0) {
      if (!filters.categories.includes(article.category)) {
        return false;
      }
    }

    // Filtros de tags
    if (filters.tags && filters.tags.length > 0) {
      if (!filters.tags.some(tag => article.tags.includes(tag))) {
        return false;
      }
    }

    // Filtros de idioma
    if (filters.languages && filters.languages.length > 0) {
      if (!filters.languages.includes(article.aiMetadata.language)) {
        return false;
      }
    }

    return true;
  });

  // Ordenar artículos
  const sortedArticles = [...filteredArticles].sort((a, b) => {
    let aValue, bValue;
    
    switch (sortOption.field) {
      case 'publishedAt':
        aValue = new Date(a.publishedAt);
        bValue = new Date(b.publishedAt);
        break;
      case 'relevanceScore':
        aValue = a.aiMetadata.relevanceScore;
        bValue = b.aiMetadata.relevanceScore;
        break;
      case 'title':
        aValue = a.title;
        bValue = b.title;
        break;
      case 'source':
        aValue = a.source;
        bValue = b.source;
        break;
      default:
        return 0;
    }

    if (aValue < bValue) return sortOption.direction === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortOption.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const handleSearchSubmit = useCallback((query: string) => {
    setSearchQuery(query);
    setIsLoading(true);
    
    // Simular búsqueda con delay
    setTimeout(() => {
      setIsLoading(false);
      setPagination(prev => ({
        ...prev,
        total: sortedArticles.length,
        totalPages: Math.ceil(sortedArticles.length / prev.limit),
        hasNext: sortedArticles.length > prev.limit,
        hasPrevious: prev.page > 1,
      }));
    }, 800);
  }, [sortedArticles.length]);

  const handleFiltersChange = useCallback((newFilters: NewsFilters) => {
    setFilters(newFilters);
  }, []);

  const handleSortChange = useCallback((newSort: SortOption) => {
    setSortOption(newSort);
  }, []);

  const handleSuggestionSelect = useCallback((suggestion: AutocompleteSuggestion) => {
    if (suggestion.type === 'keyword' || suggestion.type === 'source' || suggestion.type === 'category') {
      setSearchQuery(suggestion.value);
    }
  }, []);

  const handleLoadMore = useCallback(() => {
    if (pagination.hasNext) {
      setIsLoading(true);
      setTimeout(() => {
        const moreArticles = mockArticles.map((article, index) => ({
          ...article,
          id: `${article.id}-${Date.now()}-${index}`
        }));
        setArticles(prev => [...prev, ...moreArticles]);
        setPagination(prev => ({
          ...prev,
          total: prev.total + moreArticles.length,
          hasNext: prev.page < 3 // Simular que hay máximo 3 páginas
        }));
        setIsLoading(false);
      }, 1000);
    }
  }, [pagination.hasNext]);

  const handleRefresh = useCallback(() => {
    setIsLoading(true);
    setError(undefined);
    setTimeout(() => {
      setArticles([...mockArticles]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const handleArticleClick = useCallback((article: NewsArticle) => {
    console.log('Artículo clickeado:', article);
    // Aquí puedes manejar el clic en el artículo
    window.open(article.url, '_blank');
  }, []);

  // Manejar errores simulados
  const simulateError = useCallback(() => {
    setError('Error simulado: No se pudieron cargar las noticias');
  }, []);

  // Limpiar filtros
  const handleClearFilters = useCallback(() => {
    setFilters({});
    setSearchQuery('');
  }, []);

  return (
    <ErrorBoundary>
      <div className="h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  🧠 Noticias de Inteligencia Artificial
                </h1>
                <p className="text-gray-600 mt-1">
                  Descubre las últimas noticias sobre IA con filtros avanzados y metadatos inteligentes
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={simulateError}
                  className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200"
                >
                  Simular Error
                </button>
                <button
                  onClick={handleClearFilters}
                  className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                >
                  Limpiar Filtros
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Demo de componentes individuales */}
        <div className="max-w-7xl mx-auto px-4 py-6 space-y-8">
          {/* NewsFilters en modo compacto */}
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">Componente NewsFilters (Compact)</h3>
            <NewsFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              availableSources={mockSources}
              availableCategories={mockCategories}
              availableTags={mockTags}
              compact={true}
              onReset={handleClearFilters}
            />
          </div>

          {/* LoadingSkeleton */}
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="text-lg font-semibold mb-4">LoadingSkeleton</h3>
            <LoadingSkeleton 
              count={3} 
              viewMode="grid" 
              showFilters={true} 
            />
          </div>

          {/* ErrorState examples */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-semibold mb-4">ErrorState (Network)</h3>
              <ErrorState
                type="network"
                title="Sin conexión"
                message="No se puede conectar con el servidor"
                onRetry={handleRefresh}
                variant="card"
              />
            </div>
            <div className="bg-white p-4 rounded-lg border">
              <h3 className="text-lg font-semibold mb-4">EmptyState</h3>
              <EmptyState
                title="No hay resultados"
                message="Intenta ajustar tus filtros o términos de búsqueda"
                onClearFilters={handleClearFilters}
                actionLabel="Explorar todas las noticias"
              />
            </div>
          </div>
        </div>

        {/* Lista principal de noticias */}
        <NewsList
          articles={sortedArticles}
          isLoading={isLoading}
          error={error}
          pagination={pagination}
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSearchSubmit={handleSearchSubmit}
          filters={filters}
          onFiltersChange={handleFiltersChange}
          suggestions={suggestions}
          onSuggestionSelect={handleSuggestionSelect}
          sortOption={sortOption}
          onSortChange={handleSortChange}
          filterPanelState={filterPanelState}
          onFilterPanelStateChange={setFilterPanelState}
          availableSources={mockSources}
          availableCategories={mockCategories}
          availableTags={mockTags}
          onLoadMore={handleLoadMore}
          onRefresh={handleRefresh}
          onArticleClick={handleArticleClick}
          enableInfiniteScroll={true}
          enableFilters={true}
          enableSearch={true}
          enableSort={true}
          className="h-[calc(100vh-400px)]"
        />
      </div>
    </ErrorBoundary>
  );
};

export default NewsExample;