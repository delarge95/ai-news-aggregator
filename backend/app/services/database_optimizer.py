"""
Sistema de optimización de consultas SQLAlchemy para AI News Aggregator

Optimizaciones implementadas:
- Eager loading inteligente (selectinload, joinedload)
- Paginación eficiente con cursor-based pagination
- Cache de consultas frecuentes con TTL
- Materialización de vistas complejas
- Índices compuestos optimizados
- Métricas de performance y monitoring
- Logging automático de consultas lentas
- Query plan optimization
"""

import asyncio
import functools
import hashlib
import json
import logging
import time
import weakref
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import (
    and_, or_, text, func, select, update, delete, insert,
    Index, UniqueConstraint, event, inspect
)
from sqlalchemy.orm import (
    Session, query, joinedload, selectinload, subqueryload,
    lazyload, immediate, defer, undefer, Load
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.engine.result import Result
from sqlalchemy.orm.query import Query
from sqlalchemy.dialects.postgresql import UUID
import redis
from redis.exceptions import RedisError

# Configuración de logging
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Tipos de consultas para optimización"""
    LIST_ARTICLES = "list_articles"
    SEARCH_ARTICLES = "search_articles"
    GET_TRENDING = "get_trending"
    DASHBOARD_STATS = "dashboard_stats"
    USER_PREFERENCES = "user_preferences"
    ANALYSIS_RESULTS = "analysis_results"
    SOURCE_PERFORMANCE = "source_performance"
    DUPLICATE_DETECTION = "duplicate_detection"


@dataclass
class PerformanceMetrics:
    """Métricas de performance para consultas"""
    query_time_ms: float
    rows_returned: int
    cache_hit: bool
    optimization_used: str
    execution_plan: Optional[str] = None
    query_type: Optional[QueryType] = None
    timestamp: Optional[datetime] = None


@dataclass
class CacheStats:
    """Estadísticas del sistema de cache"""
    hits: int = 0
    misses: int = 0
    hit_ratio: float = 0.0
    memory_usage: int = 0
    items_cached: int = 0


class QueryCache:
    """Sistema de cache de consultas con TTL y invalidación inteligente"""
    
    def __init__(self, redis_client: redis.Redis, default_ttl: int = 300):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.memory_cache = {}
        self.access_times = OrderedDict()
        self.max_memory_items = 1000
        self._query_stats = defaultdict(int)
        
    def _make_key(self, query_hash: str, query_type: QueryType, params: dict) -> str:
        """Genera clave única para la consulta"""
        key_data = {
            "hash": query_hash,
            "type": query_type.value,
            "params": sorted(params.items())
        }
        return f"query_cache:{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"
    
    def _hash_query(self, query: Union[str, Query]) -> str:
        """Genera hash de la consulta"""
        if isinstance(query, str):
            return hashlib.md5(query.encode()).hexdigest()
        else:
            # Para consultas SQLAlchemy, generamos hash basado en componentes
            query_str = str(query.statement.compile(
                compile_kwargs={"literal_binds": True}
            ))
            return hashlib.md5(query_str.encode()).hexdigest()
    
    def get(self, query: Union[str, Query], query_type: QueryType, params: dict = None) -> Optional[Any]:
        """Obtiene resultado del cache"""
        if params is None:
            params = {}
            
        query_hash = self._hash_query(query)
        cache_key = self._make_key(query_hash, query_type, params)
        
        # Primero intenta cache de memoria (más rápido)
        if cache_key in self.memory_cache:
            self.access_times[cache_key] = time.time()
            return self.memory_cache[cache_key]
        
        # Luego intenta Redis
        try:
            cached_result = self.redis.get(cache_key)
            if cached_result:
                result = json.loads(cached_result)
                # Promote to memory cache
                self._promote_to_memory(cache_key, result)
                return result
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Error accessing Redis cache: {e}")
        
        return None
    
    def set(self, query: Union[str, Query], result: Any, query_type: QueryType, 
            params: dict = None, ttl: int = None) -> bool:
        """Guarda resultado en cache"""
        if params is None:
            params = {}
        if ttl is None:
            ttl = self.default_ttl
            
        query_hash = self._hash_query(query)
        cache_key = self._make_key(query_hash, query_type, params)
        
        # Intenta guardar en Redis primero
        try:
            serialized_result = json.dumps(result, default=str)
            if self.redis.setex(cache_key, ttl, serialized_result):
                # Promover a cache de memoria para acceso rápido
                self._promote_to_memory(cache_key, result)
                return True
        except (RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Error saving to Redis cache: {e}")
        
        # Fallback a cache de memoria
        return self._save_to_memory(cache_key, result)
    
    def _promote_to_memory(self, cache_key: str, result: Any):
        """Promueve resultado a cache de memoria"""
        if len(self.memory_cache) >= self.max_memory_items:
            # Remove oldest item
            oldest_key = next(iter(self.access_times))
            self._remove_from_memory(oldest_key)
        
        self.memory_cache[cache_key] = result
        self.access_times[cache_key] = time.time()
    
    def _save_to_memory(self, cache_key: str, result: Any) -> bool:
        """Guarda en cache de memoria"""
        try:
            if len(self.memory_cache) >= self.max_memory_items:
                # Remove oldest items
                while len(self.memory_cache) >= self.max_memory_items:
                    oldest_key = next(iter(self.access_times))
                    self._remove_from_memory(oldest_key)
            
            self.memory_cache[cache_key] = result
            self.access_times[cache_key] = time.time()
            return True
        except Exception as e:
            logger.warning(f"Error saving to memory cache: {e}")
            return False
    
    def _remove_from_memory(self, cache_key: str):
        """Remueve item del cache de memoria"""
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        if cache_key in self.access_times:
            del self.access_times[cache_key]
    
    def invalidate_pattern(self, pattern: str):
        """Invalida cache que coincida con el patrón"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except RedisError as e:
            logger.warning(f"Error invalidating cache pattern: {e}")
    
    def get_stats(self) -> CacheStats:
        """Obtiene estadísticas del cache"""
        # Implementación simplificada - en producción would be more sophisticated
        return CacheStats(
            hits=0,  # Would track these
            misses=0,
            hit_ratio=0.0,
            memory_usage=len(self.memory_cache) * 100,  # Estimated
            items_cached=len(self.memory_cache)
        )


class MaterializedViewManager:
    """Gestor de vistas materializadas para consultas complejas"""
    
    def __init__(self, engine):
        self.engine = engine
        self.views = {}
        self.refresh_intervals = {}
    
    def create_article_statistics_view(self):
        """Crea vista materializada de estadísticas de artículos"""
        view_sql = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS article_statistics AS
        SELECT 
            s.id as source_id,
            s.name as source_name,
            COUNT(a.id) as total_articles,
            COUNT(CASE WHEN a.processing_status = 'completed' THEN 1 END) as processed_articles,
            AVG(a.sentiment_score) as avg_sentiment,
            AVG(a.relevance_score) as avg_relevance,
            MAX(a.published_at) as last_article_date,
            COUNT(CASE WHEN a.created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as articles_last_24h
        FROM sources s
        LEFT JOIN articles a ON s.id = a.source_id
        GROUP BY s.id, s.name;
        
        CREATE INDEX IF NOT EXISTS idx_article_statistics_source_id ON article_statistics(source_id);
        CREATE INDEX IF NOT EXISTS idx_article_statistics_last_article ON article_statistics(last_article_date);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(view_sql))
            conn.commit()
    
    def create_trending_topics_view(self):
        """Crea vista materializada de temas en tendencia"""
        view_sql = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS trending_topics_detailed AS
        SELECT 
            topic,
            topic_category,
            COUNT(*) as article_count,
            COUNT(DISTINCT source_id) as sources_count,
            AVG(relevance_score) as avg_relevance,
            AVG(sentiment_score) as avg_sentiment,
            array_agg(DISTINCT tags.tag) as all_tags
        FROM articles a
        CROSS JOIN LATERAL jsonb_array_elements_text(a.topic_tags) as topic_tags(tag)
        WHERE a.created_at > NOW() - INTERVAL '7 days'
        GROUP BY topic, topic_category
        ORDER BY article_count DESC;
        
        CREATE INDEX IF NOT EXISTS idx_trending_topics_detailed_category ON trending_topics_detailed(topic_category);
        CREATE INDEX IF NOT EXISTS idx_trending_topics_detailed_article_count ON trending_topics_detailed(article_count DESC);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(view_sql))
            conn.commit()
    
    def create_daily_metrics_view(self):
        """Crea vista materializada de métricas diarias"""
        view_sql = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metrics AS
        SELECT 
            DATE_TRUNC('day', created_at) as metric_date,
            COUNT(*) as articles_created,
            COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as articles_processed,
            COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as articles_failed,
            AVG(relevance_score) as avg_relevance_score,
            AVG(sentiment_score) as avg_sentiment_score
        FROM articles
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', created_at)
        ORDER BY metric_date DESC;
        
        CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(metric_date DESC);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(view_sql))
            conn.commit()
    
    def refresh_view(self, view_name: str, concurrently: bool = False):
        """Actualiza una vista materializada"""
        sql = f"REFRESH MATERIALIZED VIEW {'CONCURRENTLY' if concurrently else ''} {view_name}"
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Refreshed materialized view: {view_name}")
        except Exception as e:
            logger.error(f"Error refreshing view {view_name}: {e}")
    
    def schedule_refresh(self, view_name: str, interval_minutes: int):
        """Programa actualización automática de vista"""
        self.refresh_intervals[view_name] = interval_minutes
    
    def refresh_all_views(self):
        """Actualiza todas las vistas programadas"""
        for view_name, interval in self.refresh_intervals.items():
            self.refresh_view(view_name)


class IndexOptimizer:
    """Optimizador de índices de base de datos"""
    
    def __init__(self, engine):
        self.engine = engine
        self.performance_stats = defaultdict(list)
    
    def create_optimized_indexes(self):
        """Crea índices optimizados para las consultas principales"""
        
        # Índices compuestos para búsquedas frecuentes
        compound_indexes = [
            # Para búsqueda de artículos por fecha y fuente
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_source_date ON articles(source_id, published_at DESC) WHERE published_at IS NOT NULL",
            
            # Para filtrado por sentimiento y relevancia
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_sentiment_relevance ON articles(sentiment_label, relevance_score DESC) WHERE sentiment_label IS NOT NULL",
            
            # Para análisis de tendencias
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_created_processing ON articles(created_at, processing_status) WHERE created_at > NOW() - INTERVAL '30 days'",
            
            # Para detección de duplicados
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_hash_status ON articles(content_hash, processing_status) WHERE content_hash IS NOT NULL",
            
            # Para tareas de análisis
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analysis_tasks_status_priority ON analysis_tasks(status, priority, scheduled_at) WHERE status = 'pending'",
            
            # Para trending topics
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trending_topics_category_date ON trending_topics(topic_category, date_recorded DESC, trend_score DESC)",
            
            # Índice de texto completo para búsquedas en títulos y contenido
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_fts ON articles USING gin(to_tsvector('english', title || ' ' || COALESCE(content, '')))",
            
            # Para consultas de rendimiento de fuentes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sources_api_active ON sources(api_name, is_active, credibility_score DESC) WHERE is_active = true",
            
            # Para análisis de resultados por fecha
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_article_analysis_type_date ON article_analysis(analysis_type, processed_at DESC) WHERE processed_at > NOW() - INTERVAL '7 days'"
        ]
        
        with self.engine.connect() as conn:
            for index_sql in compound_indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"Created optimized index: {index_sql[:50]}...")
                except Exception as e:
                    logger.warning(f"Error creating index: {e}")
            conn.commit()
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analiza el performance de una consulta"""
        try:
            with self.engine.connect() as conn:
                # Obtiene plan de ejecución
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                result = conn.execute(text(explain_query))
                plan_data = result.fetchone()[0]
                
                # Extrae métricas clave
                execution_time = plan_data[0]['Execution Time']
                planning_time = plan_data[0]['Planning Time']
                total_cost = plan_data[0]['Plan']['Total Cost']
                rows = plan_data[0]['Plan']['Plan Rows']
                
                return {
                    'execution_time_ms': execution_time,
                    'planning_time_ms': planning_time,
                    'total_cost': total_cost,
                    'estimated_rows': rows,
                    'query_plan': plan_data
                }
        except Exception as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {}


class PerformanceMonitor:
    """Monitor de performance de consultas con alertas"""
    
    def __init__(self, slow_query_threshold_ms: float = 1000):
        self.slow_query_threshold = slow_query_threshold_ms
        self.query_metrics = defaultdict(list)
        self.slow_queries = []
        
    def record_query(self, query: str, metrics: PerformanceMetrics):
        """Registra métricas de una consulta"""
        self.query_metrics[metrics.query_type].append(metrics)
        
        # Alertas para consultas lentas
        if metrics.query_time_ms > self.slow_query_threshold:
            self.slow_queries.append({
                'query': query[:200],  # Truncate para logging
                'execution_time': metrics.query_time_ms,
                'timestamp': metrics.timestamp or datetime.utcnow(),
                'query_type': metrics.query_type
            })
            
            logger.warning(
                f"Slow query detected ({metrics.query_time_ms:.2f}ms): "
                f"{query[:100]}... (Type: {metrics.query_type})"
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de performance"""
        summary = {}
        
        for query_type, metrics_list in self.query_metrics.items():
            if metrics_list:
                times = [m.query_time_ms for m in metrics_list]
                summary[query_type.value] = {
                    'total_queries': len(metrics_list),
                    'avg_time_ms': sum(times) / len(times),
                    'max_time_ms': max(times),
                    'min_time_ms': min(times),
                    'cache_hit_ratio': sum(1 for m in metrics_list if m.cache_hit) / len(metrics_list)
                }
        
        return summary
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene las consultas más lentas"""
        return sorted(self.slow_queries, key=lambda x: x['execution_time'], reverse=True)[:limit]


class OptimizedQueryBuilder:
    """Constructor de consultas optimizadas con eager loading inteligente"""
    
    def __init__(self):
        self._eager_loaders = {
            'articles': {
                'source': joinedload('source'),
                'analysis_results': selectinload('analysis_results')
            }
        }
    
    def build_articles_list_query(self, session: Session, filters: Dict[str, Any], 
                                pagination: Dict[str, Any]) -> Query:
        """Construye consulta optimizada para listado de artículos"""
        from ..db.models import Article, Source, ArticleAnalysis
        
        # Consulta base con joins optimizados
        query = session.query(Article).options(
            joinedload(Article.source),
            selectinload(Article.analysis_results),
            defer(Article.content),  # Contenido grande, solo cuando sea necesario
            defer(Article.summary)   # Se puede cargar después
        )
        
        # Aplicar filtros
        if filters.get('source_ids'):
            query = query.filter(Article.source_id.in_(filters['source_ids']))
        
        if filters.get('sentiment'):
            query = query.filter(Article.sentiment_label == filters['sentiment'])
        
        if filters.get('date_from'):
            query = query.filter(Article.published_at >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(Article.published_at <= filters['date_to'])
        
        if filters.get('min_relevance'):
            query = query.filter(Article.relevance_score >= filters['min_relevance'])
        
        if filters.get('processing_status'):
            query = query.filter(Article.processing_status == filters['processing_status'])
        
        # Ordenamiento optimizado
        sort_by = filters.get('sort_by', 'published_at')
        sort_order = filters.get('sort_order', 'desc')
        
        if sort_by == 'relevance':
            sort_column = Article.relevance_score
        elif sort_by == 'sentiment':
            sort_column = Article.sentiment_score
        else:
            sort_column = Article.published_at
        
        if sort_order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Paginación
        if pagination.get('limit'):
            query = query.limit(pagination['limit'])
        if pagination.get('offset'):
            query = query.offset(pagination['offset'])
        
        return query
    
    def build_cursor_pagination_query(self, session: Session, filters: Dict[str, Any], 
                                    cursor: Optional[str], limit: int) -> Query:
        """Construye consulta con cursor-based pagination"""
        from ..db.models import Article
        
        query = session.query(Article).options(
            joinedload(Article.source)
        )
        
        # Aplicar filtros
        query = self._apply_filters(query, Article, filters)
        
        # Cursor-based pagination
        if cursor:
            try:
                # Decodificar cursor (contiene ID y fecha del último elemento)
                cursor_data = json.loads(cursor)
                last_id = cursor_data.get('id')
                last_date = cursor_data.get('date')
                
                if last_id and last_date:
                    query = query.filter(
                        or_(
                            Article.published_at < last_date,
                            and_(
                                Article.published_at == last_date,
                                Article.id < last_id
                            )
                        )
                    )
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Ordenamiento consistente para cursor pagination
        query = query.order_by(
            Article.published_at.desc(),
            Article.id.desc()
        ).limit(limit)
        
        return query
    
    def build_search_query(self, session: Session, search_term: str, 
                          filters: Dict[str, Any], pagination: Dict[str, Any]) -> Query:
        """Construye consulta de búsqueda optimizada"""
        from ..db.models import Article, Source
        
        query = session.query(Article).options(
            joinedload(Article.source),
            undefer(Article.title)  # Necesario para búsqueda de texto
        )
        
        # Búsqueda de texto completo
        if search_term:
            # Usar texto completo en PostgreSQL
            query = query.filter(
                func.to_tsvector('english', Article.title + ' ' + Article.content).op('@@')(
                    func.plainto_tsquery('english', search_term)
                )
            )
        
        # Aplicar filtros adicionales
        query = self._apply_filters(query, Article, filters)
        
        # Ordenamiento para búsqueda (relevance first)
        sort_by = filters.get('sort_by', 'relevance')
        if sort_by == 'relevance':
            query = query.order_by(
                func.ts_rank(
                    func.to_tsvector('english', Article.title + ' ' + Article.content),
                    func.plainto_tsquery('english', search_term)
                ).desc(),
                Article.published_at.desc()
            )
        else:
            query = query.order_by(Article.published_at.desc())
        
        # Paginación
        if pagination.get('limit'):
            query = query.limit(pagination['limit'])
        if pagination.get('offset'):
            query = query.offset(pagination['offset'])
        
        return query
    
    def _apply_filters(self, query, model, filters: Dict[str, Any]):
        """Aplica filtros a la consulta"""
        if filters.get('source_ids'):
            query = query.filter(model.source_id.in_(filters['source_ids']))
        
        if filters.get('sentiment'):
            query = query.filter(model.sentiment_label == filters['sentiment'])
        
        if filters.get('date_from'):
            query = query.filter(model.published_at >= filters['date_from'])
        
        if filters.get('date_to'):
            query = query.filter(model.published_at <= filters['date_to'])
        
        if filters.get('min_relevance'):
            query = query.filter(model.relevance_score >= filters['min_relevance'])
        
        return query


class DatabaseOptimizer:
    """Clase principal del optimizador de base de datos"""
    
    def __init__(self, redis_client: redis.Redis, engine):
        self.redis = redis_client
        self.engine = engine
        self.cache = QueryCache(redis_client)
        self.view_manager = MaterializedViewManager(engine)
        self.index_optimizer = IndexOptimizer(engine)
        self.performance_monitor = PerformanceMonitor()
        self.query_builder = OptimizedQueryBuilder()
        
        # Configurar logging de consultas SQL
        self._setup_sql_logging()
        
        logger.info("Database Optimizer initialized")
    
    def _setup_sql_logging(self):
        """Configura el logging de consultas SQL"""
        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if hasattr(context, '_query_start_time'):
                execution_time = (time.time() - context._query_start_time) * 1000
                
                # Solo log de consultas que exceden el umbral
                if execution_time > 100:  # 100ms
                    logger.info(f"Slow query ({execution_time:.2f}ms): {statement[:100]}...")
    
    def optimize_articles_list(self, session: Session, filters: Dict[str, Any], 
                             pagination: Dict[str, Any]) -> Tuple[List, Dict[str, Any]]:
        """Optimiza listado de artículos con cache y eager loading"""
        start_time = time.time()
        
        # Generar parámetros de cache
        cache_key_params = {
            'filters': filters,
            'pagination': pagination
        }
        
        # Intentar obtener del cache
        cached_result = self.cache.get(
            "articles_list", 
            QueryType.LIST_ARTICLES, 
            cache_key_params
        )
        
        if cached_result:
            self.performance_monitor.record_query(
                "articles_list",
                PerformanceMetrics(
                    query_time_ms=(time.time() - start_time) * 1000,
                    rows_returned=len(cached_result['articles']),
                    cache_hit=True,
                    optimization_used="cache",
                    query_type=QueryType.LIST_ARTICLES
                )
            )
            return cached_result['articles'], cached_result['metadata']
        
        # Construir consulta optimizada
        query = self.query_builder.build_articles_list_query(session, filters, pagination)
        
        # Ejecutar consulta
        articles = query.all()
        
        # Generar metadatos de paginación
        total_count = session.query(func.count(Article.id)).filter(
            *self._build_filter_conditions(Article, filters)
        ).scalar()
        
        metadata = {
            'total_count': total_count,
            'page_size': len(articles),
            'has_more': len(articles) == pagination.get('limit', 20),
            'cache_ttl': 300  # 5 minutos
        }
        
        # Guardar en cache
        result = {'articles': articles, 'metadata': metadata}
        self.cache.set(
            "articles_list",
            result,
            QueryType.LIST_ARTICLES,
            cache_key_params
        )
        
        # Registrar métricas
        execution_time = (time.time() - start_time) * 1000
        self.performance_monitor.record_query(
            "articles_list",
            PerformanceMetrics(
                query_time_ms=execution_time,
                rows_returned=len(articles),
                cache_hit=False,
                optimization_used="eager_loading",
                query_type=QueryType.LIST_ARTICLES
            )
        )
        
        return articles, metadata
    
    def optimize_search(self, session: Session, search_term: str, filters: Dict[str, Any], 
                       pagination: Dict[str, Any]) -> Tuple[List, Dict[str, Any]]:
        """Optimiza búsqueda de artículos"""
        start_time = time.time()
        
        cache_params = {
            'search_term': search_term,
            'filters': filters,
            'pagination': pagination
        }
        
        # Verificar cache
        cached_result = self.cache.get(
            "search_articles",
            QueryType.SEARCH_ARTICLES,
            cache_params
        )
        
        if cached_result:
            return cached_result['articles'], cached_result['metadata']
        
        # Construir consulta de búsqueda
        query = self.query_builder.build_search_query(session, search_term, filters, pagination)
        
        # Ejecutar consulta
        articles = query.all()
        
        # Metadatos
        metadata = {
            'search_term': search_term,
            'results_count': len(articles),
            'cache_ttl': 180  # 3 minutos para búsquedas
        }
        
        # Cache result
        result = {'articles': articles, 'metadata': metadata}
        self.cache.set(
            "search_articles",
            result,
            QueryType.SEARCH_ARTICLES,
            cache_params
        )
        
        # Métricas
        execution_time = (time.time() - start_time) * 1000
        self.performance_monitor.record_query(
            "search_articles",
            PerformanceMetrics(
                query_time_ms=execution_time,
                rows_returned=len(articles),
                cache_hit=False,
                optimization_used="full_text_search",
                query_type=QueryType.SEARCH_ARTICLES
            )
        )
        
        return articles, metadata
    
    def get_trending_optimized(self, session: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene temas en tendencia optimizado"""
        start_time = time.time()
        
        cache_key = f"trending_{limit}"
        
        # Intentar obtener del cache
        cached_result = self.cache.get(cache_key, QueryType.GET_TRENDING)
        
        if cached_result:
            return cached_result
        
        # Usar vista materializada si está disponible
        try:
            query = text("""
                SELECT topic, topic_category, article_count, sources_count, 
                       avg_relevance, avg_sentiment, all_tags
                FROM trending_topics_detailed
                WHERE date_recorded > NOW() - INTERVAL '24 hours'
                ORDER BY article_count DESC, trend_score DESC
                LIMIT :limit
            """)
            
            with session.connection() as conn:
                result = conn.execute(query, {'limit': limit})
                trending = [
                    {
                        'topic': row[0],
                        'category': row[1],
                        'article_count': row[2],
                        'sources_count': row[3],
                        'avg_relevance': float(row[4]) if row[4] else 0,
                        'avg_sentiment': float(row[5]) if row[5] else 0,
                        'tags': row[6]
                    }
                    for row in result.fetchall()
                ]
        
        except Exception as e:
            logger.warning(f"Error using materialized view, falling back to regular query: {e}")
            
            # Fallback a consulta regular
            from ..db.models import TrendingTopic
            trending = session.query(TrendingTopic).order_by(
                TrendingTopic.trend_score.desc(),
                TrendingTopic.article_count.desc()
            ).limit(limit).all()
            
            trending = [
                {
                    'topic': t.topic,
                    'category': t.topic_category,
                    'article_count': t.article_count,
                    'sources_count': t.sources_count,
                    'trend_score': t.trend_score,
                    'metadata': t.metadata
                }
                for t in trending
            ]
        
        # Guardar en cache
        self.cache.set(
            cache_key,
            trending,
            QueryType.GET_TRENDING,
            ttl=600  # 10 minutos
        )
        
        # Métricas
        execution_time = (time.time() - start_time) * 1000
        self.performance_monitor.record_query(
            "get_trending",
            PerformanceMetrics(
                query_time_ms=execution_time,
                rows_returned=len(trending),
                cache_hit=False,
                optimization_used="materialized_view",
                query_type=QueryType.GET_TRENDING
            )
        )
        
        return trending
    
    def get_dashboard_stats(self, session: Session) -> Dict[str, Any]:
        """Obtiene estadísticas del dashboard optimizado"""
        start_time = time.time()
        
        # Intentar usar vista materializada
        try:
            query = text("""
                SELECT 
                    DATE_TRUNC('day', metric_date) as date,
                    articles_created,
                    articles_processed,
                    articles_failed,
                    ROUND(avg_relevance_score, 3) as avg_relevance,
                    ROUND(avg_sentiment_score, 3) as avg_sentiment
                FROM daily_metrics
                ORDER BY date DESC
                LIMIT 30
            """)
            
            with session.connection() as conn:
                result = conn.execute(query)
                daily_stats = [
                    {
                        'date': row[0].isoformat(),
                        'articles_created': row[1],
                        'articles_processed': row[2],
                        'articles_failed': row[3],
                        'avg_relevance': row[4],
                        'avg_sentiment': row[5]
                    }
                    for row in result.fetchall()
                ]
        
        except Exception as e:
            logger.warning(f"Error using materialized view for dashboard: {e}")
            
            # Fallback a consultas separadas optimizadas
            from ..db.models import Article, Source, AnalysisTask
            
            # Métricas generales
            total_articles = session.query(func.count(Article.id)).scalar()
            processed_articles = session.query(func.count(Article.id)).filter(
                Article.processing_status == 'completed'
            ).scalar()
            
            recent_articles = session.query(func.count(Article.id)).filter(
                Article.created_at >= datetime.utcnow() - timedelta(days=7)
            ).scalar()
            
            avg_sentiment = session.query(func.avg(Article.sentiment_score)).filter(
                Article.sentiment_score.isnot(None)
            ).scalar()
            
            daily_stats = [
                {
                    'date': datetime.utcnow().isoformat(),
                    'articles_created': total_articles,
                    'articles_processed': processed_articles,
                    'articles_failed': total_articles - processed_articles,
                    'avg_relevance': 0.0,
                    'avg_sentiment': float(avg_sentiment) if avg_sentiment else 0.0
                }
            ]
        
        # Estadísticas de cache
        cache_stats = self.cache.get_stats()
        
        stats = {
            'daily_metrics': daily_stats,
            'cache_stats': {
                'hit_ratio': cache_stats.hit_ratio,
                'memory_usage': cache_stats.memory_usage,
                'items_cached': cache_stats.items_cached
            },
            'performance_summary': self.performance_monitor.get_performance_summary()
        }
        
        # Métricas
        execution_time = (time.time() - start_time) * 1000
        self.performance_monitor.record_query(
            "dashboard_stats",
            PerformanceMetrics(
                query_time_ms=execution_time,
                rows_returned=len(daily_stats),
                cache_hit=False,
                optimization_used="materialized_view",
                query_type=QueryType.DASHBOARD_STATS
            )
        )
        
        return stats
    
    def _build_filter_conditions(self, model, filters: Dict[str, Any]):
        """Construye condiciones de filtro para consultas"""
        from ..db.models import Article
        
        conditions = []
        
        if filters.get('source_ids'):
            conditions.append(Article.source_id.in_(filters['source_ids']))
        
        if filters.get('sentiment'):
            conditions.append(Article.sentiment_label == filters['sentiment'])
        
        if filters.get('date_from'):
            conditions.append(Article.published_at >= filters['date_from'])
        
        if filters.get('date_to'):
            conditions.append(Article.published_at <= filters['date_to'])
        
        if filters.get('min_relevance'):
            conditions.append(Article.relevance_score >= filters['min_relevance'])
        
        if filters.get('processing_status'):
            conditions.append(Article.processing_status == filters['processing_status'])
        
        return conditions
    
    def create_performance_indexes(self):
        """Crea índices optimizados para mejor performance"""
        self.index_optimizer.create_optimized_indexes()
    
    def refresh_materialized_views(self):
        """Actualiza todas las vistas materializadas"""
        self.view_manager.refresh_all_views()
    
    def analyze_slow_queries(self) -> List[Dict[str, Any]]:
        """Analiza las consultas más lentas"""
        return self.performance_monitor.get_slow_queries(20)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Genera reporte completo de performance"""
        return {
            'cache_stats': self.cache.get_stats().__dict__,
            'performance_summary': self.performance_monitor.get_performance_summary(),
            'slow_queries': self.analyze_slow_queries(),
            'query_performance': self.index_optimizer.performance_stats
        }
    
    @contextmanager
    def monitor_query(self, query_type: QueryType, optimization_used: str):
        """Context manager para monitoreo de consultas"""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = (time.time() - start_time) * 1000
            self.performance_monitor.record_query(
                str(query_type),
                PerformanceMetrics(
                    query_time_ms=execution_time,
                    rows_returned=0,
                    cache_hit=False,
                    optimization_used=optimization_used,
                    query_type=query_type,
                    timestamp=datetime.utcnow()
                )
            )


# Función de inicialización
def init_database_optimizer(redis_client: redis.Redis, engine) -> DatabaseOptimizer:
    """Inicializa el optimizador de base de datos"""
    optimizer = DatabaseOptimizer(redis_client, engine)
    
    # Crear índices optimizados en background
    try:
        optimizer.create_performance_indexes()
        logger.info("Performance indexes created successfully")
    except Exception as e:
        logger.warning(f"Error creating performance indexes: {e}")
    
    # Crear vistas materializadas
    try:
        optimizer.view_manager.create_article_statistics_view()
        optimizer.view_manager.create_trending_topics_view()
        optimizer.view_manager.create_daily_metrics_view()
        logger.info("Materialized views created successfully")
    except Exception as e:
        logger.warning(f"Error creating materialized views: {e}")
    
    # Programar refresh de vistas cada hora
    optimizer.view_manager.schedule_refresh('article_statistics', 60)
    optimizer.view_manager.schedule_refresh('trending_topics_detailed', 30)
    optimizer.view_manager.schedule_refresh('daily_metrics', 120)
    
    return optimizer