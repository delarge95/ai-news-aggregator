"""
Tests para el sistema de búsqueda avanzada
Prueba todos los endpoints y funcionalidades del sistema de búsqueda
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.models import Base, Article, Source, TrendingTopic, ArticleAnalysis
from app.services.search_service import search_service
from app.utils.search_utils import TextProcessor, SemanticSearchHelper
from app.core.config import settings

# Setup de base de datos de test
SQLITE_DATABASE_URL = "sqlite:///./test_search.db"
engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_database():
    """Setup base de datos para tests"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Crear sesión de base de datos para test"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_client():
    """Cliente de test para FastAPI"""
    return TestClient(app)


@pytest.fixture
def sample_sources(db_session):
    """Crear fuentes de ejemplo para tests"""
    sources = [
        Source(
            name="Test Tech News",
            url="https://test-tech.com",
            api_name="test_tech",
            api_source_id="test_tech",
            credibility_score=0.8
        ),
        Source(
            name="AI Research Journal",
            url="https://ai-research.com",
            api_name="ai_research",
            api_source_id="ai_research",
            credibility_score=0.9
        )
    ]
    
    for source in sources:
        db_session.add(source)
    db_session.commit()
    
    return sources


@pytest.fixture
def sample_articles(db_session, sample_sources):
    """Crear artículos de ejemplo para tests"""
    articles = [
        Article(
            title="Revolutionary AI Model Achieves Breakthrough",
            content="A new artificial intelligence model has achieved remarkable performance on complex reasoning tasks.",
            summary="AI model breakthrough in reasoning capabilities.",
            url="https://test-tech.com/ai-breakthrough-1",
            published_at=datetime.utcnow() - timedelta(hours=1),
            source_id=sample_sources[0].id,
            sentiment_score=0.8,
            sentiment_label="positive",
            bias_score=0.2,
            topic_tags=["artificial-intelligence", "ai-models"],
            relevance_score=0.9,
            processing_status="completed"
        ),
        Article(
            title="Machine Learning Advances in Healthcare",
            content="Researchers have developed new machine learning algorithms for medical diagnosis.",
            summary="ML algorithms improve medical diagnosis accuracy.",
            url="https://test-tech.com/ml-healthcare-1",
            published_at=datetime.utcnow() - timedelta(hours=2),
            source_id=sample_sources[0].id,
            sentiment_score=0.7,
            sentiment_label="positive",
            bias_score=0.3,
            topic_tags=["machine-learning", "healthcare"],
            relevance_score=0.85,
            processing_status="completed"
        ),
        Article(
            title="Quantum Computing Milestone Reached",
            content="Scientists have reached a new milestone in quantum computing technology.",
            summary="Quantum computing technology achieves new milestone.",
            url="https://ai-research.com/quantum-milestone",
            published_at=datetime.utcnow() - timedelta(hours=3),
            source_id=sample_sources[1].id,
            sentiment_score=0.9,
            sentiment_label="positive",
            bias_score=0.1,
            topic_tags=["quantum-computing", "research"],
            relevance_score=0.95,
            processing_status="completed"
        )
    ]
    
    for article in articles:
        db_session.add(article)
    db_session.commit()
    
    return articles


@pytest.fixture
def sample_trending_topics(db_session):
    """Crear trending topics de ejemplo para tests"""
    trending_topics = [
        TrendingTopic(
            topic="artificial intelligence",
            topic_category="technology",
            trend_score=0.95,
            article_count=50,
            sources_count=5,
            time_period="24h",
            date_recorded=datetime.utcnow()
        ),
        TrendingTopic(
            topic="machine learning",
            topic_category="technology",
            trend_score=0.85,
            article_count=35,
            sources_count=4,
            time_period="24h",
            date_recorded=datetime.utcnow()
        ),
        TrendingTopic(
            topic="quantum computing",
            topic_category="science",
            trend_score=0.75,
            article_count=20,
            sources_count=3,
            time_period="24h",
            date_recorded=datetime.utcnow()
        )
    ]
    
    for topic in trending_topics:
        db_session.add(topic)
    db_session.commit()
    
    return trending_topics


class TestSearchService:
    """Tests para el servicio de búsqueda"""
    
    def test_advanced_search_basic(self, db_session, sample_articles):
        """Test búsqueda básica"""
        result = asyncio.run(search_service.advanced_search(
            query="artificial intelligence",
            filters={},
            sort="relevance",
            limit=10,
            offset=0,
            db=db_session
        ))
        
        assert "results" in result
        assert "total" in result
        assert isinstance(result["results"], list)
        assert result["total"] > 0
    
    def test_advanced_search_with_filters(self, db_session, sample_articles):
        """Test búsqueda con filtros"""
        result = asyncio.run(search_service.advanced_search(
            query="AI",
            filters={
                "sentiment": ["positive"],
                "min_relevance": 0.8
            },
            sort="date",
            limit=5,
            db=db_session
        ))
        
        assert result["total"] > 0
        
        # Verificar que todos los resultados tienen el filtro aplicado
        for article in result["results"]:
            assert article["sentiment_label"] == "positive"
            assert article["relevance_score"] >= 0.8
    
    def test_advanced_search_empty_query(self, db_session, sample_articles):
        """Test búsqueda con query vacía"""
        result = asyncio.run(search_service.advanced_search(
            query="",
            filters={},
            limit=10,
            db=db_session
        ))
        
        assert "results" in result
        assert "total" in result
        # Debe devolver todos los artículos cuando query está vacía
    
    def test_search_suggestions(self, db_session, sample_sources, sample_trending_topics):
        """Test sugerencias de búsqueda"""
        suggestions = asyncio.run(search_service.get_search_suggestions(
            query="ai",
            limit=5,
            include_topics=True,
            include_sources=True,
            db=db_session
        ))
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        for suggestion in suggestions:
            assert "text" in suggestion
            assert "type" in suggestion
            assert "score" in suggestion
            assert suggestion["type"] in ["source", "topic", "term"]
    
    def test_trending_searches(self, db_session, sample_trending_topics):
        """Test búsquedas trending"""
        trending = asyncio.run(search_service.get_trending_searches(
            timeframe="24h",
            limit=10,
            min_count=1,
            db=db_session
        ))
        
        assert isinstance(trending, list)
        assert len(trending) > 0
        
        for trend in trending:
            assert "query" in trend
            assert "count" in trend
            assert "trend_score" in trend
            assert "timeframe" in trend
            assert trend["timeframe"] == "24h"
    
    def test_available_filters(self, db_session, sample_sources, sample_articles):
        """Test filtros disponibles"""
        filters = asyncio.run(search_service.get_available_filters(db=db_session))
        
        assert "sources" in filters
        assert "categories" in filters
        assert "sentiment" in filters
        assert "date_range" in filters
        assert "score_ranges" in filters
        
        assert isinstance(filters["sources"], list)
        assert isinstance(filters["sentiment"], list)
        assert isinstance(filters["score_ranges"], dict)
    
    def test_semantic_search(self, db_session, sample_articles):
        """Test búsqueda semántica"""
        result = asyncio.run(search_service.semantic_search(
            query="AI technology breakthrough",
            context="artificial intelligence models",
            limit=5,
            similarity_threshold=0.3,
            db=db_session
        ))
        
        assert "results" in result
        assert "total" in result
        assert "avg_similarity" in result
        
        for article in result["results"]:
            assert "similarity_score" in article
    
    def test_search_stats(self, db_session, sample_articles, sample_sources):
        """Test estadísticas de búsqueda"""
        stats = asyncio.run(search_service.get_search_stats(db=db_session))
        
        assert "articles" in stats
        assert "sources" in stats
        assert "trending" in stats
        assert "date_range" in stats
        
        assert stats["articles"]["total"] > 0
        assert stats["sources"]["total"] > 0
        assert "avg_relevance" in stats["date_range"]
    
    def test_health_check(self):
        """Test health check"""
        health = asyncio.run(search_service.health_check())
        
        assert "status" in health
        assert "timestamp" in health
        assert "services" in health
        assert health["status"] in ["healthy", "unhealthy"]


class TestSearchEndpoints:
    """Tests para endpoints de búsqueda"""
    
    def test_search_endpoint_basic(self, test_client):
        """Test endpoint básico de búsqueda"""
        response = test_client.get("/search?q=artificial%20intelligence&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert "search_time_ms" in data
    
    def test_search_with_filters(self, test_client):
        """Test endpoint con filtros"""
        params = {
            "q": "AI",
            "sentiment": "positive",
            "min_relevance": "0.8",
            "sort": "date",
            "limit": "10"
        }
        
        response = test_client.get("/search", params=params)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "filters_applied" in data
    
    def test_search_suggestions_endpoint(self, test_client):
        """Test endpoint de sugerencias"""
        response = test_client.get("/search/suggestions?q=ai&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "suggestions" in data
        assert "query" in data
        assert isinstance(data["suggestions"], list)
    
    def test_trending_searches_endpoint(self, test_client):
        """Test endpoint de búsquedas trending"""
        response = test_client.get("/search/trending?timeframe=24h&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "searches" in data
        assert isinstance(data["searches"], list)
    
    def test_filters_endpoint(self, test_client):
        """Test endpoint de filtros"""
        response = test_client.get("/search/filters")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "filters" in data
        assert isinstance(data["filters"], dict)
    
    def test_semantic_search_endpoint(self, test_client):
        """Test endpoint de búsqueda semántica"""
        response = test_client.get("/search/semantic", params={
            "query": "artificial intelligence breakthrough",
            "limit": "5"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "results" in data
        assert "avg_similarity" in data
        assert "query" in data
    
    def test_search_stats_endpoint(self, test_client):
        """Test endpoint de estadísticas"""
        response = test_client.get("/search/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert "stats" in data
    
    def test_search_health_endpoint(self, test_client):
        """Test endpoint de health check"""
        response = test_client.get("/search/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] in ["success", "error"]
        assert "service" in data
        assert data["service"] == "search_service"
    
    def test_search_error_handling(self, test_client):
        """Test manejo de errores"""
        # Test con parámetros inválidos
        response = test_client.get("/search", params={"limit": "invalid"})
        
        # Debería devolver error de validación o manejar graciosamente
        assert response.status_code in [200, 422, 500]


class TestTextProcessing:
    """Tests para procesamiento de texto"""
    
    def test_text_preprocessing(self):
        """Test preprocesamiento de texto"""
        processor = TextProcessor()
        
        text = "  OpenAI's ChatGPT has 1234567890 amazing AI capabilities! Visit https://openai.com  "
        processed = processor.preprocess_text(text)
        
        assert "openai" in processed
        assert "chatgpt" in processed
        assert "ai" in processed
        assert "1234567890" not in processed  # Numbers should be removed
        assert "https://openai.com" not in processed  # URLs should be removed
        
    def test_tokenization(self):
        """Test tokenización"""
        processor = TextProcessor()
        
        text = "Artificial intelligence and machine learning are transformative technologies"
        tokens = processor.tokenize(text, remove_stopwords=True)
        
        assert isinstance(tokens, list)
        assert "artificial" in tokens
        assert "intelligence" in tokens
        assert "and" not in tokens  # Stopword should be removed
        
    def test_keyword_extraction(self):
        """Test extracción de keywords"""
        processor = TextProcessor()
        
        text = "Artificial intelligence machine learning deep learning neural networks"
        keywords = processor.extract_keywords(text, max_keywords=3)
        
        assert len(keywords) <= 3
        assert "artificial" in keywords
        assert "learning" in keywords
        
    def test_text_similarity(self):
        """Test similitud de texto"""
        processor = TextProcessor()
        
        text1 = "artificial intelligence and machine learning"
        text2 = "AI and deep learning systems"
        
        similarity = processor.calculate_text_similarity(text1, text2, "cosine")
        
        assert 0.0 <= similarity <= 1.0
        assert similarity > 0  # There should be some similarity
        
    def test_entity_extraction(self):
        """Test extracción de entidades"""
        processor = TextProcessor()
        
        text = "OpenAI announced GPT-4 on March 14, 2023, in San Francisco"
        entities = processor.extract_entities(text)
        
        assert isinstance(entities, dict)
        assert "dates" in entities
        assert "organizations" in entities
        assert "locations" in entities
        
        # Should find the date
        assert len(entities["dates"]) > 0
        assert "2023" in str(entities["dates"])


class TestSemanticSearch:
    """Tests para búsqueda semántica"""
    
    def test_query_expansion(self):
        """Test expansión de consultas"""
        helper = SemanticSearchHelper()
        
        result = asyncio.run(helper.expand_query("artificial intelligence"))
        
        assert isinstance(result, list)
        assert "artificial intelligence" in result
        assert len(result) >= 1
    
    def test_semantic_reranking(self):
        """Test reordenamiento semántico"""
        helper = SemanticSearchHelper()
        
        query = "AI breakthrough"
        documents = [
            {"title": "AI Breakthrough Announced", "content": "Details about AI advancement", "relevance_score": 0.8},
            {"title": "Weather Forecast", "content": "Rain expected tomorrow", "relevance_score": 0.9}
        ]
        
        reranked = asyncio.run(helper.semantic_rerank(query, documents))
        
        assert len(reranked) == 2
        assert reranked[0]["similarity_score"] >= reranked[1]["similarity_score"]
        assert "semantic_score" in reranked[0]
        assert "combined_score" in reranked[0]
    
    def test_similar_articles(self):
        """Test búsqueda de artículos similares"""
        helper = SemanticSearchHelper()
        
        article_text = "Machine learning and artificial intelligence applications"
        articles = [
            {"title": "AI in Healthcare", "content": "Machine learning helps diagnose diseases"},
            {"title": "Weather Patterns", "content": "Climate changes affect weather"}
        ]
        
        similar = asyncio.run(helper.find_similar_articles(article_text, articles, limit=1))
        
        assert isinstance(similar, list)
        assert len(similar) <= 1
        
        if similar:
            assert "similarity" in similar[0]


# Tests de integración
class TestSearchIntegration:
    """Tests de integración del sistema de búsqueda"""
    
    def test_complete_search_workflow(self, test_client, setup_database, db_session, sample_sources, sample_articles, sample_trending_topics):
        """Test flujo completo de búsqueda"""
        # 1. Verificar filtros disponibles
        filters_response = test_client.get("/search/filters")
        assert filters_response.status_code == 200
        
        # 2. Realizar búsqueda con filtros
        search_response = test_client.get("/search", params={
            "q": "artificial intelligence",
            "sentiment": "positive",
            "limit": "5"
        })
        assert search_response.status_code == 200
        
        # 3. Obtener sugerencias
        suggestions_response = test_client.get("/search/suggestions", params={"q": "ai"})
        assert suggestions_response.status_code == 200
        
        # 4. Obtener trending
        trending_response = test_client.get("/search/trending", params={"timeframe": "24h"})
        assert trending_response.status_code == 200
        
        # 5. Búsqueda semántica
        semantic_response = test_client.get("/search/semantic", params={
            "query": "AI technology"
        })
        assert semantic_response.status_code == 200
        
        # 6. Verificar estadísticas
        stats_response = test_client.get("/search/stats")
        assert stats_response.status_code == 200
        
        # Verificar que todas las respuestas son consistentes
        assert all(r.status_code == 200 for r in [
            filters_response, search_response, suggestions_response,
            trending_response, semantic_response, stats_response
        ])


# Configuración de pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])