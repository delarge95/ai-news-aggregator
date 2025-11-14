import React, { useState, useEffect } from 'react';
import { Wifi, WifiOff, Clock, CheckCircle, AlertCircle, XCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ConnectionStatusProps {
  className?: string;
  showTimestamp?: boolean;
  showDetails?: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  className,
  showTimestamp = true,
  showDetails = false
}) => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connectionQuality, setConnectionQuality] = useState<'good' | 'poor' | 'offline'>('good');

  // Detectar cambios en el estado de conexión
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setConnectionQuality('good');
      setLastUpdate(new Date());
    };

    const handleOffline = () => {
      setIsOnline(false);
      setConnectionQuality('offline');
      setLastUpdate(new Date());
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Verificar calidad de conexión periódicamente
    const checkConnectionQuality = async () => {
      if (isOnline) {
        try {
          const start = performance.now();
          await fetch('/', { 
            method: 'HEAD', 
            cache: 'no-cache',
            signal: AbortSignal.timeout(5000) // Timeout de 5 segundos
          });
          const end = performance.now();
          const latency = end - start;
          
          if (latency < 200) {
            setConnectionQuality('good');
          } else if (latency < 1000) {
            setConnectionQuality('poor');
          } else {
            setConnectionQuality('offline');
          }
        } catch {
          setConnectionQuality('offline');
        }
      }
    };

    const interval = setInterval(checkConnectionQuality, 30000); // Cada 30 segundos
    checkConnectionQuality();

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [isOnline]);

  const getStatusConfig = () => {
    if (!isOnline) {
      return {
        icon: WifiOff,
        color: 'text-red-500',
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        text: 'Sin conexión',
        tooltip: 'No hay conexión a internet'
      };
    }

    switch (connectionQuality) {
      case 'good':
        return {
          icon: Wifi,
          color: 'text-green-500',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          text: 'Conectado',
          tooltip: 'Conexión estable'
        };
      
      case 'poor':
        return {
          icon: AlertCircle,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-50',
          borderColor: 'border-yellow-200',
          text: 'Conexión lenta',
          tooltip: 'La conexión es lenta'
        };
      
      case 'offline':
        return {
          icon: XCircle,
          color: 'text-red-500',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          text: 'Desconectado',
          tooltip: 'Sin acceso al servidor'
        };
      
      default:
        return {
          icon: Wifi,
          color: 'text-gray-500',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          text: 'Estado desconocido',
          tooltip: 'No se puede determinar el estado'
        };
    }
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div 
        className={cn(
          "flex items-center gap-1 px-2 py-1 rounded-full border text-xs font-medium",
          statusConfig.bgColor,
          statusConfig.borderColor,
          statusConfig.color
        )}
        title={statusConfig.tooltip}
      >
        <StatusIcon className="w-3 h-3" />
        <span>{statusConfig.text}</span>
      </div>

      {showTimestamp && (
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{formatTimestamp(lastUpdate)}</span>
        </div>
      )}

      {showDetails && (
        <div className="text-xs text-gray-400">
          {connectionQuality === 'good' && '🟢 Latencia óptima'}
          {connectionQuality === 'poor' && '🟡 Latencia alta'}
          {connectionQuality === 'offline' && '🔴 Sin respuesta'}
        </div>
      )}
    </div>
  );
};

// Componente para mostrar múltiples estados de conexión
export const SystemStatus: React.FC = () => {
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [databaseStatus, setDatabaseStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    const checkServices = async () => {
      // Simular verificación de servicios
      setApiStatus('checking');
      setDatabaseStatus('checking');

      // Aquí iría la lógica real de verificación
      setTimeout(() => setApiStatus('online'), 1000);
      setTimeout(() => setDatabaseStatus('online'), 1500);
    };

    checkServices();
  }, []);

  const getServiceStatus = (status: string) => {
    switch (status) {
      case 'online':
        return { icon: CheckCircle, color: 'text-green-500', text: 'Operativo' };
      case 'offline':
        return { icon: XCircle, color: 'text-red-500', text: 'Caído' };
      case 'checking':
        return { icon: AlertCircle, color: 'text-yellow-500', text: 'Verificando...' };
      default:
        return { icon: AlertCircle, color: 'text-gray-500', text: 'Desconocido' };
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <h3 className="text-sm font-semibold text-gray-900">Estado del Sistema</h3>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">API Principal</span>
          <div className="flex items-center gap-2">
            {(() => {
              const config = getServiceStatus(apiStatus);
              const Icon = config.icon;
              return <Icon className={cn("w-4 h-4", config.color)} />;
            })()}
            <span className="text-xs text-gray-500">{getServiceStatus(apiStatus).text}</span>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Base de Datos</span>
          <div className="flex items-center gap-2">
            {(() => {
              const config = getServiceStatus(databaseStatus);
              const Icon = config.icon;
              return <Icon className={cn("w-4 h-4", config.color)} />;
            })()}
            <span className="text-xs text-gray-500">{getServiceStatus(databaseStatus).text}</span>
          </div>
        </div>
      </div>

      <div className="pt-2 border-t border-gray-200">
        <ConnectionStatus showDetails />
      </div>
    </div>
  );
};

export default ConnectionStatus;