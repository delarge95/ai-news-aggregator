export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  children?: NavigationItem[];
  protected?: boolean;
  description?: string;
  badge?: string | number;
  external?: boolean;
}

export interface BreadcrumbItem {
  label: string;
  path: string;
  isActive?: boolean;
  icon?: React.ComponentType;
}

export interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  requireAuth?: boolean;
  roles?: string[];
}

// Tipos para navegación móvil
export interface MobileNavItem {
  id: string;
  label: string;
  path: string;
  icon: React.ComponentType;
  badge?: string | number;
}

// Tipos para contexto de navegación
export interface NavigationContext {
  title: string;
  description: string;
  actions: NavigationAction[];
  metadata?: Record<string, any>;
}

export interface NavigationAction {
  label: string;
  path?: string;
  action?: () => void;
  icon?: React.ComponentType;
  variant?: 'primary' | 'secondary' | 'outline';
}

// Tipos para estado de conexión
export interface ConnectionState {
  isOnline: boolean;
  connectionQuality: 'good' | 'poor' | 'offline';
  latency?: number;
  lastUpdate: Date;
}

// Tipos para navegación contextual
export interface ContextualInfo {
  title: string;
  description: string;
  stats?: ContextualStats;
  quickActions?: NavigationAction[];
}

export interface ContextualStats {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'stable';
}

// Tipos para navegación manager
export interface NavigationConfig {
  showContext: boolean;
  showStatus: boolean;
  breadcrumbsVariant: 'default' | 'modern';
  enableAnalytics: boolean;
}

// Tipos para análisis de rutas
export interface RouteAnalysis {
  path: string;
  breadcrumbs: BreadcrumbItem[];
  title: string;
  isProtected: boolean;
  requiredRoles?: string[];
}