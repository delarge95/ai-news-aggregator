/**
 * Componente de comparación de tendencias temporales
 */

import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ComparisonData } from './types';
import { 
  TrendingUp, 
  TrendingDown, 
  ArrowUpRight, 
  ArrowDownRight,
  Minus,
  Calendar,
  BarChart3,
  LineChart as LineChartIcon,
  AreaChart as AreaChartIcon,
  Filter
} from 'lucide-react';

interface ComparisonChartProps {
  data: ComparisonData | null;
  loading?: boolean;
  onRefresh?: () => void;
}

const getChangeColor = (change: number): string => {
  if (change > 5) return '#10B981'; // Verde para aumentos significativos
  if (change > 0) return '#34D399'; // Verde claro para aumentos pequeños
  if (change > -5) return '#F59E0B'; // Ámbar para decreases pequeños
  return '#EF4444'; // Rojo para decreases significativos
};

const getChangeIcon = (change: number) => {
  if (change > 0) return <ArrowUpRight className="w-4 h-4" />;
  if (change < 0) return <ArrowDownRight className="w-4 h-4" />;
  return <Minus className="w-4 h-4" />;
};

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('es-ES', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric'
  });
};

const MetricChangeCard: React.FC<{
  metric: string;
  change: {
    metric: string;
    absolute_change: number;
    percentage_change: number;
    direction: 'up' | 'down' | 'stable';
  };
}> = ({ metric, change }) => {
  const isPositive = change.percentage_change > 0;
  const isNegative = change.percentage_change < 0;
  const isStable = Math.abs(change.percentage_change) < 1;
  
  return (
    <div className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-gray-900 capitalize">{metric}</h4>
        <Badge variant="outline" className="capitalize">
          {change.direction === 'up' ? 'Subiendo' : 
           change.direction === 'down' ? 'Bajando' : 'Estable'}
        </Badge>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Cambio absoluto:</span>
          <div className="flex items-center gap-1">
            {getChangeIcon(change.absolute_change)}
            <span className={`font-medium ${
              isPositive ? 'text-green-600' : 
              isNegative ? 'text-red-600' : 'text-gray-600'
            }`}>
              {change.absolute_change > 0 ? '+' : ''}{change.absolute_change.toFixed(2)}
            </span>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Cambio porcentual:</span>
          <div className="flex items-center gap-1">
            {getChangeIcon(change.percentage_change)}
            <span className={`font-medium ${
              isPositive ? 'text-green-600' : 
              isNegative ? 'text-red-600' : 'text-gray-600'
            }`}>
              {change.percentage_change > 0 ? '+' : ''}{change.percentage_change.toFixed(1)}%
            </span>
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
          <div
            className={`h-2 rounded-full transition-all duration-500 ${
              isPositive ? 'bg-green-500' : 
              isNegative ? 'bg-red-500' : 'bg-gray-400'
            }`}
            style={{
              width: `${Math.min(Math.abs(change.percentage_change), 100)}%`,
              marginLeft: isNegative ? `calc(50% - ${Math.min(Math.abs(change.percentage_change), 50)}%)` : '50%'
            }}
          />
        </div>
      </div>
    </div>
  );
};

// Componente de tooltip personalizado para gráficos
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    dataKey: string;
    value: number;
    color: string;
    payload: Record<string, unknown>;
  }>;
  label?: string;
}> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-medium text-gray-900 mb-2">{label}</p>
        <div className="space-y-1">
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-sm text-gray-600">
                {entry.dataKey === 'period1' ? 'Período Anterior' : 'Período Actual'}:
              </span>
              <span className="text-sm font-medium text-gray-900">
                {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

export const ComparisonChart: React.FC<ComparisonChartProps> = ({ data, loading, onRefresh }) => {
  const [activeView, setActiveView] = useState<'trends' | 'metrics' | 'analysis'>('trends');
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('line');

  // Preparar datos para el gráfico de líneas
  const lineChartData = useMemo(() => {
    if (!data?.changes) return [];
    
    return data.changes.map(change => ({
      metric: change.metric,
      period1: change.metric === 'sentiment_score' ? 0.3 : 0.5, // Valores simulados
      period2: change.metric === 'sentiment_score' ? 
        0.3 + change.absolute_change : 
        0.5 + change.absolute_change,
      change: change.percentage_change
    }));
  }, [data]);

  // Preparar datos para gráfico de barras
  const barChartData = useMemo(() => {
    if (!data?.changes) return [];
    
    return data.changes.map(change => ({
      metric: change.metric.replace(/_/g, ' ').toUpperCase(),
      period1: Math.abs(change.metric === 'sentiment_score' ? 30 : 50), // Valores simulados
      period2: Math.abs(change.metric === 'sentiment_score' ? 
        30 + (change.absolute_change * 100) : 
        50 + (change.absolute_change * 100)),
      change: change.percentage_change
    }));
  }, [data]);

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
            Comparación de Tendencias
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-64 bg-gray-100 rounded animate-pulse" />
            <div className="grid grid-cols-3 gap-4">
              <div className="h-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-20 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-gray-500" />
            Comparación de Tendencias
          </CardTitle>
          <CardDescription>
            No hay datos de comparación disponibles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <TrendingUp className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Selecciona un rango de fechas para ver comparaciones</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Comparación de Tendencias
              <Badge variant="secondary">
                {data.changes.length} métricas
              </Badge>
            </CardTitle>
            <CardDescription>
              {formatDate(data.period1.start_date)} - {formatDate(data.period1.end_date)} 
              {' vs '}
              {formatDate(data.period2.start_date)} - {formatDate(data.period2.end_date)}
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <Filter className="w-4 h-4 mr-2" />
              Actualizar
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeView} onValueChange={(value) => setActiveView(value as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="trends">Tendencias</TabsTrigger>
            <TabsTrigger value="metrics">Métricas</TabsTrigger>
            <TabsTrigger value="analysis">Análisis</TabsTrigger>
          </TabsList>

          <TabsContent value="trends" className="mt-6">
            <div className="space-y-6">
              {/* Selector de tipo de gráfico */}
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Tipo de gráfico:</span>
                <div className="flex gap-1">
                  <Button
                    variant={chartType === 'line' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('line')}
                  >
                    <LineChartIcon className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={chartType === 'area' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('area')}
                  >
                    <AreaChartIcon className="w-4 h-4" />
                  </Button>
                  <Button
                    variant={chartType === 'bar' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChartType('bar')}
                  >
                    <BarChart3 className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Gráfico principal */}
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  {chartType === 'line' && (
                    <LineChart data={lineChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="metric" 
                        fontSize={12}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis fontSize={12} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="period1" 
                        stroke="#6B7280" 
                        strokeWidth={2}
                        name="Período Anterior"
                        dot={{ r: 4 }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="period2" 
                        stroke="#3B82F6" 
                        strokeWidth={2}
                        name="Período Actual"
                        dot={{ r: 4 }}
                      />
                    </LineChart>
                  )}
                  
                  {chartType === 'area' && (
                    <AreaChart data={lineChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="metric" 
                        fontSize={12}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis fontSize={12} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="period1"
                        stackId="1"
                        stroke="#6B7280"
                        fill="#6B7280"
                        fillOpacity={0.3}
                        name="Período Anterior"
                      />
                      <Area
                        type="monotone"
                        dataKey="period2"
                        stackId="2"
                        stroke="#3B82F6"
                        fill="#3B82F6"
                        fillOpacity={0.3}
                        name="Período Actual"
                      />
                    </AreaChart>
                  )}
                  
                  {chartType === 'bar' && (
                    <BarChart data={barChartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="metric" 
                        fontSize={12}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis fontSize={12} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Bar dataKey="period1" fill="#6B7280" name="Período Anterior" />
                      <Bar dataKey="period2" fill="#3B82F6" name="Período Actual" />
                    </BarChart>
                  )}
                </ResponsiveContainer>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="metrics" className="mt-6">
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {data.changes.map((change, index) => (
                  <MetricChangeCard
                    key={change.metric}
                    metric={change.metric.replace(/_/g, ' ')}
                    change={change}
                  />
                ))}
              </div>
              
              {/* Resumen de cambios */}
              <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-4">Resumen de Cambios</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {data.changes.filter(c => c.percentage_change > 0).length}
                    </div>
                    <div className="text-sm text-gray-600">Métricas en alza</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {data.changes.filter(c => c.percentage_change < 0).length}
                    </div>
                    <div className="text-sm text-gray-600">Métricas a la baja</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-600">
                      {data.changes.filter(c => Math.abs(c.percentage_change) < 1).length}
                    </div>
                    <div className="text-sm text-gray-600">Métricas estables</div>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="analysis" className="mt-6">
            <div className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Período 1 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg text-gray-700">{data.period1.label}</CardTitle>
                    <CardDescription>
                      {formatDate(data.period1.start_date)} - {formatDate(data.period1.end_date)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(data.period1.metrics).slice(0, 5).map(([metric, value]) => (
                        <div key={metric} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">
                            {metric.replace(/_/g, ' ')}
                          </span>
                          <span className="font-medium text-gray-900">
                            {typeof value === 'number' ? value.toFixed(2) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Período 2 */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg text-gray-700">{data.period2.label}</CardTitle>
                    <CardDescription>
                      {formatDate(data.period2.start_date)} - {formatDate(data.period2.end_date)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {Object.entries(data.period2.metrics).slice(0, 5).map(([metric, value]) => (
                        <div key={metric} className="flex justify-between items-center">
                          <span className="text-sm text-gray-600 capitalize">
                            {metric.replace(/_/g, ' ')}
                          </span>
                          <span className="font-medium text-gray-900">
                            {typeof value === 'number' ? value.toFixed(2) : value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Análisis de tendencias */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Análisis de Tendencias</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {data.changes
                      .filter(change => Math.abs(change.percentage_change) > 5)
                      .map((change, index) => (
                        <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                          <div className="flex items-center gap-3">
                            {getChangeIcon(change.percentage_change)}
                            <div>
                              <h4 className="font-medium text-gray-900 capitalize">
                                {change.metric.replace(/_/g, ' ')}
                              </h4>
                              <p className="text-sm text-gray-600">
                                Cambio de {change.percentage_change > 0 ? '+' : ''}
                                {change.percentage_change.toFixed(1)}%
                              </p>
                            </div>
                          </div>
                          <Badge 
                            variant="outline"
                            className={
                              change.percentage_change > 0 
                                ? 'border-green-200 text-green-700' 
                                : 'border-red-200 text-red-700'
                            }
                          >
                            {change.percentage_change > 0 ? 'Mejora' : 'Declive'}
                          </Badge>
                        </div>
                      ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default ComparisonChart;
