# Sistema de Paginación y Filtrado Avanzado

Este documento describe el sistema universal de paginación y filtrado implementado en el AI News Aggregator.

## 📋 Índice

- [Características Principales](#características-principales)
- [Arquitectura](#arquitectura)
- [Configuración](#configuración)
- [Uso Básico](#uso-básico)
- [Filtros Avanzados](#filtros-avanzados)
- [Ordenamiento Multi-campo](#ordenamiento-multi-campo)
- [Paginación por Cursor](#paginación-por-cursor)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [API Reference](#api-reference)

## 🚀 Características Principales

### ✨ Funcionalidades Implementadas

- **Paginación Universal**: Soporte para paginación tradicional y por cursor
- **Filtros Configurables**: Sistema flexible de filtros por modelo de datos
- **Validación Automática**: Validación de parámetros con mensajes de error claros
- **Ordenamiento Multi-campo**: Soporte para ordenamiento por múltiples campos
- **Búsqueda de Texto**: Búsqueda full-text en múltiples campos
- **Middleware Automático**: Extracción automática de parámetros de query
- **Métricas de Uso**: Recopilación de estadísticas de uso y rendimiento
- **CORS Optimizado**: Headers específicos para APIs paginadas

### 🎯 Modelos Soportados

- **Articles**: Noticias con análisis de IA
- **Sources**: Fuentes de noticias
- **Trending Topics**: Temas populares
- **Analysis Tasks**: Tareas de análisis asíncronas
- **User Preferences**: Preferencias de usuario

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  Middleware      │    │  Pagination     │
│   Endpoints     │◄──►│  Auto-Extract    │◄──►│  Service        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────┐         ┌─────────────────┐
                       │ Query Params │         │ SQLAlchemy      │
                       │ Validation   │         │ Query Builder   │
                       └──────────────┘         └─────────────────┘
```

### Componentes Principales

1. **PaginationParams**: Clase para gestionar parámetros de paginación
2. **ModelFilterConfig**: Configuración de filtros por modelo
3. **QueryBuilder**: Constructor de consultas SQLAlchemy
4. **CursorManager**: Gestión de cursores para paginación eficiente
5. **PaginationMiddleware**: Middleware para extracción automática

## ⚙️ Configuración

### Instalación en main.py

```python
from app.utils.pagination_middleware import setup_pagination_middleware

# Configurar middleware de paginación
setup_pagination_middleware(
    app,
    enable_auto_extraction=True,
    enable_metrics=True,
    enable_cors=False,  # Ya configurado
    allowed_origins=["http://localhost:3000"]
)
```

### Configuración por Modelo

```python
# En pagination.py - ModelFilterConfig
FILTER_CONFIGS = {
    'article': [
        FilterConfig('published_at', datetime, [FilterOperator.DATE_RANGE]),
        FilterConfig('sentiment_label', str, [FilterOperator.EQUALS, FilterOperator.IN]),
        FilterConfig('relevance_score', float, [FilterOperator.GREATER_THAN_EQUAL]),
        FilterConfig('title', str, [FilterOperator.TEXT_SEARCH], search_fields=['title', 'content']),
    ]
}
```

## 📖 Uso Básico

### Endpoint Básico con Paginación

```python
from fastapi import Request, Depends
from app.utils.pagination import get_pagination_params, paginate_response

@router.get("/news")
async def get_news(
    request: Request,
    db: Session = Depends(get_db)
):
    # Obtener parámetros de paginación
    pagination_params = get_pagination_params(request, 'article')
    
    # Construir consulta base
    query = db.query(Article)
    
    # Aplicar filtros y paginación
    result = pagination_service.paginate_query(
        query, Article, pagination_params
    )
    
    return paginate_response(result)
```

### Uso en Endpoint Existente

```python
@router.get("/news/advanced")
async def get_news_advanced(request: Request):
    # Los parámetros se extraen automáticamente via middleware
    if hasattr(request.state, 'pagination_params'):
        pagination_params = request.state.pagination_params
    else:
        pagination_params = get_pagination_params(request, 'article')
    
    # Usar parámetros...
    page = pagination_params.page
    page_size = pagination_params.page_size
    filters = pagination_params.filters
    sort_fields = pagination_params.sort
```

## 🔍 Filtros Avanzados

### Tipos de Filtros Soportados

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `eq` | Igual a | `sentiment=positive` |
| `ne` | No igual | `status__ne=pending` |
| `gt` | Mayor que | `score__gt=0.8` |
| `gte` | Mayor o igual | `score__gte=0.8` |
| `lt` | Menor que | `score__lt=0.5` |
| `lte` | Menor o igual | `score__lte=0.5` |
| `contains` | Contiene | `title__contains=AI` |
| `in` | En lista | `status__in=completed,processing` |
| `between` | Entre valores | `score__between=0.5,0.8` |
| `date_range` | Rango de fechas | `date__date_range=2025-01-01,2025-12-31` |
| `text_search` | Búsqueda de texto | `search=artificial intelligence` |

### Ejemplos de Filtros

```http
# Filtrar por sentimiento
GET /api/v1/news?sentiment=positive

# Filtrar por múltiples criterios
GET /api/v1/news?sentiment=positive&relevance_score__gte=0.8&published_at__date_range=2025-11-01,2025-11-06

# Filtrar por lista de valores
GET /api/v1/news?processing_status__in=completed,processing

# Búsqueda de texto
GET /api/v1/news?search=artificial intelligence&sort=-relevance_score

# Rango de fechas
GET /api/v1/news?published_at__date_range=2025-11-01,2025-11-06&sort=-published_at
```

### Filtros Personalizados

```python
# Definir filtro personalizado
FilterConfig(
    field_name='custom_field',
    field_type=str,
    allowed_operators=[FilterOperator.EQUALS, FilterOperator.CONTAINS],
    validation_func=lambda x: x.lower() if isinstance(x, str) else x,
    search_fields=['custom_field', 'related_field']
)
```

## 🔄 Ordenamiento Multi-campo

### Sintaxis

```http
GET /api/v1/news?sort=field1,field2,-field3
```

- Sin prefijo: orden ascendente
- Con prefijo `-`: orden descendente

### Ejemplos

```http
# Ordenar por fecha descendente
GET /api/v1/news?sort=-published_at

# Ordenamiento multi-campo
GET /api/v1/news?sort=relevance_score,-published_at,sentiment_score

# Solo fuentes activas, ordenadas por credibilidad
GET /api/v1/news/sources?is_active=true&sort=-credibility_score,name
```

### Implementación

```python
# Los campos de ordenamiento se definen automáticamente:
sort_fields = pagination_params.sort
# [
#     SortField(field='relevance_score', order=SortOrder.DESC),
#     SortField(field='published_at', order=SortOrder.DESC)
# ]
```

## 📑 Paginación por Cursor

### Ventajas del Cursor

- **Más eficiente** para datasets grandes
- **No se rompe** con datos en tiempo real
- **Mejor rendimiento** en bases de datos

### Uso

```http
# Primera página
GET /api/v1/news?page_size=20

# Usar cursor para página siguiente
GET /api/v1/news?cursor=eyJwYWdlIjoyLCJwYWdlX3NpemUiOjIwfQ==

# El cursor se devuelve en la respuesta:
{
    "pagination": {
        "next_cursor": "eyJwYWdlIjozLCJwYWdlX3NpemUiOjIwfQ==",
        "prev_cursor": "eyJwYWdlIjoxLCJwYWdlX3NpemUiOjIwfQ=="
    }
}
```

### Implementación

```python
# En el servicio
if pagination_params.cursor:
    query, cursor_data = query_builder.apply_cursor_pagination(
        query, model, pagination_params.cursor, pagination_params.sort
    )

# Construir cursor desde datos
next_cursor = query_builder.build_cursor_data(items, pagination_params.sort)
```

## 💡 Ejemplos de Uso

### 1. Endpoint de Noticias con Filtros Completos

```python
@router.get("/news/filtered")
async def get_filtered_news(
    request: Request,
    db: Session = Depends(get_db)
):
    pagination_params = get_pagination_params(request, 'article')
    
    # Consulta base
    query = db.query(Article)
    
    # Aplicar paginación completa
    result = pagination_service.paginate_query(
        query, Article, pagination_params
    )
    
    return {
        'status': 'success',
        'data': result.items,
        'pagination': {
            'total': result.total,
            'page': result.page,
            'page_size': result.page_size,
            'total_pages': result.total_pages,
            'has_next': result.has_next,
            'has_next_cursor': result.next_cursor
        },
        'filters_applied': result.filters_applied,
        'sort_applied': [{'field': s.field, 'order': s.order.value} for s in result.sort_applied]
    }
```

### 2. Presets de Filtros

```python
@router.get("/news/presets")
async def get_filter_presets():
    return {
        'trending_ai': {
            'name': 'Tendencias en IA',
            'description': 'Artículos recientes sobre IA con alta relevancia',
            'filters': {
                'search': 'artificial intelligence',
                'relevance_score__gte': 0.8,
                'published_at__date_range': '2025-11-01,2025-11-06'
            },
            'sort': '-published_at,-relevance_score'
        },
        'positive_news': {
            'name': 'Noticias Positivas',
            'filters': {
                'sentiment': 'positive',
                'sentiment_score__gte': 0.7
            },
            'sort': '-sentiment_score'
        }
    }
```

### 3. Integración con Service Layer

```python
class NewsService:
    async def get_articles_with_pagination(
        self,
        pagination_params: PaginationParams,
        additional_filters: Dict[str, Any] = None
    ):
        query = self.db.query(Article)
        
        # Convertir filtros de paginación a formato del service
        service_filters = self._convert_pagination_filters(pagination_params)
        
        # Aplicar filtros adicionales si existen
        if additional_filters:
            service_filters.update(additional_filters)
        
        # Usar service layer para obtener datos
        articles = await self._fetch_articles(service_filters)
        
        # Aplicar paginación final si es necesario
        if self._needs_pagination(articles, pagination_params):
            return self._apply_final_pagination(articles, pagination_params)
        
        return articles
```

## 📚 API Reference

### Clases Principales

#### `PaginationParams`

```python
class PaginationParams:
    def __init__(self, request: Request, model_name: str):
        self.page: int
        self.page_size: int
        self.limit: int
        self.offset: int
        self.cursor: Optional[str]
        self.sort: List[SortField]
        self.filters: Dict[str, Dict[str, Any]]
        self.search: str
        self.fields: List[str]
        self.exclude_fields: List[str]
```

#### `FilterConfig`

```python
@dataclass
class FilterConfig:
    field_name: str
    field_type: type
    allowed_operators: List[FilterOperator]
    required: bool = False
    default_value: Any = None
    validation_func: Optional[Callable] = None
    search_fields: Optional[List[str]] = None
```

#### `PaginationResult`

```python
@dataclass
class PaginationResult:
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    sort_applied: List[SortField] = field(default_factory=list)
```

### Endpoints Disponibles

#### `GET /api/v1/news/advanced`

Endpoint completo con paginación y filtrado avanzado.

**Parámetros:**
- `page` (int): Número de página (default: 1)
- `page_size` (int): Tamaño de página (default: 20, max: 100)
- `sort` (string): Campos de ordenamiento separados por coma
- `search` (string): Término de búsqueda
- Filtros específicos del modelo

#### `GET /api/v1/news/filter-presets`

Obtener presets de filtros predefinidos.

#### `GET /api/v1/pagination/metrics`

Obtener métricas globales de uso de paginación.

### Headers Útiles

#### Request Headers

```
X-Model-Name: article                    # Forzar detección de modelo
X-Custom-Filter-Format: json             # Formato personalizado de filtros
```

#### Response Headers

```
X-Max-Page-Size: 100                     # Límite máximo de página
X-Default-Page-Size: 20                  # Tamaño por defecto
X-Available-Filters: field1,field2       # Filtros disponibles
X-Filters-Applied: true                  # Si se aplicaron filtros
```

## 🔧 Configuración Avanzada

### Personalizar Filtros por Modelo

```python
# En pagination.py
ModelFilterConfig.FILTER_CONFIGS['custom_model'] = [
    FilterConfig(
        field_name='custom_field',
        field_type=str,
        allowed_operators=[FilterOperator.EQUALS, FilterOperator.CONTAINS],
        validation_func=custom_validation,
        search_fields=['field1', 'field2']
    )
]
```

### Configurar Middleware

```python
setup_pagination_middleware(
    app,
    enable_auto_extraction=True,
    log_extractions=True,
    default_models={
        '/api/v1/custom': 'custom_model'
    }
)
```

### Métricas Personalizadas

```python
# Agregar métricas personalizadas
class CustomPaginationMetricsMiddleware(BaseHTTPMiddleware):
    def _collect_usage_metrics(self, pagination_params, model_name):
        # Implementar métricas específicas
        pass
```

## 📊 Monitoreo y Debugging

### Logs de Paginación

```python
import logging
logger = logging.getLogger('pagination')

# Los logs se generan automáticamente:
# "Query params extracted: {
#   'endpoint': '/api/v1/news',
#   'model': 'article',
#   'page': 1,
#   'filters_count': 2,
#   'sort_fields': ['published_at']
# }"
```

### Métricas de Rendimiento

```python
# Endpoint para métricas
GET /api/v1/pagination/metrics

# Respuesta ejemplo:
{
    "global_metrics": {
        "pagination_usage_rate": 0.78,
        "average_response_time_ms": 145,
        "cache_efficiency": 0.82,
        "most_used_filters": {
            "sentiment_label": 0.65,
            "relevance_score": 0.58
        }
    }
}
```

## 🚀 Mejores Prácticas

### 1. Usar Presets para Filtros Comunes

```python
# En lugar de parámetros largos, usar presets
GET /api/v1/news?preset=trending_ai

# Definir en el frontend:
const PRESETS = {
    trending_ai: {
        search: 'artificial intelligence',
        relevance_score__gte: 0.8,
        sort: '-published_at,-relevance_score'
    }
}
```

### 2. Limitar Tamaños de Página

```python
# Establecer límites razonables
pagination_params = PaginationParams(
    request=request,
    model_name='article',
    default_page_size=20,
    max_page_size=50  # No permitir páginas enormes
)
```

### 3. Indexar Campos de Filtro

```python
# Asegurar que los campos filtrados tengan índices
Index('idx_articles_sentiment_score', Article.sentiment_score)
Index('idx_articles_published_at', Article.published_at)
Index('idx_articles_relevance_score', Article.relevance_score)
```

### 4. Usar Caché para Consultas Frecuentes

```python
@router.get("/news/popular")
async def get_popular_news(request: Request, db: Session = Depends(get_db)):
    cache_key = f"popular_news:{hash(str(request.query_params))}"
    
    # Intentar obtener del caché
    cached_result = await cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Calcular resultado
    result = await calculate_popular_news(request, db)
    
    # Guardar en caché
    await cache.set(cache_key, result, ttl=300)  # 5 minutos
    
    return result
```

## 🎯 Conclusión

El sistema de paginación y filtrado avanzado proporciona:

- ✅ **Flexibilidad**: Soporte para múltiples modelos y casos de uso
- ✅ **Performance**: Paginación por cursor y optimización de queries
- ✅ **Escalabilidad**: Middleware automático y configuración modular
- ✅ **Usabilidad**: API intuitiva con validación automática
- ✅ **Monitoreo**: Métricas integradas y logs detallados
- ✅ **Compatibilidad**: Soporte para endpoints legacy

Este sistema puede extenderse fácilmente a nuevos modelos y casos de uso, proporcionando una base sólida para el manejo de datos paginados en toda la aplicación.