/**
 * Dashboard principal de análisis IA
 * Integra todos los componentes de análisis
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  AnalyticsProvider,
  useAnalyticsContext 
} from './AnalyticsProvider';
import { 
  SentimentChart,
  TopicAnalysis,
  RelevanceScoreComponent,
  AIInsights,
  ComparisonChart
} from './index';
import { AnalyticsFilters } from './types';
import { 
  Brain, 
  BarChart3, 
  TrendingUp, 
  Target, 
  Lightbulb, 
  Calendar,
  Download,
  RefreshCw,
  Settings,
  Filter,
  Search
} from 'lucide-react';

const AnalyticsDashboard: React.FC = () => {
  const {
    sentimentData,
    topicData,
    relevanceScore,
    aiInsights,
    comparisonData,
    loading,
    error,
    filters,
    updateFilters,
    refetch
  } = useAnalyticsContext();

  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const handleFilterChange = (newFilters: Partial<AnalyticsFilters>) => {
    updateFilters({ ...filters, ...newFilters });
  };

  const handleExport = () => {
    // TODO: Implementar exportación de datos
    console.log('Exportando datos de análisis...');
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-7xl mx-auto">
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 text-red-800">
                <Target className="w-6 h-6" />
                <div>
                  <h3 className="font-semibold">Error al cargar análisis</h3>
                  <p className="text-sm">{error}</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={refetch}
                    className="mt-2"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Reintentar
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Brain className="w-6 h-6 text-blue-600" />
                </div>
                Panel de Análisis IA
              </h1>
              <p className="text-gray-600 mt-1">
                Análisis inteligente de noticias y tendencias
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Buscar análisis..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              
              <Button variant="outline" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                Exportar
              </Button>
              
              <Button onClick={refetch} disabled={loading}>
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Actualizar
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="max-w-7xl mx-auto px-6 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          {/* Navegación de pestañas */}
          <div className="flex items-center justify-between mb-6">
            <TabsList className="grid w-fit grid-cols-6">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                Resumen
              </TabsTrigger>
              <TabsTrigger value="sentiment" className="flex items-center gap-2">
                <Brain className="w-4 h-4" />
                Sentimiento
              </TabsTrigger>
              <TabsTrigger value="topics" className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Temas
              </TabsTrigger>
              <TabsTrigger value="relevance" className="flex items-center gap-2">
                <Target className="w-4 h-4" />
                Relevancia
              </TabsTrigger>
              <TabsTrigger value="insights" className="flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Insights
              </TabsTrigger>
              <TabsTrigger value="comparison" className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Comparación
              </TabsTrigger>
            </TabsList>
            
            {/* Filtros rápidos */}
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="cursor-pointer"
                     onClick={() => handleFilterChange({ granularity: 'daily' })}>
                Diario
              </Badge>
              <Badge variant="outline" className="cursor-pointer"
                     onClick={() => handleFilterChange({ granularity: 'weekly' })}>
                Semanal
              </Badge>
              <Badge variant="outline" className="cursor-pointer"
                     onClick={() => handleFilterChange({ granularity: 'monthly' })}>
                Mensual
              </Badge>
            </div>
          </div>

          {/* Pestaña de Resumen */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Score de Relevancia */}
              {relevanceScore && (
                <RelevanceScoreComponent score={relevanceScore} loading={loading} />
              )}
              
              {/* Insights principales */}
              <AIInsights insights={aiInsights} loading={loading} onRefresh={refetch} />
            </div>
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              {/* Análisis de Sentimiento */}
              {sentimentData && (
                <SentimentChart data={sentimentData} loading={loading} />
              )}
              
              {/* Análisis de Temas */}
              <TopicAnalysis data={topicData} loading={loading} />
            </div>
            
            {/* Comparación de tendencias */}
            {comparisonData && (
              <ComparisonChart data={comparisonData} loading={loading} onRefresh={refetch} />
            )}
          </TabsContent>

          {/* Pestañas específicas */}
          <TabsContent value="sentiment" className="space-y-6">
            {sentimentData && (
              <SentimentChart data={sentimentData} loading={loading} />
            )}
          </TabsContent>

          <TabsContent value="topics" className="space-y-6">
            <TopicAnalysis data={topicData} loading={loading} />
          </TabsContent>

          <TabsContent value="relevance" className="space-y-6">
            {relevanceScore && (
              <RelevanceScoreComponent score={relevanceScore} loading={loading} />
            )}
          </TabsContent>

          <TabsContent value="insights" className="space-y-6">
            <AIInsights insights={aiInsights} loading={loading} onRefresh={refetch} />
          </TabsContent>

          <TabsContent value="comparison" className="space-y-6">
            {comparisonData && (
              <ComparisonChart data={comparisonData} loading={loading} onRefresh={refetch} />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Wrapper component with provider
const AnalyticsDashboardWithProvider: React.FC = () => {
  return (
    <AnalyticsProvider>
      <AnalyticsDashboard />
    </AnalyticsProvider>
  );
};

export default AnalyticsDashboardWithProvider;
