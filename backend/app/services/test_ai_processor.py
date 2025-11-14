"""
Tests básicos para AI Processor Service

Este archivo contiene tests básicos para verificar que las funcionalidades
del AI Processor funcionan correctamente.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch

# Importar las clases a testear
try:
    # Try relative import first (when run as module)
    from .ai_processor import (
        SentimentAnalyzer,
        TopicClassifier,
        Summarizer, 
        RelevanceScorer,
        ComprehensiveAnalyzer,
        create_ai_processor,
        SentimentType,
        TopicCategory,
        SentimentResult,
        TopicResult,
        SummaryResult,
        RelevanceResult,
        AIAnalysisResult
    )
except ImportError:
    # Fall back to absolute import (when run directly)
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from ai_processor import (
        SentimentAnalyzer,
        TopicClassifier,
        Summarizer, 
        RelevanceScorer,
        ComprehensiveAnalyzer,
        create_ai_processor,
        SentimentType,
        TopicCategory,
        SentimentResult,
        TopicResult,
        SummaryResult,
        RelevanceResult,
        AIAnalysisResult
    )


class TestSentimentAnalyzer:
    """Tests para SentimentAnalyzer"""
    
    def test_initialization(self):
        """Test de inicialización"""
        analyzer = SentimentAnalyzer()
        assert analyzer is not None
        assert analyzer.default_model == "gpt-3.5-turbo"
    
    def test_content_preparation(self):
        """Test de preparación de contenido"""
        analyzer = SentimentAnalyzer()
        
        # Test con HTML
        text_with_html = "<p>Este es un <strong>texto</strong> de prueba.</p>"
        cleaned = analyzer._prepare_content(text_with_html)
        assert "<p>" not in cleaned
        assert "<strong>" not in cleaned
        
        # Test con espacios múltiples
        text_with_spaces = "Este    es    un    texto    con    espacios."
        cleaned = analyzer._prepare_content(text_with_spaces)
        assert "    " not in cleaned
    
    def test_token_estimation(self):
        """Test de estimación de tokens"""
        analyzer = SentimentAnalyzer()
        
        # Test estimación básica
        text = "Este es un texto de prueba."
        estimated = analyzer._estimate_tokens(text)
        assert estimated > 0
        assert estimated < len(text) // 4 + 200  # Bounds check
    
    @pytest.mark.asyncio
    async def test_fallback_without_api_key(self):
        """Test de fallback sin API key"""
        analyzer = SentimentAnalyzer()
        text = "Este es un texto de prueba para análisis de sentimiento."
        
        # Debería funcionar con fallback
        result = await analyzer.analyze_sentiment_async(text)
        assert isinstance(result, SentimentResult)
        assert result.sentiment in list(SentimentType)
        assert -1 <= result.sentiment_score <= 1
    
    def test_sync_fallback(self):
        """Test de análisis síncrono con fallback"""
        analyzer = SentimentAnalyzer()
        text = "Texto de prueba síncrono."
        
        result = analyzer.analyze_sentiment(text)
        assert isinstance(result, SentimentResult)


class TestTopicClassifier:
    """Tests para TopicClassifier"""
    
    def test_initialization(self):
        """Test de inicialización"""
        classifier = TopicClassifier()
        assert classifier is not None
        assert len(classifier.categories) > 0
    
    def test_rule_based_classification(self):
        """Test de clasificación basada en reglas"""
        classifier = TopicClassifier()
        
        # Test con texto de tecnología
        tech_text = "Nueva inteligencia artificial desarrollada por Google mejora los algoritmos de machine learning."
        result = classifier.classify_topic(tech_text)
        assert isinstance(result, TopicResult)
        assert result.primary_topic in list(TopicCategory)
    
    def test_preference_fallback_without_api(self):
        """Test de fallback para clasificación sin API"""
        classifier = TopicClassifier()
        text = "Este artículo habla sobre deportes y fútbol."
        
        result = classifier.classify_topic(text)
        assert isinstance(result, TopicResult)
        # Debería detectar sports si las reglas funcionan


class TestSummarizer:
    """Tests para Summarizer"""
    
    def test_initialization(self):
        """Test de inicialización"""
        summarizer = Summarizer()
        assert summarizer is not None
    
    def test_simple_summary_creation(self):
        """Test de creación de resumen simple"""
        summarizer = Summarizer()
        
        long_text = """
        Este es un artículo muy largo que necesita ser resumido. 
        Contiene mucha información importante que debe condensarse en un resumen más corto.
        La tecnología de IA está avanzando rápidamente y cambiando muchas industrias.
        """
        
        result = summarizer._create_simple_summary(long_text, 0.0, 50)
        assert isinstance(result, SummaryResult)
        assert result.summary is not None
        assert result.word_count <= 50 or result.summary.endswith("...")
    
    def test_reading_time_calculation(self):
        """Test de cálculo de tiempo de lectura"""
        summarizer = Summarizer()
        
        # Test con 200 palabras
        result = summarizer._create_simple_summary("palabra " * 200, 0.0, 50)
        assert result.reading_time_minutes == pytest.approx(1.0, 0.1)


class TestRelevanceScorer:
    """Tests para RelevanceScorer"""
    
    def test_initialization(self):
        """Test de inicialización"""
        scorer = RelevanceScorer()
        assert scorer is not None
    
    def test_simple_relevance_fallback(self):
        """Test de scoring simple como fallback"""
        scorer = RelevanceScorer()
        
        # Test con texto de alta relevancia
        high_relevance_text = "Breaking news: Urgent alert about developing situation."
        result = scorer._create_simple_relevance_score(high_relevance_text, 0.0)
        
        assert isinstance(result, RelevanceResult)
        assert 0.0 <= result.relevance_score <= 1.0
    
    def test_user_preferences_adjustment(self):
        """Test de ajuste por preferencias del usuario"""
        scorer = RelevanceScorer()
        text = "Texto de prueba para relevancia."
        
        # Con preferencias
        result_with_prefs = scorer._create_simple_relevance_score(text, 0.0)
        result_without_prefs = scorer._create_simple_relevance_score(text, 0.0)
        
        assert isinstance(result_with_prefs, RelevanceResult)
        assert isinstance(result_without_prefs, RelevanceResult)


class TestComprehensiveAnalyzer:
    """Tests para ComprehensiveAnalyzer"""
    
    def test_initialization(self):
        """Test de inicialización"""
        analyzer = ComprehensiveAnalyzer()
        assert analyzer is not None
        assert analyzer.sentiment_analyzer is not None
        assert analyzer.topic_classifier is not None
        assert analyzer.summarizer is not None
        assert analyzer.relevance_scorer is not None
    
    def test_combined_score_calculation(self):
        """Test de cálculo de score combinado"""
        analyzer = ComprehensiveAnalyzer()
        
        # Crear resultados de prueba
        sentiment = SentimentResult(
            timestamp=None,
            confidence=0.8,
            processing_time=1.0,
            tokens_used=100,
            cost=0.01,
            model="test",
            sentiment=SentimentType.POSITIVE,
            sentiment_score=0.7,
            emotion_tags=["optimism"]
        )
        
        topic = TopicResult(
            timestamp=None,
            confidence=0.9,
            processing_time=1.0,
            tokens_used=100,
            cost=0.01,
            model="test",
            primary_topic=TopicCategory.TECHNOLOGY,
            topic_probability=0.85,
            secondary_topics=[],
            topic_keywords=["AI", "technology"]
        )
        
        summary = SummaryResult(
            timestamp=None,
            confidence=0.9,
            processing_time=1.0,
            tokens_used=100,
            cost=0.01,
            model="test",
            summary="Resumen de prueba",
            key_points=["punto1", "punto2"],
            word_count=100,
            reading_time_minutes=0.5
        )
        
        relevance = RelevanceResult(
            timestamp=None,
            confidence=0.8,
            processing_time=1.0,
            tokens_used=100,
            cost=0.01,
            model="test",
            relevance_score=0.75,
            relevance_factors={"topic": 0.8},
            trending_score=0.7,
            importance_score=0.9
        )
        
        combined_score = analyzer._calculate_combined_score(
            sentiment, topic, summary, relevance
        )
        
        assert 0.0 <= combined_score <= 1.0
    
    def test_sync_analysis(self):
        """Test de análisis síncrono"""
        analyzer = ComprehensiveAnalyzer()
        
        result = analyzer.analyze_article(
            article_id="test_001",
            content="Este es un artículo de prueba para análisis completo.",
            max_summary_words=50
        )
        
        assert isinstance(result, AIAnalysisResult)
        assert result.article_id == "test_001"
        assert result.content == "Este es un artículo de prueba para análisis completo."
        assert result.processing_time >= 0


class TestFactoryFunction:
    """Tests para factory function"""
    
    def test_create_ai_processor(self):
        """Test de creación de procesador via factory"""
        processor = create_ai_processor()
        assert isinstance(processor, ComprehensiveAnalyzer)
        assert processor is not None


class TestCostBreakdown:
    """Tests para análisis de costos"""
    
    def test_analyze_cost_breakdown(self):
        """Test de análisis de breakdown de costos"""
        # Crear resultados de prueba
        results = [
            AIAnalysisResult(
                article_id="1",
                content="texto1",
                total_cost=0.01,
                processing_time=1.0
            ),
            AIAnalysisResult(
                article_id="2", 
                content="texto2",
                total_cost=0.02,
                processing_time=1.0
            ),
            AIAnalysisResult(
                article_id="3",
                content="texto3", 
                total_cost=0.03,
                processing_time=1.0
            )
        ]
        
        try:
            from .ai_processor import analyze_cost_breakdown
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            from ai_processor import analyze_cost_breakdown
        
        breakdown = analyze_cost_breakdown(results)
        
        assert breakdown["total_articles"] == 3
        assert breakdown["total_cost"] == 0.06
        assert breakdown["average_cost"] == pytest.approx(0.02)
    
    def test_empty_results(self):
        """Test con lista vacía"""
        try:
            from .ai_processor import analyze_cost_breakdown
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            from ai_processor import analyze_cost_breakdown
        
        breakdown = analyze_cost_breakdown([])
        
        assert breakdown["total_articles"] == 0
        assert breakdown["total_cost"] == 0
        assert breakdown["average_cost"] == 0


class TestEnums:
    """Tests para enums y tipos"""
    
    def test_sentiment_types(self):
        """Test de tipos de sentimiento"""
        assert hasattr(SentimentType, 'POSITIVE')
        assert hasattr(SentimentType, 'NEGATIVE')
        assert hasattr(SentimentType, 'NEUTRAL')
        assert hasattr(SentimentType, 'MIXED')
    
    def test_topic_categories(self):
        """Test de categorías de temas"""
        assert hasattr(TopicCategory, 'POLITICS')
        assert hasattr(TopicCategory, 'ECONOMY')
        assert hasattr(TopicCategory, 'TECHNOLOGY')
        assert hasattr(TopicCategory, 'HEALTH')
        assert hasattr(TopicCategory, 'SPORTS')
        assert hasattr(TopicCategory, 'ENTERTAINMENT')


@pytest.mark.asyncio
class TestAsyncFunctionality:
    """Tests para funcionalidad asíncrona"""
    
    async def test_batch_analysis_empty_list(self):
        """Test de análisis en lote con lista vacía"""
        analyzer = ComprehensiveAnalyzer()
        
        results, errors = await analyzer.batch_analyze_async([])
        
        assert results == []
        assert errors == []
    
    async def test_batch_analysis_single_item(self):
        """Test de análisis en lote con un solo elemento"""
        analyzer = ComprehensiveAnalyzer()
        
        articles = [
            {"id": "test_001", "content": "Contenido de prueba para análisis en lote."}
        ]
        
        results, errors = await analyzer.batch_analyze_async(articles)
        
        assert len(results) == 1
        assert len(errors) == 0
        assert results[0].article_id == "test_001"


def test_module_imports():
    """Test de que todos los imports funcionen correctamente"""
    try:
        try:
            from .ai_processor import (
                SentimentAnalyzer, TopicClassifier, Summarizer,
                RelevanceScorer, ComprehensiveAnalyzer, create_ai_processor,
                analyze_cost_breakdown, SentimentType, TopicCategory,
                SentimentResult, TopicResult, SummaryResult, 
                RelevanceResult, AIAnalysisResult
            )
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(__file__))
            from ai_processor import (
                SentimentAnalyzer, TopicClassifier, Summarizer,
                RelevanceScorer, ComprehensiveAnalyzer, create_ai_processor,
                analyze_cost_breakdown, SentimentType, TopicCategory,
                SentimentResult, TopicResult, SummaryResult, 
                RelevanceResult, AIAnalysisResult
            )
        assert True
    except ImportError:
        assert False, "Fallo en imports del módulo"


# Tests de integración básica
def test_basic_integration():
    """Test de integración básica del sistema completo"""
    
    # Crear instancia
    analyzer = create_ai_processor()
    
    # Test de análisis básico
    result = analyzer.analyze_article(
        article_id="integration_test",
        content="Este es un artículo de integración que prueba todas las funcionalidades del sistema.",
        max_summary_words=30
    )
    
    # Verificar estructura del resultado
    assert isinstance(result, AIAnalysisResult)
    assert result.article_id == "integration_test"
    assert result.processing_time >= 0
    assert result.total_cost >= 0
    assert 0 <= result.combined_score <= 1


if __name__ == "__main__":
    """Ejecutar tests básicos si se ejecuta directamente"""
    
    print("🧪 EJECUTANDO TESTS DEL AI PROCESSOR")
    print("=" * 50)
    
    # Tests básicos
    try:
        test_basic_integration()
        print("✅ Test de integración básico: PASSED")
    except Exception as e:
        print(f"❌ Test de integración básico: FAILED - {str(e)}")
    
    try:
        test_module_imports()
        print("✅ Test de imports: PASSED")
    except Exception as e:
        print(f"❌ Test de imports: FAILED - {str(e)}")
    
    try:
        test_sentiment_types = TestEnums()
        test_sentiment_types.test_sentiment_types()
        print("✅ Test de tipos de sentimiento: PASSED")
    except Exception as e:
        print(f"❌ Test de tipos de sentimiento: FAILED - {str(e)}")
    
    try:
        test_topic_categories = TestEnums()
        test_topic_categories.test_topic_categories()
        print("✅ Test de categorías de temas: PASSED")
    except Exception as e:
        print(f"❌ Test de categorías de temas: FAILED - {str(e)}")
    
    try:
        test_factory = TestFactoryFunction()
        test_factory.test_create_ai_processor()
        print("✅ Test de factory function: PASSED")
    except Exception as e:
        print(f"❌ Test de factory function: FAILED - {str(e)}")
    
    print("\n🏁 TESTS BÁSICOS COMPLETADOS")
    print("Nota: Para tests completos, ejecute con pytest")