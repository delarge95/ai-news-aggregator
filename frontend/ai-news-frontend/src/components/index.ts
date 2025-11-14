// Componentes de navegación y routing

// Componentes principales
export { default as Layout } from './layout/Layout';
export { default as Navbar } from './navigation/Navbar';
export { default as Header } from './navigation/Header';
export { default as Sidebar } from './navigation/Sidebar';

// Componentes de navegación
export { default as Breadcrumbs, ModernBreadcrumbs } from './navigation/Breadcrumbs';
export { default as MobileNavigationOverlay } from './navigation/MobileNavigationOverlay';

// Componentes de protección y utilidades
export { default as ProtectedRoute } from './common/ProtectedRoute';
export { default as ScrollToTop, ScrollToTopButton } from './common/ScrollToTop';

// Páginas
export { default as NotFound } from '../pages/NotFound';

// Tipos
export type { NavigationItem, BreadcrumbItem, ProtectedRouteProps } from '../types';

// Utilidades
export { 
  NAVIGATION_CONFIG, 
  navigateTo, 
  generateBreadcrumbs, 
  isRouteProtected, 
  getPageTitle, 
  updatePageTitle, 
  scrollToTop, 
  navigateAndScrollToTop 
} from '../lib/navigation';