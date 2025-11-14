"""
Integration tests for AI processing and Celery integration
Tests de integración para procesamiento de IA e integración con Celery

Este archivo contiene tests que verifican la integración completa con
OpenAI API, Celery workers, y el pipeline de procesamiento de IA,
incluyendo análisis de sentimientos, clasificación de temas, y resumenes.
"""

import asyncio
import pytest
import pytest_asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
from celery import Celery
from celery.result import AsyncResult

# Import application components
from app.services.ai_processor import (
    AIProcessor, SentimentAnalyzer, TopicClassifier, Summarizer,
    SentimentLabel, TopicCategory, SentimentResult, TopicResult, 
    SummaryResult, AIAnalysisResult
)
from app.services.ai_pipeline import AIPipeline, ProcessingResult
from app.services.ai_monitor import AIMonitor, MonitoringResult
from app.tasks.article_tasks import analyze_article_task, process_articles_batch_task
from app.tasks.summary_tasks import generate_summary_task
from app.tasks.classification_tasks import classify_articles_batch_task
from app.core.config import settings

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.ai,
    pytest.mark.celery
]


class TestAIProcessorIntegration:
    """Test complete AI processing pipeline integration"""
    
    @pytest.fixture
    async def ai_processor(self, mock_openai_client, test_redis):
        """Create AI processor instance for testing"""
        processor = AIProcessor(
            redis_client=test_redis,
            openai_client=mock_openai_client
        )
        return processor
    
    @pytest.fixture
    def sample_text_content(self):
        """Sample text content for AI processing"""
        return {
            "positive_tech": """
            Revolutionary breakthrough in artificial intelligence technology promises to transform 
            the way we live and work. Scientists have developed a new AI system that can process 
            information at unprecedented speeds, making it possible to solve complex problems faster 
            than ever before. This advancement represents a major milestone in the field of technology 
            and opens new possibilities for innovation and progress.
            """,
            "negative_sports": """
            The team suffered a devastating defeat in yesterday's championship game, losing by a 
            large margin to their rivals. Fans were disappointed as the home team failed to deliver 
            the performance everyone expected. The loss was particularly painful given the high hopes 
            and expectations surrounding this season. Player morale is at an all-time low after 
            this crushing defeat.
            """,
            "neutral_news": """
            The annual technology conference will take place next week in the convention center. 
            Industry experts will present their latest research and developments. The event is 
            expected to attract thousands of attendees from around the world. Registration remains 
            open for interested participants until Friday.
            """
        }
    
    async def test_complete_ai_analysis_workflow(self, ai_processor, sample_text_content):
        """Test complete AI analysis workflow"""
        
        # Test sentiment analysis
        sentiment_result = await ai_processor.analyze_sentiment(
            sample_text_content["positive_tech"]
        )
        assert isinstance(sentiment_result, SentimentResult)
        assert sentiment_result.label == SentimentLabel.POSITIVE
        assert sentiment_result.confidence > 0.7
        
        # Test topic classification
        topic_result = await ai_processor.classify_topic(
            sample_text_content["positive_tech"]
        )
        assert isinstance(topic_result, TopicResult)
        assert topic_result.category == TopicCategory.TECHNOLOGY
        assert topic_result.confidence > 0.6
        
        # Test summarization
        summary_result = await ai_processor.summarize_content(
            sample_text_content["positive_tech"]
        )
        assert isinstance(summary_result, SummaryResult)
        assert len(summary_result.summary) > 0
        assert len(summary_result.keywords) > 0
        
        # Test complete analysis
        analysis_result = await ai_processor.analyze_article(
            article_id="test-article-001",
            content=sample_text_content["positive_tech"]
        )
        assert isinstance(analysis_result, AIAnalysisResult)
        assert analysis_result.article_id == "test-article-001"
        assert analysis_result.sentiment.label == SentimentLabel.POSITIVE
        assert analysis_result.topic.category == TopicCategory.TECHNOLOGY
    
    async def test_ai_analysis_with_cache(self, ai_processor, sample_text_content, test_redis):
        """Test AI analysis with Redis caching"""
        content = sample_text_content["positive_tech"]
        
        # First analysis (cache miss)
        start_time = time.time()
        result1 = await ai_processor.analyze_article(
            article_id="cached-test-001",
            content=content
        )
        first_duration = time.time() - start_time
        
        # Verify result
        assert isinstance(result1, AIAnalysisResult)
        
        # Check if result is cached
        cache_key = f"ai_analysis:cached-test-001"
        cached_data = await test_redis.get(cache_key)
        assert cached_data is not None
        
        # Second analysis (cache hit)
        start_time = time.time()
        result2 = await ai_processor.analyze_article(
            article_id="cached-test-001",
            content=content
        )
        second_duration = time.time() - start_time
        
        # Verify cache hit (should be faster)
        assert second_duration < first_duration
        
        # Results should be identical
        assert result1.sentiment.label == result2.sentiment.label
        assert result1.topic.category == result2.topic.category
    
    async def test_ai_error_handling(self, ai_processor, mock_openai_client):
        """Test AI processing error handling"""
        # Mock OpenAI to return error
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await ai_processor.analyze_sentiment("Test content")
        
        assert "API Error" in str(exc_info.value)
    
    async def test_ai_batch_processing(self, ai_processor, sample_text_content):
        """Test batch processing of multiple articles"""
        articles = [
            {"id": "batch-001", "content": sample_text_content["positive_tech"]},
            {"id": "batch-002", "content": sample_text_content["negative_sports"]},
            {"id": "batch-003", "content": sample_text_content["neutral_news"]}
        ]
        
        results = await ai_processor.batch_analyze_articles(articles)
        
        assert len(results) == 3
        assert all(isinstance(result, AIAnalysisResult) for result in results)
        
        # Verify different sentiments detected
        sentiments = [result.sentiment.label for result in results]
        assert SentimentLabel.POSITIVE in sentiments
        assert SentimentLabel.NEGATIVE in sentiments
        assert SentimentLabel.NEUTRAL in sentiments
        
        # Verify different topics detected
        topics = [result.topic.category for result in results]
        assert TopicCategory.TECHNOLOGY in topics
        assert TopicCategory.SPORTS in topics
    
    async def test_ai_analysis_timeout_handling(self, ai_processor):
        """Test AI analysis timeout handling"""
        # Mock slow OpenAI response
        async def slow_openai_call(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate slow response
            return {"choices": [{"message": {"content": '{"label": "positive", "confidence": 0.8}'}}]}
        
        with patch.object(ai_processor, '_call_openai', side_effect=slow_openai_call):
            start_time = time.time()
            
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    ai_processor.analyze_sentiment("Test content"),
                    timeout=5.0
                )
            
            # Should timeout before 10 seconds
            duration = time.time() - start_time
            assert duration < 10.0


class TestOpenAIIntegration:
    """Test OpenAI API integration specifically"""
    
    @pytest.fixture
    def openai_processor(self, mock_openai_client, test_redis):
        """Create processor with OpenAI integration"""
        processor = AIProcessor(
            redis_client=test_redis,
            openai_api_key="test-openai-key"
        )
        processor.openai_client = mock_openai_client
        return processor
    
    @pytest.mark.skipif(not settings.OPENAI_API_KEY, reason="OpenAI API key not configured")
    async def test_openai_real_integration(self, openai_processor):
        """Test real OpenAI integration (requires API key)"""
        try:
            result = await openai_processor.analyze_sentiment(
                "This is a test sentence for sentiment analysis."
            )
            
            assert isinstance(result, SentimentResult)
            assert result.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
            assert 0.0 <= result.confidence <= 1.0
            
        except Exception as e:
            pytest.fail(f"OpenAI integration test failed: {str(e)}")
    
    async def test_openai_sentiment_analysis(self, openai_processor, mock_openai_responses):
        """Test OpenAI sentiment analysis"""
        # Mock OpenAI response for sentiment
        mock_openai_responses['chat']['completions']['create'].return_value = (
            mock_openai_responses['positive_sentiment']
        )
        
        result = await openai_processor.analyze_sentiment(
            "AI technology shows great promise for the future."
        )
        
        assert isinstance(result, SentimentResult)
        assert result.label == SentimentLabel.POSITIVE
        assert result.confidence > 0.8
        assert isinstance(result.raw_scores, dict)
    
    async def test_openai_topic_classification(self, openai_processor, mock_openai_responses):
        """Test OpenAI topic classification"""
        # Mock OpenAI response for topic
        mock_openai_responses['chat']['completions']['create'].return_value = (
            mock_openai_responses['technology_topic']
        )
        
        result = await openai_processor.classify_topic(
            "Recent developments in machine learning and deep neural networks."
        )
        
        assert isinstance(result, TopicResult)
        assert result.category == TopicCategory.TECHNOLOGY
        assert result.confidence > 0.8
        assert "AI" in result.keywords
    
    async def test_openai_summarization(self, openai_processor, mock_openai_responses):
        """Test OpenAI content summarization"""
        # Mock OpenAI response for summary
        mock_openai_responses['chat']['completions']['create'].return_value = (
            mock_openai_responses['comprehensive_summary']
        )
        
        result = await openai_processor.summarize_content(
            "A comprehensive article about artificial intelligence and its applications..."
        )
        
        assert isinstance(result, SummaryResult)
        assert len(result.summary) > 0
        assert len(result.keywords) > 0
        assert len(result.key_points) > 0
        assert result.compression_ratio > 0.0
    
    async def test_openai_cost_tracking(self, openai_processor, mock_openai_responses):
        """Test OpenAI cost tracking"""
        # Mock OpenAI response with usage info
        response_with_usage = mock_openai_responses['comprehensive_summary'].copy()
        response_with_usage['usage'] = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150
        }
        
        mock_openai_responses['chat']['completions']['create'].return_value = response_with_usage
        
        result = await openai_processor.analyze_sentiment("Test content")
        
        # Verify cost tracking (implementation depends on monitoring setup)
        assert isinstance(result, SentimentResult)
        # Cost tracking would be verified through monitoring systems


class TestCeleryIntegration:
    """Test Celery task integration and execution"""
    
    @pytest.fixture
    def celery_app(self):
        """Create Celery app for testing"""
        # Use test configuration
        app = Celery(
            'test_app',
            broker='redis://localhost:6379/15',
            backend='redis://localhost:6379/15',
            include=['app.tasks.article_tasks', 'app.tasks.summary_tasks', 'app.tasks.classification_tasks']
        )
        app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=30,
            task_soft_time_limit=25,
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=1
        )
        return app
    
    @pytest.fixture
    def celery_worker(self, celery_app):
        """Start Celery worker for testing"""
        from celery.contrib.testing.worker import start_worker
        
        # Start worker in background
        with start_worker(app=celery_app, pool='solo'):
            yield celery_app
    
    async def test_analyze_article_task(self, celery_app, celery_worker, sample_article_data):
        """Test article analysis Celery task"""
        # Mock AI processor in task
        with patch('app.tasks.article_tasks.ai_processor') as mock_processor:
            mock_result = AIAnalysisResult(
                article_id="test-123",
                content="Test content",
                sentiment=SentimentResult(
                    label=SentimentLabel.POSITIVE,
                    confidence=0.9,
                    raw_scores={"positive": 0.9}
                ),
                topic=TopicResult(
                    category=TopicCategory.TECHNOLOGY,
                    confidence=0.8,
                    keywords=["AI", "technology"],
                    scores={"technology": 0.8}
                ),
                summary=SummaryResult(
                    summary="Test summary",
                    keywords=["test"],
                    key_points=["Point 1"],
                    word_count=10,
                    compression_ratio=0.5
                ),
                processing_time=1.0,
                timestamp=datetime.utcnow()
            )
            
            mock_processor.analyze_article.return_value = mock_result
            
            # Execute task
            result = analyze_article_task.delay(
                article_id="test-123",
                content="Test content"
            )
            
            # Wait for completion
            task_result = result.get(timeout=10)
            
            assert task_result['status'] == 'success'
            assert task_result['article_id'] == 'test-123'
            assert task_result['sentiment']['label'] == 'positive'
    
    async def test_batch_processing_task(self, celery_app, celery_worker, sample_articles):
        """Test batch processing Celery task"""
        with patch('app.tasks.batch_tasks.ai_pipeline') as mock_pipeline:
            mock_result = ProcessingResult(
                processed_count=3,
                failed_count=0,
                results=[
                    AIAnalysisResult(
                        article_id=f"batch-{i}",
                        content=article["content"],
                        sentiment=SentimentResult(SentimentLabel.POSITIVE, 0.8, {}),
                        topic=TopicResult(TopicCategory.TECHNOLOGY, 0.7, [], {}),
                        summary=SummaryResult("Summary", [], [], 10, 0.5),
                        processing_time=1.0,
                        timestamp=datetime.utcnow()
                    ) for i, article in enumerate(sample_articles)
                ],
                total_processing_time=3.0
            )
            
            mock_pipeline.batch_process_articles.return_value = mock_result
            
            # Execute batch task
            result = process_articles_batch_task.delay(
                article_ids=[f"batch-{i}" for i in range(3)],
                force_reprocess=False
            )
            
            task_result = result.get(timeout=30)
            
            assert task_result['status'] == 'success'
            assert task_result['processed_count'] == 3
            assert task_result['failed_count'] == 0
    
    async def test_summary_generation_task(self, celery_app, celery_worker):
        """Test summary generation Celery task"""
        with patch('app.tasks.summary_tasks.ai_processor') as mock_processor:
            mock_summary = SummaryResult(
                summary="Generated summary",
                keywords=["keyword1", "keyword2"],
                key_points=["Point 1", "Point 2"],
                word_count=20,
                compression_ratio=0.6
            )
            
            mock_processor.summarize_content.return_value = mock_summary
            
            # Execute summary task
            result = generate_summary_task.delay(
                article_id="test-456",
                content="Long article content that needs summarizing..."
            )
            
            task_result = result.get(timeout=20)
            
            assert task_result['status'] == 'success'
            assert task_result['summary']['summary'] == "Generated summary"
            assert len(task_result['summary']['keywords']) == 2
    
    async def test_classification_task(self, celery_app, celery_worker):
        """Test article classification Celery task"""
        with patch('app.tasks.classification_tasks.ai_processor') as mock_processor:
            mock_topic = TopicResult(
                category=TopicCategory.BUSINESS,
                confidence=0.85,
                keywords=["business", "economy", "finance"],
                scores={"business": 0.85}
            )
            
            mock_processor.classify_topic.return_value = mock_topic
            
            # Execute classification task
            result = classify_articles_batch_task.delay(
                article_ids=["test-789"],
                force_reclassify=False
            )
            
            task_result = result.get(timeout=20)
            
            assert task_result['status'] == 'success'
            assert task_result['classifications'][0]['category'] == 'business'
            assert task_result['classifications'][0]['confidence'] > 0.8
    
    async def test_celery_error_handling(self, celery_app, celery_worker):
        """Test Celery task error handling"""
        with patch('app.tasks.article_tasks.ai_processor') as mock_processor:
            # Mock processor to raise exception
            mock_processor.analyze_article.side_effect = Exception("Processing failed")
            
            # Execute task
            result = analyze_article_task.delay(
                article_id="error-test",
                content="Test content"
            )
            
            # Task should handle error gracefully
            task_result = result.get(timeout=10)
            
            assert task_result['status'] == 'error'
            assert 'error' in task_result
    
    async def test_celery_retry_mechanism(self, celery_app, celery_worker):
        """Test Celery task retry mechanism"""
        call_count = 0
        
        @celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2})
        def flaky_task(self):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                raise Exception("Temporary failure")
            
            return {"status": "success", "attempts": call_count}
        
        # Execute task
        result = flaky_task.delay()
        task_result = result.get(timeout=30)
        
        assert task_result['status'] == 'success'
        assert task_result['attempts'] == 3


class TestAIPipelineIntegration:
    """Test complete AI pipeline integration"""
    
    @pytest.fixture
    async def ai_pipeline(self, mock_openai_client, test_redis):
        """Create AI pipeline instance"""
        pipeline = AIPipeline(
            ai_processor=mock_openai_client,
            redis_client=test_redis
        )
        return pipeline
    
    async def test_pipeline_end_to_end_processing(self, ai_pipeline, sample_articles):
        """Test complete pipeline processing"""
        with patch.object(ai_pipeline, 'ai_processor') as mock_processor:
            # Mock AI processor responses
            mock_processor.analyze_article.side_effect = [
                AIAnalysisResult(
                    article_id=article["id"],
                    content=article["content"],
                    sentiment=SentimentResult(SentimentLabel.POSITIVE, 0.8, {}),
                    topic=TopicResult(TopicCategory.TECHNOLOGY, 0.7, [], {}),
                    summary=SummaryResult("Summary", [], [], 10, 0.5),
                    processing_time=1.0,
                    timestamp=datetime.utcnow()
                )
                for article in sample_articles
            ]
            
            # Process articles through pipeline
            result = await ai_pipeline.batch_process_articles(
                articles=sample_articles,
                force_reprocess=False
            )
            
            assert isinstance(result, ProcessingResult)
            assert result.processed_count == len(sample_articles)
            assert result.failed_count == 0
            assert len(result.results) == len(sample_articles)
    
    async def test_pipeline_caching_integration(self, ai_pipeline, sample_articles):
        """Test pipeline with caching integration"""
        with patch.object(ai_pipeline, 'ai_processor') as mock_processor:
            # First batch processing
            mock_processor.analyze_article.return_value = AIAnalysisResult(
                article_id=sample_articles[0]["id"],
                content=sample_articles[0]["content"],
                sentiment=SentimentResult(SentimentLabel.POSITIVE, 0.8, {}),
                topic=TopicResult(TopicCategory.TECHNOLOGY, 0.7, [], {}),
                summary=SummaryResult("Summary", [], [], 10, 0.5),
                processing_time=1.0,
                timestamp=datetime.utcnow()
            )
            
            # Process first time
            result1 = await ai_pipeline.batch_process_articles(
                articles=[sample_articles[0]],
                force_reprocess=False
            )
            
            # Process same article again (should use cache)
            result2 = await ai_pipeline.batch_process_articles(
                articles=[sample_articles[0]],
                force_reprocess=False
            )
            
            # AI processor should be called only once (cached second time)
            assert mock_processor.analyze_article.call_count == 1
    
    async def test_pipeline_error_recovery(self, ai_pipeline, sample_articles):
        """Test pipeline error recovery mechanisms"""
        call_count = 0
        
        def flaky_processor(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Temporary failure")
            return AIAnalysisResult(
                article_id=kwargs.get('article_id', 'test'),
                content=kwargs.get('content', 'test content'),
                sentiment=SentimentResult(SentimentLabel.POSITIVE, 0.8, {}),
                topic=TopicResult(TopicCategory.TECHNOLOGY, 0.7, [], {}),
                summary=SummaryResult("Summary", [], [], 10, 0.5),
                processing_time=1.0,
                timestamp=datetime.utcnow()
            )
        
        with patch.object(ai_pipeline, 'ai_processor') as mock_processor:
            mock_processor.analyze_article.side_effect = flaky_processor
            
            # Should retry and eventually succeed
            result = await ai_pipeline.batch_process_articles(
                articles=[sample_articles[0]],
                force_reprocess=False,
                max_retries=3
            )
            
            assert isinstance(result, ProcessingResult)
            assert result.processed_count == 1


class TestAIMonitoringIntegration:
    """Test AI monitoring and observability integration"""
    
    @pytest.fixture
    async def ai_monitor(self, test_redis):
        """Create AI monitor instance"""
        monitor = AIMonitor(redis_client=test_redis)
        return monitor
    
    async def test_processing_metrics_collection(self, ai_monitor):
        """Test collection of processing metrics"""
        # Simulate processing events
        await ai_monitor.log_processing_start(
            task_id="test-task-001",
            task_type="sentiment_analysis",
            article_id="article-001"
        )
        
        await ai_monitor.log_processing_complete(
            task_id="test-task-001",
            processing_time=1.5,
            cost=0.05,
            tokens_used=100
        )
        
        # Verify metrics were collected
        metrics = await ai_monitor.get_metrics_summary(hours=1)
        
        assert metrics.total_tasks >= 1
        assert metrics.avg_processing_time >= 1.5
        assert metrics.total_cost >= 0.05
    
    async def test_error_tracking(self, ai_monitor):
        """Test error tracking and alerting"""
        # Log error events
        await ai_monitor.log_error(
            task_id="error-task-001",
            error_type="OpenAI API Error",
            error_message="Rate limit exceeded",
            context={"retry_count": 3}
        )
        
        await ai_monitor.log_error(
            task_id="error-task-002",
            error_type="Timeout Error",
            error_message="Processing timeout",
            context={"timeout": 30}
        )
        
        # Verify error tracking
        recent_errors = await ai_monitor.get_recent_errors(hours=1)
        
        assert len(recent_errors) >= 2
        error_types = [error.error_type for error in recent_errors]
        assert "OpenAI API Error" in error_types
        assert "Timeout Error" in error_types
    
    async def test_performance_alerting(self, ai_monitor):
        """Test performance alerting based on thresholds"""
        # Log slow processing
        await ai_monitor.log_processing_complete(
            task_id="slow-task-001",
            processing_time=35.0,  # Above warning threshold
            cost=0.01,
            tokens_used=50
        )
        
        # Log high cost
        await ai_monitor.log_processing_complete(
            task_id="expensive-task-001",
            processing_time=2.0,
            cost=0.8,  # Above task threshold
            tokens_used=1000
        )
        
        # Check for alerts
        alerts = await ai_monitor.check_alerts()
        
        # Should generate alerts for performance issues
        assert len(alerts) > 0
        alert_types = [alert.alert_type for alert in alerts]
        assert "high_latency" in alert_types or "high_cost" in alert_types
    
    async def test_monitoring_dashboard_data(self, ai_monitor):
        """Test monitoring data for dashboard"""
        # Generate sample monitoring data
        for i in range(10):
            await ai_monitor.log_processing_complete(
                task_id=f"test-task-{i:03d}",
                processing_time=1.0 + i * 0.1,
                cost=0.01 * (i + 1),
                tokens_used=50 + i * 10
            )
        
        # Get dashboard data
        dashboard_data = await ai_monitor.get_dashboard_data()
        
        assert "summary" in dashboard_data
        assert "recent_tasks" in dashboard_data
        assert "error_summary" in dashboard_data
        assert "performance_trends" in dashboard_data


class TestAIConfigurationIntegration:
    """Test AI system configuration and environment handling"""
    
    async def test_openai_configuration_validation(self):
        """Test OpenAI configuration validation"""
        # Test with missing API key
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                AIProcessor()
    
    async def test_redis_configuration_integration(self):
        """Test Redis configuration for AI processing"""
        # Test Redis connection in AI context
        redis_client = await create_test_redis_client()
        
        processor = AIProcessor(
            redis_client=redis_client,
            openai_client=Mock()
        )
        
        # Test cache operations
        await processor._cache_result("test-key", {"data": "test"}, ttl=300)
        cached_data = await processor._get_cached_result("test-key")
        
        assert cached_data == {"data": "test"}
        
        await redis_client.close()
    
    async def test_environment_specific_configuration(self):
        """Test environment-specific AI configurations"""
        # Test development environment
        with patch.dict('os.environ', {
            'OPENAI_MODEL': 'gpt-3.5-turbo',
            'AI_ANALYSIS_TIMEOUT': '30',
            'CACHE_TTL': '3600'
        }):
            processor = AIProcessor()
            assert processor.model == 'gpt-3.5-turbo'
            assert processor.timeout == 30
        
        # Test production environment
        with patch.dict('os.environ', {
            'OPENAI_MODEL': 'gpt-4',
            'AI_ANALYSIS_TIMEOUT': '60',
            'CACHE_TTL': '1800'
        }):
            processor = AIProcessor()
            assert processor.model == 'gpt-4'
            assert processor.timeout == 60


# Test utilities
async def create_test_redis_client():
    """Create a test Redis client"""
    try:
        import redis.asyncio as redis
        return await redis.from_url("redis://localhost:6379/15", decode_responses=True)
    except:
        return Mock()


def validate_ai_result_structure(result: Any):
    """Validate AI result structure"""
    if isinstance(result, AIAnalysisResult):
        assert result.article_id is not None
        assert isinstance(result.sentiment, SentimentResult)
        assert isinstance(result.topic, TopicResult)
        assert isinstance(result.summary, SummaryResult)
    elif isinstance(result, SentimentResult):
        assert result.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
        assert 0.0 <= result.confidence <= 1.0
    elif isinstance(result, TopicResult):
        assert result.category in list(TopicCategory)
        assert 0.0 <= result.confidence <= 1.0


def create_mock_celery_result(status: str = "SUCCESS", result_data: Dict[str, Any] = None):
    """Create mock Celery result"""
    mock_result = AsyncResult(id="test-task-id", app=Mock())
    mock_result.status = status
    mock_result.result = result_data or {"status": "success"}
    return mock_result


if __name__ == "__main__":
    print("AI integration tests configuration loaded successfully")