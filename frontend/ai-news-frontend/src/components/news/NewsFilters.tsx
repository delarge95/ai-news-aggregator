import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  Filter, 
  Calendar as CalendarIcon, 
  X, 
  RotateCcw,
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  Globe,
  Tag,
  Hash,
  User,
  Settings
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { NewsFilters as NewsFiltersType, FilterPanelState } from './types';

interface NewsFiltersProps {
  filters: NewsFiltersType;
  onFiltersChange: (filters: NewsFiltersType) => void;
  availableSources: string[];
  availableCategories: string[];
  availableTags: string[];
  panelState?: FilterPanelState;
  onPanelStateChange?: (state: FilterPanelState) => void;
  compact?: boolean;
  onReset?: () => void;
  className?: string;
}

const NewsFilters: React.FC<NewsFiltersProps> = ({
  filters,
  onFiltersChange,
  availableSources,
  availableCategories,
  availableTags,
  panelState,
  onPanelStateChange,
  compact = false,
  onReset,
  className = "",
}) => {
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({
    from: filters.dateRange?.from,
    to: filters.dateRange?.to,
  });

  const handleDateRangeChange = (field: 'from' | 'to', date?: Date) => {
    const newRange = { ...dateRange, [field]: date };
    setDateRange(newRange);
    
    if (newRange.from && newRange.to) {
      onFiltersChange({
        ...filters,
        dateRange: { from: newRange.from, to: newRange.to }
      });
    }
  };

  const handleSourceToggle = (source: string) => {
    const currentSources = filters.sources || [];
    const newSources = currentSources.includes(source)
      ? currentSources.filter(s => s !== source)
      : [...currentSources, source];
    
    onFiltersChange({ ...filters, sources: newSources });
  };

  const handleSentimentToggle = (sentiment: 'positive' | 'negative' | 'neutral') => {
    const currentSentiment = filters.sentiment || [];
    const newSentiment = currentSentiment.includes(sentiment)
      ? currentSentiment.filter(s => s !== sentiment)
      : [...currentSentiment, sentiment];
    
    onFiltersChange({ ...filters, sentiment: newSentiment });
  };

  const handleRelevanceChange = (value: number[]) => {
    onFiltersChange({
      ...filters,
      relevanceRange: { min: value[0], max: value[1] }
    });
  };

  const handleCategoryToggle = (category: string) => {
    const currentCategories = filters.categories || [];
    const newCategories = currentCategories.includes(category)
      ? currentCategories.filter(c => c !== category)
      : [...currentCategories, category];
    
    onFiltersChange({ ...filters, categories: newCategories });
  };

  const handleTagToggle = (tag: string) => {
    const currentTags = filters.tags || [];
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag];
    
    onFiltersChange({ ...filters, tags: newTags });
  };

  const handleLanguageToggle = (language: string) => {
    const currentLanguages = filters.languages || [];
    const newLanguages = currentLanguages.includes(language)
      ? currentLanguages.filter(l => l !== language)
      : [...currentLanguages, language];
    
    onFiltersChange({ ...filters, languages: newLanguages });
  };

  const clearAllFilters = () => {
    onFiltersChange({});
    setDateRange({ from: undefined, to: undefined });
    onReset?.();
  };

  const activeFiltersCount = () => {
    let count = 0;
    if (filters.dateRange) count++;
    if (filters.sources && filters.sources.length > 0) count++;
    if (filters.sentiment && filters.sentiment.length > 0) count++;
    if (filters.relevanceRange) count++;
    if (filters.categories && filters.categories.length > 0) count++;
    if (filters.tags && filters.tags.length > 0) count++;
    if (filters.languages && filters.languages.length > 0) count++;
    return count;
  };

  const availableLanguages = ['español', 'inglés', 'francés', 'alemán', 'portugués'];

  if (compact) {
    // Vista compacta para el header
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filtros
              {activeFiltersCount() > 0 && (
                <Badge variant="secondary" className="ml-2 text-xs">
                  {activeFiltersCount()}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-0" align="end">
            <CompactFilterPanel
              filters={filters}
              onFiltersChange={onFiltersChange}
              availableSources={availableSources}
              availableCategories={availableCategories}
              availableTags={availableTags}
              dateRange={dateRange}
              onDateRangeChange={handleDateRangeChange}
              onSourceToggle={handleSourceToggle}
              onSentimentToggle={handleSentimentToggle}
              onRelevanceChange={handleRelevanceChange}
              onCategoryToggle={handleCategoryToggle}
              onTagToggle={handleTagToggle}
              onLanguageToggle={handleLanguageToggle}
              availableLanguages={availableLanguages}
              onClearAll={clearAllFilters}
            />
          </PopoverContent>
        </Popover>
      </div>
    );
  }

  // Vista completa
  return (
    <Card className={`w-full ${className}`}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtros de noticias
            {activeFiltersCount() > 0 && (
              <Badge variant="secondary">
                {activeFiltersCount()} activos
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={clearAllFilters}>
              <RotateCcw className="h-4 w-4 mr-1" />
              Limpiar
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs defaultValue="basic" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Básico</TabsTrigger>
            <TabsTrigger value="ai">IA</TabsTrigger>
            <TabsTrigger value="advanced">Avanzado</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-6">
            {/* Filtros de fecha */}
            <div className="space-y-3">
              <Label className="text-sm font-medium flex items-center gap-2">
                <CalendarIcon className="h-4 w-4" />
                Rango de fechas
              </Label>
              <div className="grid grid-cols-2 gap-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="justify-start text-left font-normal text-sm"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {dateRange.from ? (
                        format(dateRange.from, 'PPP', { locale: es })
                      ) : (
                        <span>Desde</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={dateRange.from}
                      onSelect={(date) => handleDateRangeChange('from', date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
                
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className="justify-start text-left font-normal text-sm"
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {dateRange.to ? (
                        format(dateRange.to, 'PPP', { locale: es })
                      ) : (
                        <span>Hasta</span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={dateRange.to}
                      onSelect={(date) => handleDateRangeChange('to', date)}
                      initialFocus
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            <Separator />

            {/* Fuentes */}
            <div className="space-y-3">
              <Label className="text-sm font-medium flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Fuentes ({availableSources.length})
              </Label>
              <ScrollArea className="h-40">
                <div className="space-y-2">
                  {availableSources.map((source) => (
                    <div key={source} className="flex items-center space-x-2">
                      <Checkbox
                        id={`source-${source}`}
                        checked={(filters.sources || []).includes(source)}
                        onCheckedChange={() => handleSourceToggle(source)}
                      />
                      <Label 
                        htmlFor={`source-${source}`} 
                        className="text-sm font-normal cursor-pointer flex-1 truncate"
                      >
                        {source}
                      </Label>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>

            <Separator />

            {/* Categorías */}
            <div className="space-y-3">
              <Label className="text-sm font-medium flex items-center gap-2">
                <Hash className="h-4 w-4" />
                Categorías ({availableCategories.length})
              </Label>
              <ScrollArea className="h-32">
                <div className="space-y-2">
                  {availableCategories.map((category) => (
                    <div key={category} className="flex items-center space-x-2">
                      <Checkbox
                        id={`category-${category}`}
                        checked={(filters.categories || []).includes(category)}
                        onCheckedChange={() => handleCategoryToggle(category)}
                      />
                      <Label 
                        htmlFor={`category-${category}`} 
                        className="text-sm font-normal cursor-pointer"
                      >
                        {category}
                      </Label>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>

          <TabsContent value="ai" className="space-y-6">
            {/* Sentimiento */}
            <div className="space-y-3">
              <Label className="text-sm font-medium flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Sentimiento del contenido
              </Label>
              <div className="space-y-3">
                {[
                  { value: 'positive' as const, label: 'Positivo', color: 'text-green-600', icon: TrendingUp },
                  { value: 'neutral' as const, label: 'Neutral', color: 'text-gray-600', icon: Minus },
                  { value: 'negative' as const, label: 'Negativo', color: 'text-red-600', icon: TrendingDown }
                ].map((sentiment) => (
                  <div key={sentiment.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`sentiment-${sentiment.value}`}
                      checked={(filters.sentiment || []).includes(sentiment.value)}
                      onCheckedChange={() => handleSentimentToggle(sentiment.value)}
                    />
                    <sentiment.icon className={`h-4 w-4 ${sentiment.color}`} />
                    <Label 
                      htmlFor={`sentiment-${sentiment.value}`} 
                      className={`text-sm font-normal cursor-pointer ${sentiment.color}`}
                    >
                      {sentiment.label}
                    </Label>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Relevancia */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Rango de relevancia</Label>
              <div className="space-y-4">
                <Slider
                  value={[
                    filters.relevanceRange?.min || 0,
                    filters.relevanceRange?.max || 100
                  ]}
                  onValueChange={handleRelevanceChange}
                  max={100}
                  step={5}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-600">
                  <span>{filters.relevanceRange?.min || 0}%</span>
                  <span>{filters.relevanceRange?.max || 100}%</span>
                </div>
              </div>
            </div>

            <Separator />

            {/* Idioma */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Idiomas</Label>
              <ScrollArea className="h-32">
                <div className="space-y-2">
                  {availableLanguages.map((language) => (
                    <div key={language} className="flex items-center space-x-2">
                      <Checkbox
                        id={`language-${language}`}
                        checked={(filters.languages || []).includes(language)}
                        onCheckedChange={() => handleLanguageToggle(language)}
                      />
                      <Label 
                        htmlFor={`language-${language}`} 
                        className="text-sm font-normal cursor-pointer capitalize"
                      >
                        {language}
                      </Label>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6">
            {/* Tags */}
            <div className="space-y-3">
              <Label className="text-sm font-medium flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Tags populares ({availableTags.length})
              </Label>
              <ScrollArea className="h-40">
                <div className="flex flex-wrap gap-2">
                  {availableTags.slice(0, 20).map((tag) => (
                    <Badge
                      key={tag}
                      variant={(filters.tags || []).includes(tag) ? "default" : "outline"}
                      className="cursor-pointer text-xs"
                      onClick={() => handleTagToggle(tag)}
                    >
                      {tag}
                    </Badge>
                  ))}
                  {availableTags.length > 20 && (
                    <Badge variant="secondary" className="text-xs">
                      +{availableTags.length - 20} más
                    </Badge>
                  )}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

// Componente para panel compacto en popover
const CompactFilterPanel: React.FC<{
  filters: NewsFiltersType;
  onFiltersChange: (filters: NewsFiltersType) => void;
  availableSources: string[];
  availableCategories: string[];
  availableTags: string[];
  dateRange: { from?: Date; to?: Date };
  onDateRangeChange: (field: 'from' | 'to', date?: Date) => void;
  onSourceToggle: (source: string) => void;
  onSentimentToggle: (sentiment: 'positive' | 'negative' | 'neutral') => void;
  onRelevanceChange: (value: number[]) => void;
  onCategoryToggle: (category: string) => void;
  onTagToggle: (tag: string) => void;
  onLanguageToggle: (language: string) => void;
  availableLanguages: string[];
  onClearAll: () => void;
}> = ({
  filters,
  onFiltersChange,
  availableSources,
  availableCategories,
  availableTags,
  dateRange,
  onDateRangeChange,
  onSourceToggle,
  onSentimentToggle,
  onRelevanceChange,
  onCategoryToggle,
  onTagToggle,
  onLanguageToggle,
  availableLanguages,
  onClearAll,
}) => {
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Filtros rápidos</h3>
        <Button variant="ghost" size="sm" onClick={onClearAll}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Fuentes populares */}
      <div className="space-y-2">
        <Label className="text-xs font-medium text-gray-600">Fuentes populares</Label>
        <div className="flex flex-wrap gap-1">
          {availableSources.slice(0, 5).map((source) => (
            <Badge
              key={source}
              variant={(filters.sources || []).includes(source) ? "default" : "outline"}
              className="cursor-pointer text-xs"
              onClick={() => onSourceToggle(source)}
            >
              {source}
            </Badge>
          ))}
        </div>
      </div>

      {/* Sentimiento */}
      <div className="space-y-2">
        <Label className="text-xs font-medium text-gray-600">Sentimiento</Label>
        <div className="flex gap-1">
          {[
            { value: 'positive' as const, label: '😊', color: 'bg-green-100 hover:bg-green-200' },
            { value: 'neutral' as const, label: '😐', color: 'bg-gray-100 hover:bg-gray-200' },
            { value: 'negative' as const, label: '😢', color: 'bg-red-100 hover:bg-red-200' }
          ].map((sentiment) => (
            <Button
              key={sentiment.value}
              variant="ghost"
              size="sm"
              className={`h-8 w-8 p-0 ${sentiment.color} ${
                (filters.sentiment || []).includes(sentiment.value) ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => onSentimentToggle(sentiment.value)}
            >
              {sentiment.label}
            </Button>
          ))}
        </div>
      </div>

      {/* Relevancia */}
      <div className="space-y-2">
        <Label className="text-xs font-medium text-gray-600">Relevancia mínima</Label>
        <Slider
          value={[filters.relevanceRange?.min || 0]}
          onValueChange={(value) => onRelevanceChange([value[0], 100])}
          max={100}
          step={10}
          className="w-full"
        />
        <div className="text-xs text-gray-500 text-center">
          {filters.relevanceRange?.min || 0}%+
        </div>
      </div>
    </div>
  );
};

export default NewsFilters;