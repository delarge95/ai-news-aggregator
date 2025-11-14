import React, { useMemo, useCallback } from 'react';
import { SearchResult } from './types';

/**
 * Hook personalizado para highlighting inteligente de términos
 * @param searchQuery - Query de búsqueda actual
 * @param results - Resultados de búsqueda
 */
export const useTextHighlighting = (searchQuery: string, results: SearchResult[]) => {
  // Extraer términos relevantes de la búsqueda
  const searchTerms = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2) return [];
    
    // Dividir por espacios y filtrar términos cortos
    const terms = searchQuery
      .toLowerCase()
      .split(/\s+/)
      .filter(term => term.length >= 2);
    
    // Remover duplicados
    return [...new Set(terms)];
  }, [searchQuery]);

  // Función para escapar caracteres especiales en regex
  const escapeRegExp = useCallback((string: string): string => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }, []);

  // Función principal de highlighting
  const highlightText = useCallback((text: string, terms: string[] = searchTerms): string => {
    if (!text || !terms || terms.length === 0) return text;
    
    // Crear regex dinámico para matching
    const escapedTerms = terms.map(escapeRegExp);
    const regex = new RegExp(`(${escapedTerms.join('|')})`, 'gi');
    
    // Reemplazar matches con markup
    return text.replace(regex, '<mark class="bg-yellow-200 dark:bg-yellow-800 text-yellow-900 dark:text-yellow-100 font-medium rounded px-1">$1</mark>');
  }, [searchTerms, escapeRegExp]);

  // Función para highlighting con contexto mejorado
  const highlightWithContext = useCallback((text: string, maxLength: number = 150): string => {
    if (!text || searchTerms.length === 0) return text;
    
    const lowerText = text.toLowerCase();
    let matchIndex = -1;
    let matchLength = 0;
    
    // Buscar el primer match para contextualizar
    for (const term of searchTerms) {
      const index = lowerText.indexOf(term.toLowerCase());
      if (index !== -1) {
        matchIndex = index;
        matchLength = term.length;
        break;
      }
    }
    
    if (matchIndex === -1) {
      return highlightText(text.substring(0, maxLength)) + (text.length > maxLength ? '...' : '');
    }
    
    // Calcular contexto alrededor del match
    const start = Math.max(0, matchIndex - Math.floor(maxLength / 2));
    const end = Math.min(text.length, start + maxLength);
    
    let contextualText = text.substring(start, end);
    
    // Añadir indicadores de texto cortado
    if (start > 0) contextualText = '...' + contextualText;
    if (end < text.length) contextualText = contextualText + '...';
    
    return highlightText(contextualText);
  }, [searchTerms, highlightText]);

  // Función para highlighting inteligente de términos relacionados
  const highlightWithRelatedTerms = useCallback((
    text: string, 
    relatedTerms: string[] = []
  ): string => {
    if (!text) return text;
    
    const allTerms = [...searchTerms, ...relatedTerms].filter(term => term.length >= 2);
    
    if (allTerms.length === 0) return text;
    
    // Prioridad 1: términos exactos de búsqueda
    let highlightedText = highlightText(text, searchTerms);
    
    // Prioridad 2: términos relacionados (subrayado)
    if (relatedTerms.length > 0) {
      const escapedTerms = relatedTerms.map(escapeRegExp);
      const regex = new RegExp(`(${escapedTerms.join('|')})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<u class="text-blue-600 dark:text-blue-400">$1</u>');
    }
    
    return highlightedText;
  }, [searchTerms, relatedTerms, highlightText, escapeRegExp]);

  // Función para contar matches
  const countMatches = useCallback((text: string): number => {
    if (!text || searchTerms.length === 0) return 0;
    
    let count = 0;
    const escapedTerms = searchTerms.map(escapeRegExp);
    const regex = new RegExp(`(${escapedTerms.join('|')})`, 'gi');
    const matches = text.match(regex);
    
    return matches ? matches.length : 0;
  }, [searchTerms, escapeRegExp]);

  // Aplicar highlighting a resultados completos
  const enhancedResults = useMemo(() => {
    if (searchTerms.length === 0) return results;
    
    return results.map(result => {
      const titleMatches = countMatches(result.title);
      const contentMatches = countMatches(result.content);
      const summaryMatches = countMatches(result.summary);
      
      return {
        ...result,
        highlightedContent: {
          title: highlightWithContext(result.title),
          content: highlightWithContext(result.content, 200),
          matchedTerms: searchTerms,
          titleMatches,
          contentMatches,
          summaryMatches,
          totalMatches: titleMatches + contentMatches + summaryMatches,
        }
      };
    });
  }, [results, searchTerms, highlightWithContext, countMatches]);

  return {
    searchTerms,
    highlightText,
    highlightWithContext,
    highlightWithRelatedTerms,
    countMatches,
    enhancedResults,
  };
};

/**
 * Componente para mostrar términos resaltados
 */
export const HighlightedText: React.FC<{
  text: string;
  searchQuery?: string;
  className?: string;
  showContext?: boolean;
  maxLength?: number;
}> = ({
  text,
  searchQuery,
  className = '',
  showContext = false,
  maxLength = 150
}) => {
  const { highlightWithContext, highlightText } = useTextHighlighting(searchQuery || '', []);
  
  const highlightedText = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2) {
      return text;
    }
    
    if (showContext) {
      return highlightWithContext(text, maxLength);
    }
    
    return highlightText(text);
  }, [text, searchQuery, showContext, maxLength, highlightWithContext, highlightText]);

  return (
    <span 
      className={className}
      dangerouslySetInnerHTML={{ __html: highlightedText }}
    />
  );
};

/**
 * Componente para badge de estadísticas de matching
 */
export const MatchStats: React.FC<{
  titleMatches: number;
  contentMatches: number;
  summaryMatches: number;
  className?: string;
}> = ({
  titleMatches,
  contentMatches,
  summaryMatches,
  className = ''
}) => {
  const totalMatches = titleMatches + contentMatches + summaryMatches;
  
  if (totalMatches === 0) return null;
  
  return (
    <div className={`flex items-center gap-2 text-xs text-muted-foreground ${className}`}>
      <span className="font-medium">{totalMatches} coincidencias</span>
      {titleMatches > 0 && (
        <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-1 rounded">
          {titleMatches} título
        </span>
      )}
      {contentMatches > 0 && (
        <span className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-1 rounded">
          {contentMatches} contenido
        </span>
      )}
    </div>
  );
};

/**
 * Utilidad para extraer términos de diferentes fuentes
 */
export const extractSearchTerms = (query: string): string[] => {
  if (!query || query.length < 2) return [];
  
  // Limpiar y dividir términos
  return query
    .toLowerCase()
    .split(/[\s,.;:!?()\[\]{}"']+/)
    .filter(term => term.length >= 2 && term.trim() !== '')
    .filter((term, index, arr) => arr.indexOf(term) === index); // Remover duplicados
};

/**
 * Función para encontrar términos relacionados
 */
export const findRelatedTerms = (mainTerm: string, allTerms: string[]): string[] => {
  if (!mainTerm || mainTerm.length < 3) return [];
  
  return allTerms.filter(term => {
    if (term === mainTerm) return false;
    
    // Buscar coincidencias parciales
    return (
      term.includes(mainTerm) ||
      mainTerm.includes(term) ||
      // Similitud fonética básica
      (mainTerm.length > 4 && term.length > 4 && 
       (mainTerm.substring(0, Math.floor(mainTerm.length * 0.7)) === term.substring(0, Math.floor(term.length * 0.7))))
    );
  });
};