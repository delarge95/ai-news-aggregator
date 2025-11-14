import React, { useState, useRef } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LabelList,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  PieChart as PieChartIcon, 
  BarChart3, 
  Download, 
  Settings,
  TrendingUp,
  Tag,
  Info
} from 'lucide-react';

import { CustomTooltip } from './CustomTooltip';
import { CustomLegend } from './CustomLegend';
import { useChartTheme } from './useChartTheme';
import { exportChart } from './exportUtils';
import { chartColorPalette } from './theme';

interface TopicData {
  name: string;
  value: number;
  percentage: number;
  color?: string;
  trend?: number;
  articles?: number;
  sentiment?: 'positive' | 'negative' | 'neutral';
}

interface TopicDistributionChartProps {
  data: TopicData[];
  chartType?: 'pie' | 'bar' | 'both';
  height?: number;
  showPercentage?: boolean;
  showTrend?: boolean;
  showLegend?: boolean;
  showLabels?: boolean;
  maxItems?: number;
  showExport?: boolean;
  onTopicClick?: (topic: TopicData) => void;
  className?: string;
}

export const TopicDistributionChart: React.FC<TopicDistributionChartProps> = ({
  data,
  chartType = 'both',
  height = 400,
  showPercentage = true,
  showTrend = true,
  showLegend = true,
  showLabels = true,
  maxItems = 10,
  showExport = true,
  onTopicClick,
  className = '',
}) => {
  const { theme } = useChartTheme();
  const chartRef = useRef<HTMLDivElement>(null);
  const [activeChart, setActiveChart] = useState<'pie' | 'bar'>(chartType === 'both' ? 'pie' : chartType);
  const [sortBy, setSortBy] = useState<'value' | 'name' | 'trend'>('value');
  const [selectedTopics, setSelectedTopics] = useState<Set<string>>(new Set());

  // Procesar y ordenar datos
  const processedData = React.useMemo(() => {
    let sortedData = [...data];
    
    // Ordenar datos
    sortedData.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'trend':
          return (b.trend || 0) - (a.trend || 0);
        case 'value':
        default:
          return b.value - a.value;
      }
    });

    // Limitar cantidad de elementos
    return sortedData.slice(0, maxItems);
  }, [data, sortBy, maxItems]);

  // Calcular total
  const total = React.useMemo(() => {
    return processedData.reduce((sum, item) => sum + item.value, 0);
  }, [processedData]);

  // Asignar colores automáticamente si no están definidos
  const getColors = React.useCallback((count: number) => {
    if (count <= chartColorPalette.categorical.length) {
      return chartColorPalette.categorical.slice(0, count);
    }
    
    // Generar colores adicionales si es necesario
    const colors = [...chartColorPalette.categorical];
    while (colors.length < count) {
      const hue = (colors.length * 137.5) % 360; // Golden angle
      colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    return colors;
  }, []);

  const colors = React.useMemo(() => {
    return processedData.map((item, index) => 
      item.color || getColors(processedData.length)[index]
    );
  }, [processedData, getColors]);

  // Formatear valor para mostrar
  const formatValue = (value: number, item: TopicData) => {
    return showPercentage ? `${item.percentage.toFixed(1)}%` : value.toLocaleString();
  };

  // Manejar clic en tema
  const handleTopicClick = (topic: TopicData) => {
    onTopicClick?.(topic);
  };

  // Toggle selección de tema
  const toggleTopicSelection = (topicName: string) => {
    setSelectedTopics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(topicName)) {
        newSet.delete(topicName);
      } else {
        newSet.add(topicName);
      }
      return newSet;
    });
  };

  // Exportar gráfico
  const handleExport = async () => {
    if (chartRef.current) {
      try {
        await exportChart({ current: chartRef.current }, {
          filename: `topic-distribution-${new Date().toISOString().split('T')[0]}`,
          format: 'png'
        });
      } catch (error) {
        console.error('Error exporting chart:', error);
      }
    }
  };

  // Obtener icono de tendencia
  const getTrendIcon = (trend?: number) => {
    if (!trend) return null;
    if (trend > 0) return <TrendingUp className="w-3 h-3 text-green-500" />;
    if (trend < 0) return <TrendingUp className="w-3 h-3 text-red-500 rotate-180" />;
    return null;
  };

  // Obtener color de sentimiento
  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return theme.colors.success;
      case 'negative': return theme.colors.error;
      case 'neutral': return theme.colors.secondary;
      default: return theme.colors.muted;
    }
  };

  // Custom label para pie chart
  const renderPieLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // No mostrar etiquetas para segmentos muy pequeños
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(1)}%`}
      </text>
    );
  };

  // Renderizar contenido del pie chart
  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={processedData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={showLabels ? renderPieLabel : false}
          outerRadius={120}
          innerRadius={60}
          fill="#8884d8"
          dataKey="value"
          animationBegin={0}
          animationDuration={800}
          onClick={(data, index) => handleTopicClick(data.payload)}
        >
          {processedData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={colors[index]}
              stroke={theme.colors.background}
              strokeWidth={2}
            />
          ))}
        </Pie>
        <Tooltip
          content={<CustomTooltip />}
          formatter={(value, name, props) => [
            formatValue(value, props.payload),
            props.payload.name
          ]}
        />
        {showLegend && (
          <Legend
            content={(props) => (
              <CustomLegend
                {...props}
                showCheckboxes={true}
                showFilters={false}
                onItemClick={(dataKey) => toggleTopicSelection(dataKey)}
              />
            )}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  );

  // Renderizar contenido del bar chart
  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={processedData}
        margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
        <XAxis 
          dataKey="name" 
          angle={-45}
          textAnchor="end"
          height={80}
          tick={{ fill: theme.colors.muted, fontSize: 12 }}
          axisLine={{ stroke: theme.colors.border }}
          tickLine={{ stroke: theme.colors.border }}
        />
        <YAxis 
          tick={{ fill: theme.colors.muted, fontSize: 12 }}
          axisLine={{ stroke: theme.colors.border }}
          tickLine={{ stroke: theme.colors.border }}
        />
        <Tooltip
          content={<CustomTooltip />}
          formatter={(value, name, props) => [
            formatValue(value, props.payload),
            'Artículos'
          ]}
        />
        {showLegend && (
          <Legend
            content={(props) => (
              <CustomLegend
                {...props}
                showCheckboxes={true}
                showFilters={false}
                onItemClick={(dataKey) => toggleTopicSelection(dataKey)}
              />
            )}
          />
        )}
        <Bar
          dataKey="value"
          fill={theme.colors.primary}
          radius={[4, 4, 0, 0]}
          onClick={(data, index) => handleTopicClick(data.payload)}
        >
          {processedData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={colors[index]}
            />
          ))}
          {showLabels && (
            <LabelList
              dataKey="percentage"
              position="top"
              formatter={(value: number) => `${value.toFixed(1)}%`}
              fill={theme.colors.foreground}
              fontSize={11}
            />
          )}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Distribución de Temas</h3>
          <p className="text-sm text-gray-500">Análisis de temas más populares</p>
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

      {/* Controles */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {chartType === 'both' && (
          <Tabs value={activeChart} onValueChange={(value) => setActiveChart(value as 'pie' | 'bar')}>
            <TabsList>
              <TabsTrigger value="pie" className="gap-2">
                <PieChartIcon className="w-4 h-4" />
                Pie
              </TabsTrigger>
              <TabsTrigger value="bar" className="gap-2">
                <BarChart3 className="w-4 h-4" />
                Barras
              </TabsTrigger>
            </TabsList>
          </Tabs>
        )}

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Ordenar por:</span>
          <Button
            variant={sortBy === 'value' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('value')}
          >
            Valor
          </Button>
          <Button
            variant={sortBy === 'name' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('name')}
          >
            Nombre
          </Button>
          {showTrend && (
            <Button
              variant={sortBy === 'trend' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSortBy('trend')}
            >
              Tendencia
            </Button>
          )}
        </div>
      </div>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-blue-600" />
            <div>
              <p className="text-xs text-blue-600 font-medium">Total Temas</p>
              <p className="text-lg font-bold text-blue-900">{processedData.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-3 rounded-lg">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-green-600" />
            <div>
              <p className="text-xs text-green-600 font-medium">Total Artículos</p>
              <p className="text-lg font-bold text-green-900">{total.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="bg-purple-50 p-3 rounded-lg">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-purple-600" />
            <div>
              <p className="text-xs text-purple-600 font-medium">Tema Principal</p>
              <p className="text-lg font-bold text-purple-900">
                {processedData[0]?.name || 'N/A'}
              </p>
              <p className="text-xs text-purple-600">
                {processedData[0]?.percentage.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Gráfico */}
      <div ref={chartRef}>
        {(chartType === 'pie' || activeChart === 'pie') && (
          <TabsContent value="pie" className="mt-0">
            {renderPieChart()}
          </TabsContent>
        )}
        
        {(chartType === 'bar' || activeChart === 'bar') && (
          <TabsContent value="bar" className="mt-0">
            {renderBarChart()}
          </TabsContent>
        )}
      </div>

      {/* Lista de temas detallados */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Detalle de Temas</h4>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {processedData.map((topic, index) => (
            <div
              key={topic.name}
              className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-md cursor-pointer transition-colors"
              onClick={() => handleTopicClick(topic)}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: colors[index] }}
                />
                <div>
                  <span className="text-sm font-medium text-gray-900">{topic.name}</span>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="secondary" className="text-xs">
                      {topic.percentage.toFixed(1)}%
                    </Badge>
                    {showTrend && topic.trend !== undefined && (
                      <div className="flex items-center gap-1">
                        {getTrendIcon(topic.trend)}
                        <span className="text-xs text-gray-500">
                          {topic.trend > 0 ? '+' : ''}{topic.trend.toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {topic.articles && (
                      <Badge variant="outline" className="text-xs">
                        {topic.articles} artículos
                      </Badge>
                    )}
                    {topic.sentiment && (
                      <div
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: getSentimentColor(topic.sentiment) }}
                      />
                    )}
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-900">{topic.value.toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <span>Última actualización: {new Date().toLocaleTimeString('es-ES')}</span>
        <Badge variant="outline" className="text-xs">
          {processedData.length} temas mostrados de {data.length}
        </Badge>
      </div>
    </Card>
  );
};

export default TopicDistributionChart;