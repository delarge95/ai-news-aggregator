import React, { useState } from 'react';
import { 
  Bookmark, 
  Trash2, 
  Search, 
  Filter, 
  Clock, 
  Bell, 
  Mail,
  Globe,
  Settings,
  Plus,
  X
} from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '../ui/select';
import { Switch } from '../ui/switch';
import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../ui/dialog';
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
import { SavedSearch } from './types';
import { cn } from '../../lib/utils';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

interface SavedSearchesProps {
  savedSearches: SavedSearch[];
  onSelectSearch: (search: SavedSearch) => void;
  onDeleteSearch: (id: string) => void;
  className?: string;
}

export const SavedSearches: React.FC<SavedSearchesProps> = ({
  savedSearches,
  onSelectSearch,
  onDeleteSearch,
  className,
}) => {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newSearchName, setNewSearchName] = useState('');
  const [newSearchFrequency, setNewSearchFrequency] = useState<'immediate' | 'daily' | 'weekly' | 'never'>('never');
  const [newSearchEmailNotifications, setNewSearchEmailNotifications] = useState(false);

  const formatFilters = (filters: any) => {
    const activeFilters: string[] = [];
    
    if (filters.dateRange.start) {
      activeFilters.push('Fecha personalizada');
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
      activeFilters.push('Idioma específico');
    }
    
    return activeFilters;
  };

  const getFrequencyLabel = (frequency: string) => {
    switch (frequency) {
      case 'immediate':
        return 'Inmediato';
      case 'daily':
        return 'Diario';
      case 'weekly':
        return 'Semanal';
      case 'never':
        return 'Nunca';
      default:
        return 'Nunca';
    }
  };

  const getFrequencyIcon = (frequency: string) => {
    switch (frequency) {
      case 'immediate':
      case 'daily':
      case 'weekly':
        return <Bell className="w-3 h-3" />;
      default:
        return <Clock className="w-3 h-3" />;
    }
  };

  const groupedSavedSearches = React.useMemo(() => {
    const groups: Record<string, SavedSearch[]> = {
      'Usadas recientemente': [],
      'Todas las búsquedas': [],
    };
    
    const now = new Date();
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    savedSearches.forEach(search => {
      if (search.lastUsed > oneDayAgo) {
        groups['Usadas recientemente'].push(search);
      } else {
        groups['Todas las búsquedas'].push(search);
      }
    });
    
    return groups;
  }, [savedSearches]);

  if (savedSearches.length === 0) {
    return (
      <div className="text-center py-8">
        <Bookmark className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          No hay búsquedas guardadas
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Guarda tus búsquedas frecuentes para acceder rápidamente
        </p>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Crear búsqueda guardada
        </Button>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bookmark className="w-5 h-5" />
          <h3 className="font-semibold">Búsquedas guardadas</h3>
          <Badge variant="secondary">{savedSearches.length}</Badge>
        </div>
        
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="w-4 h-4 mr-2" />
              Guardar búsqueda
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Crear búsqueda guardada</DialogTitle>
              <DialogDescription>
                Guarda tu búsqueda actual para acceder rápidamente más tarde
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="search-name">Nombre</Label>
                <Input
                  id="search-name"
                  value={newSearchName}
                  onChange={(e) => setNewSearchName(e.target.value)}
                  placeholder="Mi búsqueda..."
                />
              </div>
              
              <div>
                <Label htmlFor="frequency">Frecuencia de alertas</Label>
                <Select value={newSearchFrequency} onValueChange={(value: any) => setNewSearchFrequency(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="never">Nunca</SelectItem>
                    <SelectItem value="immediate">Inmediato</SelectItem>
                    <SelectItem value="daily">Diario</SelectItem>
                    <SelectItem value="weekly">Semanal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <Switch
                  id="email-notifications"
                  checked={newSearchEmailNotifications}
                  onCheckedChange={setNewSearchEmailNotifications}
                />
                <Label htmlFor="email-notifications">Notificaciones por email</Label>
              </div>
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={() => {
                  // TODO: Implement save search logic
                  console.log('Save search:', { 
                    name: newSearchName, 
                    frequency: newSearchFrequency,
                    emailNotifications: newSearchEmailNotifications 
                  });
                  setShowCreateDialog(false);
                  setNewSearchName('');
                }}
                disabled={!newSearchName.trim()}
              >
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* Saved Searches List */}
      <ScrollArea className="h-96">
        <div className="space-y-4">
          {Object.entries(groupedSavedSearches).map(([groupName, searches]) => {
            if (searches.length === 0) return null;
            
            return (
              <div key={groupName}>
                <h4 className="text-sm font-medium text-muted-foreground mb-2 px-2">
                  {groupName}
                </h4>
                <div className="space-y-2">
                  {searches.map((search) => {
                    const activeFilters = formatFilters(search.filters);
                    
                    return (
                      <Card 
                        key={search.id} 
                        className="hover:bg-accent cursor-pointer transition-colors group"
                        onClick={() => onSelectSearch(search)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <Bookmark className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                                <span className="font-medium truncate">
                                  {search.name}
                                </span>
                                <Badge variant="outline" className="text-xs">
                                  "{search.query}"
                                </Badge>
                              </div>
                              
                              <div className="flex items-center gap-4 text-sm text-muted-foreground mb-2">
                                <span>
                                  Usada {formatDistanceToNow(search.lastUsed, { 
                                    addSuffix: true,
                                    locale: es 
                                  })}
                                </span>
                                <span>•</span>
                                <span>Creada {formatDistanceToNow(search.createdAt, { 
                                    addSuffix: true,
                                    locale: es 
                                  })}
                                </span>
                              </div>
                              
                              <div className="flex items-center justify-between">
                                {activeFilters.length > 0 && (
                                  <div className="flex items-center gap-2">
                                    <Filter className="w-3 h-3 text-muted-foreground" />
                                    <div className="flex flex-wrap gap-1">
                                      {activeFilters.slice(0, 2).map((filter, index) => (
                                        <Badge key={index} variant="outline" className="text-xs">
                                          {filter}
                                        </Badge>
                                      ))}
                                      {activeFilters.length > 2 && (
                                        <Badge variant="outline" className="text-xs">
                                          +{activeFilters.length - 2}
                                        </Badge>
                                      )}
                                    </div>
                                  </div>
                                )}
                                
                                <div className="flex items-center gap-2">
                                  {search.alertFrequency !== 'never' && (
                                    <Badge variant="secondary" className="text-xs">
                                      {getFrequencyIcon(search.alertFrequency)}
                                      <span className="ml-1">
                                        {getFrequencyLabel(search.alertFrequency)}
                                      </span>
                                    </Badge>
                                  )}
                                  
                                  {search.emailNotifications && (
                                    <Badge variant="outline" className="text-xs">
                                      <Mail className="w-3 h-3" />
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>¿Eliminar búsqueda guardada?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    Esta acción eliminará permanentemente "{search.name}". 
                                    No se puede deshacer.
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancelar</AlertDialogCancel>
                                  <AlertDialogAction onClick={() => onDeleteSearch(search.id)}>
                                    Eliminar
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
                
                {Object.keys(groupedSavedSearches).indexOf(groupName) < Object.keys(groupedSavedSearches).length - 1 && (
                  <Separator className="mt-4" />
                )}
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
};