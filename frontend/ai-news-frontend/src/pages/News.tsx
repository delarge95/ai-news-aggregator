import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, ExternalLink, Loader2, AlertCircle } from 'lucide-react';
import { articleService, type Article } from '../services/articleService';

const News: React.FC = () => {
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);

  useEffect(() => {
    loadArticles();
  }, [page]);

  const loadArticles = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await articleService.getArticles(page, 20);
      setArticles(response.articles);
      setTotal(response.total);
      setHasNext(response.has_next);
      setHasPrev(response.has_prev);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar artículos');
      console.error('Error loading articles:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Fecha no disponible';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const getSentimentColor = (label?: string) => {
    switch (label?.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 text-green-800';
      case 'negative':
        return 'bg-red-100 text-red-800';
      case 'neutral':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Cargando artículos...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-2xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h2 className="text-lg font-semibold text-red-900">Error al cargar noticias</h2>
          </div>
          <p className="text-red-700 mb-4">{error}</p>
          <button
            onClick={loadArticles}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Noticias de IA</h1>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            Actualizado diariamente
          </span>
          <span className="flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            {total} artículos disponibles
          </span>
        </div>
      </div>

      <div className="grid gap-6 mb-8">
        {articles.map((article) => (
          <article key={article.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow">
            <div className="p-6">
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                {article.source_name && (
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                    {article.source_name}
                  </span>
                )}
                {article.sentiment_label && (
                  <span className={`${getSentimentColor(article.sentiment_label)} text-xs px-2 py-1 rounded`}>
                    {article.sentiment_label}
                  </span>
                )}
                <span className="text-gray-500 text-sm">{formatDate(article.published_at)}</span>
              </div>
              
              <h2 className="text-xl font-semibold text-gray-900 mb-3 hover:text-blue-600 cursor-pointer">
                {article.title}
              </h2>
              
              {article.summary && (
                <p className="text-gray-600 mb-4 line-clamp-3">{article.summary}</p>
              )}
              
              {article.topic_tags && article.topic_tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {article.topic_tags.map((tag, index) => (
                    <span key={index} className="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
              
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 font-medium"
              >
                Leer más
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </article>
        ))}
      </div>

      {/* Pagination Controls */}
      {(hasPrev || hasNext) && (
        <div className="flex justify-center items-center gap-4">
          <button
            onClick={() => setPage(p => p - 1)}
            disabled={!hasPrev}
            className={`px-4 py-2 rounded font-medium transition-colors ${
              hasPrev
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            Anterior
          </button>
          
          <span className="text-gray-600">
            Página {page}
          </span>
          
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={!hasNext}
            className={`px-4 py-2 rounded font-medium transition-colors ${
              hasNext
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  );
};

export default News;
