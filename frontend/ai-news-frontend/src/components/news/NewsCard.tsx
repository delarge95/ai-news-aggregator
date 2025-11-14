import React from 'react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { 
  ExternalLink, 
  Calendar, 
  User, 
  Tag, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Clock,
  Globe,
  Brain,
  BarChart3,
  MapPin,
  Building
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { NewsArticle } from './types';

interface NewsCardProps {
  article: NewsArticle;
  viewMode: 'grid' | 'list';
  onClick?: (article: NewsArticle) => void;
}

const getSentimentIcon = (sentiment: string) => {
  switch (sentiment) {
    case 'positive':
      return <TrendingUp className="h-4 w-4 text-green-500" />;
    case 'negative':
      return <TrendingDown className="h-4 w-4 text-red-500" />;
    default:
      return <Minus className="h-4 w-4 text-gray-500" />;
  }
};

const getSentimentColor = (sentiment: string) => {
  switch (sentiment) {
    case 'positive':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'negative':
      return 'bg-red-100 text-red-800 border-red-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const NewsCard: React.FC<NewsCardProps> = ({ article, viewMode, onClick }) => {
  const handleCardClick = () => {
    onClick?.(article);
  };

  const handleExternalClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    window.open(article.url, '_blank', 'noopener,noreferrer');
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd MMM yyyy, HH:mm', { locale: es });
    } catch {
      return dateString;
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    if (score >= 40) return 'bg-orange-500';
    return 'bg-red-500';
  };

  if (viewMode === 'list') {
    return (
      <Card className="w-full hover:shadow-lg transition-shadow cursor-pointer group" onClick={handleCardClick}>
        <CardContent className="p-6">
          <div className="flex gap-6">
            {/* Imagen */}
            {article.imageUrl && (
              <div className="flex-shrink-0">
                <img
                  src={article.imageUrl}
                  alt={article.title}
                  className="w-32 h-24 object-cover rounded-lg"
                  loading="lazy"
                />
              </div>
            )}
            
            {/* Contenido */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors">
                  {article.title}
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleExternalClick}
                  className="opacity-0 group-hover:opacity-100 transition-opacity ml-2 flex-shrink-0"
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>

              {/* Metadatos principales */}
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3">
                <div className="flex items-center gap-1">
                  <Globe className="h-4 w-4" />
                  <span>{article.source}</span>
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(article.publishedAt)}</span>
                </div>
                {article.author && (
                  <div className="flex items-center gap-1">
                    <User className="h-4 w-4" />
                    <span>{article.author}</span>
                  </div>
                )}
                <div className="flex items-center gap-1">
                  <Tag className="h-4 w-4" />
                  <Badge variant="secondary" className="text-xs">
                    {article.category}
                  </Badge>
                </div>
              </div>

              {/* Metadatos de IA */}
              <div className="flex flex-wrap items-center gap-3 mb-3">
                {/* Sentimiento */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Badge className={`text-xs ${getSentimentColor(article.aiMetadata.sentiment)}`}>
                        <div className="flex items-center gap-1">
                          {getSentimentIcon(article.aiMetadata.sentiment)}
                          <span className="capitalize">{article.aiMetadata.sentiment}</span>
                        </div>
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Confianza: {article.aiMetadata.confidence}%</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* Relevancia */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <div className="flex items-center gap-2">
                        <BarChart3 className="h-4 w-4 text-blue-500" />
                        <div className="w-16">
                          <Progress 
                            value={article.aiMetadata.relevanceScore} 
                            className="h-2"
                          />
                        </div>
                        <span className="text-xs text-gray-600 min-w-[2rem]">
                          {article.aiMetadata.relevanceScore}%
                        </span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Puntuación de relevancia</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                {/* Legibilidad */}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4 text-purple-500" />
                        <span className="text-xs text-gray-600">
                          {article.aiMetadata.readability}% legible
                        </span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Índice de legibilidad del contenido</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>

              {/* Resumen */}
              <p className="text-gray-700 line-clamp-2 text-sm">
                {article.summary}
              </p>

              {/* Tags y entidades */}
              {(article.tags.length > 0 || article.aiMetadata.keywords.length > 0) && (
                <div className="mt-3 pt-3 border-t">
                  <div className="flex flex-wrap gap-1">
                    {article.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                    {article.aiMetadata.keywords.slice(0, 2).map((keyword) => (
                      <Badge key={keyword} variant="secondary" className="text-xs">
                        {keyword}
                      </Badge>
                    ))}
                    {article.tags.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{article.tags.length - 3} más
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Vista de grid
  return (
    <Card className="w-full hover:shadow-lg transition-shadow cursor-pointer group" onClick={handleCardClick}>
      {/* Imagen de cabecera */}
      {article.imageUrl && (
        <div className="relative h-48 overflow-hidden rounded-t-lg">
          <img
            src={article.imageUrl}
            alt={article.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
          <div className="absolute top-2 right-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleExternalClick}
              className="bg-white/80 hover:bg-white text-gray-700 opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      <CardContent className="p-4">
        {/* Título */}
        <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 mb-3 group-hover:text-blue-600 transition-colors">
          {article.title}
        </h3>

        {/* Metadatos de IA - Vista Grid */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          {/* Sentimiento */}
          <div className="flex items-center gap-2">
            {getSentimentIcon(article.aiMetadata.sentiment)}
            <span className="text-xs capitalize text-gray-600">{article.aiMetadata.sentiment}</span>
          </div>
          
          {/* Relevancia */}
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-blue-500" />
            <div className="flex-1">
              <Progress value={article.aiMetadata.relevanceScore} className="h-1" />
            </div>
          </div>
        </div>

        {/* Información básica */}
        <div className="space-y-2 text-sm text-gray-600 mb-3">
          <div className="flex items-center gap-1">
            <Globe className="h-4 w-4" />
            <span className="truncate">{article.source}</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span>{formatDate(article.publishedAt)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Tag className="h-4 w-4" />
            <Badge variant="secondary" className="text-xs">
              {article.category}
            </Badge>
          </div>
        </div>

        {/* Resumen truncado */}
        <p className="text-gray-700 line-clamp-3 text-sm mb-3">
          {article.summary}
        </p>

        {/* Tags principales */}
        {article.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {article.tags.slice(0, 2).map((tag) => (
              <Badge key={tag} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
            {article.tags.length > 2 && (
              <Badge variant="outline" className="text-xs">
                +{article.tags.length - 2}
              </Badge>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default NewsCard;