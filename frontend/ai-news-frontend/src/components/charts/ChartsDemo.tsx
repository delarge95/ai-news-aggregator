import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  TrendingUp, 
  PieChart, 
  BarChart3, 
  Activity,
  Download,
  Settings,
  RefreshCw
} from 'lucide-react';

// Importar todos los componentes de gráficos
import {
  ChartsRegistryProvider,
  useChartsRegistry,
  SentimentTrendsChart,
  TopicDistributionChart,
  SourcePerformanceChart,
  RealtimeMetricsChart,
  CustomTooltip,
  CustomLegend,
  chartThemes,
  exportChart,
  useChartTheme
} from './index';

// Datos de ejemplo para SentimentTrendsChart
const sentimentData = [
  { 
    date: '2024-01-01', 
    positive: 65, 
    negative: 20, 
    neutral: 15, 
    average: 72, 
    trend: 'up',
    volume: 1200
  },
  { 
    date: '2024-01-02', 
    positive: 70, 
    negative: 18, 
    neutral: 12, 
    average: 76, 
    trend: 'up',
    volume: 1350
  },
  { 
    date: '2024-01-03', 
    positive: 68, 
    negative: 22, 
    neutral: 10, 
    average: 73, 
    trend: 'down',
    volume: 1100
  },
  { 
    date: '2024-01-04', 
    positive: 72, 
    negative: 15, 
    neutral: 13, 
    average: 78, 
    trend: 'up',
    volume: 1450
  },
  { 
    date: '2024-01-05', 
    positive: 75, 
    negative: 12, 
    neutral: 13, 
    average: 81, 
    trend: 'up',
    volume: 1600
  },
];

// Datos de ejemplo para TopicDistributionChart
const topicData = [
  { name: 'Tecnología', value: 350, percentage: 35, trend: 5.2, articles: 350 },
  { name: 'Política', value: 280, percentage: 28, trend: -2.1, articles: 280 },
  { name: 'Economía', value: 200, percentage: 20, trend: 3.8, articles: 200 },
  { name: 'Deportes', value: 120, percentage: 12, trend: 1.5, articles: 120 },
  { name: 'Cultura', value: 50, percentage: 5, trend: -1.2, articles: 50 },
];

// Datos de ejemplo para SourcePerformanceChart
const sourceData = [
  { 
    name: 'CNN Español', 
    articles: 450, 
    engagement: 8500, 
    reach: 125000, 
    quality: 85, 
    responseTime: 1.2, 
    accuracy: 92, 
    trend: 8.5, 
    category: 'Noticias', 
    verified: true 
  },
  { 
    name: 'BBC Mundo', 
    articles: 380, 
    engagement: 9200, 
    reach: 110000, 
    quality: 88, 
    responseTime: 1.8, 
    accuracy: 94, 
    trend: 6.2, 
    category: 'Noticias', 
    verified: true 
  },
  { 
    name: 'El País', 
    articles: 320, 
    engagement: 7800, 
    reach: 95000, 
    quality: 82, 
    responseTime: 2.1, 
    accuracy: 89, 
    trend: 4.8, 
    category: 'Noticias', 
    verified: true 
  },
  { 
    name: 'RT Español', 
    articles: 290, 
    engagement: 6500, 
    reach: 88000, 
    quality: 79, 
    responseTime: 1.5, 
    accuracy: 87, 
    trend: -1.3, 
    category: 'Noticias', 
    verified: false 
  },
  { 
    name: 'TeleSur', 
    articles: 250, 
    engagement: 5800, 
    reach: 72000, 
    quality: 76, 
    responseTime: 2.5, 
    accuracy: 85, 
    trend: 2.1, 
    category: 'Noticias', 
    verified: true 
  },
];

// Métricas para el gráfico en tiempo real
const realtimeMetrics = [
  'engagement', 
  'error_rate', 
  'response_time', 
  'throughput', 
  'active_users'
];

// Componente principal de demostración
const ChartsDemo: React.FC = () => {
  const { theme } = useChartTheme();
  const [activeTab, setActiveTab] = React.useState('sentiment');
  const [lastUpdate, setLastUpdate] = React.useState(new Date());

  // Manejadores de eventos
  const handleDataPointClick = (data: any, index: number) => {
    console.log('Data point clicked:', data, index);
  };

  const handleTopicClick = (topic: any) => {
    console.log('Topic clicked:', topic);
  };

  const handleSourceClick = (source: any) => {
    console.log('Source clicked:', source);
  };

  const handleDataUpdate = (newData: any[]) => {
    console.log('Real-time data update:', newData);
    setLastUpdate(new Date());
  };

  const handleAlert = (metric: string, value: number, status: string) => {
    console.log('Alert triggered:', { metric, value, status });
  };

  const handleExportAll = async () => {
    // Simular exportación de todos los gráficos
    console.log('Exporting all charts...');
    // Aquí se implementaría la lógica de exportación masiva
  };

  // Actualizar timestamp cada minuto
  React.useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date());
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Sistema de Gráficos - AI News Aggregator
            </h1>
            <p className="text-gray-600 mt-2">
              Demostración completa del sistema de gráficos con Recharts
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            <Badge variant="outline" className="flex items-center gap-2">
              <RefreshCw className="w-3 h-3" />
              Actualizado: {lastUpdate.toLocaleTimeString('es-ES')}
            </Badge>
            
            <Button onClick={handleExportAll} className="gap-2">
              <Download className="w-4 h-4" />
              Exportar Todos
            </Button>
            
            <Button variant="outline">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Estadísticas generales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Artículos Procesados</p>
                <p className="text-2xl font-bold text-gray-900">24,567</p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500" />
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <TrendingUp className="w-4 h-4 mr-1" />
              +12.5% vs. mes anterior
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Fuentes Activas</p>
                <p className="text-2xl font-bold text-gray-900">127</p>
              </div>
              <BarChart3 className="w-8 h-8 text-green-500" />
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <TrendingUp className="w-4 h-4 mr-1" />
              +8 nuevas esta semana
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Engagement Promedio</p>
                <p className="text-2xl font-bold text-gray-900">78.4%</p>
              </div>
              <Activity className="w-8 h-8 text-purple-500" />
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <TrendingUp className="w-4 h-4 mr-1" />
              +3.2% vs. semana anterior
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Tiempo de Respuesta</p>
                <p className="text-2xl font-bold text-gray-900">1.2s</p>
              </div>
              <PieChart className="w-8 h-8 text-orange-500" />
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <TrendingUp className="w-4 h-4 mr-1" />
              -0.3s más rápido
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs para diferentes tipos de gráficos */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="sentiment" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Sentimientos
          </TabsTrigger>
          <TabsTrigger value="topics" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            Temas
          </TabsTrigger>
          <TabsTrigger value="sources" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Fuentes
          </TabsTrigger>
          <TabsTrigger value="realtime" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            Tiempo Real
          </TabsTrigger>
        </TabsList>

        {/* Tab de Sentimientos */}
        <TabsContent value="sentiment">
          <SentimentTrendsChart
            data={sentimentData}
            height={500}
            showBrush={true}
            showTrendLine={true}
            showAverageLine={true}
            showVolume={true}
            onDataPointClick={handleDataPointClick}
            showExport={true}
          />
        </TabsContent>

        {/* Tab de Distribución de Temas */}
        <TabsContent value="topics">
          <TopicDistributionChart
            data={topicData}
            chartType="both"
            height={500}
            showPercentage={true}
            showTrend={true}
            showLabels={true}
            maxItems={10}
            onTopicClick={handleTopicClick}
            showExport={true}
          />
        </TabsContent>

        {/* Tab de Rendimiento de Fuentes */}
        <TabsContent value="sources">
          <SourcePerformanceChart
            data={sourceData}
            height={600}
            showBrush={true}
            showTrend={true}
            showQualityMetrics={true}
            showComparison={true}
            maxSources={10}
            sortBy="engagement"
            onSourceClick={handleSourceClick}
            showExport={true}
          />
        </TabsContent>

        {/* Tab de Métricas en Tiempo Real */}
        <TabsContent value="realtime">
          <RealtimeMetricsChart
            height={500}
            maxDataPoints={50}
            updateInterval={3000}
            autoStart={true}
            showAlerts={true}
            showTrends={true}
            metrics={realtimeMetrics}
            onDataUpdate={handleDataUpdate}
            onAlert={handleAlert}
          />
        </TabsContent>
      </Tabs>

      {/* Información adicional */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Características del Sistema</CardTitle>
            <CardDescription>
              Funcionalidades implementadas en el sistema de gráficos
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Badge variant="secondary">✓</Badge>
                <span>Gráficos responsivos con tema automático</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">✓</Badge>
                <span>Animaciones suaves y transiciones</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">✓</Badge>
                <span>Exportación a PNG y SVG</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">✓</Badge>
                <span>Tooltips y leyendas personalizadas</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">✓</Badge>
                <span>Actualizaciones en tiempo real</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="secondary">✓</Badge>
                <span>Filtros interactivos</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Próximas Funcionalidades</CardTitle>
            <CardDescription>
              Características planificadas para futuras versiones
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Badge variant="outline">•</Badge>
                <span>Exportación a PDF</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="outline">•</Badge>
                <span>Gráficos 3D y WebGL</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="outline">•</Badge>
                <span>Análisis predictivo con ML</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="outline">•</Badge>
                <span>Dashboards personalizables</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="outline">•</Badge>
                <span>Alertas inteligentes</span>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="outline">•</Badge>
                <span>Colaboración en tiempo real</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Componente principal que envuelve el proveedor
export const ChartsDemoPage: React.FC = () => {
  return (
    <ChartsRegistryProvider>
      <ChartsDemo />
    </ChartsRegistryProvider>
  );
};

export default ChartsDemoPage;