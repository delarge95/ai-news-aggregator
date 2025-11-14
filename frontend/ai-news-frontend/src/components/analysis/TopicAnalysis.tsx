/**
 * Componente de análisis de temas con nube de palabras y categorías
 */

import React, { useState, useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { TopicData, WordCloudData } from './types';
import { Search, TrendingUp, TrendingDown, Hash, Filter } from 'lucide-react';

interface TopicAnalysisProps {
  data: TopicData[];
  loading?: boolean;
}

const getSentimentColor = (sentiment: number): string => {
  if (sentiment > 0.2) return '#10B981'; // Verde para positivo
  if (sentiment < -0.2) return '#EF4444'; // Rojo para negativo
  return '#6B7280'; // Gris para neutral
};

const getGrowthIcon = (growthRate: number) => {
  if (growthRate > 0.1) return <TrendingUp className="w-4 h-4 text-green-500" />;
  if (growthRate < -0.1) return <TrendingDown className="w-4 h-4 text-red-500" />;
  return <Hash className="w-4 h-4 text-gray-400" />;
};

// Componente de nube de palabras
const WordCloud: React.FC<{ data: WordCloudData[]; onWordClick?: (word: string) => void }> = ({
  data,
  onWordClick
}) => {
  // Calcular tamaños basados en pesos
  const maxWeight = Math.max(...data.map(d => d.weight));
  const minWeight = Math.min(...data.map(d => d.weight));
  
  return (
    <div className="relative w-full h-96 bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-6 overflow-hidden">
      <div className="absolute inset-0 bg-white/30 backdrop-blur-sm rounded-lg" />
      <div className="relative h-full flex flex-wrap items-center justify-center gap-4">
        {data.map((item, index) => {
          const sizeRatio = (item.weight - minWeight) / (maxWeight - minWeight);
          const fontSize = Math.max(12, Math.min(48, 16 + sizeRatio * 32));
          const opacity = 0.6 + sizeRatio * 0.4;
          
          return (
            <button
              key={`${item.word}-${index}`}
              onClick={() => onWordClick?.(item.word)}
              className="transition-all duration-200 hover:scale-110 hover:shadow-lg cursor-pointer"
              style={{
                fontSize: `${fontSize}px`,
                color: getSentimentColor(item.sentiment),
                opacity,
                fontWeight: sizeRatio > 0.7 ? 'bold' : 'normal'
              }}
            >
              {item.word}
            </button>
          );
        })}
      </div>
    </div>
  );
};

// Componente de tooltip para scatter plot
const CustomScatterTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{
    payload: TopicData;
  }>;
}> = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-xs">
        <h4 className="font-semibold text-gray-900 mb-2">{data.name}</h4>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Artículos:</span>
            <span className="font-medium">{data.count}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Sentimiento:</span>
            <span 
              className="font-medium"
              style={{ color: getSentimentColor(data.sentiment) }}
            >
              {(data.sentiment * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Crecimiento:</span>
            <span 
              className="font-medium"
              style={{ color: data.growth_rate > 0 ? '#10B981' : '#EF4444' }}
            >
              {(data.growth_rate * 100).toFixed(1)}%
            </span>
          </div>
          {data.relevance_score && (
            <div className="flex justify-between">
              <span className="text-gray-600">Relevancia:</span>
              <span className="font-medium">{(data.relevance_score * 100).toFixed(1)}%</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

export const TopicAnalysis: React.FC<TopicAnalysisProps> = ({ data, loading }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [activeView, setActiveView] = useState<'cloud' | 'scatter' | 'list'>('cloud');

  // Procesar y filtrar datos
  const filteredData = useMemo(() => {
    let filtered = data;

    // Filtrar por búsqueda
    if (searchTerm) {
      filtered = filtered.filter(topic =>
        topic.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtrar por categoría
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(topic => topic.category === selectedCategory);
    }

    return filtered;
  }, [data, searchTerm, selectedCategory]);

  // Obtener categorías únicas
  const categories = useMemo(() => {
    const cats = Array.from(new Set(data.map(topic => topic.category).filter(Boolean)));
    return ['all', ...cats];
  }, [data]);

  // Preparar datos para nube de palabras
  const wordCloudData: WordCloudData[] = useMemo(() => {
    return filteredData.slice(0, 50).map(topic => ({
      word: topic.name,
      weight: topic.count,
      sentiment: topic.sentiment,
      category: topic.category
    }));
  }, [filteredData]);

  // Preparar datos para scatter plot
  const scatterData = useMemo(() => {
    return filteredData.map(topic => ({
      ...topic,
      x: topic.sentiment,
      y: topic.growth_rate,
      z: Math.sqrt(topic.count) * 5 // Tamaño de la burbuja
    }));
  }, [filteredData]);

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
            Análisis de Temas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-96 bg-gray-100 rounded animate-pulse" />
            <div className="flex gap-4">
              <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
              <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
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
              Análisis de Temas
              <Badge variant="secondary">{filteredData.length} temas</Badge>
            </CardTitle>
            <CardDescription>
              Temas más relevantes y sus tendencias
            </CardDescription>
          </div>
          
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Buscar temas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 w-48"
              />
            </div>
            
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              {categories.map(category => (
                <option key={category} value={category}>
                  {category === 'all' ? 'Todas las categorías' : category}
                </option>
              ))}
            </select>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeView} onValueChange={(value) => setActiveView(value as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="cloud">Nube de Palabras</TabsTrigger>
            <TabsTrigger value="scatter">Análisis Comparativo</TabsTrigger>
            <TabsTrigger value="list">Lista Detallada</TabsTrigger>
          </TabsList>

          <TabsContent value="cloud" className="mt-6">
            <div className="space-y-4">
              <WordCloud data={wordCloudData} onWordClick={setSearchTerm} />
              
              <div className="flex items-center justify-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full" />
                  <span>Sentimiento Positivo</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-gray-500 rounded-full" />
                  <span>Sentimiento Neutral</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full" />
                  <span>Sentimiento Negativo</span>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="scatter" className="mt-6">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-900">
                  Temas por Sentimiento vs Crecimiento
                </h4>
                <div className="text-sm text-gray-500">
                  Tamaño = Número de artículos
                </div>
              </div>
              
              <ResponsiveContainer width="100%" height={500}>
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    type="number" 
                    dataKey="x" 
                    domain={[-1, 1]}
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                    label={{ value: 'Sentimiento', position: 'insideBottom', offset: -10 }}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="y" 
                    domain={[-1, 1]}
                    tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                    label={{ value: 'Crecimiento', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip content={<CustomScatterTooltip />} />
                  <Scatter data={scatterData}>
                    {scatterData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={getSentimentColor(entry.sentiment)}
                        fillOpacity={0.7}
                        stroke={getSentimentColor(entry.sentiment)}
                        strokeWidth={2}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center p-3 bg-green-50 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {scatterData.filter(d => d.sentiment > 0.2).length}
                  </div>
                  <div className="text-green-700">Positivos</div>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-600">
                    {scatterData.filter(d => Math.abs(d.sentiment) <= 0.2).length}
                  </div>
                  <div className="text-gray-700">Neutrales</div>
                </div>
                <div className="text-center p-3 bg-red-50 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {scatterData.filter(d => d.sentiment < -0.2).length}
                  </div>
                  <div className="text-red-700">Negativos</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {scatterData.filter(d => d.growth_rate > 0.1).length}
                  </div>
                  <div className="text-blue-700">En Crecimiento</div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="list" className="mt-6">
            <div className="space-y-3">
              {filteredData.slice(0, 20).map((topic, index) => (
                <div
                  key={`${topic.name}-${index}`}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h4 className="font-medium text-gray-900">{topic.name}</h4>
                      {getGrowthIcon(topic.growth_rate)}
                      {topic.category && (
                        <Badge variant="outline" className="text-xs">
                          {topic.category}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                      <span>{topic.count} artículos</span>
                      <span 
                        style={{ color: getSentimentColor(topic.sentiment) }}
                      >
                        Sentimiento: {(topic.sentiment * 100).toFixed(1)}%
                      </span>
                      <span
                        style={{ 
                          color: topic.growth_rate > 0 ? '#10B981' : topic.growth_rate < 0 ? '#EF4444' : '#6B7280' 
                        }}
                      >
                        Crecimiento: {(topic.growth_rate * 100).toFixed(1)}%
                      </span>
                      {topic.relevance_score && (
                        <span>Relevancia: {(topic.relevance_score * 100).toFixed(1)}%</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="w-16 h-2 bg-gray-200 rounded-full">
                      <div
                        className="h-2 rounded-full transition-all duration-300"
                        style={{
                          backgroundColor: getSentimentColor(topic.sentiment),
                          width: `${Math.abs(topic.sentiment * 100)}%`,
                          marginLeft: topic.sentiment < 0 ? `${100 - Math.abs(topic.sentiment * 100)}%` : '0'
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default TopicAnalysis;
