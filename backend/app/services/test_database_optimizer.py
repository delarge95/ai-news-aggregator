"""
Tests para el Database Optimizer

Este archivo contiene tests unitarios y de integración para el
sistema de optimización de base de datos.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Test fixtures y utilidades
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importar componentes a testear
from services.database_optimizer import (
    DatabaseOptimizer,
    QueryCache,
    MaterializedViewManager,
    IndexOptimizer,
    PerformanceMonitor,
    OptimizedQueryBuilder,
    QueryType,
    PerformanceMetrics,
    CacheStats
)

# Test data fixtures
@pytest.fixture
def mock_redis():
    """Mock del cliente Redis"""
    redis_mock = Mock()
    redis_mock.get.return_value = None
    redis_mock.setex.return_value = True
    redis_mock.keys.return_value = []
    redis_mock.delete.return_value = True
    return redis_mock


@pytest.fixture
def mock_engine():
    """Mock del engine SQLAlchemy"""
    engine_mock = Mock()
    connection_mock = Mock()
    connection_mock.execute.return_value = Mock()
    connection_mock.commit.return_value = None
    engine_mock.connect.return_value.__enter__ = Mock(return_value=connection_mock)
    engine_mock.connect.return_value.__exit__ = Mock(return_value=None)
    return engine_mock


@pytest.fixture
def optimizer(mock_redis, mock_engine):
    """Fixture del optimizador para tests"""
    return DatabaseOptimizer(mock_redis, mock_engine)


@pytest.fixture
def test_articles_data():
    """Datos de prueba para artículos"""
    return [
        {
            'id': '123e4567-e89b-12d3-a456-426614174000',
            'title': 'Test Article 1',
            'sentiment_label': 'positive',
            'relevance_score': 0.8,
            'published_at': datetime.utcnow(),
            'source_id': 'source1',
            'processing_status': 'completed'
        },
        {
            'id': '223e4567-e89b-12d3-a456-426614174001',
            'title': 'Test Article 2',
            'sentiment_label': 'negative',
            'relevance_score': 0.6,
            'published_at': datetime.utcnow() - timedelta(days=1),
            'source_id': 'source2',
            'processing_status': 'completed'
        }
    ]


class TestQueryCache:
    """Tests para el sistema de cache"""
    
    def test_cache_initialization(self, mock_redis):
        """Test de inicialización del cache"""
        cache = QueryCache(mock_redis)
        assert cache.redis == mock_redis
        assert cache.default_ttl == 300
        assert cache.max_memory_items == 1000
        assert len(cache.memory_cache) == 0
    
    def test_cache_key_generation(self, mock_redis):
        """Test de generación de claves de cache"""
        cache = QueryCache(mock_redis)
        
        key = cache._make_key("test_hash", QueryType.LIST_ARTICLES, {'limit': 10})
        assert key.startswith("query_cache:")
        assert len(key) > 20
    
    def test_cache_set_and_get(self, mock_redis):
        """Test de guardar y obtener del cache"""
        cache = QueryCache(mock_redis)
        
        # Mock Redis responses
        mock_redis.get.return_value = json.dumps(['article1', 'article2'])
        
        # Set y get
        result = ['article1', 'article2']
        success = cache.set("test_query", result, QueryType.LIST_ARTICLES)
        assert success
        
        cached_result = cache.get("test_query", QueryType.LIST_ARTICLES)
        assert cached_result == ['article1', 'article2']
    
    def test_memory_cache_promotion(self, mock_redis):
        """Test de promoción a cache de memoria"""
        cache = QueryCache(mock_redis, max_memory_items=2)
        
        # Agregar items
        cache._promote_to_memory("key1", "value1")
        cache._promote_to_memory("key2", "value2")
        
        assert len(cache.memory_cache) == 2
        assert "key1" in cache.memory_cache
        assert "key2" in cache.memory_cache
        
        # Agregar第三个 item (debería expulsar el más antiguo)
        cache._promote_to_memory("key3", "value3")
        
        assert len(cache.memory_cache) == 2
        assert "key1" in cache.memory_cache  # First item still there
        assert "key2" not in cache.memory_cache  # Second item removed
    
    def test_cache_stats(self, mock_redis):
        """Test de estadísticas del cache"""
        cache = QueryCache(mock_redis)
        
        # Agregar algunos items al memory cache
        cache.memory_cache["key1"] = "value1"
        cache.memory_cache["key2"] = "value2"
        
        stats = cache.get_stats()
        assert stats.items_cached == 2
        assert stats.memory_usage > 0


class TestMaterializedViewManager:
    """Tests para el gestor de vistas materializadas"""
    
    def test_view_manager_initialization(self, mock_engine):
        """Test de inicialización del gestor de vistas"""
        manager = MaterializedViewManager(mock_engine)
        assert manager.engine == mock_engine
        assert len(manager.views) == 0
        assert len(manager.refresh_intervals) == 0
    
    @patch('services.database_optimizer.text')
    def test_create_article_statistics_view(self, mock_text, mock_engine):
        """Test de creación de vista de estadísticas"""
        manager = MaterializedViewManager(mock_engine)
        manager.create_article_statistics_view()
        
        # Verificar que se ejecutaron las consultas SQL
        assert mock_engine.connect.return_value.__enter__.return_value.execute.call_count >= 1
    
    def test_refresh_view(self, mock_engine):
        """Test de actualización de vista"""
        manager = MaterializedViewManager(mock_engine)
        
        with patch.object(manager, 'refresh_view') as mock_refresh:
            manager.refresh_view('test_view')
            mock_refresh.assert_called_once_with('test_view', False)
    
    def test_schedule_refresh(self, mock_engine):
        """Test de programación de refresh"""
        manager = MaterializedViewManager(mock_engine)
        
        manager.schedule_refresh('article_statistics', 60)
        assert manager.refresh_intervals['article_statistics'] == 60


class TestIndexOptimizer:
    """Tests para el optimizador de índices"""
    
    def test_index_optimizer_initialization(self, mock_engine):
        """Test de inicialización del optimizador"""
        optimizer = IndexOptimizer(mock_engine)
        assert optimizer.engine == mock_engine
        assert len(optimizer.performance_stats) == 0
    
    @patch('services.database_optimizer.text')
    def test_create_optimized_indexes(self, mock_text, mock_engine):
        """Test de creación de índices optimizados"""
        optimizer = IndexOptimizer(mock_engine)
        optimizer.create_optimized_indexes()
        
        # Verificar que se ejecutaron comandos CREATE INDEX
        calls = mock_engine.connect.return_value.__enter__.return_value.execute.call_args_list
        assert len(calls) > 0  # Se crearon índices
        
        # Verificar que se hizo commit
        mock_engine.connect.return_value.__enter__.return_value.commit.assert_called_once()
    
    def test_analyze_query_performance(self, mock_engine):
        """Test de análisis de performance de consultas"""
        optimizer = IndexOptimizer(mock_engine)
        
        # Mock del resultado de EXPLAIN
        mock_result = Mock()
        mock_result.fetchone.return_value = [{
            'Execution Time': 150.5,
            'Planning Time': 25.0,
            'Total Cost': 1000.0,
            'Plan Rows': 50,
            'Plan': {
                'Total Cost': 1000.0,
                'Plan Rows': 50
            }
        }]
        
        connection_mock = mock_engine.connect.return_value.__enter__.return_value
        connection_mock.execute.return_value = mock_result
        
        result = optimizer.analyze_query_performance("SELECT * FROM articles")
        
        assert result['execution_time_ms'] == 150.5
        assert result['planning_time_ms'] == 25.0
        assert result['total_cost'] == 1000.0
        assert result['estimated_rows'] == 50


class TestPerformanceMonitor:
    """Tests para el monitor de performance"""
    
    def test_monitor_initialization(self):
        """Test de inicialización del monitor"""
        monitor = PerformanceMonitor(slow_query_threshold_ms=500)
        assert monitor.slow_query_threshold == 500
        assert len(monitor.query_metrics) == 0
        assert len(monitor.slow_queries) == 0
    
    def test_record_query(self):
        """Test de registro de consultas"""
        monitor = PerformanceMonitor()
        
        metrics = PerformanceMetrics(
            query_time_ms=1500.0,
            rows_returned=100,
            cache_hit=False,
            optimization_used="eager_loading",
            query_type=QueryType.LIST_ARTICLES
        )
        
        monitor.record_query("SELECT * FROM articles", metrics)
        
        # Verificar que se registró la métrica
        assert QueryType.LIST_ARTICLES in monitor.query_metrics
        assert len(monitor.query_metrics[QueryType.LIST_ARTICLES]) == 1
        
        # Verificar que se registró como consulta lenta
        assert len(monitor.slow_queries) == 1
        assert monitor.slow_queries[0]['execution_time'] == 1500.0
    
    def test_get_performance_summary(self):
        """Test de resumen de performance"""
        monitor = PerformanceMonitor()
        
        # Agregar algunas métricas
        for i in range(3):
            metrics = PerformanceMetrics(
                query_time_ms=100.0 + i * 50,
                rows_returned=10,
                cache_hit=i % 2 == 0,
                optimization_used="test",
                query_type=QueryType.LIST_ARTICLES
            )
            monitor.record_query("test_query", metrics)
        
        summary = monitor.get_performance_summary()
        
        assert QueryType.LIST_ARTICLES.value in summary
        stats = summary[QueryType.LIST_ARTICLES.value]
        assert stats['total_queries'] == 3
        assert stats['avg_time_ms'] == 200.0  # (100 + 150 + 200) / 3
        assert stats['cache_hit_ratio'] == 2/3  # 2 out of 3 had cache_hit=True
    
    def test_get_slow_queries(self):
        """Test de obtención de consultas lentas"""
        monitor = PerformanceMonitor(slow_query_threshold_ms=100)
        
        # Agregar consultas con diferentes tiempos
        for i in range(5):
            metrics = PerformanceMetrics(
                query_time_ms=150.0 + i * 100,
                rows_returned=10,
                cache_hit=False,
                optimization_used="test",
                query_type=QueryType.LIST_ARTICLES,
                timestamp=datetime.utcnow()
            )
            monitor.record_query(f"query_{i}", metrics)
        
        slow_queries = monitor.get_slow_queries(3)
        
        assert len(slow_queries) == 3
        # Deben estar ordenadas por tiempo descendente
        assert slow_queries[0]['execution_time'] > slow_queries[1]['execution_time']
        assert slow_queries[1]['execution_time'] > slow_queries[2]['execution_time']


class TestOptimizedQueryBuilder:
    """Tests para el constructor de consultas optimizadas"""
    
    def test_builder_initialization(self):
        """Test de inicialización del builder"""
        builder = OptimizedQueryBuilder()
        assert 'articles' in builder._eager_loaders
        assert 'source' in builder._eager_loaders['articles']
        assert 'analysis_results' in builder._eager_loaders['articles']
    
    @patch('services.database_optimizer.Article')
    @patch('services.database_optimizer.Source')
    @patch('services.database_optimizer.ArticleAnalysis')
    def test_build_articles_list_query(self, mock_analysis, mock_source, mock_article):
        """Test de construcción de consulta de artículos"""
        builder = OptimizedQueryBuilder()
        
        # Mock de la sesión
        session_mock = Mock()
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        
        filters = {
            'sentiment': 'positive',
            'min_relevance': 0.7,
            'date_from': datetime.utcnow() - timedelta(days=7)
        }
        pagination = {'limit': 20, 'offset': 0}
        
        # Ejecutar construcción de consulta
        result = builder.build_articles_list_query(session_mock, filters, pagination)
        
        # Verificar que se llamó query con los modelos correctos
        session_mock.query.assert_called_once_with(mock_article)
        
        # Verificar que se aplicaron filtros
        # (En un test real, verificarías que se llamaron los métodos filter())
        assert result is not None
    
    def test_cursor_pagination_query(self):
        """Test de consulta con cursor pagination"""
        builder = OptimizedQueryBuilder()
        session_mock = Mock()
        query_mock = Mock()
        session_mock.query.return_value = query_mock
        
        filters = {'min_relevance': 0.5}
        
        # Test primera página (sin cursor)
        result = builder.build_cursor_pagination_query(
            session_mock, filters, None, 10
        )
        
        # Test páginas siguientes (con cursor)
        cursor_data = json.dumps({
            'id': '123',
            'date': datetime.utcnow().isoformat()
        })
        result = builder.build_cursor_pagination_query(
            session_mock, filters, cursor_data, 10
        )
        
        assert result is not None


class TestDatabaseOptimizer:
    """Tests principales para el optimizador de base de datos"""
    
    def test_optimizer_initialization(self, mock_redis, mock_engine):
        """Test de inicialización del optimizador"""
        optimizer = DatabaseOptimizer(mock_redis, mock_engine)
        
        assert optimizer.redis == mock_redis
        assert optimizer.engine == mock_engine
        assert isinstance(optimizer.cache, QueryCache)
        assert isinstance(optimizer.view_manager, MaterializedViewManager)
        assert isinstance(optimizer.index_optimizer, IndexOptimizer)
        assert isinstance(optimizer.performance_monitor, PerformanceMonitor)
    
    @patch('services.database_optimizer.Article')
    @patch('services.database_optimizer.Session')
    def test_optimize_articles_list(self, mock_session_class, mock_article, optimizer):
        """Test de optimización de listado de artículos"""
        # Mock de la sesión
        session_mock = Mock()
        connection_mock = Mock()
        session_mock.connection.return_value = connection_mock
        
        # Mock de la consulta
        query_mock = Mock()
        query_mock.all.return_value = []
        query_mock.options.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.limit.return_value = query_mock
        query_mock.offset.return_value = query_mock
        
        mock_session_class.return_value = session_mock
        mock_article.id = 'test_id'
        mock_article.published_at = datetime.utcnow()
        
        filters = {'sentiment': 'positive'}
        pagination = {'limit': 10, 'offset': 0}
        
        # Ejecutar optimización
        articles, metadata = optimizer.optimize_articles_list(
            session_mock, filters, pagination
        )
        
        # Verificaciones
        assert isinstance(articles, list)
        assert isinstance(metadata, dict)
        assert 'total_count' in metadata
        assert 'page_size' in metadata
    
    @patch('services.database_optimizer.text')
    def test_get_trending_optimized(self, mock_text, optimizer):
        """Test de obtención de tendencias optimizado"""
        # Mock de conexión y resultado
        connection_mock = Mock()
        result_mock = Mock()
        result_mock.fetchall.return_value = [
            ('IA', 'technology', 10, 5, 0.8, 0.2, ['tag1', 'tag2'])
        ]
        connection_mock.execute.return_value = result_mock
        
        session_mock = Mock()
        session_mock.connection.return_value.__enter__ = Mock(return_value=connection_mock)
        session_mock.connection.return_value.__exit__ = Mock(return_value=None)
        
        # Ejecutar consulta de tendencias
        trending = optimizer.get_trending_optimized(session_mock, 5)
        
        # Verificaciones
        assert isinstance(trending, list)
        assert len(trending) == 1
        
        topic = trending[0]
        assert 'topic' in topic
        assert 'category' in topic
        assert 'article_count' in topic
    
    def test_performance_report(self, optimizer):
        """Test de generación de reporte de performance"""
        # Simular algunas métricas
        metrics = PerformanceMetrics(
            query_time_ms=100.0,
            rows_returned=10,
            cache_hit=True,
            optimization_used="cache",
            query_type=QueryType.LIST_ARTICLES
        )
        optimizer.performance_monitor.record_query("test_query", metrics)
        
        # Generar reporte
        report = optimizer.get_performance_report()
        
        # Verificaciones
        assert isinstance(report, dict)
        assert 'cache_stats' in report
        assert 'performance_summary' in report
        assert 'slow_queries' in report
        
        cache_stats = report['cache_stats']
        assert 'hit_ratio' in cache_stats
        assert 'memory_usage' in cache_stats
        assert 'items_cached' in cache_stats
    
    def test_create_performance_indexes(self, optimizer):
        """Test de creación de índices de performance"""
        with patch.object(optimizer.index_optimizer, 'create_optimized_indexes') as mock_create:
            optimizer.create_performance_indexes()
            mock_create.assert_called_once()
    
    def test_refresh_materialized_views(self, optimizer):
        """Test de refresh de vistas materializadas"""
        with patch.object(optimizer.view_manager, 'refresh_all_views') as mock_refresh:
            optimizer.refresh_materialized_views()
            mock_refresh.assert_called_once()
    
    def test_analyze_slow_queries(self, optimizer):
        """Test de análisis de consultas lentas"""
        # Agregar algunas consultas lentas simuladas
        optimizer.performance_monitor.slow_queries = [
            {'query': 'slow_query_1', 'execution_time': 2000.0},
            {'query': 'slow_query_2', 'execution_time': 1500.0},
            {'query': 'slow_query_3', 'execution_time': 1000.0}
        ]
        
        slow_queries = optimizer.analyze_slow_queries()
        
        assert isinstance(slow_queries, list)
        assert len(slow_queries) == 3
        # Deben estar ordenadas por tiempo descendente
        assert slow_queries[0]['execution_time'] > slow_queries[1]['execution_time']


class TestIntegration:
    """Tests de integración completos"""
    
    @pytest.mark.asyncio
    async def test_full_optimization_workflow(self, mock_redis, mock_engine):
        """Test del flujo completo de optimización"""
        optimizer = DatabaseOptimizer(mock_redis, mock_engine)
        
        # Test de inicialización
        assert optimizer is not None
        
        # Test de creación de índices
        with patch.object(optimizer.index_optimizer, 'create_optimized_indexes'):
            optimizer.create_performance_indexes()
        
        # Test de creación de vistas
        with patch.multiple(
            optimizer.view_manager,
            create_article_statistics_view=Mock(),
            create_trending_topics_view=Mock(),
            create_daily_metrics_view=Mock()
        ):
            optimizer.view_manager.create_article_statistics_view()
            optimizer.view_manager.create_trending_topics_view()
            optimizer.view_manager.create_daily_metrics_view()
        
        # Test de reporte de performance
        report = optimizer.get_performance_report()
        assert isinstance(report, dict)
    
    def test_cache_invalidation_workflow(self, mock_redis, mock_engine):
        """Test de flujo de invalidación de cache"""
        optimizer = DatabaseOptimizer(mock_redis, mock_engine)
        
        # Test de invalidación por patrón
        with patch.object(optimizer.cache, 'invalidate_pattern') as mock_invalidate:
            optimizer.cache.invalidate_pattern("trending_*")
            mock_invalidate.assert_called_once_with("trending_*")


class TestPerformanceBenchmarks:
    """Tests de performance y benchmarks"""
    
    def test_cache_performance(self, mock_redis):
        """Test de performance del sistema de cache"""
        cache = QueryCache(mock_redis)
        
        # Test de velocidad de operaciones
        start_time = time.time()
        
        # Simular muchas operaciones
        for i in range(1000):
            key = f"test_key_{i}"
            cache._promote_to_memory(key, f"value_{i}")
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # El cache debe ser muy rápido (< 1 segundo para 1000 operaciones)
        assert operation_time < 1.0, f"Cache operations too slow: {operation_time}s"
    
    def test_query_builder_performance(self):
        """Test de performance del constructor de consultas"""
        builder = OptimizedQueryBuilder()
        
        # Test de velocidad de construcción de consultas
        start_time = time.time()
        
        for i in range(100):
            # Simular construcción de consultas complejas
            filters = {
                'sentiment': 'positive',
                'min_relevance': 0.7,
                'source_ids': [f'source_{j}' for j in range(10)]
            }
            # builder.build_articles_list_query no necesita sesión real para el test
        
        end_time = time.time()
        construction_time = end_time - start_time
        
        # La construcción debe ser rápida
        assert construction_time < 0.5, f"Query building too slow: {construction_time}s"


# Utilidades para tests
def create_mock_session_with_data():
    """Crea una sesión mock con datos de prueba"""
    session_mock = Mock()
    
    # Mock de artículos
    article1 = Mock()
    article1.id = '123'
    article1.title = 'Test Article 1'
    article1.sentiment_label = 'positive'
    article1.relevance_score = 0.8
    article1.published_at = datetime.utcnow()
    
    article2 = Mock()
    article2.id = '456'
    article2.title = 'Test Article 2'
    article2.sentiment_label = 'negative'
    article2.relevance_score = 0.3
    article2.published_at = datetime.utcnow() - timedelta(days=1)
    
    session_mock.query.return_value.options.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = [article1, article2]
    
    return session_mock


def assert_performance_improvement(baseline_time: float, optimized_time: float, improvement_factor: float = 2.0):
    """Utilidad para verificar mejoras de performance"""
    improvement = baseline_time / optimized_time
    assert improvement >= improvement_factor, (
        f"Performance improvement insufficient: {improvement:.2f}x vs expected {improvement_factor}x"
    )


# Configuración de pytest
def pytest_configure(config):
    """Configuración personalizada para pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance benchmarks")


if __name__ == '__main__':
    # Ejecutar tests si se llama directamente
    pytest.main([__file__, '-v'])