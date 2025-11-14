# Sistema de Búsqueda Avanzada - AI News Aggregator

## Descripción General

El sistema de búsqueda avanzada proporciona capacidades completas de búsqueda de noticias con IA, incluyendo:

- **Búsqueda Full-Text**: Búsqueda avanzada en títulos, contenido y resúmenes
- **Filtros Avanzados**: Por fecha, fuente, categoría, sentimiento, relevancia y sesgo
- **Autocompletado Inteligente**: Sugerencias de búsqueda basadas en temas y fuentes
- **Búsquedas Trending**: Identificación de temas populares en tiempo real
- **Búsqueda Semántica**: Búsqueda basada en significado usando IA
- **Facets Dinámicos**: Filtros basados en los resultados de búsqueda

## Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │───▶│  API Endpoints   │───▶│ Search Service  │
│  (React/Vue)    │    │  (FastAPI)       │    │ (Business Logic)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐            │
│  Search Utils   │◀───│ Text Processing  │◀───────────┘
│ (Preprocessing) │    │ & NLP Helpers    │
└─────────────────┘    └──────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐            │
│   Database      │◀───│   SQLAlchemy     │◀───────────┘
│  (PostgreSQL)   │    │   ORM Models     │
└─────────────────┘    └──────────────────┘
```

## Endpoints de API

### 1. Búsqueda Avanzada

**GET /search**

Endpoint principal para búsqueda avanzada con filtros múltiples.

#### Parámetros:

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `q` | string | Término principal de búsqueda | `q=artificial intelligence` |
| `date_from` | string | Fecha desde (YYYY-MM-DD) | `date_from=2024-01-01` |
| `date_to` | string | Fecha hasta (YYYY-MM-DD) | `date_to=2024-12-31` |
| `sources` | array | Lista de fuentes | `sources=BBC News,CNN` |
| `categories` | array | Lista de categorías | `categories=technology,politics` |
| `sentiment` | array | Sentimientos | `sentiment=positive,negative` |
| `min_relevance` | float | Relevancia mínima (0.0-1.0) | `min_relevance=0.8` |
| `sort` | string | Ordenamiento | `sort=relevance,date,sentiment` |
| `limit` | int | Límite de resultados (1-100) | `limit=20` |
| `offset` | int | Offset para paginación | `offset=0` |
| `semantic_search` | boolean | Usar búsqueda semántica | `semantic_search=true` |

#### Ejemplos de Uso:

```bash
# Búsqueda básica
curl "http://localhost:8000/search?q=artificial%20intelligence&limit=10"

# Búsqueda con filtros avanzados
curl "http://localhost:8000/search?q=AI&sentiment=positive&min_relevance=0.8&sources=BBC%20News&sort=date&limit=20"

# Búsqueda por rango de fechas
curl "http://localhost:8000/search?q=machine%20learning&date_from=2024-01-01&date_to=2024-12-31&limit=50"

# Búsqueda semántica
curl "http://localhost:8000/search?q=breakthrough%20in%20AI&semantic_search=true&limit=15"
```

#### Respuesta:

```json
{
  "status": "success",
  "message": "Búsqueda completada: 25 resultados encontrados",
  "query": "artificial intelligence",
  "total": 25,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "OpenAI Announces GPT-5 with Revolutionary Capabilities",
      "content": "OpenAI has unveiled GPT-5, its most advanced language model...",
      "summary": "OpenAI reveals GPT-5 with advanced multimodal AI capabilities.",
      "url": "https://techcrunch.com/openai-gpt5",
      "source": "TechCrunch",
      "source_id": "550e8400-e29b-41d4-a716-446655440001",
      "published_at": "2024-11-06T01:00:00Z",
      "sentiment_score": 0.85,
      "sentiment_label": "positive",
      "bias_score": 0.25,
      "topic_tags": ["artificial-intelligence", "openai", "gpt"],
      "relevance_score": 0.95,
      "ai_processed_at": "2024-11-06T01:05:00Z",
      "processing_status": "completed"
    }
  ],
  "filters_applied": {
    "sentiment": ["positive"],
    "min_relevance": 0.8
  },
  "search_time_ms": 45.2,
  "facets": {
    "sources": [{"name": "TechCrunch", "count": 15}],
    "categories": [{"name": "technology", "count": 20}]
  }
}
```

### 2. Sugerencias de Búsqueda

**GET /search/suggestions**

Obtener sugerencias inteligentes para autocompletado.

#### Parámetros:

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `q` | string | Término parcial (requerido) | `q=artificial` |
| `limit` | int | Número de sugerencias (1-20) | `limit=10` |
| `include_topics` | boolean | Incluir temas trending | `include_topics=true` |
| `include_sources` | boolean | Incluir nombres de fuentes | `include_sources=true` |

#### Ejemplo:

```bash
curl "http://localhost:8000/search/suggestions?q=artificial&limit=5&include_topics=true"
```

#### Respuesta:

```json
{
  "status": "success",
  "message": "Encontradas 8 sugerencias",
  "query": "artificial",
  "suggestions": [
    {
      "text": "artificial intelligence",
      "type": "term",
      "score": 0.95
    },
    {
      "text": "artificial neural networks",
      "type": "term",
      "score": 0.88
    },
    {
      "text": "TechCrunch",
      "type": "source",
      "score": 0.85
    },
    {
      "text": "machine learning",
      "type": "topic",
      "score": 0.82
    }
  ]
}
```

### 3. Búsquedas Trending

**GET /search/trending**

Obtener búsquedas populares y trending topics.

#### Parámetros:

| Parámetro | Tipo | Descripción | Opciones |
|-----------|------|-------------|----------|
| `timeframe` | string | Período de tiempo | `1h`, `6h`, `24h`, `7d` |
| `limit` | int | Límite de resultados (1-50) | `limit=20` |
| `min_count` | int | Mínimo de búsquedas | `min_count=2` |

#### Ejemplo:

```bash
curl "http://localhost:8000/search/trending?timeframe=24h&limit=10&min_count=3"
```

#### Respuesta:

```json
{
  "status": "success",
  "message": "Encontradas 10 búsquedas trending",
  "searches": [
    {
      "query": "GPT-5",
      "count": 156,
      "trend_score": 0.95,
      "timeframe": "24h"
    },
    {
      "query": "artificial intelligence",
      "count": 134,
      "trend_score": 0.88,
      "timeframe": "24h"
    },
    {
      "query": "quantum computing",
      "count": 87,
      "trend_score": 0.78,
      "timeframe": "24h"
    }
  ]
}
```

### 4. Filtros Disponibles

**GET /search/filters**

Obtener todos los filtros disponibles para la interfaz de usuario.

#### Ejemplo:

```bash
curl "http://localhost:8000/search/filters"
```

#### Respuesta:

```json
{
  "status": "success",
  "message": "Filtros obtenidos correctamente",
  "filters": {
    "sources": [
      "BBC News",
      "CNN",
      "TechCrunch",
      "MIT Technology Review",
      "Wired"
    ],
    "categories": [
      "artificial-intelligence",
      "machine-learning",
      "technology",
      "politics",
      "business"
    ],
    "sentiment": [
      "positive",
      "negative",
      "neutral"
    ],
    "date_range": {
      "min": "2024-01-01T00:00:00Z",
      "max": "2024-12-31T23:59:59Z"
    },
    "score_ranges": {
      "relevance": {"min": 0.0, "max": 1.0},
      "sentiment": {"min": -1.0, "max": 1.0},
      "bias": {"min": 0.0, "max": 1.0}
    }
  }
}
```

### 5. Búsqueda Semántica

**GET /search/semantic**

Búsqueda semántica avanzada usando IA.

#### Parámetros:

| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `query` | string | Consulta semántica | `query=AI breakthrough in healthcare` |
| `context` | string | Contexto adicional | `context=medical diagnosis applications` |
| `limit` | int | Límite de resultados (1-100) | `limit=20` |
| `similarity_threshold` | float | Umbral de similitud (0.0-1.0) | `similarity_threshold=0.3` |

#### Ejemplo:

```bash
curl "http://localhost:8000/search/semantic?query=AI%20breakthrough%20in%20healthcare&context=medical%20diagnosis&limit=10"
```

#### Respuesta:

```json
{
  "status": "success",
  "message": "Búsqueda semántica completada: 12 resultados",
  "query": "AI breakthrough in healthcare",
  "context": "medical diagnosis applications",
  "total": 12,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "AI System Achieves 95% Accuracy in Medical Diagnosis",
      "similarity_score": 0.89,
      "combined_score": 0.87,
      "relevance_score": 0.85,
      "semantic_score": 0.89,
      // ... otros campos del artículo
    }
  ],
  "search_time_ms": 78.5,
  "avg_similarity": 0.76
}
```

### 6. Estadísticas de Búsqueda

**GET /search/stats**

Obtener estadísticas del sistema de búsqueda.

#### Ejemplo:

```bash
curl "http://localhost:8000/search/stats"
```

### 7. Health Check

**GET /search/health**

Health check del servicio de búsqueda.

#### Ejemplo:

```bash
curl "http://localhost:8000/search/health"
```

## Instalación y Configuración

### 1. Dependencias

Asegúrate de tener las siguientes dependencias instaladas:

```bash
# Dependencias principales
pip install fastapi uvicorn sqlalchemy asyncpg redis
pip install scikit-learn numpy pandas
pip install jieba spacy  # Para procesamiento de texto
```

### 2. Inicialización de Datos

Puebla la base de datos con datos de ejemplo:

```bash
cd backend
python scripts/init_search_data.py
```

Para limpiar datos existentes:

```bash
python scripts/init_search_data.py --clear
```

### 3. Ejecución

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Servicios de Backend

### SearchService

Servicio principal que maneja toda la lógica de búsqueda:

```python
from app.services.search_service import search_service

# Búsqueda avanzada
results = await search_service.advanced_search(
    query="artificial intelligence",
    filters={"sentiment": ["positive"]},
    sort="relevance",
    limit=20,
    semantic_search=True,
    db=db_session
)
```

### TextProcessor

Utilidades de procesamiento de texto:

```python
from app.utils.search_utils import text_processor

# Preprocesar texto
processed = text_processor.preprocess_text("OpenAI's ChatGPT is amazing!")

# Extraer keywords
keywords = text_processor.extract_keywords(
    "Artificial intelligence and machine learning", 
    max_keywords=5
)

# Calcular similitud
similarity = text_processor.calculate_text_similarity(
    "AI breakthrough", 
    "artificial intelligence advancement",
    method="cosine"
)
```

### SemanticSearchHelper

Helper para búsqueda semántica:

```python
from app.utils.search_utils import semantic_helper

# Expandir consulta con sinónimos
expanded_queries = await semantic_helper.expand_query("AI")
```

## Modelos de Datos

### Article (Artículo)

Modelo principal de artículos con campos de búsqueda:

```python
{
    "id": "uuid",
    "title": "string",
    "content": "text", 
    "summary": "text",
    "url": "string",
    "published_at": "datetime",
    "sentiment_score": "float (-1.0 to 1.0)",
    "sentiment_label": "string",
    "bias_score": "float (0.0 to 1.0)",
    "topic_tags": "array of strings",
    "relevance_score": "float (0.0 to 1.0)",
    "processing_status": "string"
}
```

### TrendingTopic (Tema Trending)

Para búsquedas populares:

```python
{
    "id": "uuid",
    "topic": "string",
    "topic_category": "string", 
    "trend_score": "float (0.0 to 1.0)",
    "article_count": "integer",
    "sources_count": "integer",
    "time_period": "string (1h, 6h, 24h, 7d)",
    "date_recorded": "datetime"
}
```

## Testing

Ejecutar tests del sistema de búsqueda:

```bash
cd backend
pytest tests/services/test_search_service.py -v
```

## Configuración

### Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://user:password@localhost/ai_news_db

# Redis para cache (opcional)
REDIS_URL=redis://localhost:6379/0

# Configuración de búsqueda
SEARCH_MAX_RESULTS=100
SEARCH_CACHE_TTL=300
SEMANTIC_SEARCH_ENABLED=true
```

### Configuración de Índices

Para optimizar performance, configura índices en PostgreSQL:

```sql
-- Índices para búsqueda full-text
CREATE INDEX CONCURRENTLY idx_articles_title_fts ON articles 
USING gin(to_tsvector('english', title));

CREATE INDEX CONCURRENTLY idx_articles_content_fts ON articles 
USING gin(to_tsvector('english', content));

-- Índices para filtros comunes
CREATE INDEX CONCURRENTLY idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX CONCURRENTLY idx_articles_sentiment_label ON articles(sentiment_label);
CREATE INDEX CONCURRENTLY idx_articles_relevance_score ON articles(relevance_score DESC);

-- Índices para trending topics
CREATE INDEX CONCURRENTLY idx_trending_topic_score ON trending_topics(trend_score DESC);
CREATE INDEX CONCURRENTLY idx_trending_topic_period ON trending_topics(time_period, date_recorded);
```

## Casos de Uso

### 1. Búsqueda de Noticias por Tema

```javascript
// Frontend - React example
const searchNews = async (query, filters = {}) => {
  const params = new URLSearchParams({
    q: query,
    limit: 20,
    sort: 'relevance',
    ...filters
  });
  
  const response = await fetch(`/search?${params}`);
  const data = await response.json();
  return data;
};

// Uso
const results = await searchNews('artificial intelligence', {
  sentiment: ['positive'],
  min_relevance: 0.8,
  sources: ['TechCrunch', 'MIT Technology Review']
});
```

### 2. Autocompletado en Tiempo Real

```javascript
// Frontend - Sugerencias de búsqueda
const getSuggestions = async (query) => {
  const response = await fetch(`/search/suggestions?q=${encodeURIComponent(query)}`);
  const data = await response.json();
  return data.suggestions;
};

// Uso con debounce
const suggestions = await getSuggestions('artificial');
```

### 3. Dashboard de Búsquedas Trending

```javascript
// Frontend - Mostrar temas trending
const getTrending = async (timeframe = '24h') => {
  const response = await fetch(`/search/trending?timeframe=${timeframe}`);
  const data = await response.json();
  return data.searches;
};

// Mostrar en interfaz
const trendingTopics = await getTrending('7d');
```

## Optimización y Performance

### 1. Caching

El sistema usa Redis para cachear resultados frecuentes:

```python
# Configuración de cache en SearchService
import redis

redis_client = redis.from_url(settings.REDIS_URL)

# Cachear resultados por 5 minutos
CACHE_TTL = 300
cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
```

### 2. Índices de Base de Datos

- Índices GIN para full-text search
- Índices compuestos para filtros frecuentes
- Índices parciales para datos recientes

### 3. Paginación

- Offset/limit para grandes datasets
- Cursor-based pagination para mejor performance
- Límites configurables (default: 20, max: 100)

## Monitoreo y Métricas

### Métricas Disponibles

- Tiempo de búsqueda promedio
- Número de resultados por query
- Uso de filtros más frecuentes
- Búsquedas sin resultados
- Health status de servicios

### Logging

El sistema registra eventos importantes:

```python
import logging

logger.info(f"Búsqueda completada: {len(results)} resultados en {search_time}ms")
logger.warning(f"Búsqueda sin resultados para query: {query}")
logger.error(f"Error en búsqueda semántica: {str(e)}")
```

## Troubleshooting

### Problemas Comunes

1. **Error de conexión a base de datos**
   ```bash
   # Verificar conexión
   python -c "from app.db.database import get_db; next(get_db())"
   ```

2. **Búsquedas lentas**
   ```sql
   -- Verificar índices
   SELECT * FROM pg_stat_user_indexes WHERE relname LIKE '%articles%';
   ```

3. **Datos faltantes en trending**
   ```bash
   # Ejecutar actualización manual
   python -c "from app.tasks.trending_tasks import update_trending_topics; update_trending_topics()"
   ```

## Desarrollo y Extensión

### Agregar Nuevos Filtros

1. Actualizar modelo `SearchFilter` en `search.py`
2. Implementar filtro en `SearchService._apply_*_filters()`
3. Actualizar documentación de API
4. Agregar tests

### Mejorar Búsqueda Semántica

1. Integrar modelos de embeddings (Sentence-BERT)
2. Pre-computar embeddings de artículos
3. Actualizar `SemanticSearchHelper`

### Nuevos Endpoints

1. Crear función en `search.py`
2. Implementar lógica en `search_service.py`
3. Documentar en este README
4. Agregar tests

## Contribuir

Para contribuir al sistema de búsqueda:

1. Fork el repositorio
2. Crear branch de feature
3. Implementar funcionalidad con tests
4. Documentar cambios
5. Crear Pull Request

## Licencia

MIT License - ver archivo LICENSE para detalles.