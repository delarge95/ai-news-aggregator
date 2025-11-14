# Cache Redis y Rate Limiting - Documentación Técnica

## Resumen

Este documento describe la implementación completa del sistema de cache Redis y rate limiting para el backend de AI News Aggregator.

## Arquitectura del Sistema

### 1. Sistema de Cache Redis (`redis_cache.py`)

#### Características Principales

- **Gestión completa de Redis**: Conexión, pooling, y manejo de errores
- **Operaciones de cache**: `get()`, `set()`, `delete()`, `exists()`
- **Gestión TTL**: Control automático de tiempo de vida
- **Invalidación inteligente**: Por patrones, prefijos, y namespaces
- **Operaciones batch**: `batch_set()` y `batch_get()` para eficiencia
- **Cache especializado**: Funciones específicas para artículos, búsquedas, y usuarios

#### Configuración por Defecto

```python
# settings.py
REDIS_URL = "redis://localhost:6379"
CACHE_TTL = 3600  # 1 hora por defecto
ARTICLE_CACHE_TTL = 1800  # 30 minutos para artículos
```

#### Ejemplos de Uso

```python
from app.core.redis_cache import get_cache_manager

# Inicializar cache
cache_manager = await get_cache_manager()

# Operaciones básicas
await cache_manager.set("key", {"data": "value"}, ttl=300)
value = await cache_manager.get("key")
await cache_manager.delete("key")

# Cache especializado para artículos
await cache_manager.cache_article("article_123", article_data)
cached_article = await cache_manager.get_cached_article("article_123")

# Invalidación por patrón
await cache_manager.invalidate_by_prefix("articles:")
```

### 2. Sistema de Rate Limiting (`rate_limiter.py`)

#### Algoritmos Implementados

**Token Bucket Algorithm**:
- Ideal para controlar burst requests
- Permite ráfagas limitadas de tráfico
- Refill rate configurable

**Sliding Window Algorithm**:
- Más preciso para rate limiting por ventana de tiempo
- Ideal para límites estrictos por minuto/hora

#### Configuración por Defecto

```python
# Límites por API
NEWSAPI: 100 req/hora, burst de 100, block 5min
GUARDIAN: 50 req/hora, burst de 50, block 10min  
NYTIMES: 50 req/hora, burst de 50, block 5min
OPENAI: 60 req/hora, burst de 60, block 30min

# Límites por IP
DEFAULT: 100 req/hora, burst de 100
PREMIUM: 500 req/hora, burst de 500
```

#### Ejemplos de Uso

```python
from app.core.rate_limiter import get_rate_limit_manager

# Inicializar rate limiter
rate_limit_manager = await get_rate_limit_manager()

# Verificar límites por API
allowed = await rate_limit_manager.check_api_rate_limit('newsapi')

# Verificar límites por IP
allowed = await rate_limit_manager.check_ip_rate_limit('192.168.1.1', 'default')

# Obtener estadísticas
stats = await rate_limit_manager.get_api_rate_info('newsapi')
```

### 3. Middleware de FastAPI (`middleware.py`)

#### RateLimitMiddleware

- **Integración automática**: Se aplica a todas las rutas no exentas
- **Identificación inteligente**: Por IP, API key, o headers personalizados
- **Headers de respuesta**: Incluye información de límites en responses
- **Paths exentos**: `/health`, `/docs`, etc.

```python
# Configuración en main.py
app.add_middleware(
    RateLimitMiddleware,
    default_limit_type='ip',
    default_algorithm='token_bucket',
    exempt_paths=['/health', '/docs']
)
```

#### CacheMiddleware

- **Caché automático**: Para requests GET
- **Headers de cache**: Control de TTL configurable
- **Selective caching**: Por paths específicos o métodos

```python
app.add_middleware(
    CacheMiddleware,
    cache_ttl=settings.CACHE_TTL,
    cache_paths=[],  # Cache todas las rutas GET
    exempt_methods=['POST', 'PUT', 'DELETE']
)
```

### 4. Utilidades de Alto Nivel (`utils.py`)

#### Decoradores para Uso Fácil

```python
from app.core.utils import cache_result, rate_limit_by_api

# Cache automático de resultados de función
@cache_result(ttl=300, key_prefix="search")
async def search_function(query: str):
    # Resultado será cacheado automáticamente
    return expensive_search_operation(query)

# Rate limiting automático por API
@rate_limit_by_api('newsapi')
async def fetch_news():
    # Solo permitirá si el límite de newsapi no se excede
    return external_api_call('newsapi')
```

#### CacheUtils y RateLimitUtils

- **Abstracción**: Interfaz simplificada para operaciones comunes
- **Funciones especializadas**: Para news, artículos, usuarios, etc.
- **Manejo de errores**: Logging y recovery automático

```python
from app.core.utils import get_cache_utils

cache_utils = await get_cache_utils()

# Cache de noticias
await cache_utils.cache_news_articles("query", articles, ttl=900)
cached_results = await cache_utils.get_cached_news_articles("query")

# Cache de análisis de IA
await cache_utils.cache_article_analysis("article_123", analysis)
cached_analysis = await cache_utils.get_cached_article_analysis("article_123")
```

## Integración en FastAPI

### Configuración en `main.py`

```python
from app.core.middleware import RateLimitMiddleware, CacheMiddleware, HealthCheckMiddleware

# Middleware en orden
app.add_middleware(RateLimitMiddleware, default_limit_type='ip')
app.add_middleware(CacheMiddleware, cache_ttl=300)
app.add_middleware(HealthCheckMiddleware)

# Inicialización en startup
@app.on_event("startup")
async def startup_event():
    # Inicializar Redis y rate limiting
    cache_manager = await get_cache_manager()
    await cache_manager.connect()
    
    rate_limit_manager = await get_rate_limit_manager()
```

### Endpoints de Monitoreo

- `GET /api/v1/cache/stats` - Estadísticas de cache
- `GET /api/v1/rate-limit/stats` - Estadísticas de rate limiting  
- `POST /api/v1/cache/invalidate` - Invalidación manual de cache
- `POST /api/v1/rate-limit/reset` - Reset de límites

## Configuración Avanzada

### Variables de Entorno

```bash
# Redis
REDIS_URL=redis://localhost:6379

# Límites de rate limiting
NEWS_API_RATE_LIMIT=100
AI_API_RATE_LIMIT=1000

# Cache TTL
CACHE_TTL=3600
ARTICLE_CACHE_TTL=1800
```

### Configuración Personalizada

```python
# Agregar límites personalizados
await rate_limit_utils.add_custom_api_limit(
    api_name="custom_api",
    requests_per_hour=200,
    burst_capacity=50,
    block_duration=600
)

# Configurar límites por IP específica
await rate_limit_utils.add_custom_ip_limit(
    ip_address="192.168.1.100",
    requests_per_hour=1000,
    burst_capacity=200
)
```

## Monitoreo y Debugging

### Headers de Rate Limiting

Todos los responses incluyen headers informativos:

```
X-RateLimit-Type: ip
X-RateLimit-Identifier: ip:192.168.1.1
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Logs del Sistema

```python
# Cache logs
logger.debug(f"Cache hit for key: {key}")
logger.info(f"Cached {count} articles for query: {query}")

# Rate limiting logs
logger.warning(f"Rate limit: Identifier {identifier} blocked for {duration}s")
logger.info(f"Rate limit: Identifier {identifier} allowed")
```

### Métricas Disponibles

- **Cache**: Hit ratio, memoria usada, keys activas
- **Rate Limiting**: Requests por API/IP, blocks activos, reset times
- **Performance**: Response times, throughput

## Best Practices

### 1. Cache Strategy

- **TTL apropiado**: Artículos cortos (30min), análisis IA (1hora)
- **Invalidación**: Usar patrones para limpieza eficiente
- **Cache warming**: Precargar datos críticos en startup

### 2. Rate Limiting

- **Burst capacity**: Permitir ráfagas pero limitar throughput
- **Block duration**: Balance entre seguridad y usabilidad
- **Monitorización**: Revisar límites regularmente

### 3. Error Handling

- **Graceful degradation**: En caso de fallo de Redis
- **Retry logic**: Para operaciones críticas
- **Alerting**: Notificaciones de rate limit exceeded

## Ejemplos de Implementación

### Endpoint con Cache y Rate Limiting

```python
@app.get("/news/search")
@cache_result(ttl=900, key_prefix="news_search")
@rate_limit_by_api('newsapi')
async def search_news(
    query: str,
    category: str = None
):
    # Lógica de búsqueda con cache automático
    return await perform_news_search(query, category)
```

### Tarea Background con Cache

```python
async def process_articles_background():
    cache_utils = await get_cache_utils()
    
    # Procesar artículos
    results = await process_articles()
    
    # Cache resultados
    await cache_utils.cache_news_articles("background_process", results)
```

## Troubleshooting

### Problemas Comunes

1. **Redis connection failed**
   - Verificar REDIS_URL
   - Comprobar estado del servicio Redis
   - Revisar permisos de red

2. **Rate limits muy restrictivos**
   - Ajustar configuración en settings
   - Usar límites personalizados por IP/API
   - Monitorear patrones de uso

3. **Cache no funciona**
   - Verificar que Redis esté conectado
   - Comprobar TTL configuración
   - Revisar logs de cache hit/miss

### Debug Commands

```bash
# Test Redis connection
redis-cli ping

# Monitorear Redis
redis-cli monitor

# Ver keys cache
redis-cli keys "*"

# Reset rate limits
curl -X POST /api/v1/rate-limit/reset -d "identifier=192.168.1.1"
```

Este sistema proporciona una solución robusta, escalable y flexible para cache y rate limiting en AI News Aggregator, con capacidades avanzadas de monitoreo y configuración dinámica.