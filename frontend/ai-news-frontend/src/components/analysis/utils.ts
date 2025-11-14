/**
 * Utilidades UI para componentes de análisis
 */

import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const CHART_COLORS = {
  primary: '#3B82F6',
  secondary: '#6B7280',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#06B6D4',
  purple: '#8B5CF6',
  pink: '#EC4899',
  
  // Gradientes
  gradients: {
    positive: 'from-green-400 to-green-600',
    negative: 'from-red-400 to-red-600', 
    neutral: 'from-gray-400 to-gray-600',
    primary: 'from-blue-400 to-blue-600',
    purple: 'from-purple-400 to-purple-600'
  }
};

export const SENTIMENT_COLORS = {
  positive: '#10B981',
  negative: '#EF4444', 
  neutral: '#6B7280'
};

export const getSentimentColor = (sentiment: number): string => {
  if (sentiment > 0.2) return SENTIMENT_COLORS.positive;
  if (sentiment < -0.2) return SENTIMENT_COLORS.negative;
  return SENTIMENT_COLORS.neutral;
};

export const getSentimentLabel = (sentiment: number): string => {
  if (sentiment > 0.5) return 'Muy Positivo';
  if (sentiment > 0.2) return 'Positivo';
  if (sentiment > -0.2) return 'Neutral';
  if (sentiment > -0.5) return 'Negativo';
  return 'Muy Negativo';
};

export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toLocaleString();
};

export const formatPercentage = (value: number, decimals: number = 1): string => {
  return (value * 100).toFixed(decimals) + '%';
};

export const formatDate = (date: Date, format: 'short' | 'long' = 'short'): string => {
  const options: Intl.DateTimeFormatOptions = format === 'long' 
    ? { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }
    : { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric'
      };
  
  return date.toLocaleDateString('es-ES', options);
};

export const getTimeAgo = (date: Date): string => {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) {
    return `hace ${days} día${days > 1 ? 's' : ''}`;
  }
  if (hours > 0) {
    return `hace ${hours} hora${hours > 1 ? 's' : ''}`;
  }
  if (minutes > 0) {
    return `hace ${minutes} minuto${minutes > 1 ? 's' : ''}`;
  }
  return 'hace un momento';
};

export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

export const debounce = <T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

export const throttle = <T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

export const getScoreColor = (score: number): string => {
  if (score >= 80) return '#10B981'; // Verde
  if (score >= 60) return '#F59E0B'; // Ámbar
  if (score >= 40) return '#EF4444'; // Rojo
  return '#6B7280'; // Gris
};

export const getScoreLevel = (score: number): { level: string; color: string } => {
  if (score >= 90) return { level: 'Excelente', color: 'text-green-600' };
  if (score >= 80) return { level: 'Muy Bueno', color: 'text-green-500' };
  if (score >= 70) return { level: 'Bueno', color: 'text-blue-500' };
  if (score >= 60) return { level: 'Regular', color: 'text-amber-500' };
  if (score >= 40) return { level: 'Deficiente', color: 'text-red-500' };
  return { level: 'Crítico', color: 'text-red-600' };
};

export const calculateGrowthRate = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

export const interpolateColor = (color1: string, color2: string, factor: number): string => {
  const hex = (color: string) => parseInt(color.slice(1), 16);
  const r1 = hex(color1) >> 16;
  const g1 = (hex(color1) >> 8) & 0xFF;
  const b1 = hex(color1) & 0xFF;
  
  const r2 = hex(color2) >> 16;
  const g2 = (hex(color2) >> 8) & 0xFF;
  const b2 = hex(color2) & 0xFF;
  
  const r = Math.round(r1 + factor * (r2 - r1));
  const g = Math.round(g1 + factor * (g2 - g1));
  const b = Math.round(b1 + factor * (b2 - b1));
  
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
};

export const generateColors = (count: number): string[] => {
  const baseColors = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', 
    '#8B5CF6', '#06B6D4', '#EC4899', '#84CC16',
    '#F97316', '#6366F1'
  ];
  
  if (count <= baseColors.length) {
    return baseColors.slice(0, count);
  }
  
  // Generar colores adicionales interpolando
  const colors = [...baseColors];
  const extra = count - baseColors.length;
  
  for (let i = 0; i < extra; i++) {
    const color1 = baseColors[i % baseColors.length];
    const color2 = baseColors[(i + 1) % baseColors.length];
    const factor = (i + 1) / (extra + 1);
    colors.push(interpolateColor(color1, color2, factor));
  }
  
  return colors;
};

export const validateData = (data: unknown[]): { valid: unknown[]; invalid: unknown[] } => {
  const valid: unknown[] = [];
  const invalid: unknown[] = [];
  
  data.forEach(item => {
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      valid.push(item);
    } else {
      invalid.push(item);
    }
  });
  
  return { valid, invalid };
};

export const downloadCSV = (data: Record<string, unknown>[], filename: string): void => {
  if (data.length === 0) return;
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    )
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `${filename}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // Fallback para navegadores que no soportan clipboard API
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch (err) {
      document.body.removeChild(textArea);
      return false;
    }
  }
};

export const isMobile = (): boolean => {
  return window.innerWidth < 768;
};

export const getResponsiveDimensions = () => {
  const width = window.innerWidth;
  const isMobile = width < 768;
  const isTablet = width >= 768 && width < 1024;
  const isDesktop = width >= 1024;
  
  return {
    isMobile,
    isTablet,
    isDesktop,
    breakpoints: {
      mobile: 768,
      tablet: 1024,
      desktop: 1280
    }
  };
};
