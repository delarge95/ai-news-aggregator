"""
Pytest configuration and shared fixtures for AI News Aggregator tests
Configuración de test environment y fixtures comprehensivas
"""

import asyncio
import json
import os
import tempfile
from typing import Dict, List, Any, Generator
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import pytest
import pytest_asyncio
import pytest_cov
import redis.asyncio as redis
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

# Import application components
from app.main import app
from app.core.config import settings
from app.db.models import (
    Base, Article, Source, User, UserPreference, UserBookmark,
    TrendingTopic, ArticleAnalysis, AnalysisTask, ProcessingStatus, AnalysisTaskStatus
)
from app.db.database import get_database
from app.services.ai_processor import (
    SentimentAnalyzer, TopicClassifier, Summarizer, AIProcessor,
    SentimentLabel, TopicCategory, SentimentResult, TopicResult,
    SummaryResult, AIAnalysisResult
)

# Configure pytest asyncio
pytest_plugins = ["pytest_asyncio"]


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    # Add custom markers
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "redis: marks tests that require Redis")
    config.addinivalue_line("markers", "openai: marks tests that require OpenAI API")
    config.addinivalue_line("markers", "celery: marks tests that require Celery")
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use different DB for tests
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/15"
    os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/15"


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add marker based on test location
        if "test_ai_processor" in str(item.fspath):
            if any(word in item.name.lower() for word in ["sentiment", "topic", "summarizer"]):
                item.add_marker(pytest.mark.unit)
            elif any(word in item.name.lower() for word in ["integration", "ai_processor"]):
                item.add_marker(pytest.mark.integration)
            elif any(word in item.name.lower() for word in ["performance", "stress"]):
                item.add_marker(pytest.mark.performance)
                item.add_marker(pytest.mark.slow)


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """Create in-memory SQLite database engine for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine):
    """Create database session for testing"""
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture(scope="session")
def async_test_db_engine():
    """Create async in-memory SQLite database engine for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def cleanup_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    
    # Initialize database
    asyncio.get_event_loop().run_until_complete(init_db())
    
    yield engine
    
    # Cleanup
    asyncio.get_event_loop().run_until_complete(cleanup_db())


@pytest.fixture
async def async_db_session(async_test_db_engine):
    """Create async database session for testing"""
    async_session = sessionmaker(
        async_test_db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
def mock_get_database(async_db_session):
    """Mock database dependency"""
    async def mock_database():
        yield async_db_session
    
    return mock_database


# ============================================================================
# AUTHENTICATION FIXTURES
# ============================================================================

@pytest.fixture
def mock_current_user():
    """Mock current authenticated user"""
    user = User(
        id="123e4567-e89b-12d3-a456-426614174000",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
        role="user"
    )
    return user


@pytest.fixture
def mock_admin_user():
    """Mock admin user"""
    user = User(
        id="123e4567-e89b-12d3-a456-426614174001",
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        hashed_password="admin_hashed_password",
        is_active=True,
        role="admin",
        is_superuser=True
    )
    return user


@pytest.fixture
def auth_headers(mock_current_user):
    """Generate authentication headers for testing"""
    return {"Authorization": f"Bearer {mock_current_user.id}"}


# ============================================================================
# APPLICATION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_client() -> AsyncClient:
    """Create a test client for FastAPI application"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    with patch('app.core.config.settings') as mock:
        mock.OPENAI_API_KEY = "test-key"
        mock.OPENAI_MODEL = "gpt-3.5-turbo"
        mock.AI_ANALYSIS_TIMEOUT = 30
        mock.CACHE_TTL = 3600
        mock.CELERY_BROKER_URL = "redis://localhost:6379/15"
        mock.CELERY_RESULT_BACKEND = "redis://localhost:6379/15"
        mock.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
        mock.REDIS_URL = "redis://localhost:6379/15"
        mock.JWT_SECRET_KEY = "test-secret-key"
        mock.JWT_ALGORITHM = "HS256"
        mock.JWT_EXPIRE_MINUTES = 30
        yield mock


@pytest.fixture
def mock_database():
    """Mock database session"""
    mock_db = Mock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.commit.return_value = None
    mock_db.add.return_value = None
    mock_db.refresh.return_value = None
    return mock_db


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient"""
    client = AsyncMock()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "articles": [
            {
                "title": "Test Article",
                "description": "Test Description",
                "content": "Test Content",
                "url": "https://example.com/test",
                "publishedAt": "2023-12-01T10:00:00Z",
                "source": {"id": "test-source", "name": "Test Source"}
            }
        ]
    }
    
    client.get.return_value = mock_response
    return client


@pytest.fixture
def mock_config():
    """Mock configuration"""
    config = Mock()
    config.NEWSAPI_KEY = "test_newsapi_key"
    config.GUARDIAN_API_KEY = "test_guardian_key"
    config.NYTIMES_API_KEY = "test_nytimes_key"
    config.DATABASE_URL = "sqlite:///:memory:"
    config.REDIS_URL = "redis://localhost:6379/0"
    config.DEBUG = True
    config.RATE_LIMIT_ENABLED = True
    return config


# ============================================================================
# AI PROCESSOR FIXTURES
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
async def test_redis():
    """Create a test Redis client"""
    # Use in-memory Redis for testing if available, otherwise mock
    try:
        # Try to connect to Redis (for integration tests)
        redis_client = await redis.from_url(
            "redis://localhost:6379/15", 
            encoding="utf-8", 
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        
        yield redis_client
        
        # Cleanup
        await redis_client.flushdb()
        await redis_client.close()
        
    except (redis.ConnectionError, Exception):
        # Fallback to mock if Redis is not available
        mock_redis = Mock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.flushdb = AsyncMock()
        mock_redis.close = AsyncMock()
        
        yield mock_redis


@pytest.fixture
def ai_processor_factory(mock_openai_client, test_redis):
    """Factory for creating AIProcessor instances with different configurations"""
    
    def _create_processor(
        use_openai: bool = False,
        use_cache: bool = True,
        custom_config: Dict[str, Any] = None
    ):
        """Create AIProcessor with specified configuration"""
        config = {
            'redis_client': test_redis if use_cache else None,
            'openai_api_key': mock_openai_client.api_key if use_openai else None
        }
        
        if custom_config:
            config.update(custom_config)
        
        processor = AIProcessor(**config)
        
        # Inject mocked clients if needed
        if use_openai:
            processor.openai_client = mock_openai_client
        
        return processor
    
    return _create_processor


# ============================================================================
# SAMPLE DATA FIXTURES
# ============================================================================

@pytest.fixture
def sample_news_articles():
    """Comprehensive sample news articles for testing"""
    return [
        {
            'id': 'tech_001',
            'title': 'Revolutionary AI Chip Announces 100x Performance Boost',
            'content': '''A groundbreaking artificial intelligence chip developed by leading tech researchers 
            has achieved a remarkable 100x performance improvement over previous generations. The new chip, 
            built using advanced 3nm process technology, integrates specialized AI accelerators that can 
            process neural network computations at unprecedented speeds. This breakthrough promises to 
            revolutionize machine learning applications across industries, from autonomous vehicles to 
            medical diagnosis systems. Industry experts predict this technology will democratize AI access 
            and accelerate the development of next-generation intelligent systems.''',
            'expected_sentiment': SentimentLabel.POSITIVE,
            'expected_topic': TopicCategory.TECHNOLOGY,
            'keywords': ['AI', 'chip', 'performance', 'technology', 'neural']
        },
        {
            'id': 'business_001',
            'title': 'Global Markets Rally on Economic Recovery Signals',
            'content': '''Stock markets worldwide experienced significant gains today as investors responded 
            positively to stronger-than-expected economic recovery indicators. The S&P 500 climbed 2.3%, 
            while European markets saw similar gains. Major financial institutions reported quarterly earnings 
            that exceeded analyst expectations, driving confidence in the economic outlook. The rally was 
            supported by robust corporate earnings, declining unemployment rates, and positive consumer 
            sentiment surveys. Market analysts attribute the surge to effective monetary policies and 
            successful vaccination programs.''',
            'expected_sentiment': SentimentLabel.POSITIVE,
            'expected_topic': TopicCategory.BUSINESS,
            'keywords': ['markets', 'economic', 'recovery', 'earnings', 'financial']
        },
        {
            'id': 'sports_001',
            'title': 'Underdog Team Wins Championship in Stunning Upset',
            'content': '''In one of the most unexpected outcomes in sports history, the underdog team 
            defeated the heavily favored champions in a dramatic final match. Trailing by three points 
            with only thirty seconds remaining, the team executed a flawless comeback strategy that 
            resulted in a game-winning touchdown. The victory shocked millions of fans worldwide and 
            cemented the team's place in sports legend. Celebrations erupted across the city as fans 
           honored their heroes with spontaneous parades and rallies.''',
            'expected_sentiment': SentimentLabel.POSITIVE,
            'expected_topic': TopicCategory.SPORTS,
            'keywords': ['team', 'championship', 'victory', 'sports', 'upset']
        }
    ]


@pytest.fixture
def sample_articles():
    """Sample article data for testing (legacy compatibility)"""
    return [
        {
            "id": "1",
            "title": "AI Breakthrough Announced",
            "description": "Scientists announce major breakthrough in artificial intelligence",
            "content": "Artificial intelligence research has reached a new milestone with this breakthrough...",
            "url": "https://example.com/ai-breakthrough",
            "published_at": "2023-12-01T10:00:00Z",
            "author": "Dr. Smith",
            "source": {
                "id": "tech-news",
                "name": "Tech News Daily",
                "credibility_score": 0.8
            }
        },
        {
            "id": "2",
            "title": "Climate Summit Concludes",
            "description": "International climate summit reaches new agreements",
            "content": "World leaders have concluded the climate summit with new environmental commitments...",
            "url": "https://example.com/climate-summit",
            "published_at": "2023-12-01T11:00:00Z",
            "author": "Jane Reporter",
            "source": {
                "id": "world-news",
                "name": "World News Network",
                "credibility_score": 0.9
            }
        },
        {
            "id": "3",
            "title": "Sports Championship Results",
            "description": "Local team wins championship after intense match",
            "content": "The local team emerged victorious in yesterday's championship game...",
            "url": "https://example.com/sports-championship",
            "published_at": "2023-12-01T12:00:00Z",
            "author": "Sports Writer",
            "source": {
                "id": "sports-daily",
                "name": "Sports Daily",
                "credibility_score": 0.7
            }
        }
    ]


@pytest.fixture
def sample_api_responses():
    """Sample API responses for mocking"""
    return {
        "newsapi": {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "source": {"id": "bbc-news", "name": "BBC News"},
                    "author": "BBC Reporter",
                    "title": "AI Technology Advances",
                    "description": "Latest developments in AI technology",
                    "url": "https://bbc.com/news/ai-technology",
                    "urlToImage": "https://bbc.com/image.jpg",
                    "publishedAt": "2023-12-01T10:00:00Z",
                    "content": "AI technology continues to advance rapidly..."
                }
            ]
        },
        "guardian": {
            "response": {
                "status": "ok",
                "total": 1,
                "results": [
                    {
                        "id": "technology/2023/dec/01/ai-advances",
                        "type": "article",
                        "sectionId": "technology",
                        "sectionName": "Technology",
                        "webPublicationDate": "2023-12-01T10:00:00Z",
                        "webTitle": "AI Technology Shows Major Advances",
                        "webUrl": "https://theguardian.com/technology/2023/dec/01/ai-advances",
                        "apiUrl": "https://content.guardianapis.com/technology/2023/dec/01/ai-advances",
                        "fields": {
                            "headline": "AI Technology Shows Major Advances",
                            "standfirst": "Latest AI developments",
                            "trailText": "Technology news update",
                            "byline": "Guardian Reporter",
                            "body": "AI technology is advancing at an unprecedented pace..."
                        }
                    }
                ]
            }
        },
        "nytimes": {
            "status": "OK",
            "response": {
                "docs": [
                    {
                        "web_url": "https://nytimes.com/2023/12/01/technology/ai-advances.html",
                        "snippet": "Latest developments in artificial intelligence technology",
                        "lead_paragraph": "Artificial intelligence technology continues to evolve rapidly...",
                        "abstract": "Summary of AI advances",
                        "source": ["The New York Times"],
                        "headline": {
                            "main": "AI Technology Reaches New Milestone",
                            "kicker": "Technology"
                        },
                        "pub_date": "2023-12-01T10:00:00+0000",
                        "document_type": "article",
                        "news_desk": "Technology",
                        "section_name": "Technology",
                        "byline": {
                            "original": "By NYTimes Reporter"
                        }
                    }
                ],
                "meta": {
                    "hits": 1,
                    "offset": 0,
                    "time": 45
                }
            }
        }
    }


@pytest.fixture
def mock_news_sources():
    """Mock news sources"""
    return [
        {
            "id": "bbc-news",
            "name": "BBC News",
            "url": "https://bbc.com/news",
            "api_name": "newsapi",
            "api_source_id": "bbc-news",
            "country": "GB",
            "language": "en",
            "credibility_score": 0.9,
            "is_active": True,
            "rate_limit_per_hour": 100
        },
        {
            "id": "guardian",
            "name": "The Guardian",
            "url": "https://theguardian.com",
            "api_name": "guardian", 
            "api_source_id": "guardian",
            "country": "GB",
            "language": "en",
            "credibility_score": 0.8,
            "is_active": True,
            "rate_limit_per_hour": 50
        },
        {
            "id": "nytimes",
            "name": "The New York Times",
            "url": "https://nytimes.com",
            "api_name": "nytimes",
            "api_source_id": "nytimes",
            "country": "US", 
            "language": "en",
            "credibility_score": 0.9,
            "is_active": True,
            "rate_limit_per_hour": 75
        }
    ]


@pytest.fixture
def mock_redis():
    """Mock Redis client (legacy compatibility)"""
    redis_mock = Mock()
    
    # Mock Redis operations
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    redis_mock.exists.return_value = False
    redis_mock.incr.return_value = 1
    redis_mock.expire.return_value = True
    redis_mock.ttl.return_value = 3600
    redis_mock.keys.return_value = []
    redis_mock.hgetall.return_value = {}
    redis_mock.hset.return_value = 1
    redis_mock.zadd.return_value = 1
    redis_mock.zrange.return_value = []
    redis_mock.zrem.return_value = 1
    
    return redis_mock


@pytest.fixture
def mock_sentiment_analyzer():
    """Mock sentiment analyzer"""
    analyzer = AsyncMock()
    
    # Mock sentiment analysis responses
    analyzer.analyze_sentiment.return_value = {
        "sentiment": "positive",
        "confidence": 0.85,
        "scores": {
            "positive": 0.7,
            "neutral": 0.2,
            "negative": 0.1
        }
    }
    
    # Mock topic extraction
    analyzer.extract_topics.return_value = {
        "topics": ["artificial intelligence", "technology", "research"],
        "confidence": 0.8
    }
    
    # Mock bias detection
    analyzer.detect_bias.return_value = {
        "bias_score": 0.3,
        "bias_type": "minimal",
        "confidence": 0.75
    }
    
    return analyzer


@pytest.fixture
def temp_directory(tmp_path):
    """Create a temporary directory for tests"""
    return tmp_path


@pytest.fixture
def clean_environment():
    """Clean environment variables for tests"""
    original_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.mark.asyncio
async def async_test_helper():
    """Helper for async testing patterns"""
    await asyncio.sleep(0.001)  # Allow other tasks to run
    return True


# Mark slow tests
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require API keys"
    )


# ============================================================================
# MOCK RESPONSE FIXTURES
# ============================================================================

@pytest.fixture
def mock_openai_responses():
    """Predefined mock responses for OpenAI API testing"""
    return {
        'positive_sentiment': {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "label": "positive",
                        "confidence": 0.92,
                        "reasoning": "Text expresses strong positive sentiment about technology advancement"
                    })
                }
            }],
            "usage": {"total_tokens": 150}
        },
        'technology_topic': {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "category": "technology",
                        "confidence": 0.94,
                        "keywords": ["AI", "machine learning", "innovation", "technology"],
                        "reasoning": "Content focuses on technological advancement"
                    })
                }
            }],
            "usage": {"total_tokens": 180}
        },
        'comprehensive_summary': {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "summary": "Revolutionary AI technology breakthrough promises to transform industry landscape.",
                        "keywords": ["AI", "breakthrough", "technology", "innovation"],
                        "key_points": [
                            "Major technological advancement achieved",
                            "Significant performance improvements demonstrated"
                        ]
                    })
                }
            }],
            "usage": {"total_tokens": 250}
        }
    }


@pytest.fixture
def mock_transformers_responses():
    """Predefined mock responses for transformers pipeline testing"""
    return {
        'positive_sentiment': [
            [
                {'label': 'POSITIVE', 'score': 0.92},
                {'label': 'NEGATIVE', 'score': 0.05},
                {'label': 'NEUTRAL', 'score': 0.03}
            ]
        ],
        'summary_result': [
            {
                'summary_text': 'AI technology breakthrough promises to revolutionize industry applications.',
            }
        ]
    }


# ============================================================================
# PERFORMANCE TESTING FIXTURES
# ============================================================================

@pytest.fixture
def performance_test_data():
    """Data for performance and load testing"""
    return {
        'small_texts': [
            "Short text for testing performance.",
            "Another brief text sample.",
            "Quick performance test content."
        ],
        'large_texts': [
            "This is a very large text designed for stress testing the AI processing capabilities. " * 50,
        ],
        'batch_data': [
            {
                'id': f'perf_article_{i}',
                'content': f'Performance test article number {i} with varied content structure.'
            }
            for i in range(10)
        ]
    }


# ============================================================================
# HELPER FUNCTIONS FOR TESTING
# ============================================================================

def create_test_article(
    article_id: str,
    content: str,
    title: str = "",
    expected_sentiment: SentimentLabel = None,
    expected_topic: TopicCategory = None
) -> Dict[str, Any]:
    """Helper function to create test articles with metadata"""
    return {
        'id': article_id,
        'title': title or f"Test Article {article_id}",
        'content': content,
        'expected_sentiment': expected_sentiment or SentimentLabel.NEUTRAL,
        'expected_topic': expected_topic or TopicCategory.OTHER,
        'word_count': len(content.split()),
        'char_count': len(content)
    }


def assert_sentiment_result(result: SentimentResult, expected_label: SentimentLabel):
    """Helper assertion for sentiment results"""
    assert isinstance(result, SentimentResult)
    assert result.label == expected_label
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.raw_scores, dict)


def assert_topic_result(result: TopicResult, expected_category: TopicCategory):
    """Helper assertion for topic results"""
    assert isinstance(result, TopicResult)
    assert result.category == expected_category
    assert 0.0 <= result.confidence <= 1.0
    assert isinstance(result.keywords, list)
    assert isinstance(result.scores, dict)


def assert_summary_result(result: SummaryResult):
    """Helper assertion for summary results"""
    assert isinstance(result, SummaryResult)
    assert isinstance(result.summary, str)
    assert len(result.summary) > 0
    assert isinstance(result.keywords, list)
    assert isinstance(result.key_points, list)
    assert result.word_count > 0
    assert result.compression_ratio > 0.0


def assert_analysis_result(result: AIAnalysisResult, article_id: str):
    """Helper assertion for complete analysis results"""
    assert isinstance(result, AIAnalysisResult)
    assert result.article_id == article_id
    assert isinstance(result.content, str)
    assert isinstance(result.sentiment, SentimentResult)
    assert isinstance(result.topic, TopicResult)
    assert isinstance(result.summary, SummaryResult)
    assert result.processing_time >= 0.0
    assert result.timestamp is not None


# ============================================================================
# TEST ENVIRONMENT SETUP
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """Setup test environment variables and configurations"""
    # Store original values
    original_env = {}
    test_env_vars = {
        'TESTING': 'true',
        'DATABASE_URL': 'sqlite+aiosqlite:///:memory:',
        'REDIS_URL': 'redis://localhost:6379/15',
        'OPENAI_API_KEY': 'test-key-for-testing',
        'CELERY_BROKER_URL': 'redis://localhost:6379/15',
        'CELERY_RESULT_BACKEND': 'redis://localhost:6379/15',
        'DEBUG': 'true',
        'AI_ANALYSIS_TIMEOUT': '10',  # Shorter timeout for tests
        'CACHE_TTL': '300',  # 5 minutes for tests
    }
    
    # Set test environment variables
    for key, value in test_env_vars.items():
        original_env[key] = os.getenv(key)
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# ============================================================================
# FACTORY PATTERNS FOR TEST DATA
# ============================================================================

@pytest.fixture
def article_factory():
    """Factory for creating test articles"""
    def _create_article(
        title: str = "Test Article",
        content: str = "Test content for article",
        url: str = "https://example.com/test",
        source_id: str = None,
        **kwargs
    ):
        article = Article(
            title=title,
            content=content,
            url=url,
            source_id=source_id or "123e4567-e89b-12d3-a456-426614174000",
            processing_status=ProcessingStatus.PENDING,
            **kwargs
        )
        return article
    return _create_article


@pytest.fixture
def source_factory():
    """Factory for creating test sources"""
    def _create_source(
        name: str = "Test Source",
        url: str = "https://example.com",
        api_name: str = "test_api",
        **kwargs
    ):
        source = Source(
            name=name,
            url=url,
            api_name=api_name,
            **kwargs
        )
        return source
    return _create_source


@pytest.fixture
def user_factory():
    """Factory for creating test users"""
    def _create_user(
        username: str = "testuser",
        email: str = "test@example.com",
        **kwargs
    ):
        user = User(
            username=username,
            email=email,
            hashed_password="hashed_password",
            **kwargs
        )
        return user
    return _create_user


@pytest.fixture
def trending_topic_factory():
    """Factory for creating test trending topics"""
    def _create_trending_topic(
        topic: str = "Test Topic",
        topic_category: str = "technology",
        trend_score: float = 0.5,
        **kwargs
    ):
        trending_topic = TrendingTopic(
            topic=topic,
            topic_category=topic_category,
            trend_score=trend_score,
            **kwargs
        )
        return trending_topic
    return _create_trending_topic


@pytest.fixture
def analysis_task_factory():
    """Factory for creating test analysis tasks"""
    def _create_analysis_task(
        task_type: str = "sentiment",
        task_name: str = "Test Analysis Task",
        article_id: str = None,
        **kwargs
    ):
        task = AnalysisTask(
            task_type=task_type,
            task_name=task_name,
            article_id=article_id,
            status=AnalysisTaskStatus.PENDING,
            **kwargs
        )
        return task
    return _create_analysis_task


# ============================================================================
# MOCK EXTERNAL SERVICES
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    
    # Mock successful responses
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(
            message=Mock(
                content=json.dumps({
                    "label": "positive",
                    "confidence": 0.85,
                    "reasoning": "Positive sentiment detected"
                })
            )
        )],
        usage=Mock(total_tokens=100)
    )
    
    return client


@pytest.fixture
def mock_news_api_client():
    """Mock NewsAPI client"""
    client = Mock()
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "totalResults": 1,
        "articles": [
            {
                "source": {"id": "test-source", "name": "Test Source"},
                "author": "Test Author",
                "title": "Test Article",
                "description": "Test Description",
                "url": "https://example.com/test",
                "urlToImage": "https://example.com/image.jpg",
                "publishedAt": "2023-12-01T10:00:00Z",
                "content": "Test content"
            }
        ]
    }
    
    client.get.return_value = mock_response
    return client


@pytest.fixture
def mock_guardian_client():
    """Mock Guardian API client"""
    client = Mock()
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": {
            "status": "ok",
            "total": 1,
            "results": [
                {
                    "id": "test-article-123",
                    "type": "article",
                    "sectionId": "technology",
                    "sectionName": "Technology",
                    "webPublicationDate": "2023-12-01T10:00:00Z",
                    "webTitle": "Test Article from Guardian",
                    "webUrl": "https://example.com/guardian-test",
                    "apiUrl": "https://content.guardianapis.com/test",
                    "fields": {
                        "headline": "Test Guardian Article",
                        "standfirst": "Test description",
                        "byline": "Guardian Reporter",
                        "body": "Test content from Guardian"
                    }
                }
            ]
        }
    }
    
    client.get.return_value = mock_response
    return client


@pytest.fixture
def mock_nytimes_client():
    """Mock New York Times API client"""
    client = Mock()
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "OK",
        "response": {
            "docs": [
                {
                    "web_url": "https://nytimes.com/test",
                    "snippet": "Test article from NYT",
                    "lead_paragraph": "Test lead paragraph",
                    "abstract": "Test abstract",
                    "source": ["The New York Times"],
                    "headline": {
                        "main": "Test NYTimes Article",
                        "kicker": "Technology"
                    },
                    "pub_date": "2023-12-01T10:00:00+0000",
                    "document_type": "article",
                    "news_desk": "Technology",
                    "section_name": "Technology"
                }
            ],
            "meta": {
                "hits": 1,
                "offset": 0,
                "time": 45
            }
        }
    }
    
    client.get.return_value = mock_response
    return client


# ============================================================================
# TEST DATA HELPERS
# ============================================================================

@pytest.fixture
def sample_article_data():
    """Sample article data for testing"""
    return {
        "title": "Revolutionary AI Chip Announces 100x Performance Boost",
        "content": "A groundbreaking artificial intelligence chip has achieved remarkable performance improvements...",
        "summary": "AI chip breakthrough announced",
        "url": "https://example.com/ai-chip-breakthrough",
        "source_name": "Tech News Daily",
        "published_at": "2023-12-01T10:00:00Z",
        "sentiment_score": 0.8,
        "sentiment_label": "positive",
        "bias_score": 0.3,
        "topic_tags": ["artificial intelligence", "technology", "chips"],
        "relevance_score": 0.9
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user"
    }


@pytest.fixture
def sample_source_data():
    """Sample source data for testing"""
    return {
        "name": "Tech News Daily",
        "url": "https://technews.com",
        "api_name": "newsapi",
        "api_source_id": "tech-news",
        "country": "US",
        "language": "en",
        "credibility_score": 0.8,
        "is_active": True
    }


# Helper to skip tests that require external services
def pytest_runtest_setup(item):
    """Skip tests that require external services unless explicitly requested"""
    if "requires_api_key" in [mark.name for mark in item.iter_markers()]:
        if not os.getenv("ENABLE_API_TESTS"):
            pytest.skip("API tests disabled (set ENABLE_API_TESTS=1 to enable)")


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================

def pytest_configure(config):
    """Configure pytest with coverage and custom settings"""
    # Configure coverage
    config.option.cov = app
    config.option.cov_append = True
    config.option.cov_report = ['term-missing', 'html']
    config.option.cov_source = ['app/']
    
    # Add custom markers
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "redis: marks tests that require Redis")
    config.addinivalue_line("markers", "openai: marks tests that require OpenAI API")
    config.addinivalue_line("markers", "celery: marks tests that require Celery")
    config.addinivalue_line("markers", "requires_api_key: marks tests that require external API keys")
    
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["CELERY_BROKER_URL"] = "redis://localhost:6379/15"
    os.environ["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/15"
    os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"
    os.environ["JWT_ALGORITHM"] = "HS256"


# ============================================================================
# TEST DATA HELPERS
# ============================================================================

@pytest.fixture
def sample_article_data():
    """Sample article data for testing"""
    return {
        "title": "Revolutionary AI Chip Announces 100x Performance Boost",
        "content": "A groundbreaking artificial intelligence chip has achieved remarkable performance improvements...",
        "summary": "AI chip breakthrough announced",
        "url": "https://example.com/ai-chip-breakthrough",
        "source_name": "Tech News Daily",
        "published_at": "2023-12-01T10:00:00Z",
        "sentiment_score": 0.8,
        "sentiment_label": "positive",
        "bias_score": 0.3,
        "topic_tags": ["artificial intelligence", "technology", "chips"],
        "relevance_score": 0.9
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user"
    }


@pytest.fixture
def sample_source_data():
    """Sample source data for testing"""
    return {
        "name": "Tech News Daily",
        "url": "https://technews.com",
        "api_name": "newsapi",
        "api_source_id": "tech-news",
        "country": "US",
        "language": "en",
        "credibility_score": 0.8,
        "is_active": True
    }


@pytest.fixture
def sample_search_data():
    """Sample search data for testing"""
    return {
        "query": "artificial intelligence",
        "filters": {
            "date_from": "2023-12-01",
            "date_to": "2023-12-31",
            "sentiment": "positive",
            "source": "tech-news"
        },
        "sort": "relevance",
        "limit": 20,
        "offset": 0
    }


@pytest.fixture
def sample_ai_analysis_data():
    """Sample AI analysis data for testing"""
    return {
        "text": "This is a sample text for AI analysis testing",
        "analysis_types": ["sentiment", "topics", "summary"],
        "options": {
            "max_length": 200,
            "confidence_threshold": 0.7
        }
    }


# ============================================================================
# COVERAGE AND REPORTING
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for coverage and reporting"""
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test-specific environment
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15",
        "OPENAI_API_KEY": "test-key-for-testing",
        "CELERY_BROKER_URL": "redis://localhost:6379/15",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/15",
        "DEBUG": "true",
        "AI_ANALYSIS_TIMEOUT": "10",
        "CACHE_TTL": "300",
        "JWT_SECRET_KEY": "test-jwt-secret-key",
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRE_MINUTES": "30"
    }
    
    # Update environment
    os.environ.update(test_env)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# PERFORMANCE TESTING HELPERS
# ============================================================================

@pytest.fixture
def performance_monitor():
    """Monitor for performance testing"""
    import time
    import psutil
    from contextlib import contextmanager
    
    @contextmanager
    def measure_time():
        start_time = time.time()
        start_cpu = psutil.cpu_percent()
        start_memory = psutil.virtual_memory().percent
        
        yield
        
        end_time = time.time()
        end_cpu = psutil.cpu_percent()
        end_memory = psutil.virtual_memory().percent
        
        print(f"\nPerformance Metrics:")
        print(f"  Execution Time: {end_time - start_time:.4f}s")
        print(f"  CPU Usage: {end_cpu - start_cpu:.2f}%")
        print(f"  Memory Usage: {end_memory - start_memory:.2f}%")
    
    return measure_time


@pytest.fixture
def memory_profiler():
    """Memory profiling fixture"""
    import tracemalloc
    from contextlib import contextmanager
    
    @contextmanager
    def profile_memory():
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        yield
        
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        print("\nMemory Usage (Top 10):")
        for stat in top_stats[:10]:
            print(stat)
        
        tracemalloc.stop()
    
    return profile_memory


# ============================================================================
# TEST ORCHESTRATION
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_session():
    """Setup for entire test session"""
    print("\n=== Starting AI News Aggregator Test Suite ===")
    print("Database: SQLite in-memory")
    print("Cache: Mock Redis")
    print("AI Services: Mocked")
    print("External APIs: Mocked")
    print("=" * 50)
    
    yield
    
    print("\n=== Test Suite Completed ===")


@pytest.fixture(autouse=True)
def reset_mocks_between_tests():
    """Reset mocks between each test to ensure isolation"""
    yield
    # Any cleanup needed between tests