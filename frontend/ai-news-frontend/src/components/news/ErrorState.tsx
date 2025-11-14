import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  AlertCircle, 
  RefreshCw, 
  WifiOff, 
  Server, 
  Search, 
  Filter,
  Network,
  Clock,
  AlertTriangle,
  CheckCircle,
  Info
} from 'lucide-react';

interface ErrorStateProps {
  // Tipo de error
  type: 'network' | 'server' | 'search' | 'filter' | 'permission' | 'unknown' | 'empty';
  
  // Mensajes
  title?: string;
  message?: string;
  details?: string;
  
  // Acciones
  onRetry?: () => void;
  onRefresh?: () => void;
  onClearFilters?: () => void;
  onResetSearch?: () => void;
  onGoHome?: () => void;
  
  // Configuración
  showRetry?: boolean;
  showRefresh?: boolean;
  showDetails?: boolean;
  compact?: boolean;
  
  // Datos adicionales
  errorCode?: string;
  timestamp?: Date;
  retryCount?: number;
  
  // Estilos
  className?: string;
  variant?: 'default' | 'card' | 'inline' | 'fullscreen';
}

// Configuración de iconos por tipo de error
const getErrorIcon = (type: string) => {
  switch (type) {
    case 'network':
      return <WifiOff className="h-6 w-6 text-red-500" />;
    case 'server':
      return <Server className="h-6 w-6 text-red-500" />;
    case 'search':
      return <Search className="h-6 w-6 text-orange-500" />;
    case 'filter':
      return <Filter className="h-6 w-6 text-blue-500" />;
    case 'permission':
      return <AlertTriangle className="h-6 w-6 text-yellow-500" />;
    case 'empty':
      return <Search className="h-6 w-6 text-gray-400" />;
    default:
      return <AlertCircle className="h-6 w-6 text-red-500" />;
  }
};

// Configuración de mensajes por tipo
const getErrorConfig = (type: string) => {
  switch (type) {
    case 'network':
      return {
        title: 'Sin conexión a internet',
        message: 'No se puede conectar con el servidor. Verifica tu conexión e intenta nuevamente.',
        action: 'Verificar conexión'
      };
    case 'server':
      return {
        title: 'Error del servidor',
        message: 'El servidor no está respondiendo. Nuestro equipo ha sido notificado.',
        action: 'Intentar más tarde'
      };
    case 'search':
      return {
        title: 'No se encontraron resultados',
        message: 'No hay noticias que coincidan con tu búsqueda. Intenta con otros términos.',
        action: 'Limpiar búsqueda'
      };
    case 'filter':
      return {
        title: 'Filtros muy restrictivos',
        message: 'Los filtros aplicados no devuelven resultados. Intenta relajarlos.',
        action: 'Limpiar filtros'
      };
    case 'permission':
      return {
        title: 'Acceso denegado',
        message: 'No tienes permisos para ver este contenido.',
        action: 'Contactar soporte'
      };
    case 'empty':
      return {
        title: 'No hay noticias disponibles',
        message: 'Actualmente no hay noticias para mostrar. Intenta más tarde.',
        action: 'Recargar'
      };
    default:
      return {
        title: 'Algo salió mal',
        message: 'Ha ocurrido un error inesperado. Por favor, intenta nuevamente.',
        action: 'Reintentar'
      };
  }
};

// Alerta inline para errores menores
const InlineErrorAlert: React.FC<ErrorStateProps> = ({
  type,
  title,
  message,
  onRetry,
  onRefresh,
  compact = true,
  className = ""
}) => {
  const config = getErrorConfig(type);
  const finalTitle = title || config.title;
  const finalMessage = message || config.message;

  return (
    <Alert className={`border-red-200 bg-red-50 ${className}`}>
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <div className="flex-1">
          <div className="font-medium text-red-800">{finalTitle}</div>
          <div className="text-red-700 text-sm mt-1">{finalMessage}</div>
        </div>
        <div className="flex gap-2 ml-4">
          {onRetry && (
            <Button variant="outline" size="sm" onClick={onRetry}>
              <RefreshCw className="h-3 w-3 mr-1" />
              Reintentar
            </Button>
          )}
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh}>
              <RefreshCw className="h-3 w-3 mr-1" />
              Recargar
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
};

// Componente de error en tarjeta
const CardErrorState: React.FC<ErrorStateProps> = ({
  type,
  title,
  message,
  details,
  onRetry,
  onRefresh,
  onClearFilters,
  onResetSearch,
  onGoHome,
  showDetails = false,
  compact = false,
  errorCode,
  timestamp,
  retryCount = 0,
  className = ""
}) => {
  const config = getErrorConfig(type);
  const icon = getErrorIcon(type);
  const finalTitle = title || config.title;
  const finalMessage = message || config.message;

  return (
    <Card className={`w-full max-w-md mx-auto ${className}`}>
      <CardHeader className="text-center pb-4">
        <div className="mx-auto mb-4 p-3 bg-gray-50 rounded-full w-fit">
          {icon}
        </div>
        <CardTitle className="text-xl font-semibold text-gray-900">
          {finalTitle}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <p className="text-gray-600 text-center">{finalMessage}</p>
        
        {/* Detalles del error */}
        {showDetails && (errorCode || details || timestamp) && (
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            {errorCode && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Código:</span>
                <Badge variant="outline" className="font-mono">{errorCode}</Badge>
              </div>
            )}
            {timestamp && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Tiempo:</span>
                <span className="font-mono text-gray-800">
                  {timestamp.toLocaleTimeString()}
                </span>
              </div>
            )}
            {retryCount > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Reintentos:</span>
                <span className="font-mono text-gray-800">{retryCount}</span>
              </div>
            )}
            {details && (
              <div className="text-xs text-gray-500 mt-2">
                <strong>Detalles:</strong> {details}
              </div>
            )}
          </div>
        )}

        {/* Acciones */}
        <div className="space-y-2">
          {onRetry && (
            <Button 
              onClick={onRetry} 
              className="w-full"
              variant={type === 'network' || type === 'server' ? 'default' : 'outline'}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              {config.action}
            </Button>
          )}
          
          <div className="flex gap-2">
            {onRefresh && (
              <Button onClick={onRefresh} variant="outline" className="flex-1">
                <RefreshCw className="h-4 w-4 mr-2" />
                Recargar
              </Button>
            )}
            
            {onClearFilters && (
              <Button onClick={onClearFilters} variant="outline" className="flex-1">
                <Filter className="h-4 w-4 mr-2" />
                Limpiar filtros
              </Button>
            )}
          </div>
          
          {onResetSearch && (
            <Button onClick={onResetSearch} variant="outline" className="w-full">
              <Search className="h-4 w-4 mr-2" />
              Nueva búsqueda
            </Button>
          )}
          
          {onGoHome && (
            <Button onClick={onGoHome} variant="ghost" className="w-full">
              Volver al inicio
            </Button>
          )}
        </div>

        {/* Consejos adicionales */}
        {!compact && (
          <div className="border-t pt-4">
            <div className="text-xs text-gray-500 space-y-1">
              {type === 'network' && (
                <>
                  <p>• Verifica tu conexión WiFi o datos móviles</p>
                  <p>• Reinicia tu router si es necesario</p>
                </>
              )}
              {type === 'search' && (
                <>
                  <p>• Intenta con palabras clave más generales</p>
                  <p>• Revisa la ortografía de los términos</p>
                </>
              )}
              {type === 'filter' && (
                <>
                  <p>• Elimina algunos filtros para ver más resultados</p>
                  <p>• Intenta con rangos de fechas más amplios</p>
                </>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Componente de pantalla completa para errores críticos
const FullscreenErrorState: React.FC<ErrorStateProps> = (props) => {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <CardErrorState {...props} />
    </div>
  );
};

// Componente principal
const ErrorState: React.FC<ErrorStateProps> = (props) => {
  const {
    type,
    title,
    message,
    variant = 'card',
    compact = false,
    className = "",
    ...cardProps
  } = props;

  switch (variant) {
    case 'inline':
      return (
        <InlineErrorAlert 
          {...props}
          className={className}
        />
      );
    
    case 'fullscreen':
      return (
        <FullscreenErrorState 
          {...props}
          className={className}
        />
      );
    
    case 'card':
    default:
      return (
        <div className={`flex items-center justify-center py-12 ${className}`}>
          <CardErrorState 
            {...props}
            compact={compact}
          />
        </div>
      );
  }
};

// Componente especializado para errores de red
export const NetworkErrorState: React.FC<Omit<ErrorStateProps, 'type'> & {
  connectionStatus?: 'offline' | 'slow' | 'intermittent';
}> = ({ 
  connectionStatus = 'offline', 
  onRetry,
  ...props 
}) => {
  const getNetworkMessage = () => {
    switch (connectionStatus) {
      case 'slow':
        return 'La conexión es muy lenta. Esto puede afectar la carga de noticias.';
      case 'intermittent':
        return 'La conexión es intermitente. Algunos datos podrían no cargarse correctamente.';
      default:
        return 'No se puede conectar con el servidor.';
    }
  };

  return (
    <ErrorState
      {...props}
      type="network"
      message={getNetworkMessage()}
      onRetry={onRetry}
      variant="card"
    />
  );
};

// Componente para estado vacío (no es realmente un error)
export const EmptyState: React.FC<Omit<ErrorStateProps, 'type' | 'variant'> & {
  icon?: React.ReactNode;
  actionLabel?: string;
}> = ({ 
  icon,
  actionLabel = "Explorar noticias",
  onGoHome,
  ...props 
}) => {
  return (
    <div className="flex items-center justify-center py-16">
      <Card className="w-full max-w-md">
        <CardContent className="text-center py-8">
          <div className="mx-auto mb-4 p-3 bg-gray-50 rounded-full w-fit">
            {icon || <Search className="h-8 w-8 text-gray-400" />}
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {props.title || 'No hay resultados'}
          </h3>
          <p className="text-gray-600 mb-6">
            {props.message || 'Intenta ajustar tus filtros o términos de búsqueda'}
          </p>
          <div className="space-y-2">
            {onGoHome && (
              <Button onClick={onGoHome} className="w-full">
                {actionLabel}
              </Button>
            )}
            {props.onClearFilters && (
              <Button onClick={props.onClearFilters} variant="outline" className="w-full">
                <Filter className="h-4 w-4 mr-2" />
                Limpiar filtros
              </Button>
            )}
            {props.onResetSearch && (
              <Button onClick={props.onResetSearch} variant="outline" className="w-full">
                <Search className="h-4 w-4 mr-2" />
                Nueva búsqueda
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ErrorState;