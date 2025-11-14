/**
 * Componente de visualización de análisis de sentimiento
 * Incluye gráficos de barras y donut con tooltips interactivos
 */

import React, { useState } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { SentimentData, TooltipData } from './types';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface SentimentChartProps {
  data: SentimentData;
  loading?: boolean;
}

const COLORS = {
  positive: '#10B981', // Verde
  negative: '#EF4444', // Rojo  
  neutral: '#6B7280',  // Gris
  background: '#F9FAFB',
  text: '#374151'
};

// Componente de tooltip personalizado
const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ payload: TooltipData; dataKey: string; value: number }>;
  label?: string;
}> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-600">{data.context}</p>
        <div className="flex items-center gap-2 mt-1">
          <div 
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: data.color }}
          />
          <span className="text-sm font-medium">{data.value}</span>
        </div>
      </div>
    );
  }
  return null;
};

// Componente de indicador de tendencia
const SentimentTrendIndicator: React.FC<{ score: number; size?: 'sm' | 'md' }> = ({ 
  score, 
  size = 'md' 
}) => {
  const isPositive = score > 0;
  const isNegative = score < 0;
  const isNeutral = Math.abs(score) < 0.1;
  
  const iconSize = size === 'sm' ? 'w-4 h-4' : 'w-6 h-6';
  const textSize = size === 'sm' ? 'text-sm' : 'text-base';

  return (
    <div className={`flex items-center gap-2 ${textSize}`}>
      {isPositive && (
        <>
          <TrendingUp className={`${iconSize} text-green-500`} />
          <span className="text-green-600 font-medium">
            {(score * 100).toFixed(1)}%
          </span>
        </>
      )}
      {isNegative && (
        <>
          <TrendingDown className={`${iconSize} text-red-500`} />
          <span className="text-red-600 font-medium">
            {Math.abs(score * 100).toFixed(1)}%
          </span>
        </>
      )}
      {isNeutral && (
        <>
          <Minus className={`${iconSize} text-gray-400`} />
          <span className="text-gray-500 font-medium">0.0%</span>
        </>
      )}
    </div>
  );
};

export const SentimentChart: React.FC<SentimentChartProps> = ({ data, loading }) => {
  const [activeView, setActiveView] = useState<'overview' | 'distribution' | 'trends'>('overview');

  // Preparar datos para el gráfico de barras
  const barData = [
    {
      name: 'Positivo',
      value: data.positive,
      percentage: ((data.positive / data.total_articles) * 100).toFixed(1),
      color: COLORS.positive,
      context: 'Artículos con sentimiento positivo'
    },
    {
      name: 'Neutral',
      value: data.neutral,
      percentage: ((data.neutral / data.total_articles) * 100).toFixed(1),
      color: COLORS.neutral,
      context: 'Artículos con sentimiento neutral'
    },
    {
      name: 'Negativo',
      value: data.negative,
      percentage: ((data.negative / data.total_articles) * 100).toFixed(1),
      color: COLORS.negative,
      context: 'Artículos con sentimiento negativo'
    }
  ];

  // Preparar datos para el gráfico donut
  const pieData = [
    { name: 'Positivo', value: data.positive, color: COLORS.positive },
    { name: 'Neutral', value: data.neutral, color: COLORS.neutral },
    { name: 'Negativo', value: data.negative, color: COLORS.negative }
  ];

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
            Análisis de Sentimiento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-64 bg-gray-100 rounded animate-pulse" />
            <div className="flex gap-4">
              <div className="h-6 w-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-20 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-20 bg-gray-200 rounded animate-pulse" />
            </div>
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
              Análisis de Sentimiento
              <SentimentTrendIndicator score={data.score} />
            </CardTitle>
            <CardDescription>
              {data.total_articles.toLocaleString()} artículos analizados
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Badge variant="secondary">
              Promedio: {data.score > 0 ? '+' : ''}{(data.score * 100).toFixed(1)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeView} onValueChange={(value) => setActiveView(value as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Resumen</TabsTrigger>
            <TabsTrigger value="distribution">Distribución</TabsTrigger>
            <TabsTrigger value="trends">Detalles</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="col-span-1">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0];
                          const percentage = ((data.value as number / data.totalArticles) * 100).toFixed(1);
                          return (
                            <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                              <p className="font-medium text-gray-900">{data.name}</p>
                              <p className="text-sm text-gray-600">{percentage}% del total</p>
                              <p className="text-sm text-gray-600">
                                {(data.value as number).toLocaleString()} artículos
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              
              <div className="col-span-2">
                <h4 className="font-medium text-gray-900 mb-4">Distribución de Sentimientos</h4>
                <div className="space-y-4">
                  {barData.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-4 h-4 rounded"
                            style={{ backgroundColor: item.color }}
                          />
                          <span className="text-sm font-medium text-gray-900">
                            {item.name}
                          </span>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-bold text-gray-900">
                            {item.value.toLocaleString()}
                          </span>
                          <span className="text-sm text-gray-500 ml-1">
                            ({item.percentage}%)
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="h-2 rounded-full transition-all duration-300"
                          style={{
                            backgroundColor: item.color,
                            width: `${item.percentage}%`
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="distribution" className="mt-6">
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.background} />
                <XAxis 
                  dataKey="name" 
                  stroke={COLORS.text}
                  fontSize={12}
                />
                <YAxis 
                  stroke={COLORS.text}
                  fontSize={12}
                  tickFormatter={(value) => value.toLocaleString()}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </TabsContent>

          <TabsContent value="trends" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Métricas de Sentimiento</h4>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-600" />
                      <span className="text-sm font-medium text-green-900">Sentimiento Positivo</span>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-green-600">
                        {data.positive.toLocaleString()}
                      </span>
                      <span className="text-sm text-green-700 ml-1">
                        ({((data.positive / data.total_articles) * 100).toFixed(1)}%)
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Minus className="w-4 h-4 text-gray-600" />
                      <span className="text-sm font-medium text-gray-900">Sentimiento Neutral</span>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-gray-600">
                        {data.neutral.toLocaleString()}
                      </span>
                      <span className="text-sm text-gray-700 ml-1">
                        ({((data.neutral / data.total_articles) * 100).toFixed(1)}%)
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-red-600" />
                      <span className="text-sm font-medium text-red-900">Sentimiento Negativo</span>
                    </div>
                    <div className="text-right">
                      <span className="text-lg font-bold text-red-600">
                        {data.negative.toLocaleString()}
                      </span>
                      <span className="text-sm text-red-700 ml-1">
                        ({((data.negative / data.total_articles) * 100).toFixed(1)}%)
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h4 className="font-medium text-gray-900">Score Promedio</h4>
                
                <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-4xl font-bold text-gray-900 mb-2">
                      {(data.score * 100).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">
                      Sentimiento general {data.score > 0.1 ? 'positivo' : data.score < -0.1 ? 'negativo' : 'neutral'}
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all duration-500 ${
                          data.score > 0 ? 'bg-gradient-to-r from-green-400 to-green-600' :
                          data.score < 0 ? 'bg-gradient-to-r from-red-400 to-red-600' :
                          'bg-gradient-to-r from-gray-400 to-gray-600'
                        }`}
                        style={{
                          width: `${Math.abs(data.score * 100)}%`,
                          marginLeft: data.score < 0 ? `${50 + (data.score * 50)}%` : '50%',
                          transform: data.score < 0 ? 'translateX(-100%)' : 'none'
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>Negativo</span>
                      <span>Neutral</span>
                      <span>Positivo</span>
                    </div>
                  </div>
                </div>

                <div className="text-xs text-gray-500 text-center">
                  Última actualización: {new Date().toLocaleTimeString()}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default SentimentChart;
