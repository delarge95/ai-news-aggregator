import React, { createContext, useContext, ReactNode, useState } from 'react';
import { ChartComponentRegistry, ChartConfig } from './types';

// Tipos para el registro de gráficos
interface ChartsRegistryContextType {
  registerChart: (id: string, config: ChartConfig) => void;
  unregisterChart: (id: string) => void;
  getChartConfig: (id: string) => ChartConfig | undefined;
  getAllCharts: () => Record<string, ChartConfig>;
  updateChartConfig: (id: string, config: Partial<ChartConfig>) => void;
}

const ChartsRegistryContext = createContext<ChartsRegistryContextType | null>(null);

// Proveedor del contexto
interface ChartsRegistryProviderProps {
  children: ReactNode;
  initialCharts?: Record<string, ChartConfig>;
}

export const ChartsRegistryProvider: React.FC<ChartsRegistryProviderProps> = ({
  children,
  initialCharts = {}
}) => {
  const [charts, setCharts] = useState<Record<string, ChartConfig>>(initialCharts);

  const registerChart = (id: string, config: ChartConfig) => {
    setCharts(prev => ({
      ...prev,
      [id]: {
        ...config,
        id,
        registeredAt: new Date(),
      }
    }));
  };

  const unregisterChart = (id: string) => {
    setCharts(prev => {
      const newCharts = { ...prev };
      delete newCharts[id];
      return newCharts;
    });
  };

  const getChartConfig = (id: string): ChartConfig | undefined => {
    return charts[id];
  };

  const getAllCharts = (): Record<string, ChartConfig> => {
    return charts;
  };

  const updateChartConfig = (id: string, config: Partial<ChartConfig>) => {
    setCharts(prev => ({
      ...prev,
      [id]: {
        ...prev[id],
        ...config,
        updatedAt: new Date(),
      }
    }));
  };

  const value: ChartsRegistryContextType = {
    registerChart,
    unregisterChart,
    getChartConfig,
    getAllCharts,
    updateChartConfig,
  };

  return (
    <ChartsRegistryContext.Provider value={value}>
      {children}
    </ChartsRegistryContext.Provider>
  );
};

// Hook para usar el registro
export const useChartsRegistry = () => {
  const context = useContext(ChartsRegistryContext);
  if (!context) {
    throw new Error('useChartsRegistry must be used within a ChartsRegistryProvider');
  }
  return context;
};

// Componente principal del registro
interface ChartsRegistryProps {
  children: ReactNode;
  charts?: ChartConfig[];
}

const ChartsRegistry: React.FC<ChartsRegistryProps> = ({ 
  children, 
  charts = [] 
}) => {
  const { registerChart } = useChartsRegistry();

  // Registrar gráficos automáticamente
  React.useEffect(() => {
    charts.forEach(chart => {
      registerChart(chart.id, chart);
    });

    // Cleanup al desmontar
    return () => {
      charts.forEach(chart => {
        // eslint-disable-next-line react-hooks/exhaustive-deps
        // import { unregisterChart } from './ChartsRegistry'; // Circular import fix
      });
    };
  }, [charts]);

  return <>{children}</>;
};

export default ChartsRegistry;

// Hook para crear nuevas instancias de gráficos
export const useChartFactory = () => {
  const registry = useChartsRegistry();

  const createChart = <T extends ChartConfig>(
    type: T['type'],
    config: Omit<T, 'type' | 'id' | 'registeredAt'>
  ): T => {
    const id = `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const chartConfig: ChartConfig = {
      id,
      type,
      ...config,
      registeredAt: new Date(),
    } as ChartConfig;

    registry.registerChart(id, chartConfig);
    
    return chartConfig as T;
  };

  const duplicateChart = (sourceId: string, modifications?: Partial<ChartConfig>): ChartConfig | null => {
    const sourceConfig = registry.getChartConfig(sourceId);
    if (!sourceConfig) return null;

    const newId = `${sourceConfig.type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    const duplicatedConfig: ChartConfig = {
      ...sourceConfig,
      id: newId,
      title: `${sourceConfig.title} (Copia)`,
      ...modifications,
      registeredAt: new Date(),
    };

    registry.registerChart(newId, duplicatedConfig);
    return duplicatedConfig;
  };

  return { createChart, duplicateChart, registry };
};

// Utilidades para validación de configuraciones
export const validateChartConfig = (config: Partial<ChartConfig>): string[] => {
  const errors: string[] = [];

  if (!config.title) {
    errors.push('El título es requerido');
  }

  if (!config.data || config.data.length === 0) {
    errors.push('Los datos son requeridos y no pueden estar vacíos');
  }

  if (!config.type) {
    errors.push('El tipo de gráfico es requerido');
  }

  return errors;
};

// Utilidades para generar configuraciones por defecto
export const getDefaultChartConfig = (type: string, data: any[]): Partial<ChartConfig> => {
  const baseConfig = {
    data,
    title: `${type.charAt(0).toUpperCase() + type.slice(1)} Chart`,
    responsive: true,
    animation: true,
    theme: 'auto',
  };

  switch (type) {
    case 'line':
    case 'area':
      return {
        ...baseConfig,
        xAxisKey: 'name',
        yAxisKey: 'value',
        showGrid: true,
        showTooltip: true,
        showLegend: true,
      };
    
    case 'bar':
      return {
        ...baseConfig,
        xAxisKey: 'name',
        yAxisKey: 'value',
        showGrid: true,
        showTooltip: true,
        showLegend: true,
        layout: 'vertical',
      };
    
    case 'pie':
      return {
        ...baseConfig,
        dataKey: 'value',
        nameKey: 'name',
        cx: '50%',
        cy: '50%',
        outerRadius: '80%',
        innerRadius: '60%',
        showTooltip: true,
        showLegend: true,
      };
    
    default:
      return baseConfig;
  }
};