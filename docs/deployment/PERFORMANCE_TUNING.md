# Guía de Optimización de Performance

## Tabla de Contenidos
- [Análisis de Performance](#análisis-de-performance)
- [Optimización del Backend](#optimización-del-backend)
- [Optimización de Base de Datos](#optimización-de-base-de-datos)
- [Optimización de Redis](#optimización-de-redis)
- [Optimización de Frontend](#optimización-de-frontend)
- [Optimización de Docker](#optimización-de-docker)
- [Optimización de Sistema](#optimización-de-sistema)
- [Caching Strategy](#caching-strategy)
- [Load Testing](#load-testing)
- [Monitoring de Performance](#monitoring-de-performance)

## Análisis de Performance

### 1. Baseline de Performance

```bash
#!/bin/bash
# performance-baseline.sh

echo "📊 Generando baseline de performance..."

# 1. CPU Benchmark
echo "=== CPU INFO ==="
lscpu | grep -E "Model name|CPU\(s\)|Thread|MHz"
uptime
cat /proc/cpuinfo | grep processor | wc -l

# 2. Memory Benchmark
echo "=== MEMORY INFO ==="
free -h
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable"

# 3. Disk Benchmark
echo "=== DISK INFO ==="
df -h
hdparm -t /dev/sda 2>/dev/null || echo "HD parm not available"

# 4. Network Benchmark
echo "=== NETWORK INFO ==="
ip addr show | grep inet
cat /proc/net/dev | grep eth0

# 5. Database Performance
echo "=== DATABASE PERFORMANCE ==="
psql -h database_host -U postgres -d ai_news_aggregator -c "
SELECT 
    'Connections' as metric,
    count(*) as value
FROM pg_stat_activity
UNION ALL
SELECT 
    'Cache Hit Ratio' as metric,
    round(100.0 * sum(blks_hit) / sum(blks_hit + blks_read), 2) as value
FROM pg_stat_database
WHERE datname = 'ai_news_aggregator';
"

# 6. Redis Performance
echo "=== REDIS PERFORMANCE ==="
redis-cli -h redis_host --latency-history -i 1 | head -10

# 7. API Response Time
echo "=== API RESPONSE TIME ==="
curl -o /dev/null -s -w "Connect: %{time_connect}s\nStartTransfer: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
    http://localhost:8000/health

echo "✅ Baseline generado"
```

### 2. Performance Monitoring Setup

```python
# backend/app/core/performance_monitor.py
import time
import psutil
import functools
import asyncio
from typing import Dict, Any
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Métricas de performance
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
REQUEST_SIZE = Histogram('http_request_size_bytes', 'HTTP request size')
RESPONSE_SIZE = Histogram('http_response_size_bytes', 'HTTP response size')

# Métricas del sistema
CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage percentage')
DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage percentage')

# Métricas de la aplicación
DATABASE_QUERY_TIME = Histogram('database_query_duration_seconds', 'Database query duration')
CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Cache hit ratio', ['cache_name'])
CELERY_QUEUE_SIZE = Gauge('celery_queue_size', 'Celery queue size', ['queue_name'])

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor de performance de la aplicación"""
    
    def __init__(self):
        self.process = psutil.Process()
    
    def collect_system_metrics(self):
        """Recopilar métricas del sistema"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            DISK_USAGE.set((disk.used / disk.total) * 100)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def monitor_function(self, func):
        """Decorador para monitorear funciones"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = self.process.memory_info().rss
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = time.time() - start_time
                end_memory = self.process.memory_info().rss
                
                # Registrar métricas
                REQUEST_DURATION.observe(duration)
                if hasattr(func, '__name__'):
                    REQUEST_COUNT.labels(
                        method='function',
                        endpoint=func.__name__,
                        status='success' if success else 'error'
                    ).inc()
                
                # Log de performance
                logger.info(
                    f"Function {func.__name__} executed",
                    extra={
                        'duration': duration,
                        'memory_delta': end_memory - start_memory,
                        'success': success
                    }
                )
        
        return wrapper
    
    async def monitor_async_function(self, func):
        """Decorador para monitorear funciones async"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = self.process.memory_info().rss
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = time.time() - start_time
                end_memory = self.process.memory_info().rss
                
                # Registrar métricas
                REQUEST_DURATION.observe(duration)
                
                # Log de performance
                logger.info(
                    f"Async function {func.__name__} executed",
                    extra={
                        'duration': duration,
                        'memory_delta': end_memory - start_memory,
                        'success': success
                    }
                )
        
        return wrapper

# Instancia global
performance_monitor = PerformanceMonitor()

# Función para métricas endpoint
async def metrics_endpoint():
    """Endpoint para métricas de Prometheus"""
    performance_monitor.collect_system_metrics()
    return generate_latest()
```

### 3. APM Integration

```python
# backend/app/core/apm.py
from elasticapm import Client as ElasticAPM
import asyncio
import logging

# Configuración de APM
elasticapm = Client({
    'SERVICE_NAME': 'ai-news-aggregator',
    'SERVER_URL': 'http://apm-server:8200',
    'ENVIRONMENT': 'production',
    'COLLECT_LOCAL_VARIABLES': 'on',
    'TRACES_SEND_FREQUENCY': 5,
    'TRANSACTIONS_SAMPLE_RATE': 0.1,
})

# Middleware para APM
class APMMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            transaction_name = f"{scope['method']} {scope['path']}"
            
            with elasticapm.capture_transaction(transaction_name):
                # Extraer información de la request
                headers = dict(scope.get("headers", []))
                user_agent = headers.get(b"user-agent", b"").decode("utf-8")
                client_ip = scope.get("client", ["unknown"])[0]
                
                elasticapm.set_user_context(
                    user_ip=client_ip,
                    user_agent=user_agent,
                )
                
                await self.app(scope, receive, send)
        else:
            await self.app(scope, receive, send)
```

## Optimización del Backend

### 1. Configuración de FastAPI

```python
# backend/app/core/performance_config.py
from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import asyncio
import uvloop

class PerformanceOptimizer:
    def __init__(self, app: FastAPI):
        self.app = app
    
    def optimize_app(self):
        """Optimizar configuración de FastAPI"""
        
        # Gzip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)
        
        # CORS optimizado
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://yourdomain.com"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
            max_age=86400,
        )
        
        # Session management
        self.app.add_middleware(
            SessionMiddleware,
            secret_key="your-secret-key",
            same_site="lax",
            https_only=True,
        )
    
    def configure_uvicorn(self):
        """Configuración optimizada de Uvicorn"""
        config = {
            "app": self.app,
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 4,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "worker_connections": 1000,
            "max_requests": 10000,
            "max_requests_jitter": 1000,
            "preload_app": True,
            "log_config": None,  # Usar logging personalizado
            "access_log": True,
            "error_log": True,
            "loop": "uvloop",
            "http": "httptools",
            "ws": "websockets",
        }
        return config

# Optimizar event loop
def optimize_event_loop():
    """Optimizar event loop con uvloop"""
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        print("✅ Using uvloop for better performance")
    except ImportError:
        print("⚠️  uvloop not available, using default event loop")

# Optimizar memory usage
def optimize_memory_usage():
    """Configuraciones para optimizar uso de memoria"""
    import gc
    
    # Configurar garbage collection
    gc.set_threshold(700, 10, 10)
    
    # Habilitar debug de memoria en desarrollo
    # gc.set_debug(gc.DEBUG_STATS)
    
    return gc
```

### 2. Optimización de Queries

```python
# backend/app/core/query_optimization.py
from sqlalchemy import text, select, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.engine import Result
from typing import List, Optional
import asyncio
import time

class QueryOptimizer:
    """Optimizador de queries SQL"""
    
    @staticmethod
    def get_optimized_article_query():
        """Query optimizado para artículos con paginación eficiente"""
        return """
        SELECT 
            a.id, a.title, a.content, a.url, a.published_date,
            a.source_id, a.category, a.sentiment_score,
            s.name as source_name, s.logo_url as source_logo
        FROM articles a
        LEFT JOIN sources s ON a.source_id = s.id
        WHERE a.published_date >= NOW() - INTERVAL '30 days'
        ORDER BY a.published_date DESC
        LIMIT :limit OFFSET :offset
        """
    
    @staticmethod
    async def get_articles_batch(session, limit: int, offset: int):
        """Obtener artículos en batch optimizado"""
        start_time = time.time()
        
        query = text(QueryOptimizer.get_optimized_article_query())
        result = await session.execute(query, {"limit": limit, "offset": offset})
        articles = result.fetchall()
        
        # Log de performance
        duration = time.time() - start_time
        print(f"Query executed in {duration:.3f}s")
        
        return articles
    
    @staticmethod
    def get_article_stats_query():
        """Query para estadísticas de artículos"""
        return """
        SELECT 
            DATE_TRUNC('day', published_date) as day,
            COUNT(*) as article_count,
            AVG(sentiment_score) as avg_sentiment
        FROM articles 
        WHERE published_date >= NOW() - INTERVAL '7 days'
        GROUP BY day
        ORDER BY day DESC
        """
    
    @staticmethod
    def get_search_optimized_query():
        """Query optimizado para búsquedas"""
        return """
        SELECT 
            a.id, a.title, a.content, a.url, a.published_date,
            ts_rank(search_vector, plainto_tsquery('english', :query)) as rank
        FROM articles a
        WHERE search_vector @@ plainto_tsquery('english', :query)
        ORDER BY rank DESC, published_date DESC
        LIMIT :limit OFFSET :offset
        """
    
    @staticmethod
    async def execute_search(session, query: str, limit: int, offset: int):
        """Ejecutar búsqueda optimizada"""
        start_time = time.time()
        
        sql = text(QueryOptimizer.get_search_optimized_query())
        result = await session.execute(sql, {
            "query": query,
            "limit": limit,
            "offset": offset
        })
        articles = result.fetchall()
        
        duration = time.time() - start_time
        print(f"Search query executed in {duration:.3f}s")
        
        return articles

# Pagination optimizada
class OptimizedPaginator:
    """Paginador optimizado"""
    
    def __init__(self, page_size: int = 20):
        self.page_size = page_size
    
    async def paginate(self, query, session, page: int = 1):
        """Paginación con cache de counts"""
        offset = (page - 1) * self.page_size
        
        # Ejecutar query principal
        result = await session.execute(query.limit(self.page_size).offset(offset))
        items = result.scalars().all()
        
        # Obtener total (con cache)
        total = await self.get_total_count(query, session)
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": self.page_size,
            "pages": (total + self.page_size - 1) // self.page_size,
            "has_next": offset + self.page_size < total,
            "has_prev": page > 1
        }
    
    async def get_total_count(self, query, session):
        """Obtener count optimizado"""
        # Para queries complejos, usar count más eficiente
        count_query = query.with_only_columns(func.count()).order_by(None)
        result = await session.execute(count_query)
        return result.scalar()
```

### 3. Async Optimizations

```python
# backend/app/core/async_optimization.py
import asyncio
import aioredis
from aiofiles import open as aiofiles_open
from typing import List, Any
import concurrent.futures
from functools import partial

class AsyncOptimizer:
    """Optimizador para operaciones asíncronas"""
    
    def __init__(self):
        self.redis_pool = None
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    
    async def init_redis_pool(self):
        """Inicializar pool de conexiones Redis"""
        self.redis_pool = aioredis.ConnectionPool.from_url(
            "redis://redis_host:6379",
            max_connections=20,
            retry_on_timeout=True
        )
        self.redis = aioredis.Redis(connection_pool=self.redis_pool)
    
    async def parallel_api_calls(self, api_calls: List[callable]):
        """Ejecutar llamadas API en paralelo"""
        tasks = [call() for call in api_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def batch_database_operations(self, operations: List):
        """Ejecutar operaciones de base de datos en batch"""
        # Agrupar operaciones similares
        grouped_ops = self.group_operations(operations)
        
        results = []
        for group in grouped_ops:
            batch_result = await self.execute_batch(group)
            results.extend(batch_result)
        
        return results
    
    def group_operations(self, operations: List) -> List[List]:
        """Agrupar operaciones por tipo"""
        grouped = {}
        for op in operations:
            op_type = type(op).__name__
            if op_type not in grouped:
                grouped[op_type] = []
            grouped[op_type].append(op)
        
        return list(grouped.values())
    
    async def execute_batch(self, operations: List):
        """Ejecutar batch de operaciones"""
        # Implementar según el tipo de operación
        pass
    
    async def parallel_file_operations(self, file_paths: List[str]):
        """Operaciones de archivos en paralelo"""
        tasks = []
        for path in file_paths:
            task = self.read_file_async(path)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def read_file_async(self, path: str):
        """Leer archivo asíncronamente"""
        try:
            async with aiofiles_open(path, 'r') as f:
                content = await f.read()
                return {"path": path, "content": content}
        except Exception as e:
            return {"path": path, "error": str(e)}
    
    async def cache_warm_up(self, keys: List[str]):
        """Calentar cache con datos importantes"""
        tasks = []
        for key in keys:
            task = self.warm_cache_key(key)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def warm_cache_key(self, key: str):
        """Calentar una clave específica del cache"""
        # Lógica para cargar datos en cache
        pass
    
    def close(self):
        """Cerrar recursos"""
        if self.redis_pool:
            self.redis_pool.disconnect()
        self.executor.shutdown(wait=True)

# Rate limiting optimizado
class AsyncRateLimiter:
    """Rate limiter asíncrono optimizado"""
    
    def __init__(self, max_calls: int, time_window: int):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Adquirir permiso para ejecutar"""
        async with self.lock:
            now = asyncio.get_event_loop().time()
            
            # Limpiar calls antiguas
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.time_window]
            
            # Verificar si podemos hacer otra llamada
            if len(self.calls) >= self.max_calls:
                sleep_time = self.time_window - (now - self.calls[0])
                await asyncio.sleep(sleep_time)
                return await self.acquire()
            
            # Registrar esta llamada
            self.calls.append(now)
            return True
```

## Optimización de Base de Datos

### 1. Configuración PostgreSQL

```sql
-- postgresql-performance.conf

-- Configuración de memoria
shared_buffers = 2GB                    -- 25% de RAM total
effective_cache_size = 6GB              -- 75% de RAM disponible
work_mem = 128MB                        -- Por operación
maintenance_work_mem = 512MB            -- Para maintenance
max_wal_size = 4GB                      -- WAL maximum size
min_wal_size = 1GB                      -- WAL minimum size

-- Configuración de checkpoint
checkpoint_completion_target = 0.9      -- Spread checkpoint I/O
wal_buffers = 32MB                      -- WAL buffer size
checkpoint_timeout = 15min              -- Checkpoint timeout

-- Configuración de consultas
random_page_cost = 1.1                  -- SSD optimization
effective_io_concurrency = 200          -- Parallel I/O
work_mem = 128MB                        -- Query work memory
maintenance_work_mem = 512MB            -- Maintenance operations

-- Configuración de conexiones
max_connections = 200                   -- Maximum connections
max_worker_processes = 8                -- Parallel workers
max_parallel_workers = 8                -- Parallel query workers
max_parallel_workers_per_gather = 4     -- Workers per node

-- Configuración de planificación
default_statistics_target = 1000        -- Statistics target
constraint_exclusion = partition        -- Partition elimination

-- Configuración de logs
log_min_duration_statement = 1000       -- Log slow queries
log_checkpoints = on                    -- Log checkpoints
log_connections = on                    -- Log connections
log_disconnections = on                 -- Log disconnections
log_lock_waits = on                     -- Log lock waits
log_temp_files = 0                      -- Don't log temp files

-- Configuración de autovacuum
autovacuum = on                         -- Enable autovacuum
autovacuum_max_workers = 6              -- Max autovacuum workers
autovacuum_naptime = 1min               -- Autovacuum interval
autovacuum_vacuum_threshold = 50        -- Vacuum threshold
autovacuum_analyze_threshold = 50       -- Analyze threshold

-- Extensiones
shared_preload_libraries = 'pg_stat_statements,pg_trgm'
```

### 2. Indexes Optimizados

```sql
-- indexes-optimization.sql

-- Índice compuesto para búsquedas frecuentes
CREATE INDEX CONCURRENTLY idx_articles_search_composite 
ON articles(category, published_date DESC) 
WHERE published_date >= CURRENT_DATE - INTERVAL '30 days';

-- Índice GIN para búsquedas de texto
CREATE INDEX CONCURRENTLY idx_articles_gin_search 
ON articles USING gin(search_vector);

-- Índice para estadísticas por categoría
CREATE INDEX CONCURRENTLY idx_articles_category_stats 
ON articles(category, published_date DESC);

-- Índice para artículos populares
CREATE INDEX CONCURRENTLY idx_articles_popular 
ON articles(engagement_score DESC, published_date DESC);

-- Índice para deduplicación
CREATE UNIQUE INDEX CONCURRENTLY idx_articles_url_unique 
ON articles(url) WHERE published_date >= CURRENT_DATE - INTERVAL '7 days';

-- Índice para usuarios y preferencias
CREATE INDEX CONCURRENTLY idx_user_preferences_user_category 
ON user_preferences(user_id, category) 
WHERE is_active = true;

-- Índice parcial para contenido público
CREATE INDEX CONCURRENTLY idx_articles_public 
ON articles(published_date DESC) 
WHERE is_public = true;

-- Índice para trending articles
CREATE INDEX CONCURRENTLY idx_articles_trending 
ON articles(trending_score DESC, published_date DESC);

-- Stats para índices
ANALYZE articles;
ANALYZE users;
ANALYZE user_preferences;
```

### 3. Query Optimization

```sql
-- query-optimization-examples.sql

-- 1. Optimización de paginación
-- Malo: OFFSET en tablas grandes
SELECT * FROM articles ORDER BY published_date DESC LIMIT 20 OFFSET 10000;

-- Bueno: Cursor-based pagination
SELECT * FROM articles 
WHERE published_date < '2023-12-01 12:00:00'
ORDER BY published_date DESC LIMIT 20;

-- 2. Optimización de JOINs
-- Malo: Subquery en SELECT
SELECT 
    a.*,
    (SELECT COUNT(*) FROM article_interactions ai WHERE ai.article_id = a.id) as interaction_count
FROM articles a
WHERE a.category = 'technology';

-- Bueno: LEFT JOIN con agregación
SELECT 
    a.*,
    COUNT(ai.id) as interaction_count
FROM articles a
LEFT JOIN article_interactions ai ON a.id = ai.article_id
WHERE a.category = 'technology'
GROUP BY a.id
ORDER BY a.published_date DESC;

-- 3. Optimización de agregaciones
-- Malo: Multiple aggregations
SELECT 
    category,
    COUNT(*) as total,
    AVG(engagement_score) as avg_engagement,
    MAX(published_date) as latest
FROM articles
GROUP BY category;

-- Bueno: Query específico por necesidad
-- Para conteos simples
SELECT category, COUNT(*) as total
FROM articles
GROUP BY category;

-- Para engagement promedio
SELECT 
    category,
    AVG(engagement_score) as avg_engagement
FROM articles
WHERE engagement_score IS NOT NULL
GROUP BY category;

-- 4. Partitioning para tablas grandes
CREATE TABLE articles_2023 PARTITION OF articles
FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE articles_2024 PARTITION OF articles
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

-- 5. Materialized views para estadísticas
CREATE MATERIALIZED VIEW daily_stats AS
SELECT 
    DATE(published_date) as day,
    category,
    COUNT(*) as article_count,
    AVG(engagement_score) as avg_engagement,
    COUNT(DISTINCT source_id) as unique_sources
FROM articles
WHERE published_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(published_date), category;

-- Index on materialized view
CREATE INDEX idx_daily_stats_day_category ON daily_stats(day, category);

-- Refresh automático
CREATE OR REPLACE FUNCTION refresh_daily_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_stats;
END;
$$ LANGUAGE plpgsql;

-- Cron job para refresh
-- SELECT cron.schedule('refresh-stats', '0 */6 * * *', 'SELECT refresh_daily_stats();');
```

## Optimización de Redis

### 1. Configuración Redis

```bash
# redis-performance.conf

# Memory optimization
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 10

# Persistence optimization
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb

# Network optimization
tcp-keepalive 300
timeout 300
tcp-backlog 511

# Client optimization
maxclients 10000

# Performance optimization
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency monitoring
latency-monitor-threshold 100
```

### 2. Redis Optimization Patterns

```python
# backend/app/core/redis_optimization.py
import aioredis
import asyncio
import json
from typing import Any, Optional, List
import pickle

class RedisOptimizer:
    """Optimizador para Redis"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_pool = None
    
    async def init_pool(self):
        """Inicializar pool de conexiones"""
        self.redis_pool = aioredis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=20,
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={}
        )
        self.redis = aioredis.Redis(connection_pool=self.redis_pool)
    
    async def cache_article_batch(self, articles: List[dict]):
        """Cachear artículos en batch"""
        pipeline = self.redis.pipeline()
        
        for article in articles:
            key = f"article:{article['id']}"
            value = pickle.dumps(article)
            pipeline.setex(key, 3600, value)  # 1 hora TTL
        
        await pipeline.execute()
    
    async def get_articles_batch(self, article_ids: List[str]) -> List[Optional[dict]]:
        """Obtener artículos en batch"""
        keys = [f"article:{id}" for id in article_ids]
        values = await self.redis.mget(keys)
        
        articles = []
        for value in values:
            if value:
                articles.append(pickle.loads(value))
            else:
                articles.append(None)
        
        return articles
    
    async def cache_search_results(self, query: str, results: List[dict], ttl: int = 300):
        """Cachear resultados de búsqueda"""
        key = f"search:{hash(query)}"
        value = pickle.dumps(results)
        await self.redis.setex(key, ttl, value)
    
    async def get_search_cache(self, query: str) -> Optional[List[dict]]:
        """Obtener cache de búsqueda"""
        key = f"search:{hash(query)}"
        value = await self.redis.get(key)
        
        if value:
            return pickle.loads(value)
        return None
    
    async def get_redis_stats(self) -> dict:
        """Obtener estadísticas de Redis"""
        info = await self.redis.info()
        
        return {
            "used_memory": info["used_memory_human"],
            "used_memory_peak": info["used_memory_peak_human"],
            "connected_clients": info["connected_clients"],
            "total_commands_processed": info["total_commands_processed"],
            "keyspace_hits": info["keyspace_hits"],
            "keyspace_misses": info["keyspace_misses"],
            "hit_rate": info["keyspace_hits"] / (info["keyspace_hits"] + info["keyspace_misses"]) if (info["keyspace_hits"] + info["keyspace_misses"]) > 0 else 0
        }
    
    async def warm_cache(self):
        """Calentar cache con datos frecuentes"""
        # Artículo más reciente por categoría
        categories = ["technology", "sports", "business", "politics"]
        
        for category in categories:
            # Obtener de base de datos (implementar según necesidad)
            # articles = await self.get_latest_articles(category, limit=10)
            # await self.cache_article_batch(articles)
            pass
    
    async def cleanup_expired_keys(self):
        """Limpiar claves expiradas"""
        await self.redis.execute_command('EVAL', '''
            local removed = 0
            local keys = redis.call('KEYS', 'article:*')
            for i=1,#keys do
                if redis.call('TTL', keys[i]) == -1 then
                    redis.call('EXPIRE', keys[i], 3600)
                    removed = removed + 1
                end
            end
            return removed
        ''', 0)

# Cache decorator optimizado
def cache_result(expiry: int = 3600):
    """Decorator para cachear resultados"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar key basado en función y argumentos
            key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener del cache
            cached_result = await redis_optimizer.redis.get(key)
            if cached_result:
                return pickle.loads(cached_result)
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            await redis_optimizer.redis.setex(
                key, 
                expiry, 
                pickle.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

## Optimización de Frontend

### 1. Bundle Optimization

```javascript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  
  build: {
    // Optimización de bundle
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-toast'],
          utils: ['lodash', 'date-fns'],
          charts: ['recharts', 'd3']
        },
        // Hash para cache busting
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]'
      }
    },
    
    // Minificación
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log']
      }
    },
    
    // Chunks size warnings
    chunkSizeWarningLimit: 1000,
    
    // Source maps en producción
    sourcemap: false,
    
    // Compresión
    reportCompressedSize: false
  },
  
  // Optimización de desarrollo
  server: {
    hmr: true,
    open: false
  },
  
  // Resolución de módulos
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
      '@/components': resolve(__dirname, './src/components'),
      '@/pages': resolve(__dirname, './src/pages'),
      '@/hooks': resolve(__dirname, './src/hooks'),
      '@/utils': resolve(__dirname, './src/utils')
    }
  },
  
  // Optimización de CSS
  css: {
    modules: {
      localsConvention: 'camelCase'
    }
  }
})
```

### 2. Performance Optimizations

```typescript
// frontend/src/utils/performance.ts

// Lazy loading de componentes
import { lazy, Suspense } from 'react'
import { LoadingSpinner } from '@/components/ui/loading'

// Lazy load heavy components
const Dashboard = lazy(() => import('@/pages/Dashboard'))
const Analytics = lazy(() => import('@/pages/Analytics'))
const SearchResults = lazy(() => import('@/pages/SearchResults'))

// Code splitting por rutas
export const LazyRoutes = {
  Dashboard: () => (
    <Suspense fallback={<LoadingSpinner />}>
      <Dashboard />
    </Suspense>
  ),
  Analytics: () => (
    <Suspense fallback={<LoadingSpinner />}>
      <Analytics />
    </Suspense>
  )
}

// Virtual scrolling para listas grandes
export interface VirtualScrollProps<T> {
  items: T[]
  itemHeight: number
  containerHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
}

export function VirtualScroll<T>({
  items,
  itemHeight,
  containerHeight,
  renderItem
}: VirtualScrollProps<T>) {
  const [scrollTop, setScrollTop] = useState(0)
  
  const startIndex = Math.floor(scrollTop / itemHeight)
  const endIndex = Math.min(
    startIndex + Math.ceil(containerHeight / itemHeight) + 1,
    items.length
  )
  
  const visibleItems = items.slice(startIndex, endIndex)
  const totalHeight = items.length * itemHeight
  
  return (
    <div 
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        {visibleItems.map((item, index) => (
          <div
            key={startIndex + index}
            style={{
              position: 'absolute',
              top: (startIndex + index) * itemHeight,
              height: itemHeight,
              width: '100%'
            }}
          >
            {renderItem(item, startIndex + index)}
          </div>
        ))}
      </div>
    </div>
  )
}

// Debounce hook optimizado
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

// Memoization optimizada
export const MemoizedArticleCard = memo(({ article }: { article: Article }) => {
  return (
    <article className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <h3 className="font-semibold text-lg mb-2">{article.title}</h3>
      <p className="text-gray-600 text-sm mb-3 line-clamp-3">
        {article.content}
      </p>
      <div className="flex items-center justify-between text-sm text-gray-500">
        <span>{article.source}</span>
        <time dateTime={article.publishedDate}>
          {formatDistanceToNow(new Date(article.publishedDate))} ago
        </time>
      </div>
    </article>
  )
})

// Virtual scroller para artículos
export function ArticleList({ articles }: { articles: Article[] }) {
  return (
    <VirtualScroll
      items={articles}
      itemHeight={200}
      containerHeight={600}
      renderItem={(article) => (
        <MemoizedArticleCard key={article.id} article={article} />
      )}
    />
  )
}

// Service Worker para cache
export function registerSW() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration)
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError)
        })
    })
  }
}
```

### 3. Image Optimization

```typescript
// frontend/src/components/OptimizedImage.tsx
import { useState, useRef, useEffect } from 'react'

interface OptimizedImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  lazy?: boolean
}

export function OptimizedImage({
  src,
  alt,
  width,
  height,
  className,
  lazy = true
}: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false)
  const [isInView, setIsInView] = useState(!lazy)
  const imgRef = useRef<HTMLImageElement>(null)
  const observerRef = useRef<IntersectionObserver>()

  useEffect(() => {
    if (!lazy || isInView) return

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observerRef.current?.disconnect()
        }
      },
      {
        rootMargin: '50px'
      }
    )

    if (imgRef.current) {
      observerRef.current.observe(imgRef.current)
    }

    return () => {
      observerRef.current?.disconnect()
    }
  }, [lazy, isInView])

  const handleLoad = () => {
    setIsLoaded(true)
  }

  if (!isInView) {
    return (
      <div
        ref={imgRef}
        className={`bg-gray-200 animate-pulse ${className}`}
        style={{ width, height }}
      />
    )
  }

  return (
    <img
      ref={imgRef}
      src={src}
      alt={alt}
      width={width}
      height={height}
      className={`${className} ${isLoaded ? 'opacity-100' : 'opacity-0'} transition-opacity`}
      onLoad={handleLoad}
      loading={lazy ? 'lazy' : 'eager'}
    />
  )
}

// Responsive images con srcSet
export function ResponsiveImage({
  src,
  alt,
  sizes = '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw'
}: {
  src: string
  alt: string
  sizes?: string
}) {
  const [srcSet, setSrcSet] = useState('')

  useEffect(() => {
    // Generar srcSet para diferentes resoluciones
    const widths = [320, 640, 960, 1280, 1920]
    const srcSetValues = widths
      .map((width) => `${src}?w=${width} ${width}w`)
      .join(', ')
    setSrcSet(srcSetValues)
  }, [src])

  return (
    <OptimizedImage
      src={src}
      alt={alt}
      srcSet={srcSet}
      sizes={sizes}
      lazy
    />
  )
}
```

## Optimización de Docker

### 1. Dockerfile Optimizado

```dockerfile
# backend/Dockerfile.optimized
# Multi-stage build for optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy application
WORKDIR /app
COPY --chown=appuser:appuser . .

# Compile Python bytecode
RUN python -m compileall -b app/

# Set environment variables for optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONMALLOC=malloc \
    MALLOC_ARENA_MAX=2 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 2. Docker Compose Optimizado

```yaml
# docker-compose.optimized.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.optimized
    container_name: ai-news-backend
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - MALLOC_ARENA_MAX=2
    env_file:
      - .env
    volumes:
      - backend_logs:/app/logs
    networks:
      - app_network
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 60s

  redis:
    image: redis:7-alpine
    container_name: ai-news-redis
    restart: unless-stopped
    command: >
      redis-server 
      --maxmemory 1gb
      --maxmemory-policy allkeys-lru
      --tcp-keepalive 300
      --timeout 300
    volumes:
      - redis_data:/data
    networks:
      - app_network
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "5m"
        max-file: "2"

  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.optimized
    container_name: ai-news-celery
    restart: unless-stopped
    command: celery -A celery_app worker --loglevel=info --concurrency=4
    environment:
      - C_FORCE_ROOT=0
      - PYTHONUNBUFFERED=1
    env_file:
      - .env
    volumes:
      - celery_logs:/var/log/celery
      - backend_logs:/app/logs
    networks:
      - app_network
    depends_on:
      - redis
      - backend
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  backend_logs:
    driver: local
  celery_logs:
    driver: local
  redis_data:
    driver: local

networks:
  app_network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
      com.docker.network.driver.mtu: "1500"
```

### 3. Docker Swarm Optimization

```yaml
# docker-stack.yml
version: '3.8'

services:
  backend:
    image: ai-news-aggregator/backend:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    secrets:
      - source: app_env
        target: /app/.env
    configs:
      - source: nginx_config
        target: /etc/nginx/nginx.conf
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 30s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

secrets:
  app_env:
    external: true

configs:
  nginx_config:
    external: true
```

## Optimización de Sistema

### 1. Kernel Parameters

```bash
# /etc/sysctl.d/99-performance.conf

# Network performance
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr

# File system performance
fs.file-max = 2097152
fs.nr_open = 1048576
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.swappiness = 10
vm.vfs_cache_pressure = 50

# Memory management
vm.overcommit_memory = 1
vm.overcommit_ratio = 50

# CPU performance
kernel.sched_min_granularity_ns = 10000000
kernel.sched_wakeup_granularity_ns = 15000000
kernel.sched_migration_cost_ns = 5000000

# Apply settings
sysctl -p /etc/sysctl.d/99-performance.conf
```

### 2. System Monitoring

```bash
#!/bin/bash
# system-performance-monitor.sh

LOG_FILE="/var/log/performance-monitor.log"

monitor_system_performance() {
    echo "$(date) - System Performance Report" >> "$LOG_FILE"
    
    # CPU usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    echo "CPU Usage: ${cpu_usage}%" >> "$LOG_FILE"
    
    # Memory usage
    memory=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    echo "Memory Usage: $memory" >> "$LOG_FILE"
    
    # Disk I/O
    iostat -x 1 1 | tail -n +4 | awk '{print $4, $5}' | head -1 >> "$LOG_FILE"
    
    # Network usage
    network_stats=$(cat /proc/net/dev | grep eth0)
    echo "Network: $network_stats" >> "$LOG_FILE"
    
    # Load average
    load_avg=$(uptime | awk -F'load average:' '{print $2}')
    echo "Load Average: $load_avg" >> "$LOG_FILE"
    
    # Database connections
    db_connections=$(psql -h database_host -U postgres -d ai_news_aggregator -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null)
    echo "DB Connections: $db_connections" >> "$LOG_FILE"
    
    # Redis stats
    redis_stats=$(redis-cli -h redis_host info stats | grep -E "connected_clients|total_commands_processed" 2>/dev/null)
    echo "Redis Stats: $redis_stats" >> "$LOG_FILE"
    
    echo "----------------------------------------" >> "$LOG_FILE"
}

# Run every minute
*/1 * * * * /path/to/system-performance-monitor.sh
```

## Load Testing

### 1. Apache Bench Scripts

```bash
#!/bin/bash
# load-test.sh

BASE_URL="https://yourdomain.com"
RESULTS_DIR="/tmp/load-test-results"

mkdir -p "$RESULTS_DIR"

echo "🔥 Iniciando load testing..."

# Test 1: Homepage load
echo "Testing homepage..."
ab -n 1000 -c 10 -H "Accept-Encoding: gzip" \
   "$BASE_URL/" > "$RESULTS_DIR/homepage_10c_1000n.txt"

# Test 2: API endpoints
echo "Testing API health endpoint..."
ab -n 5000 -c 50 -H "Accept-Encoding: gzip" \
   "$BASE_URL/api/health" > "$RESULTS_DIR/api_health_50c_5000n.txt"

# Test 3: Articles endpoint
echo "Testing articles endpoint..."
ab -n 2000 -c 20 -H "Accept-Encoding: gzip" \
   "$BASE_URL/api/articles?limit=20" > "$RESULTS_DIR/articles_20c_2000n.txt"

# Test 4: Search endpoint
echo "Testing search endpoint..."
ab -n 1000 -c 10 -H "Accept-Encoding: gzip" \
   -p search-data.json -T "application/json" \
   "$BASE_URL/api/search" > "$RESULTS_DIR/search_10c_1000n.txt"

# Generate report
echo "Generating performance report..."
python3 /path/to/generate-load-test-report.py "$RESULTS_DIR"

echo "✅ Load testing completed"
```

### 2. Artillery Configuration

```yaml
# load-test-artillery.yml
config:
  target: 'https://yourdomain.com'
  phases:
    - duration: 60
      arrivalRate: 10
    - duration: 120
      arrivalRate: 20
    - duration: 300
      arrivalRate: 50
    - duration: 60
      arrivalRate: 0
  defaults:
    headers:
      User-Agent: 'Artillery Load Test'

scenarios:
  - name: "Homepage test"
    weight: 30
    flow:
      - get:
          url: "/"
          expect:
            - statusCode: 200
            - contentType: html

  - name: "API Health check"
    weight: 20
    flow:
      - get:
          url: "/api/health"
          expect:
            - statusCode: 200
            - hasProperty: "status"

  - name: "Articles endpoint"
    weight: 25
    flow:
      - get:
          url: "/api/articles?limit=20"
          expect:
            - statusCode: 200

  - name: "Search endpoint"
    weight: 15
    flow:
      - post:
          url: "/api/search"
          json:
            query: "artificial intelligence"
            limit: 10
          expect:
            - statusCode: 200

  - name: "Article detail"
    weight: 10
    flow:
      - get:
          url: "/api/articles/1"
          expect:
            - statusCode: 200
```

### 3. Custom Load Test Tool

```python
# performance/load_test.py
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
import json

class LoadTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
    
    async def create_session(self):
        """Crear sesión HTTP"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'AI News Aggregator Load Test'}
        )
    
    async def test_endpoint(self, endpoint: str, method: str = 'GET', data: Dict = None) -> Dict[str, Any]:
        """Testear un endpoint específico"""
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    content = await response.text()
                    duration = time.time() - start_time
                    
                    return {
                        'endpoint': endpoint,
                        'method': method,
                        'status_code': response.status,
                        'duration': duration,
                        'content_length': len(content),
                        'success': response.status < 400
                    }
            
            elif method.upper() == 'POST':
                async with self.session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    content = await response.text()
                    duration = time.time() - start_time
                    
                    return {
                        'endpoint': endpoint,
                        'method': method,
                        'status_code': response.status,
                        'duration': duration,
                        'content_length': len(content),
                        'success': response.status < 400
                    }
        
        except Exception as e:
            duration = time.time() - start_time
            return {
                'endpoint': endpoint,
                'method': method,
                'error': str(e),
                'duration': duration,
                'success': False
            }
    
    async def run_load_test(self, endpoints: List[Dict], concurrent_users: int, duration: int) -> Dict[str, Any]:
        """Ejecutar test de carga"""
        await self.create_session()
        
        print(f"🚀 Starting load test: {concurrent_users} users, {duration} seconds")
        
        start_time = time.time()
        results = []
        
        # Crear tareas para usuarios concurrentes
        tasks = []
        for _ in range(concurrent_users):
            for _ in range(duration):  # Ejecutar durante duración especificada
                endpoint_config = endpoints[_ % len(endpoints)]
                task = self.test_endpoint(
                    endpoint_config['endpoint'],
                    endpoint_config.get('method', 'GET'),
                    endpoint_config.get('data')
                )
                tasks.append(task)
        
        # Ejecutar todas las tareas
        print(f"Running {len(tasks)} requests...")
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Procesar resultados
        for result in batch_results:
            if isinstance(result, dict):
                results.append(result)
        
        # Generar estadísticas
        stats = self.generate_statistics(results, total_duration)
        
        await self.session.close()
        
        return stats
    
    def generate_statistics(self, results: List[Dict], total_duration: float) -> Dict[str, Any]:
        """Generar estadísticas del test"""
        successful_results = [r for r in results if r.get('success', False)]
        failed_results = [r for r in results if not r.get('success', True)]
        
        if successful_results:
            durations = [r['duration'] for r in successful_results]
            status_codes = [r.get('status_code') for r in successful_results]
            
            return {
                'total_requests': len(results),
                'successful_requests': len(successful_results),
                'failed_requests': len(failed_results),
                'success_rate': len(successful_results) / len(results) * 100,
                'total_duration': total_duration,
                'requests_per_second': len(results) / total_duration,
                'response_times': {
                    'mean': statistics.mean(durations),
                    'median': statistics.median(durations),
                    'p95': self.percentile(durations, 95),
                    'p99': self.percentile(durations, 99),
                    'min': min(durations),
                    'max': max(durations)
                },
                'status_codes': dict(statistics.Counter(status_codes)),
                'errors': [r.get('error') for r in failed_results if r.get('error')]
            }
        else:
            return {
                'total_requests': len(results),
                'successful_requests': 0,
                'failed_requests': len(results),
                'success_rate': 0,
                'error': 'No successful requests'
            }
    
    def percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil"""
        sorted_data = sorted(data)
        index = (percentile / 100) * len(sorted_data)
        if index.is_integer():
            return sorted_data[int(index) - 1]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

# Uso del LoadTester
async def run_comprehensive_load_test():
    tester = LoadTester("https://yourdomain.com")
    
    endpoints = [
        {'endpoint': '/', 'method': 'GET'},
        {'endpoint': '/api/health', 'method': 'GET'},
        {'endpoint': '/api/articles?limit=20', 'method': 'GET'},
        {'endpoint': '/api/search', 'method': 'POST', 'data': {'query': 'AI', 'limit': 10}},
        {'endpoint': '/api/categories', 'method': 'GET'},
        {'endpoint': '/api/sources', 'method': 'GET'},
    ]
    
    # Test con diferentes configuraciones
    test_configs = [
        {'concurrent_users': 10, 'duration': 60},
        {'concurrent_users': 25, 'duration': 120},
        {'concurrent_users': 50, 'duration': 180},
    ]
    
    all_results = {}
    
    for config in test_configs:
        print(f"\n🧪 Testing with {config['concurrent_users']} users for {config['duration']} seconds...")
        
        result = await tester.run_load_test(
            endpoints,
            config['concurrent_users'],
            config['duration']
        )
        
        all_results[f"{config['concurrent_users']}users"] = result
        
        # Imprimir resultados clave
        print(f"✅ Completed:")
        print(f"  - Success Rate: {result['success_rate']:.2f}%")
        print(f"  - RPS: {result['requests_per_second']:.2f}")
        print(f"  - Response Time (p95): {result['response_times']['p95']:.3f}s")
    
    return all_results

if __name__ == "__main__":
    results = asyncio.run(run_comprehensive_load_test())
    
    # Guardar resultados
    with open('/tmp/load_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n📊 Load test completed. Results saved to /tmp/load_test_results.json")
```

## Monitoring de Performance

### 1. Custom Metrics

```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
import psutil
import time
from typing import Dict, Any

# Registry personalizado
custom_registry = CollectorRegistry()

# Métricas de aplicación
REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['method', 'endpoint', 'status'], registry=custom_registry)
REQUEST_DURATION = Histogram('app_request_duration_seconds', 'Request duration', ['method', 'endpoint'], registry=custom_registry)
ACTIVE_USERS = Gauge('app_active_users', 'Active users', registry=custom_registry)
CACHE_HIT_RATIO = Gauge('app_cache_hit_ratio', 'Cache hit ratio', ['cache_name'], registry=custom_registry)

# Métricas de sistema
SYSTEM_CPU_USAGE = Gauge('system_cpu_usage_percent', 'CPU usage', registry=custom_registry)
SYSTEM_MEMORY_USAGE = Gauge('system_memory_usage_percent', 'Memory usage', registry=custom_registry)
SYSTEM_DISK_USAGE = Gauge('system_disk_usage_percent', 'Disk usage', registry=custom_registry)
SYSTEM_NETWORK_IO = Gauge('system_network_io_bytes', 'Network I/O', ['direction'], registry=custom_registry)

# Métricas de base de datos
DB_CONNECTIONS_ACTIVE = Gauge('db_connections_active', 'Active DB connections', registry=custom_registry)
DB_QUERY_TIME = Histogram('db_query_duration_seconds', 'DB query duration', ['query_type'], registry=custom_registry)
DB_SLOW_QUERIES = Counter('db_slow_queries_total', 'Slow queries', ['query_type'], registry=custom_registry)

# Métricas de API externa
EXTERNAL_API_REQUESTS = Counter('external_api_requests_total', 'External API requests', ['api', 'status'], registry=custom_registry)
EXTERNAL_API_DURATION = Histogram('external_api_duration_seconds', 'External API duration', ['api'], registry=custom_registry)

class MetricsCollector:
    """Colector de métricas personalizadas"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.last_network = None
    
    def collect_system_metrics(self):
        """Recopilar métricas del sistema"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            SYSTEM_CPU_USAGE.set(cpu_percent)
            
            # Memory
            memory = psutil.virtual_memory()
            SYSTEM_MEMORY_USAGE.set(memory.percent)
            
            # Disk
            disk = psutil.disk_usage('/')
            SYSTEM_DISK_USAGE.set((disk.used / disk.total) * 100)
            
            # Network I/O
            network_io = psutil.net_io_counters()
            if self.last_network:
                bytes_sent_per_sec = network_io.bytes_sent - self.last_network.bytes_sent
                bytes_recv_per_sec = network_io.bytes_recv - self.last_network.bytes_recv
                SYSTEM_NETWORK_IO.labels(direction='sent').set(bytes_sent_per_sec)
                SYSTEM_NETWORK_IO.labels(direction='recv').set(bytes_recv_per_sec)
            
            self.last_network = network_io
            
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
    
    def collect_business_metrics(self):
        """Recopilar métricas de negocio"""
        # Estas métricas dependen de la lógica de negocio específica
        # Implementar según las necesidades de la aplicación
        
        # Ejemplo: Contar usuarios activos
        # active_user_count = get_active_user_count()
        # ACTIVE_USERS.set(active_user_count)
        
        pass
    
    def collect_all_metrics(self):
        """Recopilar todas las métricas"""
        self.collect_system_metrics()
        self.collect_business_metrics()
    
    def get_metrics(self):
        """Obtener todas las métricas"""
        self.collect_all_metrics()
        return generate_latest(custom_registry)

# Instancia global
metrics_collector = MetricsCollector()

# Endpoint para métricas
async def metrics_endpoint():
    """Endpoint para Prometheus"""
    return metrics_collector.get_metrics()
```

### 2. Performance Alerting

```yaml
# performance-alerts.yml
groups:
- name: ai-news-performance
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(app_request_duration_seconds_bucket[5m])) > 1.0
    for: 5m
    labels:
      severity: warning
      team: backend
    annotations:
      summary: "High response time detected"
      description: "95th percentile response time is {{ $value }}s, threshold is 1.0s"
      action: "Check slow queries and optimize database indexes"

  - alert: HighErrorRate
    expr: rate(app_requests_total{status=~"5.."}[5m]) / rate(app_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: critical
      team: backend
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value | humanizePercentage }}"
      action: "Check application logs and investigate root cause"

  - alert: DatabaseConnectionsNearLimit
    expr: db_connections_active / 200 > 0.9
    for: 5m
    labels:
      severity: warning
      team: database
    annotations:
      summary: "Database connections near limit"
      description: "Active connections: {{ $value }}, limit: 200"
      action: "Check for connection leaks and optimize connection pooling"

  - alert: CacheHitRatioLow
    expr: app_cache_hit_ratio < 0.8
    for: 10m
    labels:
      severity: warning
      team: backend
    annotations:
      summary: "Cache hit ratio is low"
      description: "Cache hit ratio: {{ $value | humanizePercentage }}"
      action: "Review cache strategy and warm frequently accessed data"

  - alert: SystemResourcesHigh
    expr: system_cpu_usage_percent > 80 or system_memory_usage_percent > 85
    for: 5m
    labels:
      severity: warning
      team: infrastructure
    annotations:
      summary: "High system resource usage"
      description: "CPU: {{ $labels.system_cpu_usage_percent }}%, Memory: {{ $labels.system_memory_usage_percent }}%"
      action: "Consider scaling horizontally or optimizing resource usage"

  - alert: ExternalAPISlow
    expr: rate(external_api_duration_seconds_sum[5m]) / rate(external_api_duration_seconds_count[5m]) > 2.0
    for: 10m
    labels:
      severity: warning
      team: backend
    annotations:
      summary: "External API is responding slowly"
      description: "Average response time: {{ $value }}s"
      action: "Check external API status and consider implementing circuit breaker"
```

---

**Nota**: Esta guía debe ser utilizada como referencia para optimización continua. Monitorea regularmente las métricas y ajusta las configuraciones según las necesidades de tu aplicación específica.