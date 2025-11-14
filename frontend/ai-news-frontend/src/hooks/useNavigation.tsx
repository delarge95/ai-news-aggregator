import { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { generateBreadcrumbs, updatePageTitle } from '../lib/navigation';
import { BreadcrumbItem } from '../types';

interface UseNavigationOptions {
  updateTitle?: boolean;
  scrollToTop?: boolean;
  generateBreadcrumbs?: boolean;
}

interface UseNavigationReturn {
  breadcrumbs: BreadcrumbItem[];
  currentPath: string;
  isLoading: boolean;
  navigate: (path: string, options?: { replace?: boolean; state?: any }) => void;
  goBack: () => void;
  goForward: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
}

/**
 * Hook personalizado para manejo avanzado de navegación
 */
export const useNavigation = (options: UseNavigationOptions = {}): UseNavigationReturn => {
  const {
    updateTitle = true,
    scrollToTop = true,
    generateBreadcrumbs: shouldGenerate = true
  } = options;

  const location = useLocation();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  // Estado de historial del navegador
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);

  // Actualizar estado del historial
  useEffect(() => {
    setCanGoBack(window.history.length > 1);
    setCanGoForward(false); // No podemos detectar esto fácilmente en el navegador
  }, []);

  // Actualizar breadcrumbs si está habilitado
  const breadcrumbs = shouldGenerate ? generateBreadcrumbs(location.pathname) : [];

  // Actualizar título de la página si está habilitado
  useEffect(() => {
    if (updateTitle) {
      updatePageTitle(location.pathname);
    }
  }, [location.pathname, updateTitle]);

  // Scroll to top si está habilitado
  useEffect(() => {
    if (scrollToTop) {
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'smooth'
      });
    }
  }, [location.pathname, scrollToTop]);

  // Función de navegación mejorada
  const enhancedNavigate = useCallback((
    path: string, 
    navigationOptions?: { replace?: boolean; state?: any }
  ) => {
    setIsLoading(true);
    
    try {
      if (navigationOptions?.replace) {
        navigate(path, { replace: true, state: navigationOptions?.state });
      } else {
        navigate(path, { state: navigationOptions?.state });
      }
    } catch (error) {
      console.error('Error navigating:', error);
      setIsLoading(false);
    }
  }, [navigate]);

  // Función para ir hacia atrás
  const goBack = useCallback(() => {
    if (canGoBack) {
      window.history.back();
    }
  }, [canGoBack]);

  // Función para ir hacia adelante
  const goForward = useCallback(() => {
    if (canGoForward) {
      window.history.forward();
    }
  }, [canGoForward]);

  return {
    breadcrumbs,
    currentPath: location.pathname,
    isLoading,
    navigate: enhancedNavigate,
    goBack,
    goForward,
    canGoBack,
    canGoForward
  };
};

export default useNavigation;