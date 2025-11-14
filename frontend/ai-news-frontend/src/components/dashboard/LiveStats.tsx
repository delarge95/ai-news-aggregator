import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { LiveStats } from '../../types/dashboard';
import { dashboardService } from '../../services/dashboardService';
import { Activity, Database, Clock, Wifi } from 'lucide-react';
import { cn } from '../../lib/utils';

const LiveStatsComponent: React.FC = () => {
  const [stats, setStats] = useState<LiveStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchStats = async () => {
    try {
      const data = await dashboardService.getLiveStats();
      setStats(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    
    // Polling cada 30 segundos
    const interval = setInterval(fetchStats, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Estadísticas en Vivo</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-2 text-muted-foreground">Cargando...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-red-600">
            <Activity className="h-5 w-5" />
            <span>Estadísticas en Vivo</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="text-red-500 mb-2">Error al cargar datos</div>
            <button
              onClick={fetchStats}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-green-200 bg-green-50/50">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5 text-green-600" />
            <span className="text-green-800">Estadísticas en Vivo</span>
            <Wifi className="h-4 w-4 text-green-600" />
          </div>
          <div className="text-xs text-green-600">
            Última actualización: {formatTime(lastUpdate)}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-full">
              <Database className="h-4 w-4 text-green-600" />
            </div>
            <div>
              <div className="text-sm text-green-800">Artículos Procesados</div>
              <div className="text-lg font-semibold text-green-900">
                {stats?.current_articles?.toLocaleString() || '0'}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <Activity className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <div className="text-sm text-blue-800">Fuentes Activas</div>
              <div className="text-lg font-semibold text-blue-900">
                {stats?.sources_online || '0'}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-100 rounded-full">
              <Clock className="h-4 w-4 text-purple-600" />
            </div>
            <div>
              <div className="text-sm text-purple-800">Tiempo Promedio</div>
              <div className="text-lg font-semibold text-purple-900">
                {stats?.average_processing_time ? `${stats.average_processing_time.toFixed(1)}s` : '0s'}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default LiveStatsComponent;