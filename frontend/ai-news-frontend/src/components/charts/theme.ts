import { Theme } from 'recharts/types/util/types';

export interface ChartThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    success: string;
    warning: string;
    error: string;
    info: string;
    muted: string;
    background: string;
    foreground: string;
    border: string;
  };
  gradients: {
    primary: string[];
    secondary: string[];
    accent: string[];
  };
  shadows: {
    small: string;
    medium: string;
    large: string;
  };
  animations: {
    duration: number;
    easing: string;
  };
  responsive: {
    breakpoints: {
      sm: number;
      md: number;
      lg: number;
      xl: number;
    };
  };
}

export const chartThemes: Record<string, ChartThemeConfig> = {
  light: {
    colors: {
      primary: '#3b82f6',
      secondary: '#64748b',
      accent: '#8b5cf6',
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#06b6d4',
      muted: '#94a3b8',
      background: '#ffffff',
      foreground: '#1e293b',
      border: '#e2e8f0',
    },
    gradients: {
      primary: ['#3b82f6', '#1d4ed8'],
      secondary: ['#64748b', '#475569'],
      accent: ['#8b5cf6', '#7c3aed'],
    },
    shadows: {
      small: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
      medium: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
      large: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
    },
    animations: {
      duration: 300,
      easing: 'ease-in-out',
    },
    responsive: {
      breakpoints: {
        sm: 640,
        md: 768,
        lg: 1024,
        xl: 1280,
      },
    },
  },
  dark: {
    colors: {
      primary: '#60a5fa',
      secondary: '#94a3b8',
      accent: '#a78bfa',
      success: '#34d399',
      warning: '#fbbf24',
      error: '#f87171',
      info: '#22d3ee',
      muted: '#64748b',
      background: '#0f172a',
      foreground: '#f1f5f9',
      border: '#334155',
    },
    gradients: {
      primary: ['#60a5fa', '#3b82f6'],
      secondary: ['#94a3b8', '#64748b'],
      accent: ['#a78bfa', '#8b5cf6'],
    },
    shadows: {
      small: '0 1px 3px 0 rgb(0 0 0 / 0.3)',
      medium: '0 4px 6px -1px rgb(0 0 0 / 0.3)',
      large: '0 20px 25px -5px rgb(0 0 0 / 0.3)',
    },
    animations: {
      duration: 300,
      easing: 'ease-in-out',
    },
    responsive: {
      breakpoints: {
        sm: 640,
        md: 768,
        lg: 1024,
        xl: 1280,
      },
    },
  },
};

export const getTheme = (mode: 'light' | 'dark' = 'light'): ChartThemeConfig => {
  return chartThemes[mode] || chartThemes.light;
};

export const chartColorPalette = {
  categorical: [
    '#3b82f6',
    '#10b981',
    '#f59e0b',
    '#ef4444',
    '#8b5cf6',
    '#06b6d4',
    '#f97316',
    '#84cc16',
    '#ec4899',
    '#6366f1',
  ],
  diverging: [
    '#ef4444',
    '#f97316',
    '#f59e0b',
    '#eab308',
    '#84cc16',
    '#22c55e',
    '#10b981',
    '#14b8a6',
    '#06b6d4',
  ],
  sequential: [
    '#f0f9ff',
    '#e0f2fe',
    '#bae6fd',
    '#7dd3fc',
    '#38bdf8',
    '#0ea5e9',
    '#0284c7',
    '#0369a1',
    '#075985',
  ],
};