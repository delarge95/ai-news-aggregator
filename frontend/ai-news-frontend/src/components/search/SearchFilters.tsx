import React, { useState, useEffect, useCallback } from 'react';
import { 
  Filter, 
  Calendar, 
  Clock, 
  Tag, 
  User, 
  Globe, 
  Save, 
  RotateCcw,
  ChevronDown,
  X,
  Settings,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '../ui/select';
import { 
  Popover, 
  PopoverContent, 
  PopoverTrigger 
} from '../ui/popover';
import { Checkbox } from '../ui/checkbox';
import { 
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../ui/collapsible';
import { Badge } from '../ui/badge';
import { Slider } from '../ui/slider';
import { 
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '../ui/command';
import { Switch } from '../ui/switch';
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
import { 
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../ui/sheet';
import { 
  SearchFilters as SearchFiltersType,
  SavedSearch 
} from './types';
import { cn } from '../../lib/utils';
import { storageService } from '../../services/storageService';

interface SearchFiltersProps {
  filters: SearchFiltersType;
  onFiltersChange: (filters: Partial<SearchFiltersType>) => void;
  onClearFilters: () => void;
  onSaveFilterPreset?: (name: string, filters: SearchFiltersType) => void;
  onLoadFilterPreset?: (presetId: string) => void;
  availableFilters?: {
    sources: string[];
    categories: string[];
    authors: string[];
    languages: string[];
  };
  filterPresets?: SavedSearch[];
  className?: string;
  isPersistent?: boolean;
  showSavePreset?: boolean;
  showLoadPreset?: boolean;
}

const DATE_PRESETS = [
  { label: 'Última hora', value: '1h' },
  { label: 'Últimas 24 horas', value: '24h' },
  { label: 'Últimos 7 días', value: '7d' },
  { label: 'Últimos 30 días', value: '30d' },
  { label: 'Último año', value: '1y' },
  { label: 'Sin restricción', value: 'all' },
];

const LANGUAGES = [
  { code: 'all', label: 'Todos los idiomas' },
  { code: 'es', label: 'Español' },
  { code: 'en', label: 'English' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'it', label: 'Italiano' },
  { code: 'pt', label: 'Português' },
];

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevancia' },
  { value: 'date_desc', label: 'Más recientes' },
  { value: 'date_asc', label: 'Más antiguos' },
  { value: 'popularity', label: 'Popularidad' },
  { value: 'ai_score', label: 'Puntuación IA' },
  { value: 'author_az', label: 'Autor A-Z' },
  { value: 'source_az', label: 'Fuente A-Z' },
];

export const SearchFilters: React.FC<SearchFiltersProps> = ({
  filters,
  onFiltersChange,
  onClearFilters,
  onSaveFilterPreset,
  onLoadFilterPreset,
  availableFilters = {
    sources: ['BBC News', 'CNN', 'Reuters', 'Associated Press', 'The Guardian'],
    categories: ['Tecnología', 'Salud', 'Negocios', 'Deportes', 'Política', 'Ciencia'],
    authors: ['Juan Pérez', 'María García', 'Carlos López', 'Ana Martín', 'Luis Rodríguez'],
    languages: ['es', 'en', 'fr', 'de', 'it', 'pt'],
  },
  filterPresets = [],
  className,
  isPersistent = true,
  showSavePreset = true,
  showLoadPreset = true,
}) => {
  const [datePreset, setDatePreset] = useState('all');
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [isLoaded, setIsLoaded] = useState(false);
  const [persistedFilters, setPersistedFilters] = useState<SearchFiltersType | null>(null);

  // Cargar filtros persistidos
  useEffect(() => {
    if (isPersistent) {
      const savedFilters = storageService.getUserPreference('search_filters');
      if (savedFilters && !isLoaded) {
        onFiltersChange(savedFilters);
        setPersistedFilters(savedFilters);
        setIsLoaded(true);
      }
    }
  }, [isPersistent, isLoaded, onFiltersChange]);

  // Persistir filtros automáticamente
  useEffect(() => {
    if (isPersistent && isLoaded) {
      storageService.setUserPreference('search_filters', filters);
      storageService.setUserPreference('last_filter_update', new Date().toISOString());
    }
  }, [filters, isPersistent, isLoaded]);

  // Detectar cambios en filtros
  const hasChanges = persistedFilters && JSON.stringify(filters) !== JSON.stringify(persistedFilters);

  const handleDatePresetChange = useCallback((preset: string) => {
    setDatePreset(preset);
    const now = new Date();
    let start: Date | null = null;

    switch (preset) {
      case '1h':
        start = new Date(now.getTime() - 60 * 60 * 1000);
        break;
      case '24h':
        start = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case '1y':
        start = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000);
        break;
      default:
        start = null;
    }

    onFiltersChange({
      dateRange: {
        start,
        end: preset === 'all' ? null : now,
      },
    });
  }, [onFiltersChange]);

  const handleCustomDateChange = useCallback((field: 'start' | 'end', value: string) => {
    const date = value ? new Date(value) : null;
    onFiltersChange({
      dateRange: {
        ...filters.dateRange,
        [field]: date,
      },
    });
  }, [filters.dateRange, onFiltersChange]);

  const toggleFilterArray = useCallback((
    arrayName: 'sources' | 'categories' | 'authors',
    value: string
  ) => {
    const currentArray = filters[arrayName];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    
    onFiltersChange({ [arrayName]: newArray });
  }, [filters, onFiltersChange]);

  const clearAllFilters = useCallback(() => {
    onClearFilters();
    setDatePreset('all');
    if (isPersistent) {
      storageService.setUserPreference('search_filters', null);
    }
  }, [onClearFilters, isPersistent]);

  const saveFilterPreset = useCallback(() => {
    if (presetName.trim() && onSaveFilterPreset) {
      onSaveFilterPreset(presetName.trim(), filters);
      setPresetName('');
      setShowSaveDialog(false);
      
      // Mostrar notificación de éxito
      // toast.success('Filtros guardados correctamente');
    }
  }, [presetName, filters, onSaveFilterPreset]);

  const loadFilterPreset = useCallback((preset: SavedSearch) => {
    if (onLoadFilterPreset) {
      onLoadFilterPreset(preset.id);
    }
  }, [onLoadFilterPreset]);

  const hasActiveFilters = useCallback(() => {
    return (
      filters.dateRange.start !== null ||
      filters.sources.length > 0 ||
      filters.categories.length > 0 ||
      filters.authors.length > 0 ||
      filters.language !== 'all' ||
      filters.minScore > 0 ||
      filters.maxScore < 100
    );
  }, [filters]);

  const getActiveFiltersCount = useCallback(() => {
    let count = 0;
    if (filters.dateRange.start) count++;
    if (filters.sources.length > 0) count++;
    if (filters.categories.length > 0) count++;
    if (filters.authors.length > 0) count++;
    if (filters.language !== 'all') count++;
    if (filters.minScore > 0) count++;
    if (filters.maxScore < 100) count++;
    return count;
  }, [filters]);

  const filteredSources = availableFilters.sources.filter(source =>
    source.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredCategories = availableFilters.categories.filter(category =>
    category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredAuthors = availableFilters.authors.filter(author =>
    author.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header con indicadores */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4" />
          <h3 className="font-semibold">Filtros avanzados</h3>
          
          {hasActiveFilters() && (
            <Badge variant="secondary" className="ml-2">
              {getActiveFiltersCount()}
            </Badge>
          )}
          
          {isPersistent && (
            <Badge variant={hasChanges ? "destructive" : "outline"} className="ml-2">
              <div className="flex items-center gap-1">
                {hasChanges ? (
                  <AlertCircle className="w-3 h-3" />
                ) : (
                  <CheckCircle className="w-3 h-3" />
                )}
                {hasChanges ? 'Sin guardar' : 'Guardado'}
              </div>
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Guardar preset */}
          {showSavePreset && hasActiveFilters() && (
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => setShowSaveDialog(true)}
            >
              <Save className="w-4 h-4 mr-1" />
              Guardar
            </Button>
          )}
          
          {/* Cargar preset */}
          {showLoadPreset && filterPresets.length > 0 && (
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="sm">
                  <Settings className="w-4 h-4 mr-1" />
                  Presets
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-64" align="end">
                <div className="space-y-2">
                  <h4 className="font-medium text-sm">Filtros guardados</h4>
                  <div className="space-y-1">
                    {filterPresets.map((preset) => (
                      <Button
                        key={preset.id}
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start h-auto p-2"
                        onClick={() => loadFilterPreset(preset)}
                      >
                        <div className="text-left">
                          <div className="font-medium text-sm">{preset.name}</div>
                          <div className="text-xs text-muted-foreground">
                            "{preset.query}"
                          </div>
                        </div>
                      </Button>
                    ))}
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          )}
          
          {/* Limpiar filtros */}
          {hasActiveFilters() && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm">
                  <RotateCcw className="w-4 h-4 mr-1" />
                  Limpiar
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>¿Limpiar todos los filtros?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Esta acción eliminará todos los filtros aplicados y restaurará 
                    la configuración por defecto.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancelar</AlertDialogCancel>
                  <AlertDialogAction onClick={clearAllFilters}>
                    Limpiar filtros
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </div>

      {/* Date Range */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Calendar className="w-4 h-4" />
          Rango de fechas
        </Label>
        <div className="grid grid-cols-2 gap-2">
          <Select value={datePreset} onValueChange={handleDatePresetChange}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DATE_PRESETS.map(preset => (
                <SelectItem key={preset.value} value={preset.value}>
                  {preset.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDatePresetChange('custom')}
            className={cn(
              datePreset === 'custom' && "bg-accent"
            )}
          >
            Personalizado
          </Button>
        </div>
        
        {datePreset === 'custom' && (
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label htmlFor="date-start" className="text-xs">Desde</Label>
              <Input
                id="date-start"
                type="date"
                value={filters.dateRange.start?.toISOString().split('T')[0] || ''}
                onChange={(e) => handleCustomDateChange('start', e.target.value)}
                className="h-8"
              />
            </div>
            <div>
              <Label htmlFor="date-end" className="text-xs">Hasta</Label>
              <Input
                id="date-end"
                type="date"
                value={filters.dateRange.end?.toISOString().split('T')[0] || ''}
                onChange={(e) => handleCustomDateChange('end', e.target.value)}
                className="h-8"
              />
            </div>
          </div>
        )}
      </div>

      {/* Language */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Globe className="w-4 h-4" />
          Idioma
        </Label>
        <Select 
          value={filters.language} 
          onValueChange={(value) => onFiltersChange({ language: value })}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {LANGUAGES.map(lang => (
              <SelectItem key={lang.code} value={lang.code}>
                {lang.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Sort */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <RotateCcw className="w-4 h-4" />
          Ordenar por
        </Label>
        <Select 
          value={`${filters.sortBy}_${filters.sortOrder}`} 
          onValueChange={(value) => {
            const [sortBy, sortOrder] = value.split('_') as [string, 'asc' | 'desc'];
            onFiltersChange({ sortBy, sortOrder });
          }}
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map(option => (
              <SelectItem key={option.value} value={`${option.value}_desc`}>
                {option.label} (Desc)
              </SelectItem>
            ))}
            {SORT_OPTIONS.map(option => (
              <SelectItem key={`${option.value}_asc`} value={`${option.value}_asc`}>
                {option.label} (Asc)
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Advanced Filters */}
      <Collapsible open={isAdvancedOpen} onOpenChange={setIsAdvancedOpen}>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" className="w-full justify-between p-2">
            Filtros avanzados
            <ChevronDown className={cn(
              "h-4 w-4 transition-transform",
              isAdvancedOpen && "rotate-180"
            )} />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-4 mt-4">
          {/* Sources */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Globe className="w-4 h-4" />
              Fuentes
            </Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  {filters.sources.length > 0 
                    ? `${filters.sources.length} fuentes seleccionadas`
                    : 'Seleccionar fuentes'
                  }
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-72 p-0" align="start">
                <div className="p-2 border-b">
                  <Input
                    placeholder="Buscar fuentes..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <Command>
                  <CommandList>
                    <CommandEmpty>No se encontraron fuentes.</CommandEmpty>
                    <CommandGroup>
                      {filteredSources.map(source => (
                        <CommandItem
                          key={source}
                          onSelect={() => toggleFilterArray('sources', source)}
                        >
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={filters.sources.includes(source)}
                              onCheckedChange={() => toggleFilterArray('sources', source)}
                            />
                            <span>{source}</span>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
            {filters.sources.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {filters.sources.map(source => (
                  <Badge
                    key={source}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => toggleFilterArray('sources', source)}
                  >
                    {source}
                    <X className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Categories */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Tag className="w-4 h-4" />
              Categorías
            </Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  {filters.categories.length > 0 
                    ? `${filters.categories.length} categorías seleccionadas`
                    : 'Seleccionar categorías'
                  }
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-72 p-0" align="start">
                <Command>
                  <CommandList>
                    <CommandEmpty>No se encontraron categorías.</CommandEmpty>
                    <CommandGroup>
                      {filteredCategories.map(category => (
                        <CommandItem
                          key={category}
                          onSelect={() => toggleFilterArray('categories', category)}
                        >
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={filters.categories.includes(category)}
                              onCheckedChange={() => toggleFilterArray('categories', category)}
                            />
                            <span>{category}</span>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
            {filters.categories.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {filters.categories.map(category => (
                  <Badge
                    key={category}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => toggleFilterArray('categories', category)}
                  >
                    {category}
                    <X className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Authors */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <User className="w-4 h-4" />
              Autores
            </Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  {filters.authors.length > 0 
                    ? `${filters.authors.length} autores seleccionados`
                    : 'Seleccionar autores'
                  }
                  <ChevronDown className="h-4 w-4" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-72 p-0" align="start">
                <Command>
                  <CommandList>
                    <CommandEmpty>No se encontraron autores.</CommandEmpty>
                    <CommandGroup>
                      {filteredAuthors.map(author => (
                        <CommandItem
                          key={author}
                          onSelect={() => toggleFilterArray('authors', author)}
                        >
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={filters.authors.includes(author)}
                              onCheckedChange={() => toggleFilterArray('authors', author)}
                            />
                            <span>{author}</span>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
            {filters.authors.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {filters.authors.map(author => (
                  <Badge
                    key={author}
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => toggleFilterArray('authors', author)}
                  >
                    {author}
                    <X className="w-3 h-3 ml-1" />
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* AI Score Range */}
          <div className="space-y-2">
            <Label>Puntuación IA: {filters.minScore}% - {filters.maxScore}%</Label>
            <div className="px-2">
              <Slider
                value={[filters.minScore, filters.maxScore]}
                onValueChange={([min, max]) => onFiltersChange({ minScore: min, maxScore: max })}
                max={100}
                min={0}
                step={5}
                className="w-full"
              />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>

      {/* Dialog para guardar preset */}
      <Sheet open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Guardar filtro como preset</SheetTitle>
            <SheetDescription>
              Guarda la configuración actual de filtros para reutilizar más tarde
            </SheetDescription>
          </SheetHeader>
          
          <div className="space-y-4 mt-6">
            <div>
              <Label htmlFor="preset-name">Nombre del preset</Label>
              <Input
                id="preset-name"
                value={presetName}
                onChange={(e) => setPresetName(e.target.value)}
                placeholder="Ej: Noticias de tecnología 2024"
              />
            </div>
            
            <div className="bg-muted p-3 rounded-lg">
              <h4 className="font-medium mb-2">Configuración actual:</h4>
              <div className="text-sm space-y-1">
                {filters.dateRange.start && (
                  <div>Fecha: desde {filters.dateRange.start.toLocaleDateString()}</div>
                )}
                {filters.language !== 'all' && (
                  <div>Idioma: {filters.language}</div>
                )}
                {filters.sources.length > 0 && (
                  <div>Fuentes: {filters.sources.length} seleccionadas</div>
                )}
                {filters.categories.length > 0 && (
                  <div>Categorías: {filters.categories.length} seleccionadas</div>
                )}
                {filters.authors.length > 0 && (
                  <div>Autores: {filters.authors.length} seleccionados</div>
                )}
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
                Cancelar
              </Button>
              <Button 
                onClick={saveFilterPreset}
                disabled={!presetName.trim()}
              >
                Guardar preset
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
};