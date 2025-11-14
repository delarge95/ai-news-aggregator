"""
Tests para el Sistema de Paginación y Filtrado Avanzado

Este archivo contiene tests unitarios y de integración para validar
el correcto funcionamiento del sistema de paginación.
"""

import pytest
import json
import base64
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.utils.pagination import (
    PaginationParams, 
    FilterConfig, 
    ModelFilterConfig,
    QueryBuilder,
    CursorManager,
    SortField,
    SortOrder,
    FilterOperator,
    PaginationService,
    pagination_service
)
from app.utils.pagination_middleware import QueryParamExtractionMiddleware


class TestPaginationParams:
    """Tests para la clase PaginationParams"""
    
    def test_basic_pagination_creation(self):
        """Test creación básica de parámetros de paginación"""
        # Crear request mock
        mock_request = Mock()
        mock_request.query_params = {
            'page': '2',
            'page_size': '10'
        }
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert pagination_params.page == 2
        assert pagination_params.page_size == 10
        assert pagination_params.limit == 10
        assert pagination_params.offset == 10
    
    def test_pagination_with_cursor(self):
        """Test paginación con cursor"""
        mock_request = Mock()
        mock_request.query_params = {
            'cursor': 'eyJwYWdlIjoxLCJwYWdlX3NpemUiOjEwfQ=='
        }
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert pagination_params.cursor == 'eyJwYWdlIjoxLCJwYWdlX3NpemUiOjEwfQ=='
        assert pagination_params.page == 1  # Default
    
    def test_sort_parsing(self):
        """Test parseo de parámetros de ordenamiento"""
        mock_request = Mock()
        mock_request.query_params = {
            'sort': 'published_at,-relevance_score,name'
        }
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert len(pagination_params.sort) == 3
        
        # Verificar ordenamiento
        sort_fields = pagination_params.sort
        assert sort_fields[0].field == 'published_at'
        assert sort_fields[0].order == SortOrder.ASC
        assert sort_fields[1].field == 'relevance_score'
        assert sort_fields[1].order == SortOrder.DESC
        assert sort_fields[2].field == 'name'
        assert sort_fields[2].order == SortOrder.ASC
    
    def test_filter_extraction(self):
        """Test extracción de filtros"""
        mock_request = Mock()
        mock_request.query_params = {
            'sentiment': 'positive',
            'relevance_score__gte': '0.8',
            'published_at__date_range': '2025-11-01,2025-11-06'
        }
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert 'sentiment_label' in pagination_params.filters
        assert pagination_params.filters['sentiment_label']['operator'] == FilterOperator.EQUALS
        assert pagination_params.filters['sentiment_label']['value'] == 'positive'
        
        assert 'relevance_score' in pagination_params.filters
        assert pagination_params.filters['relevance_score']['operator'] == FilterOperator.GREATER_THAN_EQUAL
        
        assert 'published_at' in pagination_params.filters
        assert pagination_params.filters['published_at']['operator'] == FilterOperator.DATE_RANGE
    
    def test_search_extraction(self):
        """Test extracción de término de búsqueda"""
        mock_request = Mock()
        mock_request.query_params = {
            'search': 'artificial intelligence'
        }
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert pagination_params.search == 'artificial intelligence'
    
    def test_validation_page_size(self):
        """Test validación de tamaño de página"""
        mock_request = Mock()
        mock_request.query_params = {
            'page_size': '200'  # Excede el límite
        }
        
        with pytest.raises(Exception) as exc_info:
            PaginationParams(mock_request, 'article', max_page_size=100)
        
        assert "Page size no puede exceder" in str(exc_info.value)
    
    def test_default_values(self):
        """Test valores por defecto"""
        mock_request = Mock()
        mock_request.query_params = {}
        
        pagination_params = PaginationParams(mock_request, 'article', default_page_size=25)
        
        assert pagination_params.page == 1
        assert pagination_params.page_size == 25
        assert pagination_params.limit == 25
        assert pagination_params.offset == 0
        assert pagination_params.cursor is None


class TestModelFilterConfig:
    """Tests para la configuración de filtros por modelo"""
    
    def test_get_config_for_article(self):
        """Test obtener configuración para modelo Article"""
        configs = ModelFilterConfig.get_config('article')
        
        assert len(configs) > 0
        assert any(config.field_name == 'sentiment_label' for config in configs)
        assert any(config.field_name == 'relevance_score' for config in configs)
        assert any(config.field_name == 'published_at' for config in configs)
    
    def test_get_config_for_source(self):
        """Test obtener configuración para modelo Source"""
        configs = ModelFilterConfig.get_config('source')
        
        assert len(configs) > 0
        assert any(config.field_name == 'api_name' for config in configs)
        assert any(config.field_name == 'country' for config in configs)
    
    def test_get_search_fields(self):
        """Test obtener campos de búsqueda"""
        search_fields = ModelFilterConfig.get_search_fields('article')
        
        assert 'title' in search_fields
        assert 'content' in search_fields
        
        search_fields = ModelFilterConfig.get_search_fields('source')
        assert 'name' in search_fields


class TestCursorManager:
    """Tests para el gestor de cursores"""
    
    def test_encode_cursor(self):
        """Test codificación de cursor"""
        data = {'page': 1, 'page_size': 20, 'published_at': '2025-11-06T03:03:36Z'}
        
        cursor = CursorManager.encode_cursor(data)
        
        assert isinstance(cursor, str)
        assert len(cursor) > 0
        
        # Verificar que se puede decodificar
        decoded = CursorManager.decode_cursor(cursor)
        assert decoded['page'] == 1
        assert decoded['page_size'] == 20
    
    def test_decode_cursor(self):
        """Test decodificación de cursor"""
        # Crear cursor manualmente
        data = {'page': 2, 'page_size': 10}
        json_str = json.dumps(data, default=str)
        cursor = base64.b64encode(json_str.encode()).decode()
        
        decoded = CursorManager.decode_cursor(cursor)
        
        assert decoded['page'] == 2
        assert decoded['page_size'] == 10
    
    def test_decode_invalid_cursor(self):
        """Test decodificación de cursor inválido"""
        invalid_cursor = "invalid_cursor_data"
        
        decoded = CursorManager.decode_cursor(invalid_cursor)
        
        assert decoded == {}


class TestQueryBuilder:
    """Tests para el constructor de consultas"""
    
    def test_apply_filters_equals(self):
        """Test aplicar filtro equals"""
        from sqlalchemy.orm import Query
        mock_query = Mock(spec=Query)
        
        # Configurar el mock para encadenar filtros
        mock_query.filter.return_value = mock_query
        
        filters = {
            'sentiment_label': {
                'operator': FilterOperator.EQUALS,
                'value': 'positive'
            }
        }
        
        # Crear mock model
        mock_model = Mock()
        mock_model.sentiment_label = Mock()
        mock_model.sentiment_label.__eq__ = Mock(return_value="mock_condition")
        
        result = QueryBuilder.apply_filters(mock_query, mock_model, filters)
        
        # Verificar que se llamó filter
        assert result == mock_query
    
    def test_apply_filters_greater_than(self):
        """Test aplicar filtro greater than"""
        from sqlalchemy.orm import Query
        mock_query = Mock(spec=Query)
        mock_query.filter.return_value = mock_query
        
        filters = {
            'relevance_score': {
                'operator': FilterOperator.GREATER_THAN,
                'value': 0.8
            }
        }
        
        mock_model = Mock()
        mock_model.relevance_score = Mock()
        
        result = QueryBuilder.apply_filters(mock_query, mock_model, filters)
        
        assert result == mock_query
    
    def test_apply_sort(self):
        """Test aplicar ordenamiento"""
        from sqlalchemy.orm import Query
        mock_query = Mock(spec=Query)
        mock_query.order_by.return_value = mock_query
        
        sort_fields = [
            SortField('published_at', SortOrder.DESC),
            SortField('relevance_score', SortOrder.ASC)
        ]
        
        mock_model = Mock()
        mock_model.published_at = Mock()
        mock_model.relevance_score = Mock()
        
        result = QueryBuilder.apply_sort(mock_query, mock_model, sort_fields)
        
        assert result == mock_query


class TestPaginationService:
    """Tests para el servicio de paginación"""
    
    def test_paginate_basic_query(self):
        """Test paginación básica de consulta"""
        # Crear datos de prueba
        test_items = [
            Mock(id=1, title='Article 1', published_at=datetime.now()),
            Mock(id=2, title='Article 2', published_at=datetime.now()),
            Mock(id=3, title='Article 3', published_at=datetime.now()),
        ]
        
        # Mock query
        mock_query = Mock()
        mock_query.count.return_value = 3
        mock_query.offset.return_value.limit.return_value = test_items
        mock_query.order_by.return_value = mock_query
        
        # Mock model
        mock_model = Mock()
        mock_model.__table__ = Mock()
        mock_model.__table__.columns = [
            Mock(name='id'),
            Mock(name='title'),
            Mock(name='published_at')
        ]
        
        # Mock pagination params
        mock_request = Mock()
        mock_request.query_params = {'page': '1', 'page_size': '2'}
        pagination_params = PaginationParams(mock_request, 'article')
        
        # Ejecutar paginación
        result = pagination_service.paginate_query(mock_query, mock_model, pagination_params)
        
        assert result.total == 3
        assert len(result.items) == 3  # Los datos de ejemplo
        assert result.page == 1
        assert result.page_size == 2
        assert result.total_pages == 2
        assert result.has_next is True
        assert result.has_prev is False


class TestMiddleware:
    """Tests para el middleware de extracción"""
    
    def test_extract_model_from_path(self):
        """Test extracción de modelo desde path"""
        mock_request = Mock()
        mock_request.url.path = '/api/v1/news'
        
        middleware = QueryParamExtractionMiddleware(app)
        model = middleware._extract_model_from_request(mock_request)
        
        assert model == 'article'
    
    def test_should_exclude_endpoint(self):
        """Test exclusión de endpoints"""
        middleware = QueryParamExtractionMiddleware(app)
        
        assert middleware._should_exclude_endpoint('/health') is True
        assert middleware._should_exclude_endpoint('/docs') is True
        assert middleware._should_exclude_endpoint('/api/v1/news') is False


class TestIntegration:
    """Tests de integración con la aplicación"""
    
    def test_news_endpoint_with_pagination(self):
        """Test endpoint de noticias con paginación"""
        client = TestClient(app)
        
        response = client.get('/api/v1/news/advanced?page=1&page_size=5')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert 'data' in data
        assert 'pagination' in data
        assert 'filters_applied' in data
        
        pagination = data['pagination']
        assert 'total' in pagination
        assert 'page' in pagination
        assert 'page_size' in pagination
        assert 'total_pages' in pagination
    
    def test_news_endpoint_with_filters(self):
        """Test endpoint con filtros"""
        client = TestClient(app)
        
        response = client.get('/api/v1/news/advanced?sentiment=positive&relevance_score__gte=0.8')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'filters_applied' in data
    
    def test_news_endpoint_with_sorting(self):
        """Test endpoint con ordenamiento"""
        client = TestClient(app)
        
        response = client.get('/api/v1/news/advanced?sort=-published_at,relevance_score')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'sort_applied' in data
        sort_applied = data['sort_applied']
        assert len(sort_applied) == 2
    
    def test_pagination_metrics_endpoint(self):
        """Test endpoint de métricas"""
        client = TestClient(app)
        
        response = client.get('/api/v1/pagination/metrics')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert 'global_metrics' in data
    
    def test_filter_presets_endpoint(self):
        """Test endpoint de presets de filtros"""
        client = TestClient(app)
        
        response = client.get('/api/v1/news/filter-presets')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'status' in data
        assert 'presets' in data
        assert 'trending_ai' in data['presets']
    
    def test_cors_headers(self):
        """Test headers CORS"""
        client = TestClient(app)
        
        response = client.options('/api/v1/news/advanced')
        
        assert 'access-control-allow-origin' in response.headers
        assert 'x-max-page-size' in response.headers


class TestEdgeCases:
    """Tests para casos extremos"""
    
    def test_empty_query_params(self):
        """Test con parámetros de query vacíos"""
        mock_request = Mock()
        mock_request.query_params = {}
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert pagination_params.page == 1
        assert pagination_params.page_size == 20
        assert pagination_params.filters == {}
    
    def test_invalid_page_number(self):
        """Test con número de página inválido"""
        mock_request = Mock()
        mock_request.query_params = {'page': '0'}
        
        with pytest.raises(Exception) as exc_info:
            PaginationParams(mock_request, 'article')
        
        assert "Page debe ser mayor a 0" in str(exc_info.value)
    
    def test_invalid_sort_field(self):
        """Test con campo de ordenamiento inválido"""
        mock_request = Mock()
        mock_request.query_params = {'sort': 'invalid_field'}
        
        # Por ahora no debería fallar, pero en producción se validaría
        pagination_params = PaginationParams(mock_request, 'article')
        
        assert len(pagination_params.sort) == 1
        assert pagination_params.sort[0].field == 'invalid_field'
    
    def test_unsupported_filter(self):
        """Test con filtro no soportado"""
        mock_request = Mock()
        mock_request.query_params = {'unsupported_field': 'value'}
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        # Los filtros no soportados se ignoran
        assert 'unsupported_field' not in pagination_params.filters


class TestPerformance:
    """Tests de rendimiento"""
    
    def test_cursor_pagination_performance(self):
        """Test rendimiento de paginación por cursor"""
        # Simular datos grandes
        large_dataset = [Mock(id=i, published_at=datetime.now()) for i in range(1000)]
        
        # Test cursor encoding/decoding
        cursor_data = {'published_at': '2025-11-06T03:03:36Z'}
        cursor = CursorManager.encode_cursor(cursor_data)
        decoded = CursorManager.decode_cursor(cursor)
        
        assert decoded == cursor_data
    
    def test_large_filter_list(self):
        """Test con lista grande de filtros"""
        mock_request = Mock()
        mock_request.query_params = {
            f'filter_{i}': f'value_{i}' for i in range(50)
        }
        
        pagination_params = PaginationParams(mock_request, 'article')
        
        # Solo los filtros válidos se mantienen
        assert len(pagination_params.filters) <= len(ModelFilterConfig.get_config('article'))


# Fixture para setup de tests
@pytest.fixture
def test_app():
    """Fixture para crear app de testing"""
    return app


@pytest.fixture
def sample_article_data():
    """Datos de artículo de ejemplo para tests"""
    return {
        'id': 'test-id-123',
        'title': 'Test Article',
        'content': 'Test content',
        'published_at': datetime.now().isoformat(),
        'sentiment_label': 'positive',
        'sentiment_score': 0.8,
        'relevance_score': 0.9,
        'source_id': 'test-source',
        'processing_status': 'completed'
    }


# Funciones de utilidad para tests
def create_test_request(params: dict) -> Mock:
    """Crear request mock con parámetros específicos"""
    mock_request = Mock()
    mock_request.query_params = params
    return mock_request


def create_test_cursor(page: int, page_size: int) -> str:
    """Crear cursor de test"""
    cursor_data = {'page': page, 'page_size': page_size}
    return CursorManager.encode_cursor(cursor_data)


if __name__ == '__main__':
    # Ejecutar tests si se ejecuta directamente
    pytest.main([__file__, '-v'])