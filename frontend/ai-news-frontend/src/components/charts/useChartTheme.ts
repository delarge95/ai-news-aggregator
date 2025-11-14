import { useState, useEffect } from 'react';
import { ChartThemeConfig } from './theme';

export const useChartTheme = () => {
  const [theme, setTheme] = useState<ChartThemeConfig>(() => {
    // Detectar tema del sistema o usar 'light' por defecto
    if (typeof window !== 'undefined') {
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      return isDark ? chartThemes.dark : chartThemes.light;
    }
    return chartThemes.light;
  });

  useEffect(() => {
    // Escuchar cambios en el tema del sistema
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? chartThemes.dark : chartThemes.light);
    };

    mediaQuery.addEventListener('change', handleChange);
    
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const updateTheme = (newTheme: Partial<ChartThemeConfig>) => {
    setTheme(prev => ({ ...prev, ...newTheme }));
  };

  return { theme, updateTheme };
};

// Import necesario para el hook
import { chartThemes } from './theme';