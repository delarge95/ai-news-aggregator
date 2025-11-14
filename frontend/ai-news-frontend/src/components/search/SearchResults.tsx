import React, { useState } from 'react';
import { 
  ExternalLink, 
  Calendar, 
  Clock, 
  User, 
  Tag, 
  TrendingUp,
  Heart,
  Share2,
  Bookmark,
  Brain,
  Target,
  Eye,
  AlertCircle,
  Hash
} from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { Progress } from '../ui/progress';
import { SearchResult, SortOption } from './types';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { 
  useTextHighlighting, 
  HighlightedText, 
  MatchStats 
} from './useTextHighlighting';

interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
  onSaveArticle?: (article: SearchResult) => void;
  onShareArticle?: (article: SearchResult) => void;
  onLikeArticle?: (article: SearchResult) => void;
  onViewArticle?: (article: SearchResult) => void;
  highlightTerms?: (text: string, terms: string[]) => string;
  searchQuery?: string;
  className?: string;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  isLoading,
  hasMore,
  onLoadMore,
  onSaveArticle,
  onShareArticle,
  onLikeArticle,
  onViewArticle,
  highlightTerms,
  searchQuery = '',
  className,
}) => {
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [likedArticles, setLikedArticles] = useState<Set<string>>(new Set());
  const [savedArticles, setSavedArticles] = useState<Set<string>>(new Set());

  const toggleExpanded = (articleId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev);
      if (newSet.has(articleId)) {
        newSet.delete(articleId);
      } else {
        newSet.add(articleId);
      }
      return newSet;
    });
  };

  const handleLike = (article: SearchResult) => {
    setLikedArticles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(article.id)) {
        newSet.delete(article.id);
      } else {
        newSet.add(article.id);
      }
      return newSet;
    });
    onLikeArticle?.(article);
  };

  const handleSave = (article: SearchResult) => {
    setSavedArticles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(article.id)) {
        newSet.delete(article.id);
      } else {
        newSet.add(article.id);
      }
      return newSet;
    });
    onSaveArticle?.(article);
  };

  const handleView = (article: SearchResult) => {
    onViewArticle?.(article);
    // Open in new tab
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
      case 'negative':
        return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
      case 'neutral':
        return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-300';
      default:
        return 'text-gray-600 bg-gray-100 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return '😊';
      case 'negative':
        return '😞';
      case 'neutral':
        return '😐';
      default:
        return '😐';
    }
  };

  // Usar el nuevo sistema de highlighting
  const { 
    searchTerms, 
    highlightWithContext, 
    enhancedResults 
  } = useTextHighlighting(searchQuery, results);

  // Si hay resultados mejorados con highlighting, usarlos
  const displayResults = enhancedResults.length > 0 ? enhancedResults : results;

  const highlightedContent = (text: string) => {
    if (!highlightTerms || !searchQuery) return text;
    
    const terms = searchQuery.toLowerCase().split(' ').filter(term => term.length > 2);
    return highlightTerms(text, terms);
  };

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (results.length === 0 && !isLoading) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No se encontraron resultados
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Intenta ajustar tus términos de búsqueda o filtros.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Results Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold">
            Resultados de búsqueda
          </h2>
          {searchQuery && (
            <Badge variant="outline">
              "{searchQuery}"
            </Badge>
          )}
        </div>
      </div>

      {/* Results List */}
      <div className="space-y-4">
        {displayResults.map((article) => {
          const isExpanded = expandedCards.has(article.id);
          const isLiked = likedArticles.has(article.id);
          const isSaved = savedArticles.has(article.id);
          
          // Obtener estadísticas de matching
          const matchStats = article.highlightedContent ? {
            titleMatches: article.highlightedContent.titleMatches || 0,
            contentMatches: article.highlightedContent.contentMatches || 0,
            summaryMatches: article.highlightedContent.summaryMatches || 0,
          } : { titleMatches: 0, contentMatches: 0, summaryMatches: 0 };

          return (
            <Card key={article.id} className="hover:shadow-md transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="font-semibold text-lg leading-tight flex-1">
                        <button
                          onClick={() => handleView(article)}
                          className="text-left hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                          dangerouslySetInnerHTML={{
                            __html: article.highlightedContent?.title || 
                                    highlightedContent(article.title)
                          }}
                        />
                      </h3>
                      
                      {/* Mostrar estadísticas de matching solo si hay highlighting */}
                      {article.highlightedContent && searchQuery && (
                        <MatchStats
                          titleMatches={matchStats.titleMatches}
                          contentMatches={matchStats.contentMatches}
                          summaryMatches={matchStats.summaryMatches}
                        />
                      )}
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center gap-1">
                        <Avatar className="w-6 h-6">
                          <AvatarImage src={article.source.logo} />
                          <AvatarFallback className="text-xs">
                            {article.source.name.charAt(0)}
                          </AvatarFallback>
                        </Avatar>
                        <span>{article.source.name}</span>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        <span>{article.author}</span>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>
                          {formatDistanceToNow(article.publishedAt, { 
                            addSuffix: true,
                            locale: es 
                          })}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge className={cn("text-xs", getSentimentColor(article.sentiment))}>
                            {getSentimentIcon(article.sentiment)} {article.sentiment}
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Análisis de sentimiento: {article.sentiment}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    
                    <Badge variant="outline" className="text-xs">
                      {article.category}
                    </Badge>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="pt-0">
                {/* Summary/Content */}
                <div className="mb-4">
                  {searchQuery && searchTerms.length > 0 ? (
                    // Usar el nuevo highlighting inteligente con contexto
                    <div>
                      <HighlightedText
                        text={isExpanded 
                          ? article.content 
                          : (article.summary || truncateText(article.content, 200))
                        }
                        searchQuery={searchQuery}
                        showContext={!isExpanded}
                        maxLength={200}
                        className="text-gray-700 dark:text-gray-300 leading-relaxed"
                      />
                      {article.content.length > 200 && (
                        <button
                          onClick={() => toggleExpanded(article.id)}
                          className="text-blue-600 dark:text-blue-400 text-sm hover:underline mt-2"
                        >
                          {isExpanded ? 'Ver menos' : 'Ver más'}
                        </button>
                      )}
                    </div>
                  ) : (
                    // Fallback al sistema original
                    <p 
                      className="text-gray-700 dark:text-gray-300 leading-relaxed"
                      dangerouslySetInnerHTML={{
                        __html: isExpanded 
                          ? article.highlightedContent?.content || highlightedContent(article.content)
                          : highlightedContent(truncateText(article.summary || article.content, 200))
                      }}
                    />
                  )}
                </div>

                {/* AI Insights */}
                {article.aiInsights && (
                  <div className="bg-blue-50 dark:bg-blue-950 rounded-lg p-3 mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="w-4 h-4 text-blue-600" />
                      <span className="font-medium text-sm text-blue-900 dark:text-blue-100">
                        Insights de IA
                      </span>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <span className="text-xs font-medium text-blue-800 dark:text-blue-200">
                          Temas clave:
                        </span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {article.aiInsights.keyTopics.map((topic, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-blue-800 dark:text-blue-200">
                          Confianza: {article.aiInsights.confidence}%
                        </span>
                        <Progress 
                          value={article.aiInsights.confidence} 
                          className="w-20 h-2" 
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Tags */}
                {article.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {article.tags.slice(0, 5).map((tag, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        <Tag className="w-2 h-2 mr-1" />
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                {/* Metrics */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center gap-1">
                            <Target className="w-3 h-3" />
                            <span>{article.relevanceScore}% relevante</span>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Puntuación de relevancia</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleLike(article)}
                            className={cn(
                              "h-8 w-8 p-0",
                              isLiked && "text-red-600"
                            )}
                          >
                            <Heart className={cn("w-4 h-4", isLiked && "fill-current")} />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{isLiked ? 'Quitar de favoritos' : 'Agregar a favoritos'}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleSave(article)}
                            className={cn(
                              "h-8 w-8 p-0",
                              isSaved && "text-blue-600"
                            )}
                          >
                            <Bookmark className={cn("w-4 h-4", isSaved && "fill-current")} />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{isSaved ? 'Quitar de guardados' : 'Guardar artículo'}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>

                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                          <Share2 className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => onShareArticle?.(article)}>
                          <Share2 className="w-4 h-4 mr-2" />
                          Compartir
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleView(article)}>
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Abrir enlace
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => navigator.clipboard.writeText(article.url)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          Copiar URL
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Load More */}
      {hasMore && (
        <div className="text-center pt-4">
          <Button
            onClick={onLoadMore}
            disabled={isLoading}
            className="min-w-32"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Cargando...
              </>
            ) : (
              'Cargar más resultados'
            )}
          </Button>
        </div>
      )}
    </div>
  );
};