/**
 * Panel de insights de IA con resumen de análisis
 */

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AIInsight } from './types';
import { 
  Brain, 
  TrendingUp, 
  AlertTriangle, 
  Lightbulb, 
  Eye,
  Clock,
  ArrowUp,
  ArrowDown,
  Minus,
  Filter,
  RefreshCw,
  ChevronRight,
  Target,
  Zap
} from 'lucide-react';

interface AIInsightsProps {
  insights: AIInsight[];
  loading?: boolean;
  onRefresh?: () => void;
}

const getInsightIcon = (type: AIInsight['type']) => {
  switch (type) {
    case 'sentiment':
      return <Brain className="w-5 h-5" />;
    case 'trend':
      return <TrendingUp className="w-5 h-5" />;
    case 'anomaly':
      return <AlertTriangle className="w-5 h-5" />;
    case 'prediction':
      return <Eye className="w-5 h-5" />;
    case 'alert':
      return <Zap className="w-5 h-5" />;
    default:
      return <Lightbulb className="w-5 h-5" />;
  }
};

const getInsightColor = (type: AIInsight['type']) => {
  switch (type) {
    case 'sentiment':
      return 'text-blue-600 bg-blue-100 border-blue-200';
    case 'trend':
      return 'text-green-600 bg-green-100 border-green-200';
    case 'anomaly':
      return 'text-orange-600 bg-orange-100 border-orange-200';
    case 'prediction':
      return 'text-purple-600 bg-purple-100 border-purple-200';
    case 'alert':
      return 'text-red-600 bg-red-100 border-red-200';
    default:
      return 'text-gray-600 bg-gray-100 border-gray-200';
  }
};

const getImpactColor = (impact: AIInsight['impact']) => {
  switch (impact) {
    case 'high':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'medium':
      return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    case 'low':
      return 'text-green-600 bg-green-50 border-green-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return '#10B981'; // Verde
  if (confidence >= 0.6) return '#F59E0B'; // Ámbar
  return '#EF4444'; // Rojo
};

const getConfidenceIcon = (confidence: number) => {
  if (confidence >= 0.8) return <ArrowUp className="w-4 h-4" />;
  if (confidence >= 0.6) return <Minus className="w-4 h-4" />;
  return <ArrowDown className="w-4 h-4" />;
};

const InsightCard: React.FC<{ insight: AIInsight; onExpand?: (insight: AIInsight) => void }> = ({
  insight,
  onExpand
}) => {
  const timeAgo = useMemo(() => {
    const now = new Date();
    const diff = now.getTime() - insight.timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d`;
    if (hours > 0) return `${hours}h`;
    return `${minutes}m`;
  }, [insight.timestamp]);

  return (
    <Card className="border-l-4 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onExpand?.(insight)}
          style={{ borderLeftColor: getInsightColor(insight.type).split(' ')[2].replace('border-', '') }}>
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${getInsightColor(insight.type)}`}>
            {getInsightIcon(insight.type)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <h4 className="font-medium text-gray-900 leading-tight">
                  {insight.title}
                </h4>
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                  {insight.description}
                </p>
              </div>
              
              <ChevronRight className="w-4 h-4 text-gray-400 mt-1" />
            </div>
            
            <div className="flex items-center gap-3 mt-3">
              <Badge variant="outline" className={getImpactColor(insight.impact)}>
                {insight.impact === 'high' ? 'Alto' : 
                 insight.impact === 'medium' ? 'Medio' : 'Bajo'} Impacto
              </Badge>
              
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: getConfidenceColor(insight.confidence) }}
                />
                <span>{(insight.confidence * 100).toFixed(0)}% confianza</span>
              </div>
              
              <div className="flex items-center gap-1 text-sm text-gray-500">
                <Clock className="w-3 h-3" />
                <span>{timeAgo}</span>
              </div>
            </div>
            
            <div className="flex items-center gap-2 mt-2">
              <div className="flex items-center gap-1">
                {getConfidenceIcon(insight.confidence)}
                <span 
                  className="text-sm font-medium"
                  style={{ color: getConfidenceColor(insight.confidence) }}
                >
                  {insight.confidence >= 0.8 ? 'Alta confianza' :
                   insight.confidence >= 0.6 ? 'Confianza media' : 'Baja confianza'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const InsightsSummary: React.FC<{ insights: AIInsight[] }> = ({ insights }) => {
  const summary = useMemo(() => {
    const total = insights.length;
    const byType = insights.reduce((acc, insight) => {
      acc[insight.type] = (acc[insight.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    const byImpact = insights.reduce((acc, insight) => {
      acc[insight.impact] = (acc[insight.impact] || 0) + 1;
      return acc;
    }, {} as Record<AIInsight['impact'], number>);
    
    const avgConfidence = insights.reduce((sum, insight) => sum + insight.confidence, 0) / total;
    
    return { total, byType, byImpact, avgConfidence };
  }, [insights]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Lightbulb className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{summary.total}</div>
              <div className="text-sm text-gray-600">Total Insights</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{summary.byImpact.high || 0}</div>
              <div className="text-sm text-gray-600">Alto Impacto</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Eye className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">
                {(summary.avgConfidence * 100).toFixed(0)}%
              </div>
              <div className="text-sm text-gray-600">Confianza Promedio</div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{summary.byType.trend || 0}</div>
              <div className="text-sm text-gray-600">Tendencias</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export const AIInsights: React.FC<AIInsightsProps> = ({ insights, loading, onRefresh }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [filterImpact, setFilterImpact] = useState<string>('all');
  const [expandedInsight, setExpandedInsight] = useState<AIInsight | null>(null);

  const filteredInsights = useMemo(() => {
    return insights.filter(insight => {
      const typeMatch = filterType === 'all' || insight.type === filterType;
      const impactMatch = filterImpact === 'all' || insight.impact === filterImpact;
      return typeMatch && impactMatch;
    });
  }, [insights, filterType, filterImpact]);

  const insightTypes = useMemo(() => {
    const types = Array.from(new Set(insights.map(i => i.type)));
    return ['all', ...types];
  }, [insights]);

  const impactLevels = ['all', 'high', 'medium', 'low'];

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
            Insights de IA
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-24 bg-gray-100 rounded animate-pulse" />
            <div className="space-y-3">
              <div className="h-16 bg-gray-200 rounded animate-pulse" />
              <div className="h-16 bg-gray-200 rounded animate-pulse" />
              <div className="h-16 bg-gray-200 rounded animate-pulse" />
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
              Insights de IA
              <Badge variant="secondary">{filteredInsights.length}</Badge>
            </CardTitle>
            <CardDescription>
              Análisis inteligente y recomendaciones automáticas
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualizar
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="overview">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="overview">Resumen</TabsTrigger>
            <TabsTrigger value="insights">Insights Detallados</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="space-y-6">
              {/* Resumen de métricas */}
              <InsightsSummary insights={insights} />
              
              {/* Distribución por tipo */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Distribución por Tipo</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(
                      insights.reduce((acc, insight) => {
                        acc[insight.type] = (acc[insight.type] || 0) + 1;
                        return acc;
                      }, {} as Record<string, number>)
                    ).map(([type, count]) => (
                      <div key={type} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`p-1 rounded ${getInsightColor(type as AIInsight['type'])}`}>
                            {getInsightIcon(type as AIInsight['type'])}
                          </div>
                          <span className="capitalize font-medium">{type}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-600">{count}</span>
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className="h-2 rounded-full"
                              style={{
                                backgroundColor: getInsightColor(type as AIInsight['type']).split(' ')[1],
                                width: `${(count / insights.length) * 100}%`
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="insights" className="mt-6">
            <div className="space-y-4">
              {/* Filtros */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-500" />
                  <span className="text-sm font-medium text-gray-700">Filtros:</span>
                </div>
                
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                >
                  {insightTypes.map(type => (
                    <option key={type} value={type}>
                      {type === 'all' ? 'Todos los tipos' : type.charAt(0).toUpperCase() + type.slice(1)}
                    </option>
                  ))}
                </select>
                
                <select
                  value={filterImpact}
                  onChange={(e) => setFilterImpact(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                >
                  {impactLevels.map(impact => (
                    <option key={impact} value={impact}>
                      {impact === 'all' ? 'Todos los impactos' : 
                       impact === 'high' ? 'Alto impacto' :
                       impact === 'medium' ? 'Impacto medio' : 'Bajo impacto'}
                    </option>
                  ))}
                </select>
              </div>
              
              {/* Lista de insights */}
              <ScrollArea className="h-96">
                <div className="space-y-3 pr-4">
                  {filteredInsights.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p>No hay insights que coincidan con los filtros seleccionados</p>
                    </div>
                  ) : (
                    filteredInsights.map((insight) => (
                      <InsightCard
                        key={insight.id}
                        insight={insight}
                        onExpand={setExpandedInsight}
                      />
                    ))
                  )}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>
        </Tabs>
        
        {/* Modal de insight expandido */}
        {expandedInsight && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${getInsightColor(expandedInsight.type)}`}>
                      {getInsightIcon(expandedInsight.type)}
                    </div>
                    <div>
                      <CardTitle className="text-xl">{expandedInsight.title}</CardTitle>
                      <CardDescription className="text-base mt-1">
                        {expandedInsight.description}
                      </CardDescription>
                    </div>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => setExpandedInsight(null)}
                  >
                    ✕
                  </Button>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <Badge variant="outline" className={getImpactColor(expandedInsight.impact)}>
                      Impacto {expandedInsight.impact === 'high' ? 'Alto' : 
                              expandedInsight.impact === 'medium' ? 'Medio' : 'Bajo'}
                    </Badge>
                    
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getConfidenceColor(expandedInsight.confidence) }}
                      />
                      <span className="font-medium">
                        {(expandedInsight.confidence * 100).toFixed(0)}% confianza
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-1 text-sm text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>{expandedInsight.timestamp.toLocaleString()}</span>
                    </div>
                  </div>
                  
                  {expandedInsight.related_data && (
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <h4 className="font-medium text-gray-900 mb-2">Datos Relacionados</h4>
                      <pre className="text-sm text-gray-600 whitespace-pre-wrap">
                        {JSON.stringify(expandedInsight.related_data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AIInsights;
