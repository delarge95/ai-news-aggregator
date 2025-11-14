# Schemas Pydantic - AI News Aggregator

Este directorio contiene los schemas Pydantic completos para el sistema de validación y serialización del AI News Aggregator.

## Estructura de Archivos

### 📄 `article.py` - Schemas de Artículos

**Clases principales:**
- `ArticleBase` - Schema base con validaciones para título, URL, contenido
- `ArticleCreate` - Schema para creación con validaciones de sentiment y bias
- `ArticleUpdate` - Schema para actualización parcial
- `ArticleResponse` - Schema de respuesta con metadatos completos
- `ArticleAnalysisResponse` - Schema para resultados de análisis IA

**Validaciones incluidas:**
- ✅ Validación de URLs con regex robusto
- ✅ Validación de fechas (no futuras)
- ✅ Scores de sentiment (-1.0 a 1.0)
- ✅ Scores de bias (0.0 a 1.0)
- ✅ Topic tags sin duplicados
- ✅ Consistencia entre sentiment_score y sentiment_label

**Utilidades incluidas:**
- `validate_article_content()` - Validación de contenido
- `calculate_reading_time()` - Tiempo estimado de lectura
- `extract_keywords()` - Extracción de keywords

### 📄 `user.py` - Schemas de Usuarios

**Clases principales:**
- `UserBase` - Schema base con validaciones de email y username
- `UserCreate` - Schema para registro con validación de contraseñas
- `UserLogin` - Schema para autenticación
- `UserResponse` - Schema de respuesta con estadísticas
- `UserPreferenceUpdate` - Schema para actualización de preferencias

**Validaciones incluidas:**
- ✅ Formato de email con regex
- ✅ Username alfanumérico con guiones/guiones bajos
- ✅ Fortaleza de contraseña (mínimo 8 chars, mayúscula, minúscula, número, símbolo)
- ✅ Confirmación de contraseña
- ✅ Preferencias de usuario consistentes
- ✅ Topics sin conflictos entre preferidos/ignorados

**Utilidades incluidas:**
- `validate_password_strength()` - Validación detallada con feedback
- `generate_username_suggestions()` - Sugerencias de username
- `validate_email_format()` - Validación simple de email

### 📄 `analytics.py` - Schemas de Analytics

**Clases principales:**
- `AnalyticsParams` - Parámetros de consulta con validaciones de fecha
- `AnalyticsResponse` - Respuesta completa de analytics
- `SentimentAnalytics` - Métricas de sentiment analysis
- `TrendAnalytics` - Métricas de tendencias
- `SourceAnalytics` - Métricas de fuentes de noticias
- `EngagementAnalytics` - Métricas de engagement
- `ContentQualityAnalytics` - Métricas de calidad de contenido
- `AIProcessingAnalytics` - Métricas de procesamiento IA

**Validaciones incluidas:**
- ✅ Rangos de fecha consistentes
- ✅ Granularidad apropiada para rangos de tiempo
- ✅ Distribución de sentiment (suma 100%)
- ✅ Scores entre 0.0 y 1.0
- ✅ Consistencia en conteos

**Utilidades incluidas:**
- `calculate_growth_rate()` - Cálculo de tasa de crecimiento
- `calculate_percentage_change()` - Cambio porcentual detallado
- `detect_anomalies()` - Detección de anomalías con z-score
- `calculate_moving_average()` - Media móvil para series temporales

### 📄 `search.py` - Schemas de Búsqueda

**Clases principales:**
- `SearchParams` - Parámetros básicos de búsqueda
- `AdvancedSearchParams` - Búsqueda avanzada con filtros IA
- `SearchResponse` - Respuesta completa con facets
- `SearchResult` - Resultado individual con highlighting
- `SavedSearch` - Búsquedas guardadas
- `SearchAnalytics` - Analytics de búsqueda

**Validaciones incluidas:**
- ✅ Query entre 1-500 caracteres
- ✅ Rangos de scores (sentiment, bias, relevance)
- ✅ Topics sin duplicados
- ✅ Fuentes con límites
- ✅ Consistencia en filtros de fecha/longitud
- ✅ Al menos un campo de búsqueda habilitado

**Utilidades incluidas:**
- `parse_search_query()` - Parsing de queries con operadores
- `calculate_search_score()` - Scoring de relevancia
- `extract_search_keywords()` - Extracción de keywords
- `build_search_index()` - Construcción de índice de búsqueda

### 📄 `pagination.py` - Schemas de Paginación

**Clases principales:**
- `PaginationParams` - Parámetros de paginación
- `CursorPaginationParams` - Paginación basada en cursor
- `Meta` - Metadatos de paginación completos
- `Links` - Enlaces de navegación
- `PaginatedResponse` - Respuesta genérica paginada
- `BulkResponse` - Respuesta para operaciones en lote
- `StreamResponse` - Respuesta para streaming
- `ExportResponse` - Respuesta para exportaciones

**Validaciones incluidas:**
- ✅ Página entre 1-10,000
- ✅ per_page entre 1-100 (configurable)
- ✅ Índices válidos (1-based)
- ✅ Consistencia en conteos
- ✅ Progress 0.0-100.0%

**Utilidades incluidas:**
- `calculate_page_bounds()` - Cálculo de límites de página
- `generate_cursor()` - Generación de tokens cursor
- `get_pagination_info()` - Información completa de paginación
- `optimize_per_page()` - Optimización de per_page
- `create_pagination_links()` - Creación de enlaces de navegación

## Características Principales

### ✅ Validaciones Personalizadas
- **Fechas:** No futuras, rangos consistentes
- **URLs:** Regex robusto para validación
- **Scores:** Rangos numéricos específicos por tipo
- **Textos:** Longitudes, formatos, contenido
- **IDs:** UUIDs, consistencia referencial

### ✅ Serialización Optimizada
- **Fechas:** ISO format consistente
- **Números:** Decimales con precisión controlada
- **Arrays:** Eliminación de duplicados preservando orden
- **JSON:** Serialización limpia para APIs

### ✅ Compatibilidad de Fechas
- **ISO 8601:** `2023-12-01T10:30:00Z`
- **UTC:** Todas las fechas almacenadas en UTC
- **Timezone:** Soporte completo para timezone
- **Validación:** No fechas futuras, rangos lógicos

### ✅ Tipado Estricto
- **Python 3.11+:** Support para typing mejorado
- **Generic Types:** `PaginatedResponse[T]`
- **Union Types:** `Optional[str | UUID`
- **Literal Types:** Valores fijos específicos

### ✅ Funciones de Utilidad
- **Cálculos:** Growth rates, moving averages
- **Validación:** Password strength, content analysis
- **Procesamiento:** Keyword extraction, search indexing
- **Paginación:** Optimización, cursor management

## Ejemplos de Uso

### Crear un Artículo
```python
from app.schemas.article import ArticleCreate

article_data = ArticleCreate(
    title="Breaking: AI Advances in Healthcare",
    content="Artificial intelligence is revolutionizing medical diagnosis...",
    url="https://example.com/ai-healthcare",
    source_id="uuid-here",
    published_at=datetime.now(timezone.utc),
    sentiment_score=0.7,
    sentiment_label="positive"
)
```

### Búsqueda Avanzada
```python
from app.schemas.search import AdvancedSearchParams

search_params = AdvancedSearchParams(
    query="artificial intelligence healthcare",
    page=1,
    per_page=20,
    sentiment="positive",
    min_relevance_score=0.8,
    topics=["healthcare", "AI"],
    search_in_content=True,
    fuzzy_search=True
)
```

### Respuesta Paginada
```python
from app.schemas.pagination import PaginatedResponse, ArticleResponse

response = PaginatedResponse.create(
    data=articles,
    total=150,
    page=1,
    per_page=20
)
```

### Analytics Completo
```python
from app.schemas.analytics import AnalyticsResponse, SentimentAnalytics

analytics = AnalyticsResponse(
    query_params=AnalyticsParams(date_from=start_date, date_to=end_date),
    generated_at=datetime.now(timezone.utc),
    sentiment_analytics=SentimentAnalytics(
        total_articles=1000,
        positive_count=600,
        negative_count=200,
        neutral_count=200,
        average_sentiment_score=0.2
    )
)
```

## Configuración

Los schemas están diseñados para ser utilizados con:
- **FastAPI** - Pydantic integration nativa
- **SQLAlchemy** - ORM integration
- **AsyncPG** - PostgreSQL async driver
- **Redis** - Cache layer support

## Testing

Todos los schemas incluyen:
- **Validaciones:** Test cases para cada validator
- **Edge cases:** Casos límite y errores
- **Performance:** Optimización para grandes datasets
- **Compatibility:** Multiple date formats support

## Extensibilidad

El sistema está diseñado para:
- **Nuevos schemas:** Fácil adición de nuevos tipos
- **Validaciones custom:** Validators adicionales
- **Serialization:** Custom serializers
- **Performance:** Optimizaciones específicas

---

**Nota:** Todos los schemas implementan best practices de Pydantic v2 con validación en tiempo real, serialización optimizada y soporte completo para APIs RESTful.