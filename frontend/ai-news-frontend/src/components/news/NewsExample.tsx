import React, { useCallback, useEffect, useState } from 'react';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import {
  NewsList,
  type NewsArticle,
  type NewsFilters,
  type SortOption,
  type PaginationInfo,
  type AutocompleteSuggestion,
  type FilterPanelState,
  DEFAULT_SORT_OPTIONS,
} from './index';
import { articleService, type Article as ArticleDTO } from '@/services/articleService';

const DEFAULT_PAGE_SIZE = 20;

const EMPTY_PAGINATION: PaginationInfo = {
  page: 1,
  limit: DEFAULT_PAGE_SIZE,
  total: 0,
  totalPages: 0,
  hasNext: false,
  hasPrevious: false,
};

const normalizeTags = (tags: ArticleDTO['topic_tags']): string[] => {
  if (!tags) {
    return [];
  }

  if (Array.isArray(tags)) {
    return tags
      .map((tag) => String(tag).trim())
      .filter(Boolean);
  }

  if (typeof tags === 'string') {
    return tags
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  if (typeof tags === 'object') {
    if ('tags' in tags && Array.isArray((tags as Record<string, unknown>).tags)) {
      return (tags as { tags: unknown[] }).tags
        .map((tag) => String(tag).trim())
        .filter(Boolean);
    }

    return Object.values(tags)
      .flat()
      .map((tag) => String(tag).trim())
      .filter(Boolean);
  }

  return [];
};

const ensureSentiment = (label?: string | null): 'positive' | 'negative' | 'neutral' => {
  if (label === 'positive' || label === 'negative' || label === 'neutral') {
    return label;
  }
  return 'neutral';
};

const toPercentage = (value?: number | null, fallback = 0): number => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return fallback;
  }

  if (value <= 1 && value >= -1) {
    return Math.round((value + 1) * 50); // map [-1,1] to [0,100]
  }

  return Math.round(Math.min(100, Math.max(0, value)));
};

const transformArticle = (article: ArticleDTO): NewsArticle => {
  const tags = normalizeTags(article.topic_tags);
  const publishedAt = article.published_at ?? article.created_at ?? new Date().toISOString();
  const relevance = toPercentage(article.relevance_score);
  const sentimentLabel = ensureSentiment(article.sentiment_label);

  return {
    id: article.id,
    title: article.title || 'Artículo sin título',
    content: article.content ?? '',
    summary:
      article.summary ??
      (article.content ? `${article.content.slice(0, 240)}…` : 'Sin resumen disponible.'),
    url: article.url,
    source: article.source_name ?? 'Fuente desconocida',
    author: undefined,
    publishedAt,
    imageUrl: undefined,
    tags,
    category: tags[0] ?? 'General',
    aiMetadata: {
      sentiment: sentimentLabel,
      confidence: toPercentage(article.sentiment_score, 50),
      keywords: tags,
      entities: {
        organization: article.source_name ? [article.source_name] : undefined,
      },
      relevanceScore: relevance,
      topic: tags.length > 0 ? tags : ['General'],
      readability: 72,
      language: 'en',
    },
  };
};

const NewsExample: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string>();
  const [pagination, setPagination] = useState<PaginationInfo>(EMPTY_PAGINATION);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<NewsFilters>({});
  const [sortOption, setSortOption] = useState<SortOption>(DEFAULT_SORT_OPTIONS[0]);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [filterPanelState, setFilterPanelState] = useState<FilterPanelState>({
    isOpen: false,
    activeTab: 'date',
  });
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  const updateDerivedCollections = useCallback((items: NewsArticle[]) => {
    const sources = new Set<string>();
    const categories = new Set<string>();
    const tags = new Set<string>();
    const suggestionsMap = new Map<string, AutocompleteSuggestion>();

    items.forEach((item) => {
      if (item.source) {
        sources.add(item.source);
        suggestionsMap.set(`source-${item.source}`, {
          value: item.source,
          label: item.source,
          type: 'source',
        });
      }

      if (item.category) {
        categories.add(item.category);
        suggestionsMap.set(`category-${item.category}`, {
          value: item.category,
          label: item.category,
          type: 'category',
        });
      }

      item.tags.forEach((tag) => {
        tags.add(tag);
        suggestionsMap.set(`tag-${tag}`, {
          value: tag,
          label: tag,
          type: 'tag',
        });
      });

      suggestionsMap.set(`keyword-${item.id}`, {
        value: item.title,
        label: item.title,
        type: 'keyword',
      });
    });

    setAvailableSources(Array.from(sources.values()).sort());
    setAvailableCategories(Array.from(categories.values()).sort());
    setAvailableTags(Array.from(tags.values()).sort());
    setSuggestions(Array.from(suggestionsMap.values()).slice(0, 40));
  }, []);

  const fetchArticles = useCallback(
    async ({
      page = 1,
      query,
      append = false,
    }: {
      page?: number;
      query?: string;
      append?: boolean;
    } = {}) => {
      const effectiveQuery = query ?? searchQuery;
      const pageSize = pagination.limit || DEFAULT_PAGE_SIZE;

      if (append) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
      }
      setError(undefined);

      try {
        let response;
        if (effectiveQuery.trim().length > 0) {
          response = await articleService.searchArticles(
            effectiveQuery.trim(),
            page,
            pageSize,
          );
        } else {
          response = await articleService.getArticles(page, pageSize);
        }

        const transformed = response.articles.map(transformArticle);

        setArticles((prev) => {
          const merged = append ? [...prev, ...transformed] : transformed;
          updateDerivedCollections(merged);
          return merged;
        });

        setPagination({
          page: response.page,
          limit: response.per_page,
          total: response.total,
          totalPages: response.pages,
          hasNext: response.has_next,
          hasPrevious: response.has_prev,
        });
      } catch (err) {
        console.error('Error loading articles', err);
        setError('No se pudieron cargar las noticias. Intenta nuevamente.');
      } finally {
        if (append) {
          setIsLoadingMore(false);
        } else {
          setIsLoading(false);
        }
      }
    },
    [pagination.limit, searchQuery, updateDerivedCollections],
  );

  useEffect(() => {
    void fetchArticles({ page: 1 });
  }, [fetchArticles]);

  const filteredArticles = articles.filter((article) => {
    const query = searchQuery.trim().toLowerCase();
    if (
      query &&
      !article.title.toLowerCase().includes(query) &&
      !article.summary.toLowerCase().includes(query) &&
      !article.tags.some((tag) => tag.toLowerCase().includes(query)) &&
      !article.aiMetadata.keywords.some((keyword) => keyword.toLowerCase().includes(query))
    ) {
      return false;
    }

    if (filters.sentiment?.length) {
      if (!filters.sentiment.includes(article.aiMetadata.sentiment)) {
        return false;
      }
    }

    if (filters.sources?.length) {
      if (!filters.sources.includes(article.source)) {
        return false;
      }
    }

    if (filters.relevanceRange) {
      const score = article.aiMetadata.relevanceScore;
      if (
        score < filters.relevanceRange.min ||
        score > filters.relevanceRange.max
      ) {
        return false;
      }
    }

    if (filters.categories?.length) {
      if (!filters.categories.includes(article.category)) {
        return false;
      }
    }

    if (filters.tags?.length) {
      if (!filters.tags.some((tag) => article.tags.includes(tag))) {
        return false;
      }
    }

    if (filters.languages?.length) {
      if (!filters.languages.includes(article.aiMetadata.language)) {
        return false;
      }
    }

    return true;
  });

  const sortedArticles = [...filteredArticles].sort((a, b) => {
    const direction = sortOption.direction === 'asc' ? 1 : -1;

    switch (sortOption.field) {
      case 'publishedAt':
        return (
          (new Date(a.publishedAt).getTime() - new Date(b.publishedAt).getTime()) *
          direction
        );
      case 'relevanceScore':
        return (a.aiMetadata.relevanceScore - b.aiMetadata.relevanceScore) * direction;
      case 'title':
        return a.title.localeCompare(b.title) * direction;
      case 'source':
        return a.source.localeCompare(b.source) * direction;
      default:
        return 0;
    }
  });

  const handleSearchSubmit = useCallback(
    (query: string) => {
      setSearchQuery(query);
      void fetchArticles({ page: 1, query });
    },
    [fetchArticles],
  );

  const handleFiltersChange = useCallback((newFilters: NewsFilters) => {
    setFilters(newFilters);
  }, []);

  const handleSortChange = useCallback((newSort: SortOption) => {
    setSortOption(newSort);
  }, []);

  const handleSuggestionSelect = useCallback(
    (suggestion: AutocompleteSuggestion) => {
      const value = suggestion.value;
      setSearchQuery(value);
      void fetchArticles({ page: 1, query: value });
    },
    [fetchArticles],
  );

  const handleLoadMore = useCallback(() => {
    if (!pagination.hasNext || isLoading || isLoadingMore) {
      return;
    }

    void fetchArticles({
      page: pagination.page + 1,
      query: searchQuery,
      append: true,
    });
  }, [fetchArticles, pagination.hasNext, pagination.page, searchQuery, isLoading, isLoadingMore]);

  const handleRefresh = useCallback(() => {
    return fetchArticles({ page: 1, query: searchQuery });
  }, [fetchArticles, searchQuery]);

  const handleArticleClick = useCallback((article: NewsArticle) => {
    window.open(article.url, '_blank', 'noopener,noreferrer');
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilters({});
    setSearchQuery('');
    void fetchArticles({ page: 1, query: '' });
  }, [fetchArticles]);

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-6 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                🧠 Noticias de Inteligencia Artificial
              </h1>
              <p className="text-gray-600 mt-1">
                Fuentes reales conectadas al backend. Usa la búsqueda y los filtros para explorar.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => void handleRefresh()}
                className="px-3 py-1 text-sm rounded-md bg-gray-900 text-white hover:bg-gray-800 transition"
              >
                Actualizar
              </button>
              <button
                onClick={handleClearFilters}
                className="px-3 py-1 text-sm rounded-md bg-gray-100 text-gray-700 hover:bg-gray-200 transition"
              >
                Limpiar filtros
              </button>
            </div>
          </div>
        </div>

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
          availableSources={availableSources}
          availableCategories={availableCategories}
          availableTags={availableTags}
          onLoadMore={handleLoadMore}
          onRefresh={handleRefresh}
          onArticleClick={handleArticleClick}
          enableInfiniteScroll={pagination.hasNext}
          enableFilters={true}
          enableSearch={true}
          enableSort={true}
          className="max-w-7xl mx-auto px-4 py-6"
        />

        {isLoadingMore && (
          <div className="text-center text-sm text-gray-500 pb-6">
            Cargando más artículos…
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};

export default NewsExample;