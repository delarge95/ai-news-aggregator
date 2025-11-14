import React, { useState } from 'react';
import { 
  Filter, 
  Calendar, 
  Clock, 
  Tag, 
  User, 
  Globe, 
  ChevronDown,
  X,
  RefreshCw,
  Check
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
import { 
  SearchFilters 
} from './types';
import { cn } from '../../lib/utils';

interface FilterPanelProps {
  filters: SearchFilters;
  onFiltersChange: (filters: Partial<SearchFilters>) => void;
  onClearFilters: () => void;
  className?: string;
  availableFilters?: {
    sources: string[];
    categories: string[];
    authors: string[];
    languages: string[];
  };
}

const DATE_PRESETS = [
  { label: 'Última hora', value: '1h' },
  { label: 'Últimas 24 horas', value: '24h' },
  { label: 'Últimos 7 días', value: '7d' },
  { label: 'Últimos 30 días', value: '30d' },
  { label: 'Último año', value: '1y' },
  { label: 'Personalizado', value: 'custom' },
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

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  onClearFilters,
  className,
  availableFilters = {
    sources: ['BBC News', 'CNN', 'Reuters', 'Associated Press'],
    categories: ['Tecnología', 'Salud', 'Negocios', 'Deportes', 'Política', 'Ciencia'],
    authors: ['Juan Pérez', 'María García', 'Carlos López', 'Ana Martín'],
    languages: ['es', 'en', 'fr', 'de', 'it', 'pt'],
  },
}) => {
  const [datePreset, setDatePreset] = useState('all');
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleDatePresetChange = (preset: string) => {
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
        end: preset === 'custom' ? filters.dateRange.end : now,
      },
    });
  };

  const handleCustomDateChange = (field: 'start' | 'end', value: string) => {
    const date = value ? new Date(value) : null;
    onFiltersChange({
      dateRange: {
        ...filters.dateRange,
        [field]: date,
      },
    });
  };

  const toggleFilterArray = (
    arrayName: 'sources' | 'categories' | 'authors',
    value: string
  ) => {
    const currentArray = filters[arrayName];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    
    onFiltersChange({ [arrayName]: newArray });
  };

  const clearAllFilters = () => {
    onClearFilters();
    setDatePreset('all');
  };

  const hasActiveFilters = () => {
    return (
      filters.dateRange.start !== null ||
      filters.sources.length > 0 ||
      filters.categories.length > 0 ||
      filters.authors.length > 0 ||
      filters.language !== 'all' ||
      filters.minScore > 0 ||
      filters.maxScore < 100
    );
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.dateRange.start) count++;
    if (filters.sources.length > 0) count++;
    if (filters.categories.length > 0) count++;
    if (filters.authors.length > 0) count++;
    if (filters.language !== 'all') count++;
    if (filters.minScore > 0) count++;
    if (filters.maxScore < 100) count++;
    return count;
  };

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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4" />
          <h3 className="font-semibold">Filtros</h3>
          {hasActiveFilters() && (
            <Badge variant="secondary" className="ml-2">
              {getActiveFiltersCount()}
            </Badge>
          )}
        </div>
        {hasActiveFilters() && (
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            <X className="w-4 h-4 mr-1" />
            Limpiar
          </Button>
        )}
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
          <RefreshCw className="w-4 h-4" />
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
    </div>
  );
};