import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Newspaper, 
  TrendingUp, 
  BookOpen, 
  BarChart3,
  User,
  Search,
  Bell,
  Settings,
  HelpCircle,
  MessageCircle,
  ChevronRight
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useNavigation } from '../../hooks/useNavigation';

interface NavigationContextProps {
  className?: string;
  showQuickActions?: boolean;
  showRecentItems?: boolean;
}

const NavigationContext: React.FC<NavigationContextProps> = ({
  className,
  showQuickActions = true,
  showRecentItems = true
}) => {
  const location = useLocation();
  const { navigate } = useNavigation();

  // Contenido contextual basado en la ruta actual
  const getContextualContent = () => {
    const path = location.pathname;
    
    switch (true) {
      case path === '/':
        return {
          title: 'Panel Principal',
          description: 'Bienvenido al agregador de noticias de IA',
          actions: [
            { label: 'Ver noticias', path: '/news', icon: Newspaper },
            { label: 'Explorar tendencias', path: '/trends', icon: TrendingUp },
            { label: 'Análisis IA', path: '/analysis', icon: BarChart3 }
          ]
        };
      
      case path.startsWith('/news'):
        return {
          title: 'Centro de Noticias',
          description: 'Las últimas noticias y actualizaciones en Inteligencia Artificial',
          actions: [
            { label: 'Filtrar por categoría', action: () => console.log('Filter news') },
            { label: 'Guardar búsqueda', action: () => console.log('Save search') },
            { label: 'Suscribirse', action: () => console.log('Subscribe') }
          ]
        };
      
      case path.startsWith('/trends'):
        return {
          title: 'Tendencias de IA',
          description: 'Descubre las tendencias más relevantes en el mundo de la IA',
          actions: [
            { label: 'Ver gráficos', action: () => console.log('View charts') },
            { label: 'Exportar datos', action: () => console.log('Export data') },
            { label: 'Configurar alertas', action: () => console.log('Setup alerts') }
          ]
        };
      
      case path.startsWith('/analysis'):
        return {
          title: 'Análisis Inteligente',
          description: 'Análisis profundo y insights de noticias de IA',
          actions: [
            { label: 'Nuevo análisis', action: () => console.log('New analysis') },
            { label: 'Reportes guardados', action: () => console.log('Saved reports') },
            { label: 'Programar análisis', action: () => console.log('Schedule analysis') }
          ]
        };
      
      case path.startsWith('/resources'):
        return {
          title: 'Centro de Recursos',
          description: 'Recursos útiles y herramientas para IA',
          actions: [
            { label: 'Añadir recurso', action: () => console.log('Add resource') },
            { label: 'Categorías', action: () => console.log('Categories') },
            { label: 'Favoritos', action: () => console.log('Favorites') }
          ]
        };
      
      default:
        return null;
    }
  };

  const contextualContent = getContextualContent();

  if (!contextualContent) return null;

  return (
    <div className={cn("bg-white border border-gray-200 rounded-lg p-6 mb-6", className)}>
      {/* Título y descripción */}
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {contextualContent.title}
        </h2>
        <p className="text-gray-600">
          {contextualContent.description}
        </p>
      </div>

      {/* Acciones rápidas */}
      {showQuickActions && contextualContent.actions && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-700">Acciones rápidas</h3>
          <div className="flex flex-wrap gap-2">
            {contextualContent.actions.map((action, index) => {
              const Icon = action.icon;
              
              return action.path ? (
                <Link
                  key={index}
                  to={action.path}
                  className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  {Icon && <Icon className="w-4 h-4" />}
                  {action.label}
                </Link>
              ) : (
                <button
                  key={index}
                  onClick={action.action}
                  className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {Icon && <Icon className="w-4 h-4" />}
                  {action.label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Información adicional según la página */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        {location.pathname === '/' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center gap-2 text-gray-600">
              <Bell className="w-4 h-4" />
              <span>5 nuevas notificaciones</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Search className="w-4 h-4" />
              <span>3 búsquedas guardadas</span>
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <BarChart3 className="w-4 h-4" />
              <span>Última actualización: hace 5 min</span>
            </div>
          </div>
        )}
        
        {location.pathname.startsWith('/profile') && (
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <span>Nivel de suscripción:</span>
              <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium">
                Gratuito
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Última actividad:</span>
              <span>Hace 2 horas</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NavigationContext;