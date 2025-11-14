# Sistema de Búsqueda y Filtrado Frontend

## Descripción

Sistema completo de búsqueda y filtrado para la aplicación AI News Aggregator, implementado con React, TypeScript y Tailwind CSS. Incluye búsqueda inteligente, filtros avanzados, historial de búsquedas, búsquedas guardadas y análisis de IA.

## Características Principales

### 🔍 Búsqueda Inteligente
- **Autocompletado**: Sugerencias en tiempo real mientras el usuario escribe
- **Búsqueda semántica**: Búsqueda por múltiples términos relacionados
- **Debouncing**: Optimización de rendimiento con retraso en las solicitudes
- **Highlighting**: Resaltado de términos de búsqueda en los resultados

### 🎛️ Filtros Avanzados
- **Rango de fechas**: Filtros preestablecidos y personalizados
- **Fuentes**: Selección múltiple de fuentes de noticias
- **Categorías**: Filtrado por categorías de contenido
- **Autores**: Búsqueda por autor específico
- **Idioma**: Filtrado por idioma del artículo
- **Puntuación IA**: Rango de puntuación de relevancia por IA

### 📚 Gestión de Búsquedas
- **Historial local**: Almacenamiento en localStorage
- **Búsquedas guardadas**: Para usuarios autenticados
- **Alertas**: Notificaciones automáticas de nuevos resultados
- **Exportación/Importación**: Respaldo de datos del usuario

### 🎨 Interfaz de Usuario
- **Responsive**: Adaptable a todos los tamaños de pantalla
- **Skeleton loading**: Estados de carga elegantes
- **Accesibilidad**: Completamente accesible con ARIA
- **Temas**: Soporte para modo claro y oscuro

## Estructura de Componentes

```
search/
├── SearchInterface.tsx      # Componente principal
├── SearchBar.tsx           # Barra de búsqueda con autocompletado
├── FilterPanel.tsx         # Panel de filtros avanzados
├── SearchResults.tsx       # Visualización de resultados
├── SearchHistory.tsx       # Historial de búsquedas
├── SavedSearches.tsx       # Búsquedas guardadas
├── SearchSkeleton.tsx      # Componentes de carga
├── useSearch.ts            # Hook personalizado para lógica de búsqueda
└── types.ts                # Tipos TypeScript
```

## Uso Básico

### Implementación Simple

```tsx
import { SearchInterface } from './components/search';

function MyPage() {
  const handleArticleClick = (article) => {
    console.log('Article clicked:', article);
    // Handle article click
  };

  return (
    <div className="container mx-auto py-8">
      <SearchInterface 
        showSavedSearches={true}
        showHistory={true}
        showFilters={true}
        onArticleClick={handleArticleClick}
      />
    </div>
  );
}
```

### Uso Avanzado

```tsx
import { useSearch } from './components/search/useSearch';

function CustomSearchComponent() {
  const {
    query,
    results,
    isSearching,
    filters,
    search,
    updateFilters,
    saveSearch,
    highlightTerms,
  } = useSearch();

  const handleSearch = (searchQuery) => {
    search(searchQuery);
  };

  const handleFilterChange = (newFilters) => {
    updateFilters(newFilters);
  };

  return (
    <div>
      <SearchBar
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        suggestions={suggestions}
        onGetSuggestions={getSuggestions}
      />
      
      <FilterPanel
        filters={filters}
        onFiltersChange={handleFilterChange}
        onClearFilters={clearFilters}
      />
      
      <SearchResults
        results={results}
        isLoading={isSearching}
        hasMore={hasMore}
        onLoadMore={loadMore}
        highlightTerms={highlightTerms}
        searchQuery={query}
      />
    </div>
  );
}
```

## API de Componentes

### SearchInterface

Props:
- `className?: string` - Clases CSS adicionales
- `showSavedSearches?: boolean` - Mostrar búsquedas guardadas
- `showHistory?: boolean` - Mostrar historial
- `showFilters?: boolean` - Mostrar panel de filtros
- `initialQuery?: string` - Consulta inicial
- `onArticleClick?: (article) => void` - Callback al hacer clic en artículo

### SearchBar

Props:
- `value: string` - Valor actual de la búsqueda
- `onChange: (value) => void` - Callback al cambiar el valor
- `onSearch: (query) => void` - Callback al realizar búsqueda
- `suggestions: SearchSuggestion[]` - Lista de sugerencias
- `onGetSuggestions: (query) => Promise<void>` - Función para obtener sugerencias
- `placeholder?: string` - Texto de placeholder
- `disabled?: boolean` - Estado deshabilitado

### FilterPanel

Props:
- `filters: SearchFilters` - Filtros actuales
- `onFiltersChange: (filters) => void` - Callback al cambiar filtros
- `onClearFilters: () => void` - Callback para limpiar filtros
- `availableFilters?: AvailableFilters` - Filtros disponibles

### SearchResults

Props:
- `results: SearchResult[]` - Resultados de búsqueda
- `isLoading: boolean` - Estado de carga
- `hasMore: boolean` - Si hay más resultados para cargar
- `onLoadMore: () => void` - Callback para cargar más
- `highlightTerms?: (text, terms) => string` - Función para resaltar términos
- `searchQuery?: string` - Consulta de búsqueda

## Estado Global

El hook `useSearch` maneja:
- Estado de búsqueda (query, isSearching, results)
- Filtros activos
- Historial de búsquedas
- Búsquedas guardadas
- Sugerencias de autocompletado
- Paginación de resultados

## Persistencia

### LocalStorage

```typescript
// Historial de búsquedas (máximo 50 elementos)
const STORAGE_KEYS = {
  SEARCH_HISTORY: 'ai-news-search-history',
  SAVED_SEARCHES: 'ai-news-saved-searches',
  USER_PREFERENCES: 'ai-news-user-preferences',
};
```

### Servicios

- **searchAPI**: Interfaz con el backend
- **storageService**: Gestión de almacenamiento local

## Integración con Backend

### API Endpoints

```
GET /api/v1/search?q={query}&filters={filters}&page={page}&sort={sort}
GET /api/v1/search/suggestions?q={query}
GET /api/v1/search/trending
```

### Respuesta de API

```typescript
interface SearchResponse {
  results: SearchResult[];
  totalResults: number;
  hasMore: boolean;
  searchTime: number;
  facets?: {
    sources: Array<{ name: string; count: number }>;
    categories: Array<{ name: string; count: number }>;
    authors: Array<{ name: string; count: number }>;
  };
}
```

## Características de IA

### Análisis de Sentimiento
- Clasificación automática (positive, negative, neutral)
- Puntuación de confianza
- Visualización en badges de colores

### Insights de IA
- Temas clave extraídos automáticamente
- Puntuación de relevancia
- Análisis de contenido

### Highlighting Inteligente
- Resaltado de términos de búsqueda
- Búsqueda en título y contenido
- Términos relacionados

## Performance

### Optimizaciones
- **Debouncing**: 300ms de retraso en búsquedas
- **Lazy Loading**: Carga bajo demanda de componentes
- **Memoización**: React.memo para componentes pesados
- **Skeleton Loading**: Estados de carga inmediatos
- **AbortController**: Cancelación de solicitudes anteriores

### Caché
- LocalStorage para datos persistentes
- Caché de sugerencias
- Cache de resultados de búsqueda

## Accesibilidad

### Características
- Navegación por teclado completa
- ARIA labels y roles
- Contraste de colores adecuado
- Soporte para lectores de pantalla
- Focus management

## Temas y Estilos

### Tailwind CSS
- Clases utilitarias personalizadas
- Sistema de colores consistente
- Animaciones y transiciones
- Responsive design

### Modo Oscuro
- Soporte completo para temas
- Persistencia de preferencia
- Transiciones suaves

## Instalación

### Dependencias Requeridas

```json
{
  "react": "^18.3.1",
  "react-router-dom": "^6",
  "lucide-react": "^0.364.0",
  "date-fns": "^3.0.0",
  "@radix-ui/*": "/*",
  "lodash": "^4.17.21",
  "clsx": "^2.1.1",
  "tailwind-merge": "^2.6.0"
}
```

### Instalación de Componentes UI

```bash
# Los componentes UI están incluidos en el sistema:
# - button, input, badge, card, dialog, popover
# - select, checkbox, collapsible, slider
# - command, tabs, sheet, alert-dialog
# - dropdown-menu, tooltip, avatar, progress
# - scroll-area, separator, skeleton
```

## Ejemplos de Uso

### Página de Búsqueda Principal

```tsx
import { SearchInterface } from './components/search';

export default function SearchPage() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Búsqueda de Noticias</h1>
        </div>
      </header>
      
      <main className="container mx-auto px-4 py-8">
        <SearchInterface 
          showSavedSearches={true}
          showHistory={true}
          showFilters={true}
          initialQuery=""
          onArticleClick={(article) => {
            // Navegar a detalle del artículo
            window.open(article.url, '_blank');
          }}
        />
      </main>
    </div>
  );
}
```

### Widget de Búsqueda Compacto

```tsx
import { SearchBar } from './components/search';

export default function SearchWidget({ onSearch }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  const handleSearch = (searchQuery) => {
    onSearch(searchQuery);
  };

  return (
    <div className="w-full max-w-2xl">
      <SearchBar
        value={query}
        onChange={setQuery}
        onSearch={handleSearch}
        suggestions={suggestions}
        onGetSuggestions={async (q) => {
          // Fetch suggestions
          const results = await fetchSuggestions(q);
          setSuggestions(results);
        }}
        placeholder="Buscar noticias..."
      />
    </div>
  );
}
```

## Contribución

Para contribuir al sistema de búsqueda:

1. Seguir las convenciones de TypeScript
2. Mantener la accesibilidad
3. Optimizar para performance
4. Escribir tests para nuevas funcionalidades
5. Documentar cambios importantes

## Licencia

Este sistema es parte del proyecto AI News Aggregator y está sujeto a la misma licencia.