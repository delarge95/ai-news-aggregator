/**
 * Componente de score de relevancia con indicadores visuales
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RelevanceScore } from './types';
import { 
  Star, 
  Shield, 
  Heart, 
  Award, 
  TrendingUp, 
  Info,
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react';

interface RelevanceScoreProps {
  score: RelevanceScore;
  loading?: boolean;
}

const getScoreColor = (score: number): string => {
  if (score >= 80) return '#10B981'; // Verde
  if (score >= 60) return '#F59E0B'; // Ámbar
  if (score >= 40) return '#EF4444'; // Rojo
  return '#6B7280'; // Gris
};

const getScoreIcon = (score: number) => {
  if (score >= 80) return <CheckCircle className="w-5 h-5 text-green-500" />;
  if (score >= 60) return <AlertCircle className="w-5 h-5 text-amber-500" />;
  return <XCircle className="w-5 h-5 text-red-500" />;
};

const getScoreLevel = (score: number): { level: string; color: string } => {
  if (score >= 90) return { level: 'Excelente', color: 'text-green-600' };
  if (score >= 80) return { level: 'Muy Bueno', color: 'text-green-500' };
  if (score >= 70) return { level: 'Bueno', color: 'text-blue-500' };
  if (score >= 60) return { level: 'Regular', color: 'text-amber-500' };
  if (score >= 40) return { level: 'Deficiente', color: 'text-red-500' };
  return { level: 'Crítico', color: 'text-red-600' };
};

const ScoreIndicator: React.FC<{
  icon: React.ReactNode;
  label: string;
  score: number;
  maxScore?: number;
  description?: string;
}> = ({ icon, label, score, maxScore = 100, description }) => {
  const percentage = (score / maxScore) * 100;
  const color = getScoreColor(percentage);
  const scoreLevel = getScoreLevel(percentage);
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-gray-900">{label}</span>
        </div>
        <div className="flex items-center gap-2">
          {getScoreIcon(percentage)}
          <span className="text-lg font-bold" style={{ color }}>
            {Math.round(percentage)}
          </span>
          <span className="text-sm text-gray-500">/100</span>
        </div>
      </div>
      
      <div className="space-y-2">
        <Progress 
          value={percentage} 
          className="h-3"
          style={{ 
            '--progress-foreground': color 
          } as React.CSSProperties}
        />
        
        <div className="flex items-center justify-between">
          <span className={`text-sm font-medium ${scoreLevel.color}`}>
            {scoreLevel.level}
          </span>
          <span className="text-xs text-gray-500">
            {score} {score !== maxScore && `/ ${maxScore}`}
          </span>
        </div>
        
        {description && (
          <p className="text-xs text-gray-600">{description}</p>
        )}
      </div>
    </div>
  );
};

const CircularProgress: React.FC<{ 
  score: number; 
  size?: number; 
  strokeWidth?: number; 
  showLabel?: boolean;
  label?: string;
}> = ({ 
  score, 
  size = 120, 
  strokeWidth = 8, 
  showLabel = true,
  label = 'Overall'
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const color = getScoreColor(score);
  const scoreLevel = getScoreLevel(score);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-in-out"
        />
      </svg>
      {showLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <div className="text-2xl font-bold" style={{ color }}>
            {Math.round(score)}
          </div>
          <div className="text-xs text-gray-500">
            {scoreLevel.level}
          </div>
          {label && (
            <div className="text-xs text-gray-600 mt-1">
              {label}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const RelevanceScoreComponent: React.FC<RelevanceScoreProps> = ({ score, loading }) => {
  const [activeView, setActiveView] = useState<'overview' | 'detailed' | 'breakdown'>('overview');

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="w-5 h-5 bg-gray-200 rounded animate-pulse" />
            Score de Relevancia
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="h-32 bg-gray-100 rounded animate-pulse" />
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
              <div className="h-4 bg-gray-200 rounded animate-pulse" />
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
              Score de Relevancia
              <Badge variant="secondary">General</Badge>
            </CardTitle>
            <CardDescription>
              Evaluación integral de la calidad y relevancia del contenido
            </CardDescription>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold" style={{ color: getScoreColor(score.overall) }}>
              {Math.round(score.overall)}
            </div>
            <div className="text-sm text-gray-500">
              {getScoreLevel(score.overall).level}
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={activeView} onValueChange={(value) => setActiveView(value as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Resumen</TabsTrigger>
            <TabsTrigger value="detailed">Detalles</TabsTrigger>
            <TabsTrigger value="breakdown">Desglose</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Score general */}
              <div className="flex flex-col items-center space-y-4">
                <CircularProgress 
                  score={score.overall} 
                  size={150} 
                  strokeWidth={10}
                  label="Score General"
                />
                
                <div className="text-center space-y-2">
                  <p className="text-sm text-gray-600">
                    {score.overall >= 80 
                      ? 'Excelente calidad y relevancia del contenido'
                      : score.overall >= 60
                      ? 'Buena calidad con oportunidades de mejora'
                      : 'Necesita mejoras significativas'
                    }
                  </p>
                  
                  <div className="flex items-center justify-center gap-2">
                    {getScoreIcon(score.overall)}
                    <span className={`text-sm font-medium ${getScoreLevel(score.overall).color}`}>
                      {getScoreLevel(score.overall).level}
                    </span>
                  </div>
                </div>
              </div>

              {/* Scores por categoría */}
              <div className="space-y-6">
                <ScoreIndicator
                  icon={<Shield className="w-5 h-5 text-blue-500" />}
                  label="Credibilidad"
                  score={score.credibility}
                  description="Fuentes confiables y verificadas"
                />
                
                <ScoreIndicator
                  icon={<Heart className="w-5 h-5 text-red-500" />}
                  label="Engagement"
                  score={score.engagement}
                  description="Nivel de interacción de usuarios"
                />
                
                <ScoreIndicator
                  icon={<Award className="w-5 h-5 text-purple-500" />}
                  label="Calidad"
                  score={score.quality}
                  description="Calidad del contenido generado"
                />
                
                <ScoreIndicator
                  icon={<TrendingUp className="w-5 h-5 text-green-500" />}
                  label="Tendencias"
                  score={score.trends}
                  description="Relevancia de temas trending"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="detailed" className="mt-6">
            <div className="space-y-6">
              <h4 className="font-medium text-gray-900">Análisis Detallado por Métrica</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <ScoreIndicator
                    icon={<Shield className="w-5 h-5 text-blue-500" />}
                    label="Credibilidad de Fuentes"
                    score={score.credibility}
                    description={
                      <div className="text-xs space-y-1">
                        <div>• Diversidad de fuentes: {Math.min(100, score.credibility * 1.2)}%</div>
                        <div>• Reputación verificada: {Math.min(100, score.credibility * 0.9)}%</div>
                        <div>• Historial de confiabilidad: {Math.min(100, score.credibility * 0.85)}%</div>
                      </div>
                    }
                  />
                  
                  <ScoreIndicator
                    icon={<Heart className="w-5 h-5 text-red-500" />}
                    label="Engagement de Usuarios"
                    score={score.engagement}
                    description={
                      <div className="text-xs space-y-1">
                        <div>• Tasa de lectura: {Math.min(100, score.engagement * 1.1)}%</div>
                        <div>• Tiempo en página: {Math.min(100, score.engagement * 0.95)}%</div>
                        <div>• Interacciones sociales: {Math.min(100, score.engagement * 0.8)}%</div>
                      </div>
                    }
                  />
                </div>
                
                <div className="space-y-4">
                  <ScoreIndicator
                    icon={<Award className="w-5 h-5 text-purple-500" />}
                    label="Calidad de Contenido"
                    score={score.quality}
                    description={
                      <div className="text-xs space-y-1">
                        <div>• Originalidad: {Math.min(100, score.quality * 1.05)}%</div>
                        <div>• Profundidad: {Math.min(100, score.quality * 0.92)}%</div>
                        <div>• Factibilidad: {Math.min(100, score.quality * 0.88)}%</div>
                      </div>
                    }
                  />
                  
                  <ScoreIndicator
                    icon={<TrendingUp className="w-5 h-5 text-green-500" />}
                    label="Relevancia de Tendencias"
                    score={score.trends}
                    description={
                      <div className="text-xs space-y-1">
                        <div>• Temas emergentes: {Math.min(100, score.trends * 1.15)}%</div>
                        <div>• Momento de publicación: {Math.min(100, score.trends * 0.9)}%</div>
                        <div>• Potencial viral: {Math.min(100, score.trends * 0.85)}%</div>
                      </div>
                    }
                  />
                </div>
              </div>
              
              {/* Recomendaciones */}
              <div className="mt-8 p-4 bg-blue-50 rounded-lg">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <h5 className="font-medium text-blue-900 mb-2">Recomendaciones</h5>
                    <ul className="text-sm text-blue-800 space-y-1">
                      {score.credibility < 70 && (
                        <li>• Considera diversificar las fuentes de noticias</li>
                      )}
                      {score.engagement < 70 && (
                        <li>• Mejora el formato y presentación del contenido</li>
                      )}
                      {score.quality < 70 && (
                        <li>• Enfócate en contenido más original y profundo</li>
                      )}
                      {score.trends < 70 && (
                        <li>• Analiza más temprano las tendencias emergentes</li>
                      )}
                      {score.overall >= 80 && (
                        <li>• Mantén la excelente calidad actual del contenido</li>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="breakdown" className="mt-6">
            <div className="space-y-8">
              <h4 className="font-medium text-gray-900">Desglose Visual del Score</h4>
              
              {/* Comparación con benchmarks */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { 
                    key: 'credibility', 
                    label: 'Credibilidad', 
                    icon: <Shield className="w-6 h-6 text-blue-500" />,
                    benchmark: 75,
                    current: score.credibility
                  },
                  { 
                    key: 'engagement', 
                    label: 'Engagement', 
                    icon: <Heart className="w-6 h-6 text-red-500" />,
                    benchmark: 60,
                    current: score.engagement
                  },
                  { 
                    key: 'quality', 
                    label: 'Calidad', 
                    icon: <Award className="w-6 h-6 text-purple-500" />,
                    benchmark: 80,
                    current: score.quality
                  },
                  { 
                    key: 'trends', 
                    label: 'Tendencias', 
                    icon: <TrendingUp className="w-6 h-6 text-green-500" />,
                    benchmark: 65,
                    current: score.trends
                  }
                ].map(({ key, label, icon, benchmark, current }) => {
                  const performance = current >= benchmark ? 'above' : 'below';
                  const performanceColor = performance === 'above' ? 'text-green-600' : 'text-red-600';
                  
                  return (
                    <div key={key} className="text-center p-4 border border-gray-200 rounded-lg">
                      <div className="flex justify-center mb-3">{icon}</div>
                      <h5 className="font-medium text-gray-900 mb-2">{label}</h5>
                      <div className="text-2xl font-bold mb-1" style={{ color: getScoreColor(current) }}>
                        {Math.round(current)}
                      </div>
                      <div className={`text-sm ${performanceColor}`}>
                        {performance === 'above' ? '↑ Sobre' : '↓ Bajo'} el promedio
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Benchmark: {benchmark}
                      </div>
                    </div>
                  );
                })}
              </div>
              
              {/* Distribución visual */}
              <div className="p-6 bg-gray-50 rounded-lg">
                <h5 className="font-medium text-gray-900 mb-4">Distribución del Score General</h5>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Score Actual</span>
                    <span className="font-bold" style={{ color: getScoreColor(score.overall) }}>
                      {Math.round(score.overall)}/100
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className="h-4 rounded-full transition-all duration-700"
                      style={{
                        backgroundColor: getScoreColor(score.overall),
                        width: `${score.overall}%`
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>0</span>
                    <span>25</span>
                    <span>50</span>
                    <span>75</span>
                    <span>100</span>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default RelevanceScoreComponent;
