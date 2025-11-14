import React from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { 
  ArrowUpDown, 
  ArrowUp, 
  ArrowDown, 
  Plus, 
  X,
  BarChart3,
  Calendar,
  Tag,
  Globe,
  FileText,
  TrendingUp
} from 'lucide-react';
import { SortOption } from './types';

interface SortControlsProps {
  currentSort: SortOption;
  onSortChange: (sort: SortOption) => void;
  availableSorts?: SortOption[];
  multiSortMode?: boolean;
  onToggleMultiSort?: () => void;
  className?: string;
}

const SortControls: React.FC<SortControlsProps> = ({
  currentSort,
  onSortChange,
  availableSorts = [
    { field: 'publishedAt', direction: 'desc', label: 'Fecha (más reciente)' },
    { field: 'publishedAt', direction: 'asc', label: 'Fecha (más antigua)' },
    { field: 'relevanceScore', direction: 'desc', label: 'Relevancia (mayor)' },
    { field: 'relevanceScore', direction: 'asc', label: 'Relevancia (menor)' },
    { field: 'title', direction: 'asc', label: 'Título (A-Z)' },
    { field: 'title', direction: 'desc', label: 'Título (Z-A)' },
    { field: 'source', direction: 'asc', label: 'Fuente (A-Z)' },
    { field: 'source', direction: 'desc', label: 'Fuente (Z-A)' },
  ],
  multiSortMode = false,
  onToggleMultiSort,
  className = "",
}) => {
  const getFieldIcon = (field: string) => {
    switch (field) {
      case 'publishedAt':
        return <Calendar className="h-4 w-4" />;
      case 'relevanceScore':
        return <BarChart3 className="h-4 w-4" />;
      case 'title':
        return <FileText className="h-4 w-4" />;
      case 'source':
        return <Globe className="h-4 w-4" />;
      case 'sentiment':
        return <TrendingUp className="h-4 w-4" />;
      default:
        return <ArrowUpDown className="h-4 w-4" />;
    }
  };

  const getCurrentSortLabel = (sort: SortOption) => {
    return `${sort.label} ${sort.direction === 'desc' ? '↓' : '↑'}`;
  };

  const handleSortSelect = (sort: SortOption) => {
    onSortChange(sort);
  };

  const toggleSortDirection = () => {
    onSortChange({
      ...currentSort,
      direction: currentSort.direction === 'asc' ? 'desc' : 'asc'
    });
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Botón principal de ordenamiento */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="h-10">
            {getFieldIcon(currentSort.field)}
            <span className="ml-2 text-sm">
              {getCurrentSortLabel(currentSort)}
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-64">
          <DropdownMenuLabel>Ordenar por</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {availableSorts.map((sort, index) => (
            <DropdownMenuItem
              key={`sort-${index}`}
              onClick={() => handleSortSelect(sort)}
              className="flex items-center gap-2 cursor-pointer"
            >
              {getFieldIcon(sort.field)}
              <div className="flex-1">
                <div className="text-sm font-medium">{sort.label}</div>
              </div>
              {sort.direction === 'desc' ? (
                <ArrowDown className="h-4 w-4" />
              ) : (
                <ArrowUp className="h-4 w-4" />
              )}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Botón para cambiar dirección */}
      <Button
        variant="outline"
        size="sm"
        onClick={toggleSortDirection}
        className="h-10 w-10 p-0"
        title={`Cambiar dirección (${currentSort.direction === 'asc' ? 'ascendente' : 'descendente'})`}
      >
        {currentSort.direction === 'desc' ? (
          <ArrowDown className="h-4 w-4" />
        ) : (
          <ArrowUp className="h-4 w-4" />
        )}
      </Button>

      {/* Toggle para ordenamiento múltiple */}
      {onToggleMultiSort && (
        <Button
          variant={multiSortMode ? "default" : "outline"}
          size="sm"
          onClick={onToggleMultiSort}
          className="h-10"
        >
          <Plus className="h-4 w-4" />
          <span className="ml-1 text-sm">Múltiple</span>
        </Button>
      )}

      {/* Indicador del orden actual */}
      <div className="hidden sm:flex items-center gap-1 text-xs text-gray-500">
        <span>Ordenado por:</span>
        <Badge variant="secondary" className="text-xs">
          {currentSort.label}
        </Badge>
      </div>
    </div>
  );
};

export default SortControls;