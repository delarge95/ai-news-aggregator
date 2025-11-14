import React, { useState, useRef, useEffect } from 'react';
import { Search, Clock, TrendingUp, X } from 'lucide-react';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandList,
} from '../ui/command';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: (query: string) => void;
  suggestions: Array<{
    id: string;
    text: string;
    type: 'query' | 'source' | 'category' | 'tag' | 'author';
    count?: number;
    isRecent?: boolean;
  }>;
  onGetSuggestions: (query: string) => Promise<void>;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChange,
  onSearch,
  suggestions,
  onGetSuggestions,
  placeholder = "Buscar noticias...",
  className,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (value.length >= 2) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        onGetSuggestions(value);
      }, 300);
    }
  }, [value, onGetSuggestions]);

  useEffect(() => {
    if (isOpen) {
      setFocusedIndex(-1);
    }
  }, [suggestions, isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter') {
        e.preventDefault();
        handleSearch();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setFocusedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setFocusedIndex(prev => prev > 0 ? prev - 1 : prev);
        break;
      case 'Enter':
        e.preventDefault();
        if (focusedIndex >= 0 && focusedIndex < suggestions.length) {
          handleSuggestionSelect(suggestions[focusedIndex]);
        } else {
          handleSearch();
        }
        break;
      case 'Escape':
        setIsOpen(false);
        inputRef.current?.blur();
        break;
    }
  };

  const handleSearch = () => {
    if (value.trim()) {
      onSearch(value.trim());
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleSuggestionSelect = (suggestion: typeof suggestions[0]) => {
    onChange(suggestion.text);
    onSearch(suggestion.text);
    setIsOpen(false);
    inputRef.current?.blur();
  };

  const handleClear = () => {
    onChange('');
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const getSuggestionIcon = (type: string, isRecent?: boolean) => {
    if (isRecent) return <Clock className="w-4 h-4" />;
    
    switch (type) {
      case 'query':
        return <Search className="w-4 h-4" />;
      case 'trending':
        return <TrendingUp className="w-4 h-4" />;
      default:
        return <Search className="w-4 h-4" />;
    }
  };

  const getSuggestionTypeColor = (type: string) => {
    switch (type) {
      case 'query':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'source':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'category':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'tag':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'author':
        return 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const groupedSuggestions = suggestions.reduce((groups, suggestion) => {
    const type = suggestion.isRecent ? 'recent' : suggestion.type;
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(suggestion);
    return groups;
  }, {} as Record<string, typeof suggestions>);

  const suggestionGroups = [
    { key: 'recent', label: 'Búsquedas Recientes' },
    { key: 'query', label: 'Sugerencias' },
    { key: 'trending', label: 'Tendencias' },
    { key: 'source', label: 'Fuentes' },
    { key: 'category', label: 'Categorías' },
    { key: 'tag', label: 'Etiquetas' },
    { key: 'author', label: 'Autores' },
  ].filter(group => groupedSuggestions[group.key]?.length > 0);

  return (
    <div className={cn("relative w-full", className)}>
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              ref={inputRef}
              type="text"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setIsOpen(true)}
              placeholder={placeholder}
              disabled={disabled}
              className="pl-10 pr-10"
            />
            {value && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClear}
                className="absolute right-1 top-1/2 transform -translate-y-1/2 w-8 h-8 p-0"
              >
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </PopoverTrigger>
        
        <PopoverContent 
          className="w-full max-w-lg p-0" 
          align="start"
          side="bottom"
        >
          <Command>
            <CommandList>
              {suggestionGroups.length === 0 && !value && (
                <CommandEmpty className="p-4 text-center text-gray-500">
                  Escribe para ver sugerencias
                </CommandEmpty>
              )}

              {suggestionGroups.map((group) => (
                <CommandGroup key={group.key} heading={group.label}>
                  {groupedSuggestions[group.key].map((suggestion, index) => {
                    const globalIndex = suggestions.findIndex(s => s.id === suggestion.id);
                    const isFocused = globalIndex === focusedIndex;
                    
                    return (
                      <CommandItem
                        key={suggestion.id}
                        value={suggestion.text}
                        onSelect={() => handleSuggestionSelect(suggestion)}
                        className={cn(
                          "flex items-center gap-2 cursor-pointer",
                          isFocused && "bg-gray-100 dark:bg-gray-800"
                        )}
                      >
                        {getSuggestionIcon(suggestion.type, suggestion.isRecent)}
                        <span className="flex-1 truncate">{suggestion.text}</span>
                        {suggestion.count && (
                          <Badge 
                            variant="secondary" 
                            className="text-xs"
                          >
                            {suggestion.count}
                          </Badge>
                        )}
                        <Badge 
                          variant="outline" 
                          className={cn("text-xs", getSuggestionTypeColor(suggestion.type))}
                        >
                          {suggestion.type}
                        </Badge>
                      </CommandItem>
                    );
                  })}
                </CommandGroup>
              ))}

              {suggestions.length === 0 && value && (
                <CommandEmpty className="p-4 text-center text-gray-500">
                  No se encontraron sugerencias para "{value}"
                </CommandEmpty>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
};