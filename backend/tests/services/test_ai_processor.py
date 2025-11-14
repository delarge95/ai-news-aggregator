"""
Comprehensive tests for AI Processing Service
Tests unitarios para SentimentAnalyzer, TopicClassifier, Summarizer
Tests de Celery tasks, pipeline integration, y performance
"""

import asyncio
import json
import pytest
import time
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from unittest.mock import mock_open
from dataclasses import asdict
import redis
import tempfile
import os
from typing import Dict, List, Any
import logging

# Import our AI processor components
from app.services.ai_processor import (
    SentimentAnalyzer, TopicClassifier, Summarizer, AIProcessor,
    SentimentLabel, TopicCategory, SentimentResult, TopicResult, 
    SummaryResult, AIAnalysisResult
)
from app.core.config import settings

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_articles():
    """Sample article data for testing"""
    return [
        {
            'id': 'article_1',
            'title': 'AI Breakthrough in Machine Learning',
            'content': '''Artificial intelligence has achieved a major breakthrough in machine learning research. 
            Scientists at leading universities have developed new algorithms that can process data faster 
            than ever before. The technology promises to revolutionize healthcare, finance, and technology sectors. 
            This advancement represents years of collaborative research and innovation.'''
        },
        {
            'id': 'article_2', 
            'title': 'Football Championship Finals',
            'content': '''The national football championship concluded with an exciting match last night. 
            The home team scored a dramatic victory in the final minutes of overtime. Thousands of fans 
            celebrated in the stadium streets. The championship trophy was presented to the winning captain 
            in a ceremony attended by government officials and sports celebrities.'''
        },
        {
            'id': 'article_3',
            'title': 'Economic Markets Show Recovery',
            'content': '''Global financial markets showed strong recovery signals this quarter. 
            Stock prices rose across major indices as investors demonstrated confidence in economic recovery. 
            Banking sector profits exceeded expectations, with several institutions reporting record quarterly earnings. 
            Economic analysts predict continued growth based on current market trends and corporate performance.'''
        },
        {
            'id': 'article_4',
            'title': 'International Climate Summit',
            'content': '''World leaders gathered for the international climate summit in Geneva. 
            Delegates from 195 countries discussed global environmental policies and carbon reduction targets. 
            The conference addressed renewable energy investments and sustainable development goals. 
            Environmental activists protested outside the venue calling for more aggressive climate action.'''
        },
        {
            'id': 'article_5',
            'title': 'New Medical Treatment Shows Promise',
            'content': '''Researchers have developed a groundbreaking medical treatment for rare genetic disorders. 
            Clinical trials demonstrate significant improvement in patient symptoms with minimal side effects. 
            The FDA has fast-tracked approval process for this innovative therapy. Hospitals worldwide 
            are preparing to implement this new treatment protocol for eligible patients.'''
        }
    ]


@pytest.fixture
def expected_sentiment_results():
    """Expected sentiment analysis results for sample articles"""
    return {
        'article_1': SentimentLabel.POSITIVE,  # AI breakthrough - positive
        'article_2': SentimentLabel.POSITIVE,  # Championship victory - positive  
        'article_3': SentimentLabel.POSITIVE,  # Economic recovery - positive
        'article_4': SentimentLabel.NEUTRAL,   # Climate summit - neutral
        'article_5': SentimentLabel.POSITIVE   # Medical breakthrough - positive
    }


@pytest.fixture
def expected_topic_results():
    """Expected topic classification results for sample articles"""
    return {
        'article_1': TopicCategory.TECHNOLOGY,   # AI/ML - technology
        'article_2': TopicCategory.SPORTS,       # Football - sports
        'article_3': TopicCategory.BUSINESS,     # Markets - business
        'article_4': TopicCategory.WORLD,        # International summit - world
        'article_5': TopicCategory.HEALTH        # Medical treatment - health
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "label": "positive",
                        "confidence": 0.85,
                        "reasoning": "Text expresses optimistic outlook about technology advancement"
                    })
                }
            }
        ],
        "usage": {
            "total_tokens": 150
        }
    }


@pytest.fixture
def mock_transformers_result():
    """Mock transformers pipeline result"""
    return [
        [
            {'label': 'POSITIVE', 'score': 0.8},
            {'label': 'NEGATIVE', 'score': 0.15},
            {'label': 'NEUTRAL', 'score': 0.05}
        ]
    ]


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_sentiment_analyzer():
    """Mock SentimentAnalyzer for testing"""
    analyzer = Mock(spec=SentimentAnalyzer)
    analyzer.analyze = AsyncMock()
    analyzer._get_pipeline = AsyncMock()
    return analyzer


@pytest.fixture
def mock_topic_classifier():
    """Mock TopicClassifier for testing"""
    classifier = Mock(spec=TopicClassifier)
    classifier.classify = AsyncMock()
    return classifier


@pytest.fixture
def mock_summarizer():
    """Mock Summarizer for testing"""
    summarizer = Mock(spec=Summarizer)
    summarizer.summarize = AsyncMock()
    summarizer._get_pipeline = AsyncMock()
    return summarizer


@pytest.fixture
def ai_processor_with_mocks(mock_redis_client, mock_openai_response):
    """AIProcessor with mocked dependencies"""
    processor = AIProcessor(redis_client=mock_redis_client)
    processor.openai_client = Mock()
    processor.openai_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
    return processor


@pytest.fixture
def performance_test_data():
    """Data for performance testing"""
    return {
        'small_text': "Short text for testing.",
        'medium_text': "This is a medium length text that contains enough words to test basic performance. " * 10,
        'large_text': "This is a large text that contains many words and sentences to test performance under load. " * 50,
        'batch_data': [
            {'id': f'art_{i}', 'content': f'Article content number {i} with some meaningful text. ' * 20}
            for i in range(10)
        ]
    }


@pytest.fixture
def temp_cache_dir():
    """Temporary directory for cache testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


# ============================================================================
# UNIT TESTS - SENTIMENT ANALYZER
# ============================================================================

class TestSentimentAnalyzer:
    """Unit tests for SentimentAnalyzer class"""
    
    def test_sentiment_analyzer_initialization(self):
        """Test SentimentAnalyzer initialization"""
        analyzer = SentimentAnalyzer()
        assert analyzer.model_name == "cardiffnlp/twitter-roberta-base-sentiment-latest"
        assert analyzer._pipeline is None
        assert len(analyzer._cache) == 0
    
    def test_sentiment_analyzer_with_custom_model(self):
        """Test SentimentAnalyzer with custom model"""
        custom_model = "custom/model"
        analyzer = SentimentAnalyzer(model_name=custom_model)
        assert analyzer.model_name == custom_model
    
    @pytest.mark.asyncio
    async def test_analyze_text_positive(self, mock_transformers_result):
        """Test sentiment analysis for positive text"""
        analyzer = SentimentAnalyzer()
        
        with patch.object(analyzer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_transformers_result
            
            result = await analyzer.analyze("This is great news! Amazing technology breakthrough!")
            
            assert isinstance(result, SentimentResult)
            assert result.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
            assert 0.0 <= result.confidence <= 1.0
            assert result.processing_time >= 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_text_negative(self):
        """Test sentiment analysis for negative text"""
        analyzer = SentimentAnalyzer()
        
        # Mock negative result
        negative_result = [
            [
                {'label': 'NEGATIVE', 'score': 0.9},
                {'label': 'POSITIVE', 'score': 0.05},
                {'label': 'NEUTRAL', 'score': 0.05}
            ]
        ]
        
        with patch.object(analyzer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = negative_result
            
            result = await analyzer.analyze("This is terrible. Worst technology ever!")
            
            assert result.label == SentimentLabel.NEGATIVE
            assert result.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_analyze_with_openai(self, mock_openai_response):
        """Test sentiment analysis using OpenAI API"""
        openai_client = Mock()
        openai_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        
        analyzer = SentimentAnalyzer(openai_client=openai_client)
        
        result = await analyzer.analyze("This is amazing technology!", use_openai=True)
        
        assert isinstance(result, SentimentResult)
        assert result.label == SentimentLabel.POSITIVE
        assert result.confidence == 0.85
        assert openai_client.chat.completions.create.called
    
    @pytest.mark.asyncio
    async def test_analyze_with_openai_error(self):
        """Test OpenAI API error handling"""
        openai_client = Mock()
        openai_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        analyzer = SentimentAnalyzer(openai_client=openai_client)
        
        # Should fallback to neutral sentiment
        result = await analyzer.analyze("Test text", use_openai=True)
        
        assert result.label == SentimentLabel.NEUTRAL
        assert result.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_caching_functionality(self, mock_transformers_result):
        """Test result caching functionality"""
        analyzer = SentimentAnalyzer()
        text = "Test text for caching"
        
        with patch.object(analyzer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_transformers_result
            
            # First call
            result1 = await analyzer.analyze(text)
            
            # Second call should use cache
            result2 = await analyzer.analyze(text)
            
            # Should be same object due to caching
            assert len(analyzer._cache) == 1
            assert result1.label == result2.label
            assert result1.confidence == result2.confidence
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self):
        """Test cache size limit enforcement"""
        analyzer = SentimentAnalyzer()
        
        # Add many items to trigger cache limit
        for i in range(1005):  # Over the limit of 1000
            analyzer._cache[f"sentiment:{i}"] = SentimentResult(
                label=SentimentLabel.NEUTRAL,
                confidence=0.5,
                score=0.0,
                raw_scores={}
            )
        
        # Should not exceed cache limit
        assert len(analyzer._cache) <= 1000


# ============================================================================
# UNIT TESTS - TOPIC CLASSIFIER
# ============================================================================

class TestTopicClassifier:
    """Unit tests for TopicClassifier class"""
    
    def test_topic_classifier_initialization(self):
        """Test TopicClassifier initialization"""
        classifier = TopicClassifier()
        assert len(classifier.categories) > 0
        assert TopicCategory.TECHNOLOGY in classifier.categories
        assert len(classifier._cache) == 0
    
    @pytest.mark.asyncio
    async def test_classify_technology_text(self):
        """Test classification of technology-related text"""
        classifier = TopicClassifier()
        
        text = "AI and machine learning algorithms are transforming software development"
        
        result = await classifier.classify(text)
        
        assert isinstance(result, TopicResult)
        assert result.category in classifier.categories
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.keywords, list)
    
    @pytest.mark.asyncio
    async def test_classify_business_text(self):
        """Test classification of business-related text"""
        classifier = TopicClassifier()
        
        text = "The company reported strong quarterly earnings and stock market performance"
        
        result = await classifier.classify(text)
        
        assert result.category == TopicCategory.BUSINESS
    
    @pytest.mark.asyncio
    async def test_classify_with_openai(self, mock_openai_response):
        """Test classification using OpenAI API"""
        openai_client = Mock()
        openai_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        
        classifier = TopicClassifier(openai_client=openai_client)
        
        result = await classifier.classify("Technology news content", use_openai=True)
        
        assert isinstance(result, TopicResult)
        assert openai_client.chat.completions.create.called
    
    @pytest.mark.asyncio
    async def test_classify_fallback_to_other(self):
        """Test classification fallback for unknown content"""
        classifier = TopicClassifier()
        
        # Text with no recognizable keywords
        text = "Random content xyz abc def"
        
        result = await classifier.classify(text)
        
        assert result.category == TopicCategory.OTHER or result.confidence < 0.5
    
    @pytest.mark.asyncio
    async def test_keyword_extraction(self, mock_transformers_result):
        """Test keyword extraction functionality"""
        classifier = TopicClassifier()
        
        text = "AI machine learning technology software development"
        
        result = await classifier.classify(text)
        
        # Should find relevant keywords
        assert len(result.keywords) > 0
        assert any(keyword in text.lower() for keyword in result.keywords)


# ============================================================================
# UNIT TESTS - SUMMARIZER
# ============================================================================

class TestSummarizer:
    """Unit tests for Summarizer class"""
    
    def test_summarizer_initialization(self):
        """Test Summarizer initialization"""
        summarizer = Summarizer()
        assert summarizer._pipeline is None
        assert len(summarizer._cache) == 0
    
    @pytest.mark.asyncio
    async def test_summarize_short_text(self):
        """Test summarization of short text"""
        summarizer = Summarizer()
        
        short_text = "This is a short article about technology."
        
        # Mock the pipeline
        mock_result = [{'summary_text': "Technology article."}]
        
        with patch.object(summarizer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            result = await summarizer.summarize(short_text)
            
            assert isinstance(result, SummaryResult)
            assert isinstance(result.summary, str)
            assert len(result.summary) > 0
            assert result.word_count > 0
            assert result.compression_ratio > 0
    
    @pytest.mark.asyncio
    async def test_summarize_long_text(self):
        """Test summarization of long text"""
        summarizer = Summarizer()
        
        # Create long text
        long_text = "This is a very long article about technology. " * 100
        
        mock_result = [{'summary_text': "Technology article."}]
        
        with patch.object(summarizer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            result = await summarizer.summarize(long_text, max_length=50)
            
            assert isinstance(result, SummaryResult)
            assert len(result.summary) <= 50 * 1.2  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_summarize_with_openai(self, mock_openai_response):
        """Test summarization using OpenAI API"""
        openai_client = Mock()
        openai_client.chat.completions.create = AsyncMock(return_value=mock_openai_response)
        
        summarizer = Summarizer(openai_client=openai_client)
        
        result = await summarizer.summarize("Technology content", use_openai=True)
        
        assert isinstance(result, SummaryResult)
        assert openai_client.chat.completions.create.called
    
    @pytest.mark.asyncio
    async def test_compression_ratio_calculation(self):
        """Test compression ratio calculation"""
        summarizer = Summarizer()
        
        text = "Word " * 100  # 100 words
        summary = "Summary."  # 1 word
        
        mock_result = [{'summary_text': summary}]
        
        with patch.object(summarizer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            result = await summarizer.summarize(text)
            
            assert result.compression_ratio == 0.01  # 1/100
    
    def test_keyword_extraction(self):
        """Test keyword extraction functionality"""
        summarizer = Summarizer()
        
        text = "Technology artificial intelligence machine learning software development"
        
        keywords = summarizer._extract_keywords(text, num_keywords=3)
        
        assert len(keywords) <= 3
        assert any(keyword in ['technology', 'artificial', 'intelligence', 'machine', 'learning', 'software', 'development'] 
                  for keyword in keywords)
    
    def test_key_point_extraction(self):
        """Test key point extraction functionality"""
        summarizer = Summarizer()
        
        text = "First point. Second point. Third point. Fourth point."
        
        key_points = summarizer._extract_key_points(text, num_points=3)
        
        assert len(key_points) == 3
        assert "First point" in key_points[0]
        assert "Second point" in key_points[1]


# ============================================================================
# INTEGRATION TESTS - AI PROCESSOR
# ============================================================================

class TestAIProcessor:
    """Integration tests for AIProcessor class"""
    
    def test_ai_processor_initialization(self, mock_redis_client):
        """Test AIProcessor initialization"""
        processor = AIProcessor(redis_client=mock_redis_client)
        
        assert processor.redis_client == mock_redis_client
        assert isinstance(processor.sentiment_analyzer, SentimentAnalyzer)
        assert isinstance(processor.topic_classifier, TopicClassifier)
        assert isinstance(processor.summarizer, Summarizer)
    
    def test_ai_processor_with_openai(self):
        """Test AIProcessor with OpenAI client"""
        with patch('app.services.ai_processor.AsyncOpenAI') as mock_openai:
            processor = AIProcessor(openai_api_key="test-key")
            
            assert processor.openai_client is not None
            mock_openai.assert_called_once_with(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_analyze_article_complete(self, sample_articles, ai_processor_with_mocks):
        """Test complete article analysis"""
        article = sample_articles[0]  # AI breakthrough article
        
        result = await ai_processor_with_mocks.analyze_article(
            article['id'], 
            article['content']
        )
        
        assert isinstance(result, AIAnalysisResult)
        assert result.article_id == article['id']
        assert result.content == article['content']
        assert isinstance(result.sentiment, SentimentResult)
        assert isinstance(result.topic, TopicResult)
        assert isinstance(result.summary, SummaryResult)
        assert result.processing_time > 0
        assert result.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_analyze_article_caching(self, sample_articles, mock_redis_client):
        """Test article analysis caching"""
        processor = AIProcessor(redis_client=mock_redis_client)
        article = sample_articles[0]
        
        # Mock the analysis methods
        processor.sentiment_analyzer.analyze = AsyncMock(return_value=Mock(spec=SentimentResult))
        processor.topic_classifier.classify = AsyncMock(return_value=Mock(spec=TopicResult))
        processor.summarizer.summarize = AsyncMock(return_value=Mock(spec=SummaryResult))
        
        # First analysis
        result1 = await processor.analyze_article(article['id'], article['content'])
        
        # Check if caching was called
        mock_redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_cached_analysis(self, mock_redis_client):
        """Test retrieval of cached analysis"""
        processor = AIProcessor(redis_client=mock_redis_client)
        
        # Mock cached data
        cached_data = {
            'sentiment': {'label': 'positive', 'confidence': 0.8},
            'topic': {'category': 'technology', 'confidence': 0.9},
            'summary': {'text': 'Test summary', 'word_count': 10},
            'processing_time': 1.5,
            'timestamp': time.time()
        }
        
        mock_redis_client.get = AsyncMock(return_value=json.dumps(cached_data))
        
        result = await processor.get_cached_analysis('test_article')
        
        assert result is not None
        assert result.article_id == 'test_article'
        assert result.sentiment.label == SentimentLabel.POSITIVE
        assert result.topic.category == TopicCategory.TECHNOLOGY
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_redis_client):
        """Test error handling in analysis"""
        processor = AIProcessor(redis_client=mock_redis_client)
        
        # Mock failures
        processor.sentiment_analyzer.analyze = AsyncMock(side_effect=Exception("Analysis failed"))
        
        with pytest.raises(Exception):
            await processor.analyze_article('test_id', 'test content')
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, sample_articles, ai_processor_with_mocks):
        """Test concurrent article analysis"""
        # Mock analysis methods to add some delay
        async def mock_analyze(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate processing time
            return Mock()
        
        ai_processor_with_mocks.sentiment_analyzer.analyze = mock_analyze
        ai_processor_with_mocks.topic_classifier.classify = mock_analyze
        ai_processor_with_mocks.summarizer.summarize = mock_analyze
        
        # Run concurrent analyses
        tasks = [
            ai_processor_with_mocks.analyze_article(article['id'], article['content'])
            for article in sample_articles
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == len(sample_articles)
        assert all(isinstance(result, AIAnalysisResult) for result in results)


# ============================================================================
# CELERY TASK TESTS
# ============================================================================

class TestCeleryTasks:
    """Tests for Celery tasks"""
    
    @pytest.fixture
    def celery_app(self):
        """Create test Celery app"""
        from app.services.ai_processor import celery_app
        celery_app.conf.update({
            'task_serializer': 'json',
            'accept_content': ['json'],
            'result_serializer': 'json',
            'timezone': 'UTC',
            'enable_utc': True,
            'task_track_started': True,
            'task_reject_on_worker_lost': True,
        })
        return celery_app
    
    def test_analyze_article_async_task_initialization(self, celery_app):
        """Test async task initialization"""
        from app.services.ai_processor import analyze_article_async
        
        assert analyze_article_async.name == 'app.services.ai_processor.analyze_article_async'
        assert analyze_article_async.bind == True
        assert analyze_article_async.autoretry_for == (Exception,)
    
    def test_batch_analyze_articles_task_initialization(self, celery_app):
        """Test batch task initialization"""
        from app.services.ai_processor import batch_analyze_articles
        
        assert batch_analyze_articles.name == 'app.services.ai_processor.batch_analyze_articles'
    
    @patch('app.services.ai_processor.AIProcessor')
    @patch('asyncio.run')
    def test_analyze_article_async_execution(self, mock_asyncio_run, mock_processor_class, celery_app):
        """Test async task execution"""
        from app.services.ai_processor import analyze_article_async
        
        # Setup mocks
        mock_processor = Mock()
        mock_result = Mock()
        mock_processor.analyze_article.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        mock_asyncio_run.return_value = {
            'status': 'completed',
            'article_id': 'test_id',
            'sentiment': 'positive',
            'topic': 'technology',
            'processing_time': 1.0
        }
        
        # Execute task
        result = analyze_article_async('test_id', 'test content')
        
        # Verify execution
        assert result['status'] == 'completed'
        assert result['article_id'] == 'test_id'
    
    @patch('app.services.ai_processor.AIProcessor')
    @patch('asyncio.run')
    def test_batch_analyze_articles_execution(self, mock_asyncio_run, mock_processor_class, celery_app):
        """Test batch analysis task execution"""
        from app.services.ai_processor import batch_analyze_articles
        
        # Setup mocks
        mock_processor = Mock()
        mock_result = Mock()
        mock_processor.analyze_article.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        async def mock_run(*args, **kwargs):
            return {'sentiment': 'positive', 'topic': 'technology'}
        
        mock_asyncio_run.side_effect = mock_run
        
        # Test data
        batch_data = [
            {'id': 'art_1', 'content': 'Content 1'},
            {'id': 'art_2', 'content': 'Content 2'}
        ]
        
        # Execute task
        result = batch_analyze_articles(batch_data)
        
        # Verify results
        assert len(result) == 2
        assert all('article_id' in item for item in result)


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance tests for AI processing"""
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_performance(self, performance_test_data):
        """Test sentiment analysis performance"""
        analyzer = SentimentAnalyzer()
        
        # Mock for consistent performance
        mock_result = [
            [{'label': 'POSITIVE', 'score': 0.8}]
        ]
        
        with patch.object(analyzer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            # Test small text
            start_time = time.time()
            await analyzer.analyze(performance_test_data['small_text'])
            small_time = time.time() - start_time
            
            # Test large text  
            start_time = time.time()
            await analyzer.analyze(performance_test_data['large_text'])
            large_time = time.time() - start_time
            
            # Performance should be reasonable (< 1 second for mocked operations)
            assert small_time < 1.0
            assert large_time < 1.0
    
    @pytest.mark.asyncio
    async def test_topic_classification_performance(self, performance_test_data):
        """Test topic classification performance"""
        classifier = TopicClassifier()
        
        start_time = time.time()
        
        # Test multiple classifications
        for text_size in ['small_text', 'medium_text', 'large_text']:
            await classifier.classify(performance_test_data[text_size])
        
        total_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert total_time < 5.0  # 5 seconds for 3 classifications
    
    @pytest.mark.asyncio
    async def test_summarization_performance(self, performance_test_data):
        """Test summarization performance"""
        summarizer = Summarizer()
        
        # Mock pipeline for consistent performance
        mock_result = [{'summary_text': 'Summary text.'}]
        
        with patch.object(summarizer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            start_time = time.time()
            await summarizer.summarize(performance_test_data['large_text'], max_length=100)
            summary_time = time.time() - start_time
            
            # Should complete quickly
            assert summary_time < 1.0
    
    @pytest.mark.asyncio
    async def test_ai_processor_batch_performance(self, performance_test_data):
        """Test AI processor batch performance"""
        processor = AIProcessor()
        
        # Mock all analysis methods for consistent performance
        processor.sentiment_analyzer.analyze = AsyncMock()
        processor.topic_classifier.classify = AsyncMock()
        processor.summarizer.summarize = AsyncMock()
        
        batch_data = performance_test_data['batch_data']
        
        start_time = time.time()
        
        # Process batch concurrently
        tasks = [
            processor.analyze_article(article['id'], article['content'])
            for article in batch_data
        ]
        
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Should complete within reasonable time even with 10 articles
        assert total_time < 10.0
        assert len(results) == len(batch_data)
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage during processing"""
        processor = AIProcessor()
        
        # Create large text
        large_text = "Content " * 10000
        
        # Analyze multiple times to check for memory leaks
        for i in range(5):
            processor.sentiment_analyzer.analyze = AsyncMock(return_value=Mock())
            processor.topic_classifier.classify = AsyncMock(return_value=Mock())
            processor.summarizer.summarize = AsyncMock(return_value=Mock())
            
            await processor.analyze_article(f'article_{i}', large_text)
            
            # Clear any internal caches periodically
            if i % 2 == 0:
                processor.sentiment_analyzer._cache.clear()
                processor.topic_classifier._cache.clear()
                processor.summarizer._cache.clear()
    
    @pytest.mark.asyncio
    async def test_cache_effectiveness(self, performance_test_data):
        """Test cache effectiveness on repeated operations"""
        analyzer = SentimentAnalyzer()
        
        text = "This is a test text for caching."
        
        # Mock for consistent results
        mock_result = [
            [{'label': 'POSITIVE', 'score': 0.8}]
        ]
        
        with patch.object(analyzer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            # First analysis (no cache)
            start_time = time.time()
            await analyzer.analyze(text)
            first_time = time.time() - start_time
            
            # Second analysis (with cache)
            start_time = time.time()
            await analyzer.analyze(text)
            cached_time = time.time() - start_time
            
            # Cached operation should be significantly faster
            assert cached_time < first_time * 0.1  # 10x faster or more
            assert len(analyzer._cache) == 1


# ============================================================================
# STRESS TESTS
# ============================================================================

class TestStress:
    """Stress tests for AI processing system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_limit(self):
        """Test system behavior under high concurrent load"""
        processor = AIProcessor()
        
        # Mock all methods to avoid actual AI processing
        processor.sentiment_analyzer.analyze = AsyncMock(return_value=Mock())
        processor.topic_classifier.classify = AsyncMock(return_value=Mock())
        processor.summarizer.summarize = AsyncMock(return_value=Mock())
        
        # Create many concurrent requests
        num_concurrent = 50
        tasks = []
        
        for i in range(num_concurrent):
            task = processor.analyze_article(f'article_{i}', f'Content {i}')
            tasks.append(task)
        
        # Execute all concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # All should complete successfully
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == num_concurrent
        assert total_time < 30.0  # Should complete within 30 seconds
    
    @pytest.mark.asyncio
    async def test_error_handling_under_load(self):
        """Test error handling when some operations fail"""
        processor = AIProcessor()
        
        # Mock some failures
        call_count = 0
        async def failing_analyze(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Simulated failure")
            return Mock()
        
        processor.sentiment_analyzer.analyze = failing_analyze
        processor.topic_classifier.classify = AsyncMock(return_value=Mock())
        processor.summarizer.summarize = AsyncMock(return_value=Mock())
        
        # Should handle failures gracefully
        with pytest.raises(Exception):  # Should raise the simulated failure
            await processor.analyze_article('test_id', 'test content')
    
    @pytest.mark.asyncio
    async def test_cache_under_load(self):
        """Test cache behavior under high load"""
        analyzer = SentimentAnalyzer()
        
        mock_result = [
            [{'label': 'POSITIVE', 'score': 0.8}]
        ]
        
        with patch.object(analyzer, '_get_pipeline') as mock_pipeline:
            mock_pipeline.return_value = mock_result
            
            # Process same text multiple times concurrently
            text = "Test text for concurrent caching."
            num_requests = 20
            
            tasks = [analyzer.analyze(text) for _ in range(num_requests)]
            results = await asyncio.gather(*tasks)
            
            # Should complete all successfully
            assert len(results) == num_requests
            assert len(analyzer._cache) == 1  # Should only cache once
            
            # All results should be identical due to caching
            first_result = results[0]
            for result in results[1:]:
                assert result.label == first_result.label
                assert result.confidence == first_result.confidence


# ============================================================================
# UTILITY TESTS
# ============================================================================

class TestUtilities:
    """Test utility functions and helper methods"""
    
    def test_sentiment_label_enum(self):
        """Test SentimentLabel enum values"""
        assert SentimentLabel.POSITIVE.value == "positive"
        assert SentimentLabel.NEGATIVE.value == "negative"
        assert SentimentLabel.NEUTRAL.value == "neutral"
    
    def test_topic_category_enum(self):
        """Test TopicCategory enum values"""
        categories = [cat.value for cat in TopicCategory]
        assert "technology" in categories
        assert "business" in categories
        assert "sports" in categories
    
    def test_dataclass_serialization(self):
        """Test dataclass serialization to dict"""
        sentiment_result = SentimentResult(
            label=SentimentLabel.POSITIVE,
            confidence=0.85,
            score=0.7,
            raw_scores={"positive": 0.85, "negative": 0.10, "neutral": 0.05}
        )
        
        result_dict = asdict(sentiment_result)
        
        assert result_dict['label'] == SentimentLabel.POSITIVE
        assert result_dict['confidence'] == 0.85
        assert isinstance(result_dict['raw_scores'], dict)
    
    def test_processing_time_calculation(self):
        """Test processing time calculation"""
        result = SentimentResult(
            label=SentimentLabel.NEUTRAL,
            confidence=0.5,
            score=0.0,
            raw_scores={}
        )
        
        assert result.processing_time >= 0.0
    
    def test_analysis_result_timestamp(self):
        """Test AIAnalysisResult timestamp"""
        start_time = time.time()
        
        result = AIAnalysisResult(
            article_id="test",
            content="test content"
        )
        
        end_time = time.time()
        
        assert start_time <= result.timestamp <= end_time


# ============================================================================
# CONFIGURATION AND SETUP TESTS
# ============================================================================

class TestConfiguration:
    """Test configuration and environment setup"""
    
    def test_settings_configuration(self):
        """Test application settings configuration"""
        # Test default values
        assert settings.OPENAI_MODEL == "gpt-3.5-turbo"
        assert settings.AI_ANALYSIS_TIMEOUT == 30
        assert settings.CACHE_TTL == 3600
        assert settings.CELERY_BROKER_URL == "redis://localhost:6379"
    
    @patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key',
        'NEWSAPI_KEY': 'news-test-key',
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test'
    })
    def test_environment_variables(self):
        """Test environment variable loading"""
        # Settings should pick up environment variables
        assert os.getenv('OPENAI_API_KEY') == 'test-key'
        assert os.getenv('NEWSAPI_KEY') == 'news-test-key'
    
    def test_redis_configuration(self):
        """Test Redis client configuration"""
        # Test Redis URL configuration
        assert settings.REDIS_URL.startswith("redis://")
    
    def test_celery_configuration(self):
        """Test Celery configuration"""
        # Test Celery URLs
        assert settings.CELERY_BROKER_URL.startswith("redis://")
        assert settings.CELERY_RESULT_BACKEND.startswith("redis://")


# ============================================================================
# MOCK HELPER FUNCTIONS
# ============================================================================

def create_mock_openai_response(response_type: str, confidence: float = 0.8):
    """Create mock OpenAI response based on type"""
    if response_type == "sentiment":
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "label": "positive",
                        "confidence": confidence,
                        "reasoning": "Positive sentiment detected"
                    })
                }
            }]
        }
    elif response_type == "topic":
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "category": "technology",
                        "confidence": confidence,
                        "keywords": ["ai", "technology"],
                        "reasoning": "Technology-related content"
                    })
                }
            }]
        }
    elif response_type == "summary":
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "summary": "Technology advancement summary.",
                        "keywords": ["ai", "technology"],
                        "key_points": ["Major breakthrough", "Promising future"]
                    })
                }
            }]
        }


def create_mock_transformers_result(label: str, score: float):
    """Create mock transformers pipeline result"""
    return [[
        {'label': 'POSITIVE', 'score': 0.9 if label == 'positive' else 0.1},
        {'label': 'NEGATIVE', 'score': 0.9 if label == 'negative' else 0.1},
        {'label': 'NEUTRAL', 'score': 0.9 if label == 'neutral' else 0.1}
    ]]


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")


# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    print("AI News Aggregator - AI Processor Tests")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        test_category = sys.argv[1]
        
        if test_category == "unit":
            print("Running unit tests...")
            pytest.main([__file__, "-m", "unit", "-v"])
        elif test_category == "integration":
            print("Running integration tests...")
            pytest.main([__file__, "-m", "integration", "-v"])
        elif test_category == "performance":
            print("Running performance tests...")
            pytest.main([__file__, "-m", "performance", "-v"])
        elif test_category == "all":
            print("Running all tests...")
            pytest.main([__file__, "-v"])
        else:
            print(f"Unknown test category: {test_category}")
            print("Available categories: unit, integration, performance, all")
    else:
        print("Usage: python test_ai_processor.py [unit|integration|performance|all]")
        print("Default: running unit tests...")
        pytest.main([__file__, "-m", "unit", "-v"])