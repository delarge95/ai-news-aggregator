import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine,
} from 'recharts';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Download, 
  Settings,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Zap,
  Clock,
  Radio
} from 'lucide-react';

import { CustomTooltip } from './CustomTooltip';
import { CustomLegend } from './CustomLegend';
import { useChartTheme } from './useChartTheme';
import { exportChart } from './exportUtils';

interface RealtimeMetric {
  timestamp: number;
  value: number;
  label?: string;
  status?: 'normal' | 'warning' | 'critical' | 'success';
  trend?: number;
  metadata?: Record<string, any>;
}

interface RealtimeData {
  metric: string;
  value: number;
  unit?: string;
  timestamp: number;
  trend: number;
  status: 'normal' | 'warning' | 'critical' | 'success';
  category: string;
}

interface RealtimeMetricsChartProps {
  data?: RealtimeData[];
  height?: number;
  maxDataPoints?: number;
  updateInterval?: number; // en ms
  autoStart?: boolean;
  showAlerts?: boolean;
  showTrends?: boolean;
  metrics: string[];
  categories?: string[];
  onDataUpdate?: (newData: RealtimeData[]) => void;
  onAlert?: (metric: string, value: number, status: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface AlertRule {
  metric: string;
  threshold: number;
  operator: '>' | '<' | '>=' | '<=' | '==' | '!=';
  severity: 'warning' | 'critical';
  message: string;
}

export const RealtimeMetricsChart: React.FC<RealtimeMetricsChartProps> = ({
  data = [],
  height = 400,
  maxDataPoints = 100,
  updateInterval = 5000,
  autoStart = false,
  showAlerts = true,
  showTrends = true,
  metrics,
  categories = [],
  onDataUpdate,
  onAlert,
  onError,
  className = '',
}) => {
  const { theme } = useChartTheme();
  const chartRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Estados
  const [isPlaying, setIsPlaying] = useState(autoStart);
  const [realtimeData, setRealtimeData] = useState<RealtimeData[]>(data);
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set(metrics.slice(0, 3)));
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set(categories));
  const [alertRules] = useState<AlertRule[]>([
    { metric: 'engagement', threshold: 1000, operator: '>', severity: 'success', message: 'Engagement alto detectado' },
    { metric: 'error_rate', threshold: 5, operator: '>', severity: 'critical', message: 'Tasa de errores crítica' },
    { metric: 'response_time', threshold: 200, operator: '>', severity: 'warning', message: 'Tiempo de respuesta elevado' },
  ]);
  const [alerts, setAlerts] = useState<Array<{ metric: string; value: number; status: string; timestamp: number }>>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');

  // Colores para diferentes métricas
  const metricColors = {
    engagement: theme.colors.primary,
    error_rate: theme.colors.error,
    response_time: theme.colors.warning,
    throughput: theme.colors.success,
    active_users: theme.colors.accent,
    cpu_usage: theme.colors.info,
    memory_usage: theme.colors.secondary,
  };

  // Generar datos simulados para demostración
  const generateSimulatedData = useCallback((): RealtimeData[] => {
    const now = Date.now();
    const simulatedData: RealtimeData[] = [];

    metrics.forEach(metric => {
      const baseValue = Math.random() * 100 + 50;
      const variation = (Math.random() - 0.5) * 20;
      const value = Math.max(0, baseValue + variation);
      
      let status: 'normal' | 'warning' | 'critical' | 'success' = 'normal';
      if (metric === 'engagement' && value > 120) status = 'success';
      if (metric === 'error_rate' && value > 10) status = 'critical';
      if (metric === 'response_time' && value > 150) status = 'warning';

      simulatedData.push({
        metric,
        value: Number(value.toFixed(2)),
        unit: getMetricUnit(metric),
        timestamp: now,
        trend: Number((Math.random() - 0.5) * 10).toFixed(2),
        status,
        category: getMetricCategory(metric),
      });
    });

    return simulatedData;
  }, [metrics]);

  // Obtener unidad para métrica
  const getMetricUnit = (metric: string): string => {
    const units: Record<string, string> = {
      engagement: 'k',
      error_rate: '%',
      response_time: 'ms',
      throughput: 'req/s',
      active_users: 'usuarios',
      cpu_usage: '%',
      memory_usage: 'MB',
    };
    return units[metric] || '';
  };

  // Obtener categoría para métrica
  const getMetricCategory = (metric: string): string => {
    const categories: Record<string, string> = {
      engagement: 'Engagement',
      error_rate: 'Performance',
      response_time: 'Performance',
      throughput: 'Performance',
      active_users: 'Usuarios',
      cpu_usage: 'Sistema',
      memory_usage: 'Sistema',
    };
    return categories[metric] || 'General';
  };

  // Procesar nuevos datos
  const processNewData = useCallback((newData: RealtimeData[]) => {
    setRealtimeData(prevData => {
      const updated = [...prevData, ...newData];
      
      // Mantener solo los últimos maxDataPoints
      if (updated.length > maxDataPoints) {
        return updated.slice(-maxDataPoints);
      }
      
      return updated;
    });

    // Verificar alertas
    if (showAlerts) {
      newData.forEach(item => {
        checkAlertRules(item);
      });
    }

    onDataUpdate?.(newData);
  }, [maxDataPoints, showAlerts, onDataUpdate]);

  // Verificar reglas de alerta
  const checkAlertRules = (dataPoint: RealtimeData) => {
    alertRules.forEach(rule => {
      if (rule.metric === dataPoint.metric) {
        const shouldAlert = evaluateCondition(dataPoint.value, rule.threshold, rule.operator);
        
        if (shouldAlert) {
          const alert = {
            metric: dataPoint.metric,
            value: dataPoint.value,
            status: rule.severity,
            timestamp: Date.now(),
          };
          
          setAlerts(prev => [alert, ...prev.slice(0, 9)]); // Mantener solo 10 alertas
          onAlert?.(rule.metric, dataPoint.value, rule.severity);
        }
      }
    });
  };

  // Evaluar condición de alerta
  const evaluateCondition = (value: number, threshold: number, operator: string): boolean => {
    switch (operator) {
      case '>': return value > threshold;
      case '<': return value < threshold;
      case '>=': return value >= threshold;
      case '<=': return value <= threshold;
      case '==': return value === threshold;
      case '!=': return value !== threshold;
      default: return false;
    }
  };

  // Simular actualización en tiempo real
  useEffect(() => {
    if (!isPlaying) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setConnectionStatus('disconnected');
      return;
    }

    setConnectionStatus('connecting');

    intervalRef.current = setInterval(() => {
      const newData = generateSimulatedData();
      processNewData(newData);
      setConnectionStatus('connected');
    }, updateInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, updateInterval, generateSimulatedData, processNewData]);

  // Filtrar datos por métricas y categorías seleccionadas
  const filteredData = React.useMemo(() => {
    return realtimeData.filter(item => 
      selectedMetrics.has(item.metric) && 
      (selectedCategories.size === 0 || selectedCategories.has(item.category))
    );
  }, [realtimeData, selectedMetrics, selectedCategories]);

  // Formatear timestamp
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('es-ES', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  // Formatear valor
  const formatValue = (value: number, unit?: string) => {
    if (unit === 'k') return `${(value / 1000).toFixed(1)}k`;
    if (unit === '%') return `${value.toFixed(1)}%`;
    return `${value.toFixed(2)}${unit || ''}`;
  };

  // Toggle métrica
  const toggleMetric = (metric: string) => {
    setSelectedMetrics(prev => {
      const newSet = new Set(prev);
      if (newSet.has(metric)) {
        newSet.delete(metric);
      } else {
        newSet.add(metric);
      }
      return newSet;
    });
  };

  // Play/Pause
  const togglePlayback = () => {
    setIsPlaying(!isPlaying);
  };

  // Reset
  const handleReset = () => {
    setRealtimeData([]);
    setAlerts([]);
  };

  // Exportar
  const handleExport = async () => {
    if (chartRef.current) {
      try {
        await exportChart({ current: chartRef.current }, {
          filename: `realtime-metrics-${new Date().toISOString().split('T')[0]}`,
          format: 'png'
        });
      } catch (error) {
        console.error('Error exporting chart:', error);
      }
    }
  };

  // Obtener icono de estado de conexión
  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'connecting': return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />;
      case 'disconnected': return <AlertCircle className="w-4 h-4 text-red-500" />;
    }
  };

  // Obtener color de estado
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return theme.colors.success;
      case 'warning': return theme.colors.warning;
      case 'critical': return theme.colors.error;
      default: return theme.colors.secondary;
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Métricas en Tiempo Real</h3>
          <p className="text-sm text-gray-500">Monitoreo live de métricas del sistema</p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Indicador de estado */}
          <div className="flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-full">
            {getConnectionIcon()}
            <span className="text-sm font-medium text-gray-700">
              {connectionStatus === 'connected' ? 'Conectado' : 
               connectionStatus === 'connecting' ? 'Conectando...' : 'Desconectado'}
            </span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="gap-2"
          >
            <Download className="w-4 h-4" />
            Exportar
          </Button>
          
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Controles */}
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* Play/Pause/Reset */}
        <div className="flex items-center gap-2">
          <Button
            variant={isPlaying ? 'default' : 'outline'}
            size="sm"
            onClick={togglePlayback}
            className="gap-2"
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isPlaying ? 'Pausar' : 'Reproducir'}
          </Button>
          
          <Button variant="outline" size="sm" onClick={handleReset}>
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>

        {/* Intervalo de actualización */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Intervalo:</span>
          <select
            value={updateInterval}
            onChange={(e) => {/* handler */}}
            className="text-sm border border-gray-300 rounded-md px-2 py-1"
            disabled
          >
            <option value={1000}>1s</option>
            <option value={5000}>5s</option>
            <option value={10000}>10s</option>
          </select>
        </div>

        {/* Métricas visibles */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Métricas:</span>
          {metrics.slice(0, 5).map(metric => (
            <Button
              key={metric}
              variant={selectedMetrics.has(metric) ? 'default' : 'outline'}
              size="sm"
              onClick={() => toggleMetric(metric)}
              className="text-xs"
            >
              {metric}
            </Button>
          ))}
        </div>
      </div>

      {/* Alertas recientes */}
      {showAlerts && alerts.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">Alertas Recientes</h4>
          <div className="space-y-1">
            {alerts.slice(0, 3).map((alert, index) => (
              <div
                key={index}
                className={`p-2 rounded-md border-l-4 ${
                  alert.status === 'critical' 
                    ? 'bg-red-50 border-red-500' 
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-sm font-medium ${
                    alert.status === 'critical' ? 'text-red-800' : 'text-yellow-800'
                  }`}>
                    {alert.metric}: {alert.value.toFixed(2)}
                  </span>
                  <span className={`text-xs ${
                    alert.status === 'critical' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {formatTime(alert.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Gráfico principal */}
      <div ref={chartRef}>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={filteredData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.border} />
            
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={formatTime}
              tick={{ fill: theme.colors.muted, fontSize: 11 }}
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
                formatValue(value as number, props.payload.unit),
                name
              ]}
              labelFormatter={(label) => `Tiempo: ${formatTime(label)}`}
            />
            
            <Legend
              content={(props) => (
                <CustomLegend
                  {...props}
                  showCheckboxes={true}
                  showFilters={false}
                  onItemClick={(dataKey) => toggleMetric(dataKey)}
                />
              )}
            />

            {/* Líneas para cada métrica */}
            {Array.from(selectedMetrics).map(metric => (
              <Line
                key={metric}
                type="monotone"
                dataKey={metric}
                stroke={metricColors[metric as keyof typeof metricColors] || theme.colors.primary}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2 }}
                name={metric}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Panel de métricas actuales */}
      <div className="mt-6">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Valores Actuales</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from(selectedMetrics).slice(0, 8).map(metric => {
            const latestValue = [...realtimeData]
              .reverse()
              .find(item => item.metric === metric);
            
            return (
              <div
                key={metric}
                className="p-3 bg-gray-50 rounded-lg border cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={() => toggleMetric(metric)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600 font-medium">{metric}</p>
                    <p className="text-lg font-bold text-gray-900">
                      {latestValue ? formatValue(latestValue.value, latestValue.unit) : '--'}
                    </p>
                  </div>
                  <div className="flex flex-col items-end">
                    {latestValue && (
                      <>
                        <TrendingUp className={`w-4 h-4 ${
                          latestValue.trend > 0 ? 'text-green-500' : 'text-red-500'
                        } ${latestValue.trend > 0 ? '' : 'rotate-180'}`} />
                        <span className={`text-xs font-medium ${
                          latestValue.trend > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {latestValue.trend > 0 ? '+' : ''}{latestValue.trend.toFixed(1)}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                
                {/* Indicador de estado */}
                {latestValue && (
                  <div className="mt-2">
                    <Badge
                      variant="secondary"
                      className={`text-xs ${
                        latestValue.status === 'success' 
                          ? 'bg-green-100 text-green-800'
                          : latestValue.status === 'warning'
                          ? 'bg-yellow-100 text-yellow-800'
                          : latestValue.status === 'critical'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {latestValue.status}
                    </Badge>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer con información adicional */}
      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <div className="flex items-center gap-4">
          <span>Última actualización: {formatTime(Date.now())}</span>
          <span>Puntos de datos: {filteredData.length}</span>
        </div>
        <div className="flex items-center gap-2">
          <Radio className="w-3 h-3" />
          <span>Actualización cada {updateInterval / 1000}s</span>
        </div>
      </div>
    </Card>
  );
};

export default RealtimeMetricsChart;