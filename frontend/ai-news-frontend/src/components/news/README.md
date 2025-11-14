# Sistema de Lista de Noticias con Filtros - AI News Aggregator

Este directorio contiene una implementación completa y robusta de un sistema de lista de noticias con filtros avanzados para el agregador de noticias de IA.

## 🚀 Componentes Principales

### 1. NewsList.tsx
Componente principal que orquesta toda la funcionalidad de la lista de noticias.

**Características:**
- Vista de grid y lista
- Infinite scroll y paginación manual
- Responsive design
- Estados de carga y error
- Integración con todos los componentes de filtrado

**Props principales:**
```typescript
interface NewsListProps {
  articles: NewsArticle[];
  isLoading: boolean;
  error?: string;
  pagination: PaginationInfo;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  // ... más props
}
```

### 2. NewsCard.tsx
Tarjeta individual para mostrar noticias con metadatos de IA.

**Características:**
- Vista grid y lista
- Metadatos de IA (sentimiento, relevancia, legibilidad)
- Tooltips informativos
- Imagen optimizada
- Enlaces externos seguros

**Metadatos de IA mostrados:**
- 🟢 Sentimiento (positivo/negativo/neutral)
- 📊 Puntuación de relevancia
- ⏱️ Índice de legibilidad
- 🏷️ Tags y keywords
- 🏢 Entidades (personas, organizaciones, ubicaciones)

### 3. AdvancedFilters.tsx
Panel de filtros lateral con tabs organizados.

**Tipos de filtros:**
- **Fecha**: Rango de fechas con calendario
- **Fuente**: Checkbox de fuentes disponibles
- **Sentimiento**: Positivo/Negativo/Neutral
- **Relevancia**: Slider de rango
- **Categoría**: Categorías de noticias
- **Tags**: Tags populares

**Características:**
- Diseño responsive (sidebar en desktop, modal en móvil)
- Contador de filtros activos
- Limpieza rápida de filtros
- Scroll para listas largas

### 4. NewsFilters.tsx
Componente de filtros alternativo con vista compacta y completa.

**Modos:**
- **Compact**: Para usar en headers
- **Full**: Panel completo con tabs

**Organización:**
- Básico (fecha, fuente, categoría)
- IA (sentimiento, relevancia, idioma)
- Avanzado (tags populares)

### 5. SearchBar.tsx
Barra de búsqueda con autocompletado inteligente.

**Funcionalidades:**
- Autocompletado en tiempo real
- Búsquedas recientes
- Términos populares
- Navegación por teclado
- Sugerencias categorizadas

**Tipos de sugerencias:**
- 📰 Fuentes de noticias
- 🏷️ Tags específicos
- #️⃣ Categorías
- 🔍 Palabras clave

### 6. SortControls.tsx
Controles de ordenamiento múltiple.

**Opciones de ordenamiento:**
- 📅 Fecha (ascendente/descendente)
- 📊 Relevancia (mayor/menor)
- 📝 Título (A-Z/Z-A)
- 🌐 Fuente (A-Z/Z-A)

**Características:**
- Cambio rápido de dirección
- Modo de ordenamiento múltiple
- Indicadores visuales

## 🛠️ Componentes de Estado y UX

### 7. LoadingSkeleton.tsx
Sistema completo de skeletons para estados de carga.

**Tipos de skeletons:**
- `NewsListSkeleton`: Lista completa con filtros
- `NewsCardSkeleton`: Tarjeta individual (grid/lista)
- `InitialLoadingSkeleton`: Carga inicial
- `LoadingMoreSkeleton`: Cargando más contenido
- `EmptySearchSkeleton`: Estado vacío con búsqueda

**Características:**
- Responsive
- Animaciones fluidas
- Diferentes variantes según contexto

### 8. InfiniteScroll.tsx
Sistema avanzado de scroll infinito.

**Variantes:**
- `InfiniteScroll`: Implementación básica
- `BatchInfiniteScroll`: Carga por lotes
- `HybridInfiniteScroll`: Con fallback manual

**Características:**
- Detección automática de scroll
- Configuración de rootMargin y threshold
- Manejo de errores
- Estados de carga
- Fallback a paginación manual

### 9. ErrorState.tsx
Sistema completo de manejo de errores.

**Tipos de errores:**
- 🌐 Network: Problemas de conexión
- 🖥️ Server: Errores del servidor
- 🔍 Search: Sin resultados de búsqueda
- 🔧 Filter: Filtros muy restrictivos
- ⚠️ Permission: Acceso denegado
- 📭 Empty: Sin contenido disponible

**Variantes:**
- `ErrorState`: Componente general
- `NetworkErrorState`: Específico para red
- `EmptyState`: Para estados vacíos

## 📱 Responsive Design

### Mobile
- Filtros en modal deslizante
- Search bar optimizado
- Cards adaptativos
- Touch-friendly controls

### Tablet
- Layout híbrido
- Filtros colapsables
- Grid de 2 columnas

### Desktop
- Sidebar fijo para filtros
- Grid de 3 columnas
- Todas las funcionalidades visibles

## 🎨 Metadatos de IA

### Sentimiento
- 🟢 Positivo: Contenido optimista
- 🔴 Negativo: Contenido pesimista
- ⚪ Neutral: Contenido equilibrado

### Relevancia
- 0-39%: Baja relevancia
- 40-59%: Relevancia media
- 60-79%: Alta relevancia
- 80-100%: Máxima relevancia

### Legibilidad
- Porcentaje de facilidad de lectura
- Basado en longitud de sentences y palabras

### Entidades
- 👤 Personas mencionadas
- 🏢 Organizaciones
- 📍 Ubicaciones

## 🚀 Configuración y Uso

### Instalación de dependencias
```bash
cd frontend/ai-news-frontend
pnpm install
```

### Uso básico
```typescript
import { 
  NewsList, 
  NewsCard, 
  SearchBar, 
  SortControls,
  NewsFilters,
  LoadingSkeleton,
  InfiniteScroll,
  ErrorState
} from '@/components/news';

// En tu componente
<NewsList
  articles={articles}
  isLoading={isLoading}
  error={error}
  pagination={pagination}
  viewMode="grid"
  onViewModeChange={setViewMode}
  searchQuery={searchQuery}
  onSearchChange={setSearchQuery}
  onSearchSubmit={handleSearch}
  filters={filters}
  onFiltersChange={setFilters}
  suggestions={suggestions}
  onSuggestionSelect={handleSuggestion}
  sortOption={sortOption}
  onSortChange={setSortOption}
  availableSources={sources}
  availableCategories={categories}
  availableTags={tags}
  onLoadMore={loadMore}
  onRefresh={refresh}
  enableInfiniteScroll={true}
  enableFilters={true}
  enableSearch={true}
  enableSort={true}
/>
```

### Configuración de filtros
```typescript
const filters: NewsFilters = {
  dateRange: {
    from: new Date('2024-01-01'),
    to: new Date()
  },
  sources: ['El País', 'BBC'],
  sentiment: ['positive', 'neutral'],
  relevanceRange: { min: 60, max: 100 },
  categories: ['Tecnología', 'Ciencia'],
  tags: ['IA', 'Machine Learning'],
  languages: ['español', 'inglés']
};
```

### Estados de carga
```typescript
// Skeleton de carga
<LoadingSkeleton 
  count={6} 
  viewMode="grid" 
  showFilters={true} 
/>

// Error state
<ErrorState
  type="network"
  title="Sin conexión"
  message="Verifica tu internet"
  onRetry={retryFunction}
  variant="card"
/>

// Infinite scroll
<InfiniteScroll
  loadMore={loadMoreFunction}
  isLoading={loading}
  hasNextPage={hasMore}
  error={error}
  onRetry={retryFunction}
/>
```

## 🎯 Performance

### Optimizaciones implementadas:
- Lazy loading de imágenes
- Virtual scrolling para listas largas
- Debounced search
- Memoized components
- Intersection Observer para infinite scroll
- Batch loading de datos
- Caching de filtros

### Mejores prácticas:
- Código modular y reutilizable
- TypeScript para type safety
- Componentes uncontrolled cuando es posible
- Context API para estado global
- Custom hooks para lógica compartida

## 🔧 Personalización

### Temas y estilos
Los componentes usan Tailwind CSS y shadcn/ui para consistencia visual.

### Extensibilidad
Todos los componentes son altamente configurables via props y pueden extenderse según necesidades específicas.

### Testing
Estructura preparada para testing unitario y de integración.

## 📋 Roadmap

### Próximas características:
- [ ] Guardado de filtros y búsquedas
- [ ] Notificaciones push para noticias importantes
- [ ] Compartir noticias
- [ ] Lectura offline
- [ ] Modo oscuro/claro
- [ ] Exportar filtros
- [ ] Analytics de búsqueda

---

Este sistema proporciona una base sólida y escalable para cualquier aplicación de agregación de noticias con capacidades avanzadas de filtrado y búsqueda.