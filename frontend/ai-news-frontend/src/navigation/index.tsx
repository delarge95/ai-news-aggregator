// Sistema completo de navegación y routing
// Re-exporta todos los componentes y utilidades

// Componentes principales
export { default as Layout } from './layout/Layout';
export { default as Navbar } from './navigation/Navbar';
export { default as Sidebar } from './navigation/Sidebar';
export { default as Header } from './navigation/Header';
export { default as NavigationManager } from './navigation/NavigationManager';

// Componentes de navegación
export { 
  default as Breadcrumbs, 
  ModernBreadcrumbs 
} from './navigation/Breadcrumbs';
export { 
  default as MobileNavigationOverlay 
} from './navigation/MobileNavigationOverlay';
export { 
  default as NavigationContext 
} from './navigation/NavigationContext';

// Componentes de utilidad
export { 
  default as ProtectedRoute,
  SystemStatus 
} from './common/ProtectedRoute';
export { 
  default as ScrollToTop, 
  ScrollToTopButton 
} from './common/ScrollToTop';
export { 
  default as ConnectionStatus 
} from './common/ConnectionStatus';

// Páginas
export { default as NotFound } from '../pages/NotFound';

// Hooks
export { 
  default as useNavigation,
  useNavigation as useNav 
} from '../hooks/useNavigation';
export { useIsMobile } from '../hooks/use-mobile';

// Utilidades y configuraciones
export { 
  NAVIGATION_CONFIG,
  navigateTo,
  generateBreadcrumbs,
  isRouteProtected,
  getPageTitle,
  updatePageTitle,
  scrollToTop,
  navigateAndScrollToTop,
  getCurrentPath,
  matchesRoute,
  buildUrl,
  parseQueryParams,
  getQueryParam,
  navigateWithParams
} from '../lib/navigation';

// Tipos
export type {
  NavigationItem,
  BreadcrumbItem,
  ProtectedRouteProps,
  MobileNavItem,
  NavigationContext,
  NavigationAction,
  ConnectionState,
  ContextualInfo,
  ContextualStats,
  NavigationConfig,
  RouteAnalysis
} from '../types';

// Constantes
export const ROUTES = {
  HOME: '/',
  NEWS: '/news',
  TRENDS: '/trends',
  RESOURCES: '/resources',
  ANALYSIS: '/analysis',
  SEARCH: '/search',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  PRIVACY: '/privacy',
  LOGIN: '/login',
  NOT_FOUND: '*'
} as const;

// Utilidades de conveniencia
export const createBreadcrumb = (
  label: string, 
  path: string, 
  isActive = false
) => ({ label, path, isActive });

export const createNavItem = (
  id: string,
  label: string,
  path: string,
  options?: {
    icon?: string;
    protected?: boolean;
    description?: string;
    badge?: string | number;
  }
) => ({
  id,
  label,
  path,
  ...options
});

// Componentes de configuración rápida
export const QuickNavbar = ({ className }: { className?: string }) => (
  <Navbar className={className} />
);

export const QuickSidebar = ({ 
  isOpen, 
  onClose 
}: { 
  isOpen: boolean; 
  onClose: () => void; 
}) => (
  <Sidebar isOpen={isOpen} onClose={onClose} />
);

export const QuickBreadcrumbs = ({ 
  className,
  showHome = true 
}: { 
  className?: string;
  showHome?: boolean;
}) => (
  <Breadcrumbs showHome={showHome} className={className} />
);

export const QuickConnectionStatus = ({ 
  showTimestamp = true,
  showDetails = false 
}: { 
  showTimestamp?: boolean;
  showDetails?: boolean;
}) => (
  <ConnectionStatus 
    showTimestamp={showTimestamp}
    showDetails={showDetails}
  />
);

// Configuración por defecto
export const DEFAULT_NAVIGATION_CONFIG = {
  showContext: true,
  showStatus: true,
  breadcrumbsVariant: 'default' as const,
  enableAnalytics: false
};

// Validaciones
export const validateNavigationConfig = (config: any): config is NavigationConfig => {
  return (
    typeof config === 'object' &&
    typeof config.showContext === 'boolean' &&
    typeof config.showStatus === 'boolean' &&
    ['default', 'modern'].includes(config.breadcrumbsVariant) &&
    typeof config.enableAnalytics === 'boolean'
  );
};

// Helper para crear navegación context
export const createNavigationContext = (
  title: string,
  description: string,
  actions: NavigationAction[] = []
): NavigationContext => ({
  title,
  description,
  actions
});

// Información de versión
export const NAVIGATION_VERSION = '1.0.0';

export default {
  // Componentes principales
  Layout,
  Navbar,
  Sidebar,
  NavigationManager,
  
  // Navegación
  Breadcrumbs,
  NavigationContext,
  MobileNavigationOverlay,
  
  // Utilidades
  ProtectedRoute,
  ScrollToTop,
  ConnectionStatus,
  
  // Páginas
  NotFound,
  
  // Hooks
  useNavigation,
  useIsMobile,
  
  // Utilidades
  ...{
    // Aunque esto no es idiomatico, permite destructuring fácil
    navigateTo,
    generateBreadcrumbs,
    isRouteProtected,
    getPageTitle,
    updatePageTitle,
    scrollToTop,
    navigateAndScrollToTop
  },
  
  // Constantes
  ROUTES,
  
  // Configuración
  DEFAULT_NAVIGATION_CONFIG,
  validateNavigationConfig,
  
  // Versión
  NAVIGATION_VERSION
};