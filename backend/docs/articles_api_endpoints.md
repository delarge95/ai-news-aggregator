# Documentación de Endpoints de Artículos

## Resumen

Se han implementado endpoints REST completos para la gestión de artículos en el sistema AI News Aggregator. Estos endpoints proporcionan operaciones CRUD completas, filtros avanzados, búsqueda por texto y funcionalidades especiales.

## Endpoints Implementados

### 1. GET `/api/v1/articles`
**Descripción**: Obtener lista paginada de artículos con filtros avanzados y ordenamiento múltiple

**Parámetros de Consulta**:
- `page` (int, default: 1): Número de página
- `per_page` (int, default: 20, max: 100): Artículos por página
- `search` (str, optional): Término de búsqueda en título y contenido
- `source_ids` (str, optional): IDs de fuentes (separados por coma)
- `source_names` (str, optional): Nombres de fuentes (separados por coma)
- `categories` (str, optional): Categorías (separadas por coma)
- `sentiment_labels` (str, optional): Etiquetas de sentimiento ('positive', 'negative', 'neutral')
- `sentiment_score_min` (float, optional): Puntuación mínima de sentimiento (-1.0 a 1.0)
- `sentiment_score_max` (float, optional): Puntuación máxima de sentimiento (-1.0 a 1.0)
- `date_from` (date, optional): Fecha desde
- `date_to` (date, optional): Fecha hasta
- `relevance_score_min` (float, optional): Puntuación mínima de relevancia (0.0 a 1.0)
- `processing_statuses` (str, optional): Estados de procesamiento ('pending', 'processing', 'completed', 'failed', 'skipped')
- `topic_tags` (str, optional): Etiquetas de temas (separadas por coma)
- `sort_by` (str, default: 'published_at'): Campo de ordenamiento
- `sort_order` (str, default: 'desc'): Dirección del ordenamiento ('asc' o 'desc')

**Respuesta**:
```json
{
  "articles": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8,
  "has_next": true,
  "has_prev": false,
  "filters_applied": {
    "search": "machine learning",
    "source_ids": ["uuid1", "uuid2"],
    "sentiment_labels": ["positive", "neutral"],
    "sentiment_score_range": [0.2, 1.0],
    "date_range": ["2025-11-01", "2025-11-06"],
    "relevance_score_min": 0.7,
    "processing_statuses": ["completed"],
    "topic_tags": ["ai", "technology"]
  },
  "sort_info": {
    "sort_by": "published_at",
    "sort_order": "desc"
  }
}
```

### 2. GET `/api/v1/articles/{article_id}`
**Descripción**: Obtener detalle de un artículo específico

**Parámetros**:
- `article_id` (UUID): ID único del artículo

**Respuesta**:
```json
{
  "id": "uuid-article",
  "title": "Título del artículo",
  "content": "Contenido completo...",
  "summary": "Resumen del artículo",
  "url": "https://example.com/article",
  "published_at": "2025-11-06T10:00:00Z",
  "source_id": "uuid-source",
  "created_at": "2025-11-06T09:00:00Z",
  "updated_at": "2025-11-06T09:00:00Z",
  "processed_at": "2025-11-06T09:05:00Z",
  "ai_processed_at": "2025-11-06T09:10:00Z",
  "processing_status": "completed",
  "duplicate_group_id": null,
  "content_hash": "sha256hash...",
  "sentiment_score": 0.8,
  "sentiment_label": "positive",
  "bias_score": 0.3,
  "relevance_score": 0.9,
  "topic_tags": ["ai", "technology", "machine-learning"],
  "source_name": "Tech News",
  "source_url": "https://technews.com",
  "view_count": 0
}
```

### 3. POST `/api/v1/articles`
**Descripción**: Crear un nuevo artículo

**Cuerpo de la Petición**:
```json
{
  "title": "Título del artículo",
  "content": "Contenido completo del artículo",
  "summary": "Resumen del artículo",
  "url": "https://example.com/article",
  "published_at": "2025-11-06T10:00:00Z",
  "source_id": "uuid-source",
  "sentiment_score": 0.8,
  "sentiment_label": "positive",
  "bias_score": 0.3,
  "relevance_score": 0.9,
  "topic_tags": ["ai", "technology"]
}
```

**Validaciones**:
- El `title` es obligatorio (1-500 caracteres)
- La `url` es obligatoria y debe ser única
- El `source_id` debe existir
- El `sentiment_score` debe estar entre -1.0 y 1.0
- El `bias_score` debe estar entre 0.0 y 1.0
- El `relevance_score` debe estar entre 0.0 y 1.0

### 4. PUT `/api/v1/articles/{article_id}`
**Descripción**: Actualizar un artículo existente

**Parámetros**:
- `article_id` (UUID): ID único del artículo

**Cuerpo de la Petición** (campos opcionales):
```json
{
  "title": "Nuevo título",
  "summary": "Nuevo resumen",
  "sentiment_score": 0.9,
  "topic_tags": ["ai", "technology", "research"]
}
```

### 5. DELETE `/api/v1/articles/{article_id}`
**Descripción**: Eliminar un artículo

**Parámetros**:
- `article_id` (UUID): ID único del artículo

**Respuesta**: 204 No Content si se elimina correctamente

### 6. GET `/api/v1/articles/featured`
**Descripción**: Obtener artículos destacados (alta relevancia y sentimiento positivo)

**Parámetros de Consulta**:
- `page` (int, default: 1): Número de página
- `per_page` (int, default: 10, max: 50): Artículos por página

**Criterios de Selección**:
- `relevance_score >= 0.7`
- `sentiment_label = 'positive'`
- Ordenado por `relevance_score` descendente, luego por `sentiment_score` descendente

### 7. GET `/api/v1/articles/popular`
**Descripción**: Obtener artículos populares basados en período de tiempo

**Parámetros de Consulta**:
- `page` (int, default: 1): Número de página
- `per_page` (int, default: 10, max: 50): Artículos por página
- `time_period` (str, default: '7d'): Período de tiempo ('1d', '7d', '30d')

**Criterios de Selección**:
- Artículos publicados dentro del período especificado
- `relevance_score >= 0.5`
- Ordenado por `published_at` descendente, luego por `relevance_score` descendente

### 8. GET `/api/v1/articles/stats/summary`
**Descripción**: Obtener estadísticas resumen de artículos

**Respuesta**:
```json
{
  "total_articles": 1250,
  "processing_status_distribution": {
    "pending": 50,
    "processing": 25,
    "completed": 1100,
    "failed": 25,
    "skipped": 50
  },
  "sentiment_distribution": {
    "positive": 650,
    "negative": 200,
    "neutral": 400
  },
  "average_relevance_score": 0.742,
  "ai_processed_articles": 1100,
  "unique_articles": 1150,
  "duplicate_articles": 100,
  "duplicate_rate": 8.0
}
```

### 9. GET `/api/v1/sources`
**Descripción**: Obtener lista de fuentes de noticias

**Parámetros de Consulta**:
- `active_only` (bool, default: true): Solo fuentes activas

**Respuesta**:
```json
[
  {
    "id": "uuid-source",
    "name": "Tech News",
    "url": "https://technews.com",
    "country": "US",
    "language": "en",
    "credibility_score": 0.9
  },
  ...
]
```

## Características Implementadas

### ✅ Validación Pydantic
- Esquemas completos con validación de tipos
- Validación de rangos para scores numéricos
- Validación de formatos (URL, UUID, fechas)
- Mensajes de error descriptivos

### ✅ Filtros Avanzados
- **Por categoría**: Filtrado por topic_tags
- **Por fecha**: Rango de fechas de publicación
- **Por fuente**: Por ID o nombre de fuente
- **Por sentimiento**: Por etiqueta o rango de puntuación
- **Por relevancia**: Puntuación mínima
- **Por estado de procesamiento**: Estados de IA
- **Búsqueda por texto**: En título, contenido y resumen
- **Duplicados**: Filtrado por presencia de duplicados

### ✅ Ordenamiento Múltiple
- Campos soportados: `published_at`, `created_at`, `updated_at`, `relevance_score`, `sentiment_score`, `bias_score`, `view_count`, `title`
- Direcciones: `asc` y `desc`
- Combinación de filtros y ordenamiento

### ✅ Paginación
- Paginación estándar con `page` y `per_page`
- Información de navegación (`has_next`, `has_prev`)
- Cálculo de páginas totales
- Límites configurables (max 100 artículos por página)

### ✅ Artículos Destacados y Populares
- **Featured**: Algoritmo basado en relevancia alta (≥0.7) y sentimiento positivo
- **Popular**: Algoritmo basado en recencia y relevancia (≥0.5)
- Períodos configurables para populares (1d, 7d, 30d)

### ✅ Funcionalidades Adicionales
- Detección de duplicados por URL y hash de contenido
- Estadísticas completas del sistema
- Gestión de fuentes
- Manejo de errores robusto
- Información de filtros aplicados en respuestas

## Uso de Ejemplo

### Filtrar artículos por sentimiento y relevancia
```
GET /api/v1/articles?sentiment_labels=positive,neutral&relevance_score_min=0.7&sort_by=relevance_score&sort_order=desc
```

### Buscar artículos con texto específico
```
GET /api/v1/articles?search=machine%20learning&categories=ai,technology&date_from=2025-11-01
```

### Obtener artículos populares de la última semana
```
GET /api/v1/articles/popular?time_period=7d&per_page=20
```

### Obtener artículos destacados
```
GET /api/v1/articles/featured?per_page=10
```

## Consideraciones Técnicas

### Performance
- Índices optimizados en base de datos para campos de filtrado comunes
- Consultas SQLAlchemy optimizadas con `selectinload` para relaciones
- Cache Redis configurado para endpoints frecuentes

### Seguridad
- Validación de entrada robusta
- Manejo seguro de errores sin exposición de datos sensibles
- Rate limiting configurable

### Escalabilidad
- Paginación para manejar grandes volúmenes de datos
- Filtros que reducen el conjunto de resultados
- Consultas eficientes con índices apropiados

### Mantenibilidad
- Código modular y bien documentado
- Separación clara entre modelos, esquemas y endpoints
- Manejo consistente de errores