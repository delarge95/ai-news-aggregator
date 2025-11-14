import React, { useState, useEffect, useRef } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { 
  Search, 
  X, 
  TrendingUp, 
  Hash, 
  Building2, 
  Tag,
  Clock
} from 'lucide-react';
import { AutocompleteSuggestion } from './types';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: (query: string) => void;
  suggestions: AutocompleteSuggestion[];
  onSuggestionSelect: (suggestion: AutocompleteSuggestion) => void;
  placeholder?: string;
  isLoading?: boolean;
  recentSearches?: string[];
  popularSearches?: string[];
  className?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSubmit,
  suggestions,
  onSuggestionSelect,
  placeholder = "Buscar noticias...",
  isLoading = false,
  recentSearches = [],
  popularSearches = [],
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Combinar sugerencias, búsquedas recientes y populares
  const allSuggestions = [
    // Sugerencias del autocompletado
    ...suggestions.map(s => ({ ...s, type: s.type || 'keyword' as const })),
    // Búsquedas recientes (si no hay texto)
    ...(value === '' && recentSearches.length > 0 
      ? recentSearches.map(query => ({
          value: query,
          label: query,
          type: 'keyword' as const,
          count: undefined
        }))
      : []),
    // Búsquedas populares
    ...(value === '' && popularSearches.length > 0
      ? popularSearches.map(query => ({
          value: query,
          label: query,
          type: 'keyword' as const,
          count: undefined
        }))
      : []),
  ];

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  useEffect(() => {
    if (value.length > 0 || allSuggestions.length > 0) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
    setFocusedIndex(-1);
  }, [value, allSuggestions.length]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange(newValue);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showSuggestions) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev => 
          prev < allSuggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (focusedIndex >= 0 && allSuggestions[focusedIndex]) {
          handleSuggestionClick(allSuggestions[focusedIndex]);
        } else if (value.trim()) {
          handleSearchSubmit();
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setFocusedIndex(-1);
        inputRef.current?.blur();
        break;
    }
  };

  const handleSearchSubmit = () => {
    if (value.trim() && onSubmit) {
      onSubmit(value.trim());
    }
    setShowSuggestions(false);
    inputRef.current?.blur();
  };

  const handleSuggestionClick = (suggestion: AutocompleteSuggestion) => {
    onChange(suggestion.value);
    onSuggestionSelect(suggestion);
    setShowSuggestions(false);
    
    // Si es una búsqueda, ejecutar búsqueda automáticamente
    if (suggestion.type === 'keyword' && onSubmit) {
      onSubmit(suggestion.value);
    }
  };

  const clearSearch = () => {
    onChange('');
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'source':
        return <Building2 className="h-4 w-4 text-blue-500" />;
      case 'tag':
        return <Tag className="h-4 w-4 text-green-500" />;
      case 'category':
        return <Hash className="h-4 w-4 text-purple-500" />;
      case 'keyword':
        return value === '' ? <Clock className="h-4 w-4 text-gray-500" /> : <Search className="h-4 w-4 text-gray-500" />;
      default:
        return <Search className="h-4 w-4 text-gray-500" />;
    }
  };

  const getSuggestionBadgeColor = (type: string) => {
    switch (type) {
      case 'source':
        return 'bg-blue-100 text-blue-800';
      case 'tag':
        return 'bg-green-100 text-green-800';
      case 'category':
        return 'bg-purple-100 text-purple-800';
      case 'keyword':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div ref={containerRef} className={`relative w-full max-w-2xl ${className}`}>
      <div className="relative flex items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <Input
            ref={inputRef}
            type="text"
            placeholder={placeholder}
            value={value}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(true)}
            className="pl-10 pr-10 h-12 text-base"
            disabled={isLoading}
          />
          {value && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSearch}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        
        <Button 
          onClick={handleSearchSubmit}
          className="ml-2 h-12 px-6"
          disabled={!value.trim() || isLoading}
        >
          <Search className="h-4 w-4" />
          Buscar
        </Button>
      </div>

      {/* Sugerencias dropdown */}
      {showSuggestions && allSuggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto">
          {/* Sección de sugerencias */}
          {suggestions.length > 0 && (
            <div className="p-2">
              <div className="text-xs text-gray-500 px-2 py-1 font-medium">
                Sugerencias
              </div>
              {suggestions.map((suggestion, index) => (
                <button
                  key={`suggestion-${index}`}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 rounded-md transition-colors ${
                    index === focusedIndex ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleSuggestionClick(suggestion)}
                >
                  {getSuggestionIcon(suggestion.type)}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-900 truncate">
                      {suggestion.label}
                    </div>
                    {suggestion.count && (
                      <div className="text-xs text-gray-500">
                        {suggestion.count} resultados
                      </div>
                    )}
                  </div>
                  <Badge 
                    variant="secondary" 
                    className={`text-xs ${getSuggestionBadgeColor(suggestion.type)}`}
                  >
                    {suggestion.type}
                  </Badge>
                </button>
              ))}
            </div>
          )}

          {/* Sección de búsquedas recientes */}
          {value === '' && recentSearches.length > 0 && (
            <div className="border-t p-2">
              <div className="text-xs text-gray-500 px-2 py-1 font-medium flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Recientes
              </div>
              {recentSearches.slice(0, 5).map((query, index) => (
                <button
                  key={`recent-${index}`}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 rounded-md transition-colors ${
                    index + suggestions.length === focusedIndex ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleSuggestionClick({ value: query, label: query, type: 'keyword' })}
                >
                  <Clock className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-900">{query}</span>
                </button>
              ))}
            </div>
          )}

          {/* Sección de búsquedas populares */}
          {value === '' && popularSearches.length > 0 && (
            <div className="border-t p-2">
              <div className="text-xs text-gray-500 px-2 py-1 font-medium flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                Populares
              </div>
              {popularSearches.slice(0, 5).map((query, index) => (
                <button
                  key={`popular-${index}`}
                  className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-gray-50 rounded-md transition-colors ${
                    index + suggestions.length + recentSearches.length === focusedIndex ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleSuggestionClick({ value: query, label: query, type: 'keyword' })}
                >
                  <TrendingUp className="h-4 w-4 text-orange-400" />
                  <span className="text-sm text-gray-900">{query}</span>
                  <TrendingUp className="h-3 w-3 text-orange-400 ml-auto" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;