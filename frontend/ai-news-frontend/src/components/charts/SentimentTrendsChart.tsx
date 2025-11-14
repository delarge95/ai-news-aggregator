import React, { useState, useRef, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Download, 
  Eye, 
  Settings,
  Activity,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

import { CustomTooltip } from './CustomTooltip';
import { CustomLegend } from './CustomLegend';
import { useChartTheme } from './useChartTheme';
import { exportChart } from './exportUtils';
import type { ChartEventHandlers } from './types';

interface SentimentData {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
  average: number;
  trend: 'up' | 'down' | 'neutral';
  volume?: number;
}

interface SentimentTrendsChartProps {
  data: SentimentData[];
  height?: number;
  showBrush?: boolean;
  showTrendLine?: boolean;
  showAverageLine?: boolean;
  showVolume?: boolean;
  onTrendChange?: (trend: string, value: number) => void;
  onDataPointClick?: (data: SentimentData, index: number) => void;
  className?: string;
  animationDuration?: number;
  showExport?: boolean;
}

export const SentimentTrendsChart: React.FC<SentimentTrendsChartProps> = ({
  data,
  height = 400,
  showBrush = true,
  showTrendLine = true,
  showAverageLine = true,
  showVolume = false,
  onTrendChange,
  onDataPointClick,
  className = '',
  animationDuration = 1000,
  showExport = true,
}) => {
  const { theme } = useChartTheme();
  const chartRef = useRef<HTMLDivElement>(null);
  const [visibleLines, setVisibleLines] = useState<Record<string, boolean>>({
    positive: true,
    negative: true,
    neutral: true,
    average: true,
  });
  const [selectedPeriod, setSelectedPeriod] = useState<'all' | '7d' | '30d'>('all');
  const [alertThreshold, setAlertThreshold] = useState({ positive: 70, negative: 30 });

  // Calcular estadísticas
  const stats = React.useMemo(() => {
    if (data.length === 0) return null;

    const latest = data[data.length - 1];
    const previous = data[data.length - 2];
    
    const avgPositive = data.reduce((sum, d) => sum + d.positive, 0) / data.length;
    const avgNegative = data.reduce((sum, d) => sum + d.negative, 0) / data.length;
    const avgNeutral = data.reduce((sum, d) => sum + d.neutral, 0) / data.length;
    const avgAverage = data.reduce((sum, d) => sum + d.average, 0) / data.length;

    return {
      latest,
      previous,
      avgPositive,
      avgNegative,
      avgNeutral,
      avgAverage,
      changePositive: latest && previous ? ((latest.positive - previous.positive) / previous.positive) * 100 : 0,
      changeNegative: latest && previous ? ((latest.negative - previous.negative) / previous.negative) * 100 : 0,
      changeAverage: latest && previous ? ((latest.average - previous.average) / previous.average) * 100 : 0,
    };
  }, [data]);

  // Filtrar datos por período
  const filteredData = React.useMemo(() => {
    const now = new Date();
    let filterDate = new Date(0);

    switch (selectedPeriod) {
      case '7d':
        filterDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        filterDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      default:
        return data;
    }

    return data.filter(d => new Date(d.date) >= filterDate);
  }, [data, selectedPeriod]);

  // Formatear fecha para mostrar
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  // Formatear valores para tooltip
  const formatValue = (value: number) => `${value.toFixed(1)}%`;

  // Manejar clic en punto de datos
  const handleDataPointClick = (data: SentimentData, index: number) => {
    onDataPointClick?.(data, index);
  };

  // Toggle línea visible
  const toggleLine = (dataKey: string) => {
    setVisibleLines(prev => ({
      ...prev,
      [dataKey]: !prev[dataKey],
    }));
  };

  // Exportar gráfico
  const handleExport = async () => {
    if (chartRef.current) {
      try {
        await exportChart({ current: chartRef.current }, {
          filename: `sentiment-trends-${new Date().toISOString().split('T')[0]}`,
          format: 'png'
        });
      } catch (error) {
        console.error('Error exporting chart:', error);
      }
    }
  };

  // Obtener color de tendencia
  const getTrendColor = (value: number, threshold: number) => {
    if (value >= threshold) return theme.colors.success;
    if (value <= 100 - threshold) return theme.colors.error;
    return theme.colors.warning;
  };

  // Obtener icono de tendencia
  const getTrendIcon = (change: number) => {
    if (change > 1) return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (change < -1) return <TrendingDown className="w-4 h-4 text-red-500" />;
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Tendencias de Sentimiento</h3>
          <p className="text-sm text-gray-500">Análisis de sentimientos a lo largo del tiempo</p>
        </div>
        
        <div className="flex items-center gap-2">
          {showExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="gap-2"
            >
              <Download className="w-4 h-4" />
              Exportar
            </Button>
          )}
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Estadísticas rápidas */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-green-600 font-medium">Positivo</p>
                <p className="text-lg font-bold text-green-900">{stats.latest?.positive.toFixed(1)}%</p>
              </div>
              {getTrendIcon(stats.changePositive)}
            </div>
            <p className="text-xs text-green-500 mt-1">
              {stats.changePositive > 0 ? '+' : ''}{stats.changePositive.toFixed(1)}%
            </p>
          </div>

          <div className="bg-red-50 p-3 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-red-600 font-medium">Negativo</p>
                <p className="text-lg font-bold text-red-900">{stats.latest?.negative.toFixed(1)}%</p>
              </div>
              {getTrendIcon(-stats.changeNegative)}
            </div>
            <p className="text-xs text-red-500 mt-1">
              {stats.changeNegative > 0 ? '+' : ''}{stats.changeNegative.toFixed(1)}%
            </p>
          </div>

          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-600 font-medium">Neutral</p>
                <p className="text-lg font-bold text-gray-900">{stats.latest?.neutral.toFixed(1)}%</p>
              </div>
              <Activity className="w-4 h-4 text-gray-400" />
            </div>
          </div>

          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600 font-medium">Promedio</p>
                <p className="text-lg font-bold text-blue-900">{stats.latest?.average.toFixed(1)}</p>
              </div>
              {getTrendIcon(stats.changeAverage)}
            </div>
            <p className="text-xs text-blue-500 mt-1">
              {stats.changeAverage > 0 ? '+' : ''}{stats.changeAverage.toFixed(1)}%
            </p>
          </div>
        </div>
      )}

      {/* Controles de período */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-600">Período:</span>
        {(['all', '7d', '30d'] as const).map((period) => (
          <Button
            key={period}
            variant={selectedPeriod === period ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSelectedPeriod(period)}
            className="text-xs"
          >
            {period === 'all' ? 'Todos' : period}
          </Button>
        ))}
      </div>

      {/* Alertas */}
      {stats && (
        <div className="mb-4">
          {stats.latest?.positive >= alertThreshold.positive && (
            <div className="flex items-center gap-2 p-2 bg-green-100 border border-green-200 rounded-md">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm text-green-800">
                Sentimiento positivo alto: {stats.latest.positive.toFixed(1)}%
              </span>
            </div>
          )}
          {stats.latest?.negative >= alertThreshold.negative && (
            <div className="flex items-center gap-2 p-2 bg-red-100 border border-red-200 rounded-md mt-2">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <span className="text-sm text-red-800">
                Sentimiento negativo alto: {stats.latest.negative.toFixed(1)}%
              </span>
            </div>
          )}
        </div>
      )}

      {/* Gráfico */}
      <div ref={chartRef}>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={filteredData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
            
            <XAxis 
              dataKey="date" 
              tickFormatter={formatDate}
              tick={{ fill: theme.colors.muted, fontSize: 12 }}
              axisLine={{ stroke: theme.colors.border }}
              tickLine={{ stroke: theme.colors.border }}
            />
            
            <YAxis 
              tick={{ fill: theme.colors.muted, fontSize: 12 }}
              axisLine={{ stroke: theme.colors.border }}
              tickLine={{ stroke: theme.colors.border }}
              domain={[0, 100]}
            />
            
            <Tooltip
              content={<CustomTooltip />}
              formatter={formatValue}
              labelFormatter={(label) => `Fecha: ${formatDate(label)}`}
            />
            
            <Legend
              content={(props) => (
                <CustomLegend
                  {...props}
                  onItemClick={(dataKey) => toggleLine(dataKey)}
                  showCheckboxes={true}
                  showFilters={false}
                />
              )}
            />
            
            {/* Líneas de datos */}
            {visibleLines.positive && (
              <Line
                type="monotone"
                dataKey="positive"
                stroke={theme.colors.success}
                strokeWidth={3}
                dot={{ fill: theme.colors.success, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: theme.colors.success, strokeWidth: 2 }}
                name="Positivo"
                onClick={(data, index) => handleDataPointClick(data.payload, index)}
              />
            )}
            
            {visibleLines.negative && (
              <Line
                type="monotone"
                dataKey="negative"
                stroke={theme.colors.error}
                strokeWidth={3}
                dot={{ fill: theme.colors.error, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: theme.colors.error, strokeWidth: 2 }}
                name="Negativo"
                onClick={(data, index) => handleDataPointClick(data.payload, index)}
              />
            )}
            
            {visibleLines.neutral && (
              <Line
                type="monotone"
                dataKey="neutral"
                stroke={theme.colors.secondary}
                strokeWidth={3}
                dot={{ fill: theme.colors.secondary, strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, stroke: theme.colors.secondary, strokeWidth: 2 }}
                name="Neutral"
                onClick={(data, index) => handleDataPointClick(data.payload, index)}
              />
            )}
            
            {visibleLines.average && (
              <Line
                type="monotone"
                dataKey="average"
                stroke={theme.colors.primary}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ fill: theme.colors.primary, strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: theme.colors.primary, strokeWidth: 2 }}
                name="Promedio"
                onClick={(data, index) => handleDataPointClick(data.payload, index)}
              />
            )}
            
            {/* Línea de referencia del promedio */}
            {showAverageLine && (
              <ReferenceLine 
                y={stats?.avgAverage} 
                stroke={theme.colors.primary} 
                strokeDasharray="3 3" 
                label={{ value: "Promedio", position: "topRight" }}
              />
            )}
            
            {/* Brush para navegación temporal */}
            {showBrush && (
              <Brush 
                dataKey="date" 
                height={30} 
                stroke={theme.colors.primary}
                tickFormatter={formatDate}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Footer con información adicional */}
      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <span>Última actualización: {new Date().toLocaleTimeString('es-ES')}</span>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            {filteredData.length} puntos de datos
          </Badge>
          <Badge variant="outline" className="text-xs">
            Período: {selectedPeriod}
          </Badge>
        </div>
      </div>
    </Card>
  );
};

export default SentimentTrendsChart;