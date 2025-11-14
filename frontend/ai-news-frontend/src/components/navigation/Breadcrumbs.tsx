import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home, Folder } from 'lucide-react';
import { BreadcrumbItem } from '../../types';
import { cn } from '../../lib/utils';

interface BreadcrumbsProps {
  customBreadcrumbs?: BreadcrumbItem[];
  className?: string;
  showHome?: boolean;
  separator?: React.ReactNode;
}

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ 
  customBreadcrumbs, 
  className,
  showHome = true,
  separator 
}) => {
  const location = useLocation();

  // Generar breadcrumbs automáticamente si no se proporcionan personalizados
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const pathnames = location.pathname.split('/').filter(x => x);
    const breadcrumbs: BreadcrumbItem[] = [];

    // Siempre empezar con Home si está habilitado
    if (showHome) {
      breadcrumbs.push({
        label: 'Inicio',
        path: '/',
        isActive: pathnames.length === 0
      });
    }

    let currentPath = '';
    pathnames.forEach((pathname, index) => {
      currentPath += `/${pathname}`;
      const isLast = index === pathnames.length - 1;
      
      // Mapeo de rutas a labels más amigables
      const pathLabels: Record<string, string> = {
        'news': 'Noticias',
        'trends': 'Tendencias',
        'resources': 'Recursos',
        'profile': 'Mi Perfil',
        'settings': 'Configuración',
        'privacy': 'Privacidad',
        'login': 'Iniciar Sesión',
        'analysis': 'Análisis IA',
        'search': 'Búsqueda'
      };

      breadcrumbs.push({
        label: pathLabels[pathname] || pathname.charAt(0).toUpperCase() + pathname.slice(1),
        path: currentPath,
        isActive: isLast
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = customBreadcrumbs || generateBreadcrumbs();

  // No mostrar breadcrumbs si solo hay un elemento (Inicio) o none
  if (breadcrumbs.length <= (showHome ? 1 : 0)) {
    return null;
  }

  const defaultSeparator = <ChevronRight className="w-4 h-4 text-gray-400" />;

  return (
    <nav 
      className={cn("flex items-center space-x-2 text-sm", className)} 
      aria-label="Breadcrumb"
    >
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.path}>
          {index > 0 && (separator || defaultSeparator)}
          
          <div className="flex items-center">
            {index === 0 && showHome && (
              <Home className="w-4 h-4 mr-1 text-gray-500" />
            )}
            
            {index > 0 && index === breadcrumbs.length - 1 && !showHome && (
              <Folder className="w-4 h-4 mr-1 text-gray-500" />
            )}
            
            {crumb.isActive ? (
              <span 
                className="text-gray-900 font-medium max-w-xs truncate"
                title={crumb.label}
              >
                {crumb.label}
              </span>
            ) : (
              <Link
                to={crumb.path}
                className={cn(
                  "text-gray-600 hover:text-blue-600 transition-colors max-w-xs truncate",
                  "hover:underline"
                )}
                title={crumb.label}
              >
                {crumb.label}
              </Link>
            )}
          </div>
        </React.Fragment>
      ))}
    </nav>
  );
};

// Componente adicional para breadcrumbs con estilo moderno
export const ModernBreadcrumbs: React.FC<BreadcrumbsProps> = (props) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 shadow-sm">
      <Breadcrumbs 
        {...props} 
        className="text-gray-700"
        separator={
          <div className="w-1 h-1 bg-gray-400 rounded-full"></div>
        }
      />
    </div>
  );
};

export default Breadcrumbs;