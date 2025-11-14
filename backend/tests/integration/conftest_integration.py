"""
pytest configuration for integration tests
Configuración de pytest para tests de integración

Este archivo configura pytest específicamente para los tests de integración,
definiendo markers, fixtures, y configuraciones específicas.
"""

import os
import pytest
import asyncio
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch

# Import testing utilities
pytest_plugins = ["pytest_asyncio"]


# ============================================================================
# MARKER DEFINITIONS
# ============================================================================

def pytest_configure(config):
    """Configure custom markers for integration tests"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "api: marks tests that test API functionality")
    config.addinivalue_line("markers", "database: marks tests that require database")
    config.addinivalue_line("markers", "redis: marks tests that require Redis")
    config.addinivalue_line("markers", "external_api: marks tests that use external APIs")
    config.addinivalue_line("markers", "ai: marks tests that involve AI processing")
    config.addinivalue_line("markers", "celery: marks tests that require Celery")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "requires_api_key: marks tests that require real API keys")
    config.addinivalue_line("markers", "mock: marks tests that use mocks exclusively")


# ============================================================================
# TEST ENVIRONMENT SETUP
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_integration_test_env():
    """Setup test environment for integration tests"""
    
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test environment variables
    test_env_vars = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15",
        "OPENAI_API_KEY": "test-openai-key-integration",
        "NEWSAPI_KEY": "test-newsapi-key-integration",
        "GUARDIAN_API_KEY": "test-guardian-key-integration",
        "NYTIMES_API_KEY": "test-nytimes-key-integration",
        "CELERY_BROKER_URL": "redis://localhost:6379/15",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/15",
        "AI_ANALYSIS_TIMEOUT": "10",  # Faster for tests
        "CACHE_TTL": "300",  # 5 minutes for tests
        "DEBUG": "true",
        "LOG_LEVEL": "WARNING"  # Reduce noise in tests
    }
    
    # Apply test environment
    for key, value in test_env_vars.items():
        os.environ[key] = value
    
    print("\n🧪 Integration Test Environment Setup")
    print("=" * 50)
    for key, value in test_env_vars.items():
        print(f"✅ {key}={value}")
    print("=" * 50)
    
    yield
    
    # Cleanup: restore original environment
    print("\n🔧 Cleaning up integration test environment")
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# TEST MARKER CONDITIONAL SKIPPING
# ============================================================================

def pytest_runtest_setup(item):
    """Setup test run with conditional skipping"""
    
    # Skip tests requiring real API keys unless explicitly enabled
    if "requires_api_key" in [mark.name for mark in item.iter_markers()]:
        if not os.getenv("ENABLE_API_TESTS"):
            pytest.skip("API tests disabled (set ENABLE_API_TESTS=1 to enable)")
    
    # Skip slow tests unless explicitly enabled
    if "slow" in [mark.name for mark in item.iter_markers()]:
        if not os.getenv("RUN_SLOW_TESTS"):
            pytest.skip("Slow tests disabled (set RUN_SLOW_TESTS=1 to enable)")
    
    # Print test info for debugging
    print(f"\n🔍 Running test: {item.nodeid}")
    markers = [mark.name for mark in item.iter_markers()]
    if markers:
        print(f"📋 Markers: {', '.join(markers)}")


# ============================================================================
# ASYNC EVENT LOOP CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# TIMEOUT CONFIGURATION
# ============================================================================

# Global timeout for async tests
pytest_asyncio_global_timeout = 300  # 5 minutes


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================

@pytest.fixture
def integration_test_config():
    """Configuration for integration tests"""
    return {
        "timeout": 30,
        "retries": 3,
        "batch_size": 10,
        "concurrent_limit": 5,
        "cache_ttl": 300,
        "rate_limit": 100,
    }


@pytest.fixture
def test_data_factory():
    """Factory for creating test data"""
    
    def create_article_data(**overrides):
        """Create test article data with optional overrides"""
        default_data = {
            "title": "Test Article Title",
            "content": "This is test article content for integration testing.",
            "description": "Test article description",
            "url": "https://example.com/test-article",
            "author": "Test Author",
            "image_url": "https://example.com/image.jpg",
            "published_at": "2023-12-01T10:00:00Z",
            "status": "pending",
            "source_id": 1
        }
        default_data.update(overrides)
        return default_data
    
    def create_source_data(**overrides):
        """Create test source data with optional overrides"""
        default_data = {
            "name": "Test Source",
            "api_name": "test_api",
            "api_source_id": "test-source-id",
            "url": "https://example.com",
            "country": "US",
            "language": "en",
            "credibility_score": 0.8,
            "is_active": True,
            "rate_limit_per_hour": 100
        }
        default_data.update(overrides)
        return default_data
    
    def create_user_data(**overrides):
        """Create test user data with optional overrides"""
        default_data = {
            "email": "test@example.com",
            "username": "testuser",
            "is_active": True,
            "preferences": {
                "topics": ["technology", "science"],
                "sources": ["test_api"],
                "notifications": {"email": True, "push": False}
            }
        }
        default_data.update(overrides)
        return default_data
    
    return {
        "article": create_article_data,
        "source": create_source_data,
        "user": create_user_data
    }


@pytest.fixture
def mock_external_responses():
    """Mock responses for external APIs"""
    return {
        "newsapi": {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "source": {"id": "test-source", "name": "Test Source"},
                    "author": "Test Author",
                    "title": "Test News Article",
                    "description": "Test description",
                    "url": "https://example.com/news",
                    "publishedAt": "2023-12-01T10:00:00Z",
                    "content": "Test news content"
                }
            ]
        },
        "guardian": {
            "response": {
                "status": "ok",
                "total": 1,
                "results": [
                    {
                        "id": "test/2023/dec/01/test-article",
                        "webTitle": "Guardian Test Article",
                        "webUrl": "https://guardian.com/test",
                        "webPublicationDate": "2023-12-01T10:00:00Z",
                        "fields": {
                            "body": "Guardian test content",
                            "byline": "Guardian Author"
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
                        "web_url": "https://nytimes.com/test",
                        "headline": {"main": "NYTimes Test Article"},
                        "lead_paragraph": "NYTimes test content",
                        "pub_date": "2023-12-01T10:00:00Z",
                        "byline": {"original": "NYTimes Author"}
                    }
                ],
                "meta": {"hits": 1}
            }
        }
    }


@pytest.fixture
def performance_benchmark_config():
    """Configuration for performance benchmarks"""
    return {
        "warmup_iterations": 3,
        "benchmark_iterations": 10,
        "timeout_threshold": 5.0,  # seconds
        "memory_threshold": 100,   # MB
        "concurrent_users": 10
    }


# ============================================================================
# ERROR INJECTION FOR CHAOS TESTING
# ============================================================================

@pytest.fixture
def error_injector():
    """Utility for injecting errors in tests (chaos testing)"""
    
    class ErrorInjector:
        def __init__(self):
            self.enabled = os.getenv("ENABLE_ERROR_INJECTION", "false").lower() == "true"
            self.error_rate = float(os.getenv("ERROR_RATE", "0.1"))
        
        def should_inject_error(self) -> bool:
            """Determine if error should be injected"""
            if not self.enabled:
                return False
            import random
            return random.random() < self.error_rate
        
        def inject_network_error(self):
            """Inject network-related error"""
            if self.should_inject_error():
                raise ConnectionError("Injected network error")
        
        def inject_timeout_error(self):
            """Inject timeout error"""
            if self.should_inject_error():
                raise asyncio.TimeoutError("Injected timeout error")
        
        def inject_rate_limit_error(self):
            """Inject rate limit error"""
            if self.should_inject_error():
                raise Exception("Rate limit exceeded")
    
    return ErrorInjector()


# ============================================================================
# TEST REPORTING
# ============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Custom terminal summary for integration tests"""
    terminalreporter.write_sep("=", "Integration Test Summary")
    
    # Collect test results by marker
    marker_stats = {}
    for line in terminalreporter.stats.get('passed', []):
        for marker in line.iter_markers():
            marker_stats.setdefault(marker.name, {'passed': 0, 'failed': 0, 'skipped': 0})
            marker_stats[marker.name]['passed'] += 1
    
    for line in terminalreporter.stats.get('failed', []):
        for marker in line.iter_markers():
            marker_stats.setdefault(marker.name, {'passed': 0, 'failed': 0, 'skipped': 0})
            marker_stats[marker.name]['failed'] += 1
    
    for line in terminalreporter.stats.get('skipped', []):
        for marker in line.iter_markers():
            marker_stats.setdefault(marker.name, {'passed': 0, 'failed': 0, 'skipped': 0})
            marker_stats[marker.name]['skipped'] += 1
    
    if marker_stats:
        terminalreporter.write_line("\n📊 Test Results by Marker:")
        for marker, stats in marker_stats.items():
            total = sum(stats.values())
            terminalreporter.write_line(
                f"  {marker}: {stats['passed']} passed, {stats['failed']} failed, "
                f"{stats['skipped']} skipped (total: {total})"
            )
    
    # Environment info
    terminalreporter.write_line(f"\n🖥️ Environment:")
    terminalreporter.write_line(f"  Testing: {os.getenv('TESTING', 'false')}")
    terminalreporter.write_line(f"  Database: {os.getenv('DATABASE_URL', 'not set')}")
    terminalreporter.write_line(f"  Redis: {os.getenv('REDIS_URL', 'not set')}")
    terminalreporter.write_line(f"  API Tests Enabled: {os.getenv('ENABLE_API_TESTS', 'false')}")


# ============================================================================
# INTEGRATION TEST UTILITIES
# ============================================================================

def wait_for_service(url: str, timeout: int = 30, check_interval: int = 1):
    """Wait for a service to become available"""
    import asyncio
    import aiohttp
    
    async def check_service():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    return response.status < 500
            except:
                return False
    
    async def wait_loop():
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout:
            if await check_service():
                return True
            await asyncio.sleep(check_interval)
        return False
    
    return asyncio.run(wait_loop())


class IntegrationTestTimer:
    """Timer utility for integration tests"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = asyncio.get_event_loop().time()
    
    def stop(self):
        """Stop timing"""
        self.end_time = asyncio.get_event_loop().time()
    
    def elapsed(self) -> float:
        """Get elapsed time"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# ============================================================================
# PYTEST COLLECTION MODIFICATION
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Modify test collection to add integration markers automatically"""
    
    for item in items:
        # Add integration marker based on file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add specific markers based on test content
        if "api" in item.name.lower() or "api_integration" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        
        if "database" in item.name.lower() or "database_integration" in str(item.fspath):
            item.add_marker(pytest.mark.database)
        
        if "cache" in item.name.lower() or "redis" in item.name.lower() or "cache_integration" in str(item.fspath):
            item.add_marker(pytest.mark.redis)
        
        if "external" in item.name.lower() or "external_api_integration" in str(item.fspath):
            item.add_marker(pytest.mark.external_api)
        
        if "ai" in item.name.lower() or "ai_integration" in str(item.fspath):
            item.add_marker(pytest.mark.ai)
        
        # Mark slow tests
        if any(word in item.name.lower() for word in ["slow", "performance", "benchmark", "stress"]):
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.performance)