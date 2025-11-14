# News Service Layer

Este directorio contiene el service layer unificado para el agregador de noticias, que implementa el patrón Factory y facade para simplificar el acceso a múltiples APIs de noticias.

## 🏗️ Arquitectura

### Componentes Principales

1. **NewsClient (Abstract Base Class)**
   - Clase base abstracta para todos los clientes de noticias
   - Define la interfaz común: `get_latest_news()`, `search_news()`, `get_sources()`, `get_categories()`

2. **Clientes Concretos**
   - `NewsAPIClient`: Cliente para NewsAPI.org
   - `GuardianAPIClient`: Cliente para The Guardian API
   - `NYTimesAPIClient`: Cliente para New York Times API

3. **NewsClientFactory**
   - Implementa el patrón Factory
   - Crea instancias de clientes según configuración
   - Gestiona clientes disponibles y configurados

4. **NewsService**
   - Service layer facade que unifica acceso a todos los clientes
   - Implementa agregación, filtrado y deduplicación
   - Manejo centralizado de errores y logging

## 🚀 Uso Básico

### Importar el servicio

```python
from app.services import news_service

# O importar la clase para crear instancias personalizadas
from app.services import NewsService
```

### Obtener últimas noticias

```python
import asyncio

async def get_news():
    # Obtener las últimas 20 noticias de todos los clientes configurados
    latest_news = await news_service.get_latest_news(limit=20)
    
    for article in latest_news:
        print(f"{article['title']} - {article['source_name']}")
        print(f"URL: {article['url']}")
        print(f"Cliente: {article['client_type']}")
        print("---")

# Ejecutar
asyncio.run(get_news())
```

### Buscar noticias

```python
async def search_example():
    # Buscar noticias sobre un tema específico
    results = await news_service.search_news(
        query="artificial intelligence",
        limit=10
    )
    
    for article in results:
        print(f"Found: {article['title']}")
        print(f"Search query: {article.get('search_query')}")
```

### Filtrar por fuentes o categorías

```python
async def filtered_news():
    # Obtener noticias de clientes específicos
    filtered = await news_service.get_latest_news(
        limit=15,
        client_types=['newsapi', 'guardian'],  # Solo estos clientes
        categories=['technology', 'business'],  # Solo estas categorías
        sources=['BBC News', 'Reuters']  # Solo estas fuentes
    )
    
    return filtered
```

### Obtener fuentes y categorías

```python
def get_metadata():
    # Obtener todas las fuentes disponibles
    all_sources = news_service.get_sources()
    
    for client_type, sources in all_sources.items():
        print(f"\n{client_type.upper()} Sources:")
        for source in sources:
            print(f"  - {source['name']} ({source['country']})")
    
    # Obtener todas las categorías
    all_categories = news_service.get_categories()
    
    for client_type, categories in all_categories.items():
        print(f"\n{client_type.upper()} Categories:")
        print(f"  {', '.join(categories)}")
```

## 🔧 Uso Avanzado

### Factory Pattern

```python
from app.services import NewsClientFactory

# Ver clientes disponibles
available = NewsClientFactory.get_available_clients()
print(f"Available clients: {available}")

# Ver clientes configurados
configured = NewsClientFactory.get_configured_clients()
print(f"Configured clients: {configured}")

# Crear cliente específico
client = NewsClientFactory.create_client('newsapi')

# Usar cliente directamente
latest = await client.get_latest_news(limit=5)
```

### Service personalizado

```python
# Crear instancia personalizada
custom_service = NewsService()

# Configurar logging específico
import logging
logging.basicConfig(level=logging.DEBUG)

# Verificar estado de clientes
status = custom_service.health_check()
print(f"Service health: {status}")

# Estado detallado de cada cliente
client_status = custom_service.get_client_status()
for client_type, status in client_status.items():
    print(f"{client_type}: {status}")
```

## 🔐 Configuración

### Variables de Entorno

Configurar las API keys en el archivo `.env`:

```bash
# NewsAPI.org
NEWSAPI_KEY=your_newsapi_key_here

# The Guardian
GUARDIAN_API_KEY=your_guardian_key_here

# New York Times
NYTIMES_API_KEY=your_nytimes_key_here
```

### Configuración en settings

```python
from app.core.config import settings

# Las keys se leen automáticamente desde settings
# No es necesario pasarlas manualmente al service
```

## 📊 Formato de Datos

### Artículo

```python
{
    'title': 'Título del artículo',
    'content': 'Contenido del artículo',
    'url': 'https://ejemplo.com/articulo',
    'published_at': '2023-12-01T10:00:00Z',
    'source_name': 'Nombre de la fuente',
    'source_id': 'ID de la fuente en la API',
    'api_name': 'newsapi',  # Tipo de cliente
    'client_type': 'newsapi',  # Cliente que proporcionó el dato
    'author': 'Autor del artículo',
    'description': 'Descripción corta',
    'image_url': 'https://ejemplo.com/imagen.jpg',
    'search_query': 'término de búsqueda'  # Solo en resultados de búsqueda
}
```

### Fuente

```python
{
    'id': 'bbc-news',
    'name': 'BBC News',
    'country': 'gb',
    'language': 'en'
}
```

## 🛡️ Manejo de Errores

### Tipos de Errores

```python
from app.services import NewsClientError, RateLimitError, APIKeyError

try:
    news = await news_service.get_latest_news()
except RateLimitError:
    print("Límite de rate excedido. Intente más tarde.")
except APIKeyError:
    print("Error de API key. Verifique configuración.")
except NewsClientError as e:
    print(f"Error general del cliente: {e}")
```

### Logging

El service incluye logging detallado:

```python
import logging

# Configurar nivel de logging
logging.basicConfig(level=logging.INFO)

# Los logs incluyen:
# - Inicialización de clientes
# - Requests a APIs
# - Errores y timeouts
# - Estadísticas de resultados
```

## 🔄 Características

### ✅ Implementado

- **Factory Pattern**: Creación dinámica de clientes
- **Facade Pattern**: Interfaz unificada para múltiples APIs
- **Async/Await**: Operaciones asíncronas para mejor performance
- **Rate Limiting**: Manejo de límites de API (básico)
- **Error Handling**: Manejo robusto de errores por tipo
- **Logging**: Logging detallado de operaciones
- **Deduplication**: Eliminación de artículos duplicados por URL
- **Filtering**: Filtros por cliente, fuente y categoría
- **Aggregation**: Agregación de resultados de múltiples fuentes
- **Timeout Handling**: Timeouts para evitar bloqueos

### 🎯 Métodos Principales

- `get_latest_news()`: Obtener últimas noticias con filtros opcionales
- `search_news()`: Buscar noticias por término
- `get_sources()`: Obtener fuentes disponibles por cliente
- `get_categories()`: Obtener categorías disponibles por cliente
- `health_check()`: Verificar estado del servicio
- `get_client_status()`: Estado detallado de clientes

## 📝 Ejemplos

Ver el archivo `examples.py` para ejemplos completos de uso:

```bash
# Ejecutar ejemplos
cd backend/app/services
python examples.py
```

## 🔧 Integración

### En APIs/Routes

```python
from fastapi import APIRouter, HTTPException, Query
from app.services import news_service

router = APIRouter()

@router.get("/news/latest")
async def get_latest_news_endpoint(
    limit: int = Query(20, ge=1, le=100),
    client_types: str = Query(None, description="Comma-separated client types"),
    categories: str = Query(None, description="Comma-separated categories")
):
    try:
        # Procesar parámetros
        clients = client_types.split(',') if client_types else None
        cats = categories.split(',') if categories else None
        
        # Obtener noticias
        articles = await news_service.get_latest_news(
            limit=limit,
            client_types=clients,
            categories=cats
        )
        
        return {"articles": articles, "count": len(articles)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/news/search")
async def search_news_endpoint(q: str = Query(..., min_length=2)):
    try:
        articles = await news_service.search_news(query=q, limit=20)
        return {"articles": articles, "query": q, "count": len(articles)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### En Background Tasks

```python
import asyncio
from app.services import news_service

async def news_aggregator_task():
    """Tarea para agregar noticias periódicamente"""
    while True:
        try:
            # Obtener noticias cada 5 minutos
            latest_news = await news_service.get_latest_news(limit=50)
            
            # Procesar y guardar en base de datos
            # ... lógica de procesamiento ...
            
            await asyncio.sleep(300)  # 5 minutos
            
        except Exception as e:
            logging.error(f"Error en tarea de agregación: {e}")
            await asyncio.sleep(60)  # Esperar 1 minuto antes de reintentar

# Iniciar tarea
asyncio.create_task(news_aggregator_task())
```

## 🚀 Performance

### Optimizaciones Implementadas

- **Paralelización**: Requests simultáneos a múltiples APIs
- **Timeouts**: Evita bloqueos por APIs lentas
- **Deduplication**: Evita procesamiento de duplicados
- **ThreadPoolExecutor**: Pool de threads para operaciones de red
- **Rate Limit Awareness**: Respeta límites de APIs

### Límites Recomendados

- **Máximo de artículos por request**: 50-100
- **Timeout por cliente**: 30 segundos
- **Concurrent requests**: Máximo 5 clientes simultáneos
- **Cache**: Implementar cache para fuentes estáticas (categorías, fuentes)

## 📈 Monitoreo

### Métricas Disponibles

- Estado de cada cliente
- Rate limits restantes
- Número de artículos obtenidos
- Tiempo de respuesta por cliente
- Errores y excepciones

### Health Check

```python
health = news_service.health_check()
print(f"""
Estado del servicio:
- Status: {health['status']}
- Clientes configurados: {health['configured_clients']}
- Total de clientes: {health['clients_count']}
- Timestamp: {health['timestamp']}
""")
```