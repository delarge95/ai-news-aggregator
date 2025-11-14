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
  Plus,
  Minus
} from 'lucide-react';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';
import { NewsFilters, FilterPanelState } from './types';
import { useIsMobile } from '@/hooks/use-mobile';

interface AdvancedFiltersProps {
  filters: NewsFilters;
  onFiltersChange: (filters: NewsFilters) => void;
  availableSources: string[];
  availableCategories: string[];
  availableTags: string[];
  panelState: FilterPanelState;
  onPanelStateChange: (state: FilterPanelState) => void;
}

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  availableSources,
  availableCategories,
  availableTags,
  panelState,
  onPanelStateChange,
}) => {
  const isMobile = useIsMobile();
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

  const clearAllFilters = () => {
    onFiltersChange({});
    setDateRange({ from: undefined, to: undefined });
  };

  const togglePanel = () => {
    onPanelStateChange({ ...panelState, isOpen: !panelState.isOpen });
  };

  const activeFiltersCount = () => {
    let count = 0;
    if (filters.dateRange) count++;
    if (filters.sources && filters.sources.length > 0) count++;
    if (filters.sentiment && filters.sentiment.length > 0) count++;
    if (filters.relevanceRange) count++;
    if (filters.categories && filters.categories.length > 0) count++;
    if (filters.tags && filters.tags.length > 0) count++;
    return count;
  };

  const FilterSection = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-gray-900">{title}</h4>
      {children}
    </div>
  );

  const Checklist = ({ 
    items, 
    selectedItems, 
    onToggle 
  }: { 
    items: string[]; 
    selectedItems: string[]; 
    onToggle: (item: string) => void;
  }) => (
    <div className="space-y-2">
      {items.slice(0, 10).map((item) => (
        <div key={item} className="flex items-center space-x-2">
          <Checkbox
            id={item}
            checked={selectedItems.includes(item)}
            onCheckedChange={() => onToggle(item)}
          />
          <Label htmlFor={item} className="text-sm font-normal cursor-pointer truncate">
            {item}
          </Label>
        </div>
      ))}
      {items.length > 10 && (
        <p className="text-xs text-gray-500">y {items.length - 10} más...</p>
      )}
    </div>
  );

  const SidebarContent = () => (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          <h2 className="text-lg font-semibold">Filtros</h2>
          {activeFiltersCount() > 0 && (
            <Badge variant="secondary" className="text-xs">
              {activeFiltersCount()}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            <RotateCcw className="h-4 w-4" />
            Limpiar
          </Button>
          {isMobile && (
            <Button variant="ghost" size="sm" onClick={togglePanel}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Filters Content */}
      <ScrollArea className="flex-1 p-4">
        <Tabs value={panelState.activeTab} onValueChange={(value) => 
          onPanelStateChange({ ...panelState, activeTab: value as any })
        }>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="date">Fecha</TabsTrigger>
            <TabsTrigger value="source">Fuente</TabsTrigger>
            <TabsTrigger value="sentiment">Sentimiento</TabsTrigger>
          </TabsList>
          
          <TabsList className="grid w-full grid-cols-3 mt-2">
            <TabsTrigger value="relevance">Relevancia</TabsTrigger>
            <TabsTrigger value="category">Categoría</TabsTrigger>
            <TabsTrigger value="tags">Tags</TabsTrigger>
          </TabsList>

          <div className="mt-4">
            <TabsContent value="date" className="space-y-4">
              <FilterSection title="Rango de fechas">
                <div className="grid grid-cols-1 gap-2">
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="justify-start text-left font-normal"
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
                        className="justify-start text-left font-normal"
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
              </FilterSection>
            </TabsContent>

            <TabsContent value="source" className="space-y-4">
              <FilterSection title="Fuentes de noticias">
                <Checklist
                  items={availableSources}
                  selectedItems={filters.sources || []}
                  onToggle={handleSourceToggle}
                />
              </FilterSection>
            </TabsContent>

            <TabsContent value="sentiment" className="space-y-4">
              <FilterSection title="Sentimiento del contenido">
                <div className="space-y-3">
                  {[
                    { value: 'positive' as const, label: 'Positivo', color: 'text-green-600' },
                    { value: 'neutral' as const, label: 'Neutral', color: 'text-gray-600' },
                    { value: 'negative' as const, label: 'Negativo', color: 'text-red-600' }
                  ].map((sentiment) => (
                    <div key={sentiment.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={sentiment.value}
                        checked={(filters.sentiment || []).includes(sentiment.value)}
                        onCheckedChange={() => handleSentimentToggle(sentiment.value)}
                      />
                      <Label htmlFor={sentiment.value} className={`text-sm font-normal cursor-pointer ${sentiment.color}`}>
                        {sentiment.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </FilterSection>
            </TabsContent>

            <TabsContent value="relevance" className="space-y-4">
              <FilterSection title="Rango de relevancia">
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
              </FilterSection>
            </TabsContent>

            <TabsContent value="category" className="space-y-4">
              <FilterSection title="Categorías">
                <Checklist
                  items={availableCategories}
                  selectedItems={filters.categories || []}
                  onToggle={handleCategoryToggle}
                />
              </FilterSection>
            </TabsContent>

            <TabsContent value="tags" className="space-y-4">
              <FilterSection title="Tags populares">
                <Checklist
                  items={availableTags}
                  selectedItems={filters.tags || []}
                  onToggle={handleTagToggle}
                />
              </FilterSection>
            </TabsContent>
          </div>
        </Tabs>
      </ScrollArea>
    </div>
  );

  if (isMobile) {
    return (
      <>
        {/* Mobile Filter Toggle */}
        <Button
          variant="outline"
          size="sm"
          onClick={togglePanel}
          className="fixed top-4 right-4 z-40 bg-white shadow-lg"
        >
          <Filter className="h-4 w-4" />
          {activeFiltersCount() > 0 && (
            <Badge variant="secondary" className="ml-1 text-xs">
              {activeFiltersCount()}
            </Badge>
          )}
        </Button>

        {/* Mobile Filter Panel */}
        {panelState.isOpen && (
          <div className="fixed inset-0 z-50 bg-black/50" onClick={togglePanel}>
            <div 
              className="fixed right-0 top-0 h-full w-80 bg-white shadow-xl"
              onClick={(e) => e.stopPropagation()}
            >
              <SidebarContent />
            </div>
          </div>
        )}
      </>
    );
  }

  // Desktop Sidebar
  return (
    <div className="w-80 border-r bg-gray-50/50 h-full">
      <SidebarContent />
    </div>
  );
};

export default AdvancedFilters;