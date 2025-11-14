import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../ui/card';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ConnectionStatusProps {
  isOnline?: boolean;
  lastPing?: Date;
  className?: string;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isOnline = navigator.onLine,
  lastPing = new Date(),
  className
}) => {
  const [connectionStatus, setConnectionStatus] = useState(isOnline);

  useEffect(() => {
    const handleOnline = () => setConnectionStatus(true);
    const handleOffline = () => setConnectionStatus(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const formatLastPing = (date: Date) => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return `hace ${diffInSeconds}s`;
    } else if (diffInSeconds < 3600) {
      return `hace ${Math.floor(diffInSeconds / 60)}m`;
    } else {
      return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
    }
  };

  return (
    <Card className={cn("w-fit", className)}>
      <CardContent className="p-3">
        <div className="flex items-center space-x-2">
          {connectionStatus ? (
            <>
              <Wifi className="h-4 w-4 text-green-500" />
              <span className="text-sm text-green-600">Conectado</span>
              {lastPing && (
                <span className="text-xs text-muted-foreground">
                  • {formatLastPing(lastPing)}
                </span>
              )}
            </>
          ) : (
            <>
              <WifiOff className="h-4 w-4 text-red-500" />
              <span className="text-sm text-red-600">Desconectado</span>
              <AlertCircle className="h-4 w-4 text-yellow-500" />
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default ConnectionStatus;