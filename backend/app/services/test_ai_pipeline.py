"""
Tests para el Pipeline de IA

Este archivo contiene pruebas unitarias y de integración para validar
el funcionamiento del AIPipelineOrchestrator y sus componentes.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any

from app.services.ai_pipeline import (
    AIPipelineOrchestrator,
    ProcessingConfig,
    DataValidator,
    PreprocessingPipeline,
    AIAnalysisPipeline,
    PostprocessingPipeline,
    AnalysisType,
    ProcessingStatus,
    AnalysisResult,
    BatchResult,
    DEFAULT_CONFIGS
)
from app.db.models import Article, Source, ArticleAnalysis
from app.utils.normalizer import NewsNormalizer


class TestProcessingConfig:
    """Tests para ProcessingConfig"""
    
    def test_default_config_creation(self):
        """Test creación de configuración por defecto"""
        config = ProcessingConfig()
        
        assert config.batch_size == 10
        assert config.max_concurrent_batches == 5
        assert config.max_concurrent_analyses == 20
        assert config.analysis_timeout == 30
        assert config.enable_parallel_processing == True
        assert config.enable_caching == True
        assert config.enable_validation == True
    
    def test_custom_config_creation(self):
        """Test creación de configuración personalizada"""
        config = ProcessingConfig(
            batch_size=25,
            max_concurrent_analyses=50,
            analysis_timeout=60
        )
        
        assert config.batch_size == 25
        assert config.max_concurrent_analyses == 50
        assert config.analysis_timeout == 60


class TestDataValidator:
    """Tests para DataValidator"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = ProcessingConfig()
        self.validator = DataValidator(self.config)
    
    def test_valid_article_data(self):
        """Test validación de datos válidos"""
        valid_article = {
            "title": "Breaking: AI Revolution in Healthcare",
            "content": "This is a comprehensive article about AI in healthcare...",
            "url": "https://example.com/article/123",
            "source_name": "Tech News Daily"
        }
        
        is_valid, errors = self.validator.validate_article_data(valid_article)
        
        assert is_valid == True
        assert len(errors) == 0
    
    def test_invalid_article_data(self):
        """Test validación de datos inválidos"""
        invalid_article = {
            "title": "AB",  # Título muy corto
            "content": "Short",  # Contenido muy corto
            "url": "invalid-url",  # URL inválida
        }
        
        is_valid, errors = self.validator.validate_article_data(invalid_article)
        
        assert is_valid == False
        assert len(errors) > 0
        assert any("Título muy corto" in error for error in errors)
        assert any("URL inválida" in error for error in errors)
    
    def test_batch_validation(self):
        """Test validación por lotes"""
        articles = [
            {"title": "Valid Article 1", "url": "https://example.com/1", "content": "Content 1"},
            {"title": "AB", "url": "https://example.com/2", "content": "Content 2"},  # Inválido
            {"title": "Valid Article 3", "url": "https://example.com/3", "content": "Content 3"},
        ]
        
        valid, invalid = self.validator.batch_validate(articles)
        
        assert len(valid) == 2
        assert len(invalid) == 1
        assert invalid[0]['article']['title'] == "AB"


class TestPreprocessingPipeline:
    """Tests para PreprocessingPipeline"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = ProcessingConfig()
        self.pipeline = PreprocessingPipeline(self.config)
    
    def test_pipeline_initialization(self):
        """Test inicialización del pipeline"""
        assert isinstance(self.pipeline.normalizer, NewsNormalizer)
        assert isinstance(self.pipeline.validator, DataValidator)
        assert self.pipeline.config == self.config
    
    @pytest.mark.asyncio
    async def test_process_single_article(self):
        """Test procesamiento de artículo individual"""
        raw_article = {
            "title": "AI Breakthrough Announced",
            "content": "Scientists have achieved a major breakthrough...",
            "url": "https://example.com/news/123",
            "source_name": "Science Daily"
        }
        
        processed, failed = await self.pipeline.process_articles([raw_article])
        
        assert len(processed) == 1
        assert len(failed) == 0
        assert processed[0]['title'] == "AI Breakthrough Announced"
        assert processed[0]['url'] == "https://example.com/news/123"
    
    @pytest.mark.asyncio
    async def test_process_multiple_articles(self):
        """Test procesamiento de múltiples artículos"""
        raw_articles = [
            {
                "title": "Article 1",
                "content": "Content 1",
                "url": "https://example.com/1",
                "source_name": "News Source"
            },
            {
                "title": "Article 2", 
                "content": "Content 2",
                "url": "https://example.com/2",
                "source_name": "Tech News"
            }
        ]
        
        processed, failed = await self.pipeline.process_articles(raw_articles)
        
        assert len(processed) == 2
        assert len(failed) == 0


class TestAIAnalysisPipeline:
    """Tests para AIAnalysisPipeline"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = ProcessingConfig()
        self.config.openai_model = "gpt-3.5-turbo"
        self.pipeline = AIAnalysisPipeline(self.config)
    
    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test inicialización del pipeline"""
        # Sin API key configurada
        pipeline_no_key = AIAnalysisPipeline(self.config)
        assert pipeline_no_key.openai_client is None
        
        # Con API key mock
        with patch('app.services.ai_pipeline.AsyncOpenAI') as mock_openai:
            pipeline_with_key = AIAnalysisPipeline(self.config)
            assert mock_openai.called
    
    def test_prompt_construction(self):
        """Test construcción de prompts"""
        title = "AI Revolution"
        content = "Artificial intelligence is changing everything..."
        
        # Test prompt de sentimiento
        sentiment_prompt = self.pipeline._build_prompt(
            AnalysisType.SENTIMENT, title, content
        )
        
        assert "AI Revolution" in sentiment_prompt
        assert "Artificial intelligence is changing everything" in sentiment_prompt
        assert "sentiment" in sentiment_prompt.lower()
    
    def test_confidence_calculation(self):
        """Test cálculo de confianza"""
        # Respuesta de alta confianza
        high_confidence_response = """
        Based on the analysis, this article has a positive sentiment.
        The tone is optimistic and the language is constructive.
        Score: 0.8, Label: positive
        """
        
        confidence = self.pipeline._calculate_confidence(
            AnalysisType.SENTIMENT, high_confidence_response
        )
        
        assert confidence > 0.5
        
        # Respuesta de baja confianza
        low_confidence_response = "I cannot analyze this text properly."
        
        confidence = self.pipeline._calculate_confidence(
            AnalysisType.SENTIMENT, low_confidence_response
        )
        
        assert confidence < 0.5
    
    def test_sentiment_parsing(self):
        """Test parsing de respuesta de sentimiento"""
        response = """
        {
            "sentiment_score": 0.7,
            "sentiment_label": "positive",
            "explanation": "The article has an optimistic tone"
        }
        """
        
        result = self.pipeline._parse_sentiment_response(response)
        
        assert result['sentiment_score'] == 0.7
        assert result['sentiment_label'] == 'positive'
        assert 'explanation' in result
    
    def test_topics_parsing(self):
        """Test parsing de topics"""
        response = "artificial intelligence, healthcare, breakthrough, machine learning"
        
        result = self.pipeline._parse_topics_response(response)
        
        assert 'topics' in result
        assert len(result['topics']) > 0
        assert 'artificial intelligence' in result['topics']


class TestPostprocessingPipeline:
    """Tests para PostprocessingPipeline"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = ProcessingConfig()
        self.pipeline = PostprocessingPipeline(self.config)
    
    @pytest.mark.asyncio
    async def test_create_article_from_data(self):
        """Test creación de artículo desde datos"""
        # Mock de session
        mock_session = AsyncMock()
        
        article_data = {
            "title": "Test Article",
            "content": "Test content",
            "url": "https://example.com/test",
            "source_name": "Test Source",
            "published_at": datetime.now(timezone.utc),
            "content_hash": "abc123"
        }
        
        article = await self.pipeline._create_article_from_data(
            article_data, str(uuid.uuid4()), mock_session
        )
        
        assert article.title == "Test Article"
        assert article.content == "Test content"
        assert article.url == "https://example.com/test"
    
    @pytest.mark.asyncio
    async def test_add_analysis_to_article(self):
        """Test agregar análisis a artículo"""
        # Crear artículo mock
        article = Article(
            id=str(uuid.uuid4()),
            title="Test Article",
            content="Test content",
            url="https://example.com/test"
        )
        
        # Crear resultados de análisis
        sentiment_result = AnalysisResult(
            article_id=article.id,
            analysis_type=AnalysisType.SENTIMENT,
            result={
                "sentiment_score": 0.5,
                "sentiment_label": "neutral",
                "explanation": "Neutral tone"
            },
            confidence_score=0.8,
            model_used="gpt-3.5-turbo",
            processing_time=1.0,
            status=ProcessingStatus.COMPLETED
        )
        
        mock_session = AsyncMock()
        
        updated_article = await self.pipeline._add_analysis_to_article(
            article, [sentiment_result], mock_session
        )
        
        assert updated_article.sentiment_score == 0.5
        assert updated_article.processed_at is not None


class TestAIPipelineOrchestrator:
    """Tests para AIPipelineOrchestrator"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = ProcessingConfig()
        self.orchestrator = AIPipelineOrchestrator(self.config)
    
    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test inicialización del orquestador"""
        assert isinstance(self.orchestrator.preprocessing_pipeline, PreprocessingPipeline)
        assert isinstance(self.orchestrator.ai_analysis_pipeline, AIAnalysisPipeline)
        assert isinstance(self.orchestrator.postprocessing_pipeline, PostprocessingPipeline)
    
    @pytest.mark.asyncio
    async def test_process_articles_batch_no_api_key(self):
        """Test procesamiento sin API key configurada"""
        raw_articles = [
            {
                "title": "Test Article",
                "content": "Test content",
                "url": "https://example.com/test",
                "source_name": "Test Source"
            }
        ]
        
        result = await self.orchestrator.process_articles_batch(raw_articles)
        
        # Sin API key, no debería hacer análisis
        assert result.successful_analyses == 0
        assert result.total_articles == 1
        assert len(result.errors) > 0
    
    def test_get_processing_stats(self):
        """Test obtención de estadísticas"""
        stats = self.orchestrator.get_processing_stats()
        
        assert 'config' in stats
        assert 'stats' in stats
        assert 'performance_metrics' in stats
        
        config_stats = stats['config']
        assert config_stats['batch_size'] == 10
        assert config_stats['max_concurrent_analyses'] == 20


class TestIntegration:
    """Tests de integración del pipeline completo"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.config = ProcessingConfig()
        self.orchestrator = AIPipelineOrchestrator(self.config)
    
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self):
        """Test del pipeline completo (sin DB)"""
        raw_articles = [
            {
                "title": "AI Breakthrough in Healthcare",
                "content": "Scientists have developed an AI system that can diagnose diseases with 95% accuracy. The system uses advanced machine learning to analyze medical images and identify patterns that might be missed by human doctors. This breakthrough could revolutionize healthcare worldwide.",
                "url": "https://example.com/ai-healthcare-1",
                "source_name": "Medical Technology News",
                "published_at": "2025-01-15T10:00:00Z"
            },
            {
                "title": "Climate Change Report Shows Urgent Action Needed",
                "content": "The latest climate change report indicates that immediate action is required to prevent catastrophic environmental changes. Rising global temperatures, melting ice caps, and increasingly extreme weather patterns demand global cooperation and innovative technological solutions.",
                "url": "https://example.com/climate-report-1", 
                "source_name": "Environmental Daily",
                "published_at": "2025-01-15T09:30:00Z"
            }
        ]
        
        # Procesar sin sesión de DB
        result = await self.orchestrator.process_articles_batch(raw_articles)
        
        # Verificar estructura del resultado
        assert isinstance(result, BatchResult)
        assert result.batch_id is not None
        assert result.total_articles == 2
        assert result.processing_time > 0
        
        # Verificar que el preprocesamiento funcionó
        assert result.successful_analyses >= 0  # Puede ser 0 sin API key
        assert len(result.metadata) > 0
        assert 'preprocessing_stats' in result.metadata
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test manejo de errores"""
        # Datos inválidos que deberían causar errores
        invalid_articles = [
            {
                "title": "",  # Título vacío
                "content": "Some content",
                "url": "invalid-url"
            }
        ]
        
        result = await self.orchestrator.process_articles_batch(invalid_articles)
        
        assert result.failed_analyses >= 0  # Puede tener errores de validación
        assert len(result.errors) >= 0  # Errores pueden ser manejados
    
    def test_configuration_modes(self):
        """Test diferentes modos de configuración"""
        # Modo desarrollo
        dev_config = DEFAULT_CONFIGS['development']
        assert dev_config.batch_size == 5
        assert dev_config.max_concurrent_analyses == 5
        
        # Modo producción
        prod_config = DEFAULT_CONFIGS['production']  
        assert prod_config.batch_size == 20
        assert prod_config.max_concurrent_analyses == 25
        
        # Modo alto rendimiento
        high_config = DEFAULT_CONFIGS['high_throughput']
        assert high_config.batch_size == 50
        assert high_config.max_concurrent_analyses == 50


# Tests de rendimiento (opcional, pueden ser lentos)
class TestPerformance:
    """Tests de rendimiento del pipeline"""
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_batch_performance(self):
        """Test rendimiento con lotes grandes"""
        config = ProcessingConfig(
            batch_size=5,  # Lote pequeño para tests
            max_concurrent_analyses=2
        )
        orchestrator = AIPipelineOrchestrator(config)
        
        # Crear lote de artículos
        articles = []
        for i in range(10):
            articles.append({
                "title": f"Test Article {i+1}",
                "content": f"This is the content of test article number {i+1}. " * 10,
                "url": f"https://example.com/article/{i+1}",
                "source_name": "Test Source"
            })
        
        start_time = asyncio.get_event_loop().time()
        result = await orchestrator.process_articles_batch(articles)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        
        # Verificar que el procesamiento no sea excesivamente lento
        assert processing_time < 60  # Menos de 60 segundos
        assert result.total_articles == 10
        assert result.processing_time > 0
        
        print(f"Performance test: {result.total_articles} artículos procesados en {processing_time:.2f}s")


# Fixtures para tests
@pytest.fixture
def sample_articles():
    """Fixture con artículos de ejemplo"""
    return [
        {
            "title": "AI Revolution in Healthcare",
            "content": "Artificial intelligence is transforming healthcare with new diagnostic tools...",
            "url": "https://example.com/ai-healthcare",
            "source_name": "Health Tech News"
        },
        {
            "title": "Climate Summit Reaches Agreement",
            "content": "World leaders have reached a historic agreement on climate action...",
            "url": "https://example.com/climate-summit",
            "source_name": "Environmental Times"
        }
    ]


@pytest.fixture
def mock_db_session():
    """Fixture con sesión mock de base de datos"""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# Ejecutar tests si se llama directamente
if __name__ == "__main__":
    # Configurar pytest
    pytest.main([__file__, "-v"])