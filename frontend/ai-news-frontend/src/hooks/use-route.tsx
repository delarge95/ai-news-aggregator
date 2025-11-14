import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Hook para obtener el estado de carga de la página durante las transiciones de路由
 */
export const useRouteTransition = () => {
  const [isTransitioning, setIsTransitioning] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setIsTransitioning(true);
    
    // Simulamos un pequeño delay para evitar parpadeos
    const timer = setTimeout(() => {
      setIsTransitioning(false);
    }, 150);

    return () => clearTimeout(timer);
  }, [location.pathname]);

  return isTransitioning;
};

/**
 * Hook para obtener la ruta actual y información relacionada
 */
export const useCurrentRoute = () => {
  const location = useLocation();
  
  const getRouteInfo = () => {
    const path = location.pathname;
    const pathSegments = path.split('/').filter(Boolean);
    
    return {
      path,
      segments: pathSegments,
      depth: pathSegments.length,
      isRoot: path === '/',
      isExactPath: (targetPath: string) => path === targetPath,
      isPathStartsWith: (targetPath: string) => path.startsWith(targetPath),
      breadcrumbs: generateBreadcrumbs(path)
    };
  };

  const generateBreadcrumbs = (path: string) => {
    const segments = path.split('/').filter(Boolean);
    const breadcrumbs = [{ label: 'Inicio', path: '/', isActive: segments.length === 0 }];
    
    let currentPath = '';
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      const isLast = index === segments.length - 1;
      
      const labels: Record<string, string> = {
        'news': 'Noticias',
        'trends': 'Tendencias',
        'resources': 'Recursos',
        'profile': 'Perfil',
        'settings': 'Configuración',
        'privacy': 'Privacidad',
        'login': 'Iniciar Sesión'
      };
      
      breadcrumbs.push({
        label: labels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1),
        path: currentPath,
        isActive: isLast
      });
    });
    
    return breadcrumbs;
  };

  return {
    ...getRouteInfo(),
    location
  };
};

export default useCurrentRoute;