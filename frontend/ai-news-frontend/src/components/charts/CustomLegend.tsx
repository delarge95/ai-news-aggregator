import React from 'react';
import {
  Legend,
  LegendProps,
  LegendPayload,
} from 'recharts';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  Eye, 
  EyeOff, 
  Check, 
  Filter,
  MoreVertical 
} from 'lucide-react';

interface CustomLegendProps extends Omit<LegendProps, 'children'> {
  showCheckboxes?: boolean;
  showFilters?: boolean;
  maxItems?: number;
  layout?: 'horizontal' | 'vertical';
  align?: 'left' | 'center' | 'right';
  onItemClick?: (dataKey: string) => void;
  onFilterChange?: (selectedItems: string[]) => void;
  className?: string;
  itemStyle?: React.CSSProperties;
}

interface LegendItemState {
  visible: boolean;
  selected: boolean;
}

export const CustomLegend: React.FC<CustomLegendProps> = ({
  showCheckboxes = true,
  showFilters = false,
  maxItems = 10,
  layout = 'horizontal',
  align = 'center',
  onItemClick,
  onFilterChange,
  className = '',
  itemStyle,
  payload,
  ...props
}) => {
  const [itemStates, setItemStates] = React.useState<Record<string, LegendItemState>>({});

  // Inicializar estados cuando cambia el payload
  React.useEffect(() => {
    if (payload && payload.length > 0) {
      const initialStates: Record<string, LegendItemState> = {};
      payload.slice(0, maxItems).forEach((item) => {
        if (item.id) {
          initialStates[item.id] = {
            visible: true,
            selected: true,
          };
        }
      });
      setItemStates(initialStates);
    }
  }, [payload, maxItems]);

  const toggleItemVisibility = (dataKey: string) => {
    setItemStates(prev => ({
      ...prev,
      [dataKey]: {
        ...prev[dataKey],
        visible: !prev[dataKey]?.visible,
      },
    }));
    onItemClick?.(dataKey);
  };

  const selectItem = (dataKey: string) => {
    setItemStates(prev => ({
      ...prev,
      [dataKey]: {
        ...prev[dataKey],
        selected: !prev[dataKey]?.selected,
      },
    }));
  };

  const getVisibleItems = () => {
    return payload?.filter(item => 
      item.id && itemStates[item.id]?.visible
    ).slice(0, maxItems) || [];
  };

  const getSelectedItems = () => {
    const visibleItems = getVisibleItems();
    return visibleItems.filter(item => 
      item.id && itemStates[item.id]?.selected
    );
  };

  const renderLegendItem = (item: LegendPayload, index: number) => {
    const dataKey = item.id || item.dataKey || item.value || `item-${index}`;
    const state = itemStates[dataKey] || { visible: true, selected: true };

    return (
      <div
        key={dataKey}
        className={`
          flex items-center gap-2 p-1.5 rounded-md transition-all duration-200
          ${state.selected ? 'bg-blue-50 hover:bg-blue-100' : 'bg-gray-50 hover:bg-gray-100'}
          ${!state.visible ? 'opacity-50' : 'opacity-100'}
          cursor-pointer group
        `}
        onClick={() => toggleItemVisibility(dataKey)}
      >
        {/* Icono personalizado */}
        <div className="relative">
          <div
            className={`
              w-3 h-3 rounded-sm transition-all duration-200
              ${state.visible ? 'opacity-100' : 'opacity-30'}
            `}
            style={{ backgroundColor: item.color }}
          />
          
          {/* Checkbox */}
          {showCheckboxes && (
            <div className={`
              absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white shadow-sm
              ${state.selected ? 'bg-blue-500 border-blue-500' : 'bg-white border-gray-300'}
            `}>
              {state.selected && (
                <Check className="w-2 h-2 text-white m-0.5" />
              )}
            </div>
          )}
        </div>

        {/* Label */}
        <span className={`
          text-sm font-medium transition-colors duration-200
          ${state.selected ? 'text-gray-900' : 'text-gray-500'}
          ${!state.visible ? 'line-through' : ''}
        `}>
          {item.value}
        </span>

        {/* Botón de acciones adicionales */}
        {showFilters && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
            onClick={(e) => {
              e.stopPropagation();
              selectItem(dataKey);
            }}
          >
            <MoreVertical className="w-3 h-3" />
          </Button>
        )}
      </div>
    );
  };

  const visibleItems = getVisibleItems();
  const selectedItems = getSelectedItems();

  // Notificar cambios al componente padre
  React.useEffect(() => {
    if (onFilterChange) {
      const selectedDataKeys = selectedItems.map(item => item.id || item.dataKey || item.value).filter(Boolean);
      onFilterChange(selectedDataKeys as string[]);
    }
  }, [itemStates, onFilterChange]);

  return (
    <Card className={`p-4 bg-white/80 backdrop-blur-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-semibold text-gray-900">Leyenda</h4>
          <Badge variant="secondary" className="text-xs">
            {visibleItems.length} elementos
          </Badge>
        </div>
        
        {showFilters && (
          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
            <Filter className="w-4 h-4" />
          </Button>
        )}
      </div>

      {/* Grid de elementos */}
      <div className={`
        ${layout === 'horizontal' ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3' : 'flex flex-col'}
        ${align !== 'center' ? `justify-${align}` : 'justify-center'}
        gap-2 max-h-48 overflow-y-auto
      `}>
        {visibleItems.map((item, index) => renderLegendItem(item, index))}
      </div>

      {/* Resumen de selección */}
      {showFilters && selectedItems.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Seleccionados: {selectedItems.length}</span>
            <Button variant="ghost" size="sm" className="h-6 px-2 text-xs">
              <Eye className="w-3 h-3 mr-1" />
              Mostrar todos
            </Button>
          </div>
        </div>
      )}

      {/* Contador de elementos ocultos */}
      {payload && payload.length > maxItems && (
        <div className="mt-2 text-xs text-gray-400 text-center">
          Mostrando {maxItems} de {payload.length} elementos
        </div>
      )}
    </Card>
  );
};

export default CustomLegend;