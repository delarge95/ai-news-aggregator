import React, { useState, useRef, useMemo } from 'react';
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Brush,
  Area,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Download, 
  Settings,
  Activity,
  Star,
  Eye,
  Clock,
  Target,
  Zap
} from 'lucide-react';

import { CustomTooltip } from './CustomTooltip';
import { CustomLegend } from './CustomLegend';
import { useChartTheme } from './useChartTheme';
import { exportChart } from './exportUtils';
import { chartColorPalette } from './theme';

interface SourceData {
  name: string;
  articles: number;
  engagement: number;
  reach: number;
  quality: number;
  responseTime: number;
  accuracy: number;
  trend: number;
  category: string;
  verified: boolean;
}

interface SourcePerformanceChartProps {
  data: SourceData[];
  height?: number;
  showBrush?: boolean;
  showTrend?: boolean;
  showQualityMetrics?: boolean;
  showComparison?: boolean;
  maxSources?: number;
  sortBy?: 'engagement' | 'articles' | 'quality' | 'reach';
  showExport?: boolean;
  onSourceClick?: (source: SourceData) => void;
  className?: string;
}

export const SourcePerformanceChart: React.FC<SourcePerformanceChartProps> = ({
  data,
  height = 500,
  showBrush = true,
  showTrend = true,
  showQualityMetrics = true,
  showComparison = true,
  maxSources = 15,
  sortBy = 'engagement',
  showExport = true,
  onSourceClick,
  className = '',
}) => {
  const { theme } = useChartTheme();
  const chartRef = useRef<HTMLDivElement>(null);
  const [selectedMetric, setSelectedMetric] = useState<'engagement' | 'articles' | 'quality' | 'reach'>('engagement');
  const [showAreas, setShowAreas] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Procesar y filtrar datos
  const processedData = useMemo(() => {
    let filtered = data;

    // Filtrar por categoría si está seleccionada
    if (selectedCategory !== 'all') {
      filtered = data.filter(source => source.category === selectedCategory);
    }

    // Ordenar por métrica seleccionada
    const sorted = [...filtered].sort((a, b) => b[selectedMetric] - a[selectedMetric]);

    // Limitar cantidad
    return sorted.slice(0, maxSources);
  }, [data, selectedCategory, selectedMetric, maxSources]);

  // Obtener categorías únicas
  const categories = useMemo(() => {
    const cats = Array.from(new Set(data.map(source => source.category)));
    return ['all', ...cats];
  }, [data]);

  // Calcular estadísticas
  const stats = useMemo(() => {
    if (processedData.length === 0) return null;

    const totalEngagement = processedData.reduce((sum, source) => sum + source.engagement, 0);
    const totalArticles = processedData.reduce((sum, source) => sum + source.articles, 0);
    const avgQuality = processedData.reduce((sum, source) => sum + source.quality, 0) / processedData.length;
    const avgResponseTime = processedData.reduce((sum, source) => sum + source.responseTime, 0) / processedData.length;

    const topSource = processedData[0];
    const avgEngagementPerSource = totalEngagement / processedData.length;

    return {
      totalEngagement,
      totalArticles,
      avgQuality,
      avgResponseTime,
      topSource,
      avgEngagementPerSource,
      verifiedSources: processedData.filter(source => source.verified).length,
    };
  }, [processedData]);

  // Colores para diferentes métricas
  const metricColors = {
    engagement: theme.colors.primary,
    articles: theme.colors.accent,
    quality: theme.colors.success,
    reach: theme.colors.warning,
    responseTime: theme.colors.secondary,
    accuracy: theme.colors.info,
  };

  // Formatear valor para mostrar
  const formatValue = (value: number, metric: string) => {
    switch (metric) {
      case 'responseTime':
        return `${value.toFixed(1)}h`;
      case 'quality':
      case 'accuracy':
        return `${value.toFixed(1)}%`;
      default:
        return value.toLocaleString();
    }
  };

  // Manejar clic en fuente
  const handleSourceClick = (source: SourceData) => {
    onSourceClick?.(source);
  };

  // Exportar gráfico
  const handleExport = async () => {
    if (chartRef.current) {
      try {
        await exportChart({ current: chartRef.current }, {
          filename: `source-performance-${new Date().toISOString().split('T')[0]}`,
          format: 'png'
        });
      } catch (error) {
        console.error('Error exporting chart:', error);
      }
    }
  };

  // Obtener icono de rendimiento
  const getPerformanceIcon = (source: SourceData) => {
    if (source.verified) {
      return <Star className="w-4 h-4 text-yellow-500 fill-current" />;
    }
    if (source.trend > 10) {
      return <TrendingUp className="w-4 h-4 text-green-500" />;
    }
    if (source.trend < -10) {
      return <TrendingDown className="w-4 h-4 text-red-500" />;
    }
    return <Activity className="w-4 h-4 text-gray-400" />;
  };

  // Obtener color de calidad
  const getQualityColor = (quality: number) => {
    if (quality >= 80) return theme.colors.success;
    if (quality >= 60) return theme.colors.warning;
    return theme.colors.error;
  };

  // Renderizar gráfico principal
  const renderChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart
        data={processedData}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        onClick={(data, index) => handleSourceClick(data.activePayload?.[0]?.payload)}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
        
        <XAxis 
          dataKey="name" 
          angle={-45}
          textAnchor="end"
          height={100}
          tick={{ fill: theme.colors.muted, fontSize: 11 }}
          axisLine={{ stroke: theme.colors.border }}
          tickLine={{ stroke: theme.colors.border }}
        />
        
        <YAxis 
          yAxisId="left"
          orientation="left"
          tick={{ fill: theme.colors.muted, fontSize: 12 }}
          axisLine={{ stroke: theme.colors.border }}
          tickLine={{ stroke: theme.colors.border }}
        />
        
        <YAxis 
          yAxisId="right"
          orientation="right"
          tick={{ fill: theme.colors.muted, fontSize: 12 }}
          axisLine={{ stroke: theme.colors.border }}
          tickLine={{ stroke: theme.colors.border }}
          domain={[0, 100]}
        />
        
        <Tooltip
          content={<CustomTooltip />}
          formatter={(value, name, props) => [
            formatValue(value as number, name),
            name,
            props.payload
          ]}
        />
        
        <Legend
          content={(props) => (
            <CustomLegend
              {...props}
              showCheckboxes={true}
              showFilters={false}
            />
          )}
        />

        {/* Áreas para contexto */}
        {showAreas && (
          <>
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="engagement"
              fill={metricColors.engagement}
              fillOpacity={0.1}
              stroke="none"
              name="Engagement"
            />
            <Area
              yAxisId="left"
              type="monotone"
              dataKey="reach"
              fill={metricColors.reach}
              fillOpacity={0.1}
              stroke="none"
              name="Alcance"
            />
          </>
        )}

        {/* Barras para métricas principales */}
        <Bar
          yAxisId="left"
          dataKey="articles"
          fill={metricColors.articles}
          name="Artículos"
          radius={[4, 4, 0, 0]}
        />
        
        <Bar
          yAxisId="right"
          dataKey="quality"
          fill={metricColors.quality}
          name="Calidad %"
          radius={[4, 4, 0, 0]}
        />

        {/* Líneas para métricas detalladas */}
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="accuracy"
          stroke={metricColors.accuracy}
          strokeWidth={3}
          dot={{ fill: metricColors.accuracy, strokeWidth: 2, r: 4 }}
          name="Precisión %"
        />
        
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="responseTime"
          stroke={metricColors.responseTime}
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ fill: metricColors.responseTime, strokeWidth: 2, r: 3 }}
          name="Tiempo Respuesta (h)"
        />

        {/* Línea de tendencia */}
        {showTrend && (
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="trend"
            stroke={theme.colors.accent}
            strokeWidth={2}
            dot={{ fill: theme.colors.accent, strokeWidth: 2, r: 3 }}
            name="Tendencia %"
          />
        )}

        {/* Líneas de referencia */}
        <ReferenceLine 
          yAxisId="right" 
          y={80} 
          stroke={theme.colors.success} 
          strokeDasharray="3 3" 
          label={{ value: "Excelente", position: "topRight" }}
        />
        <ReferenceLine 
          yAxisId="right" 
          y={60} 
          stroke={theme.colors.warning} 
          strokeDasharray="3 3" 
          label={{ value: "Bueno", position: "topRight" }}
        />

        {/* Brush para navegación */}
        {showBrush && (
          <Brush 
            dataKey="name" 
            height={30} 
            stroke={theme.colors.primary}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Rendimiento de Fuentes</h3>
          <p className="text-sm text-gray-500">Comparación de fuentes de noticias por métricas clave</p>
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
        {/* Filtro por categoría */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Categoría:</span>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-sm border border-gray-300 rounded-md px-2 py-1"
          >
            {categories.map(category => (
              <option key={category} value={category}>
                {category === 'all' ? 'Todas' : category}
              </option>
            ))}
          </select>
        </div>

        {/* Métrica principal */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Ordenar por:</span>
          {(['engagement', 'articles', 'quality', 'reach'] as const).map((metric) => (
            <Button
              key={metric}
              variant={selectedMetric === metric ? 'default' : 'outline'}
              size="sm"
              onClick={() => setSelectedMetric(metric)}
            >
              {metric === 'engagement' && 'Engagement'}
              {metric === 'articles' && 'Artículos'}
              {metric === 'quality' && 'Calidad'}
              {metric === 'reach' && 'Alcance'}
            </Button>
          ))}
        </div>

        {/* Toggle áreas */}
        <Button
          variant={showAreas ? 'default' : 'outline'}
          size="sm"
          onClick={() => setShowAreas(!showAreas)}
        >
          <Eye className="w-4 h-4 mr-2" />
          Áreas
        </Button>
      </div>

      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <div>
                <p className="text-xs text-blue-600 font-medium">Total Engagement</p>
                <p className="text-lg font-bold text-blue-900">
                  {stats.totalEngagement.toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-green-50 p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-green-600" />
              <div>
                <p className="text-xs text-green-600 font-medium">Calidad Promedio</p>
                <p className="text-lg font-bold text-green-900">
                  {stats.avgQuality.toFixed(1)}%
                </p>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-600" />
              <div>
                <p className="text-xs text-purple-600 font-medium">Tiempo Respuesta</p>
                <p className="text-lg font-bold text-purple-900">
                  {stats.avgResponseTime.toFixed(1)}h
                </p>
              </div>
            </div>
          </div>

          <div className="bg-orange-50 p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-orange-600" />
              <div>
                <p className="text-xs text-orange-600 font-medium">Fuentes Verificadas</p>
                <p className="text-lg font-bold text-orange-900">
                  {stats.verifiedSources}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gráfico principal */}
      <div ref={chartRef}>
        {renderChart()}
      </div>

      {/* Tabla de rendimiento detallada */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Tabla de Rendimiento</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 px-3 font-medium text-gray-600">Fuente</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Engagement</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Artículos</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Calidad</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Alcance</th>
                <th className="text-right py-2 px-3 font-medium text-gray-600">Respuesta</th>
                <th className="text-center py-2 px-3 font-medium text-gray-600">Estado</th>
              </tr>
            </thead>
            <tbody>
              {processedData.slice(0, 10).map((source, index) => (
                <tr
                  key={source.name}
                  className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleSourceClick(source)}
                >
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">{source.name}</span>
                      {getPerformanceIcon(source)}
                    </div>
                    <div className="text-xs text-gray-500">{source.category}</div>
                  </td>
                  <td className="py-2 px-3 text-right font-medium">
                    {source.engagement.toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-right font-medium">
                    {source.articles.toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span 
                      className="px-2 py-1 rounded-full text-xs font-medium"
                      style={{ 
                        backgroundColor: getQualityColor(source.quality) + '20',
                        color: getQualityColor(source.quality)
                      }}
                    >
                      {source.quality.toFixed(1)}%
                    </span>
                  </td>
                  <td className="py-2 px-3 text-right font-medium">
                    {source.reach.toLocaleString()}
                  </td>
                  <td className="py-2 px-3 text-right">
                    <span className={`text-xs ${source.responseTime < 2 ? 'text-green-600' : 'text-orange-600'}`}>
                      {source.responseTime.toFixed(1)}h
                    </span>
                  </td>
                  <td className="py-2 px-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      {source.verified && (
                        <Badge variant="default" className="text-xs">
                          <Star className="w-3 h-3 mr-1" />
                          Verificada
                        </Badge>
                      )}
                      {source.trend > 10 && (
                        <TrendingUp className="w-3 h-3 text-green-500" />
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <span>Última actualización: {new Date().toLocaleTimeString('es-ES')}</span>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {processedData.length} fuentes mostradas
          </Badge>
          <Badge variant="secondary" className="text-xs">
            Categoría: {selectedCategory === 'all' ? 'Todas' : selectedCategory}
          </Badge>
        </div>
      </div>
    </Card>
  );
};

export default SourcePerformanceChart;