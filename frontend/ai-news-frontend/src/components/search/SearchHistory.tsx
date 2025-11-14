import React from 'react';
import { Clock, Trash2, Search, Filter, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader } from '../ui/card';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '../ui/alert-dialog';
import { SearchHistoryItem } from './types';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface SearchHistoryProps {
  history: SearchHistoryItem[];
  onSelectItem: (item: SearchHistoryItem) => void;
  onClearHistory: () => void;
  onRemoveItem: (id: string) => void;
  className?: string;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({
  history,
  onSelectItem,
  onClearHistory,
  onRemoveItem,
  className,
}) => {
  if (history.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No hay historial de búsqueda
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Tus búsquedas aparecerán aquí para acceder rápidamente
        </p>
      </div>
    );
  }

  const groupedHistory = React.useMemo(() => {
    const groups: Record<string, SearchHistoryItem[]> = {};
    
    history.forEach(item => {
      const date = new Date(item.timestamp);
      let groupKey: string;
      
      const now = new Date();
      const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
      
      if (diffInHours < 1) {
        groupKey = 'Última hora';
      } else if (diffInHours < 24) {
        groupKey = 'Últimas 24 horas';
      } else if (diffInHours < 24 * 7) {
        groupKey = 'Última semana';
      } else {
        groupKey = 'Más antiguo';
      }
      
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
    });
    
    return groups;
  }, [history]);

  const formatFilters = (filters: any) => {
    const activeFilters: string[] = [];
    
    if (filters.dateRange.start) {
      activeFilters.push('Filtro de fecha');
    }
    if (filters.sources.length > 0) {
      activeFilters.push(`${filters.sources.length} fuente${filters.sources.length > 1 ? 's' : ''}`);
    }
    if (filters.categories.length > 0) {
      activeFilters.push(`${filters.categories.length} categoría${filters.categories.length > 1 ? 's' : ''}`);
    }
    if (filters.authors.length > 0) {
      activeFilters.push(`${filters.authors.length} autor${filters.authors.length > 1 ? 'es' : ''}`);
    }
    if (filters.language !== 'all') {
      activeFilters.push('Idioma');
    }
    
    return activeFilters;
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-5 h-5" />
          <h3 className="font-semibold">Historial de búsqueda</h3>
          <Badge variant="secondary">{history.length}</Badge>
        </div>
        
        {history.length > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm">
                <Trash2 className="w-4 h-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>¿Limpiar historial?</AlertDialogTitle>
                <AlertDialogDescription>
                  Esta acción eliminará permanentemente tu historial de búsqueda. 
                  No se puede deshacer.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancelar</AlertDialogCancel>
                <AlertDialogAction onClick={onClearHistory}>
                  Limpiar historial
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      {/* History List */}
      <ScrollArea className="h-96">
        <div className="space-y-4">
          {Object.entries(groupedHistory).map(([groupName, items]) => (
            <div key={groupName}>
              <h4 className="text-sm font-medium text-muted-foreground mb-2 px-2">
                {groupName}
              </h4>
              <div className="space-y-2">
                {items.map((item) => {
                  const activeFilters = formatFilters(item.filters);
                  
                  return (
                    <Card 
                      key={item.id} 
                      className="hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => onSelectItem(item)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <Search className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                              <span className="font-medium truncate">
                                {item.query}
                              </span>
                            </div>
                            
                            <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                              <span>
                                {formatDistanceToNow(item.timestamp, { 
                                  addSuffix: true,
                                  locale: es 
                                })}
                              </span>
                              <span>•</span>
                              <span>{item.resultCount} resultados</span>
                            </div>
                            
                            {activeFilters.length > 0 && (
                              <div className="flex items-center gap-2">
                                <Filter className="w-3 h-3 text-muted-foreground" />
                                <div className="flex flex-wrap gap-1">
                                  {activeFilters.slice(0, 3).map((filter, index) => (
                                    <Badge key={index} variant="outline" className="text-xs">
                                      {filter}
                                    </Badge>
                                  ))}
                                  {activeFilters.length > 3 && (
                                    <Badge variant="outline" className="text-xs">
                                      +{activeFilters.length - 3}
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              onRemoveItem(item.id);
                            }}
                            className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
              
              {Object.keys(groupedHistory).indexOf(groupName) < Object.keys(groupedHistory).length - 1 && (
                <Separator className="mt-4" />
              )}
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};