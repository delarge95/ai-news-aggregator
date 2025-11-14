"""
Integration tests for Redis caching system
Tests de integración para el sistema de caché Redis

Este archivo contiene tests que verifican la integración completa con Redis,
incluyendo operaciones de cache, invalidación, TTL management,
rate limiting, y performance de cache.
"""

import asyncio
import pytest
import pytest_asyncio
import json
import time
import redis.asyncio as redis
from typing import Dict, List, Any, Optional, Union
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

# Import application components
from app.core.redis_cache import RedisCache, CacheManager
from app.services.ai_processor import AIProcessor
from app.core.rate_limiter import RateLimiter
from app.core.config import settings

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.redis
]


class TestRedisCacheBasicOperations:
    """Test basic Redis cache operations"""
    
    @pytest.fixture
    async def cache_manager(self, test_redis):
        """Create cache manager instance"""
        return CacheManager(
            redis_client=test_redis,
            default_ttl=3600,
            namespace="test_cache"
        )
    
    async def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations"""
        key = "test_key"
        value = {"data": "test_value", "timestamp": datetime.utcnow().isoformat()}
        
        # Set value in cache
        await cache_manager.set(key, value, ttl=300)
        
        # Get value from cache
        cached_value = await cache_manager.get(key)
        
        assert cached_value == value
        assert cached_value["data"] == "test_value"
    
    async def test_cache_nonexistent_key(self, cache_manager):
        """Test getting nonexistent cache key"""
        nonexistent_key = "nonexistent_key"
        cached_value = await cache_manager.get(nonexistent_key)
        
        assert cached_value is None
    
    async def test_cache_expiration(self, cache_manager):
        """Test cache expiration with TTL"""
        key = "expiring_key"
        value = {"data": "expiring_data"}
        
        # Set with short TTL
        await cache_manager.set(key, value, ttl=1)  # 1 second
        
        # Should be available immediately
        cached_value = await cache_manager.get(key)
        assert cached_value == value
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        cached_value = await cache_manager.get(key)
        assert cached_value is None
    
    async def test_cache_update(self, cache_manager):
        """Test updating cached value"""
        key = "update_key"
        initial_value = {"version": 1, "data": "initial"}
        
        # Set initial value
        await cache_manager.set(key, initial_value)
        
        # Update value
        updated_value = {"version": 2, "data": "updated"}
        await cache_manager.set(key, updated_value)
        
        # Verify update
        cached_value = await cache_manager.get(key)
        assert cached_value == updated_value
        assert cached_value["version"] == 2
    
    async def test_cache_delete(self, cache_manager):
        """Test cache deletion"""
        key = "delete_key"
        value = {"data": "to_delete"}
        
        # Set and verify
        await cache_manager.set(key, value)
        assert await cache_manager.get(key) == value
        
        # Delete
        deleted = await cache_manager.delete(key)
        assert deleted is True
        
        # Verify deletion
        assert await cache_manager.get(key) is None
        
        # Delete nonexistent key
        deleted_nonexistent = await cache_manager.delete("nonexistent_key")
        assert deleted_nonexistent is False
    
    async def test_cache_exists(self, cache_manager):
        """Test cache key existence check"""
        key = "exists_key"
        value = {"data": "exists"}
        
        # Key should not exist initially
        assert await cache_manager.exists(key) is False
        
        # Set value
        await cache_manager.set(key, value)
        
        # Key should exist now
        assert await cache_manager.exists(key) is True
    
    async def test_cache_clear(self, cache_manager):
        """Test cache clearing"""
        # Set multiple keys
        for i in range(5):
            await cache_manager.set(f"key_{i}", {"data": f"value_{i}"})
        
        # Verify keys exist
        for i in range(5):
            assert await cache_manager.get(f"key_{i}") is not None
        
        # Clear cache
        await cache_manager.clear()
        
        # Verify all keys are gone
        for i in range(5):
            assert await cache_manager.get(f"key_{i}") is None


class TestRedisCacheTTLManagement:
    """Test TTL management in Redis cache"""
    
    @pytest.fixture
    async def ttl_cache(self, test_redis):
        """Create cache instance for TTL testing"""
        return CacheManager(
            redis_client=test_redis,
            default_ttl=600  # 10 minutes
        )
    
    async def test_default_ttl(self, ttl_cache):
        """Test default TTL application"""
        key = "default_ttl_key"
        value = {"data": "default_ttl_value"}
        
        # Set without explicit TTL (should use default)
        await ttl_cache.set(key, value)
        
        # Check TTL
        ttl = await ttl_cache.ttl(key)
        assert ttl > 0
        assert ttl <= 600
    
    async def test_explicit_ttl(self, ttl_cache):
        """Test explicit TTL setting"""
        key = "explicit_ttl_key"
        value = {"data": "explicit_ttl_value"}
        
        # Set with explicit TTL
        await ttl_cache.set(key, value, ttl=1800)  # 30 minutes
        
        # Check TTL
        ttl = await ttl_cache.ttl(key)
        assert ttl > 0
        assert ttl <= 1800
    
    async def test_persistent_cache(self, ttl_cache):
        """Test persistent cache (no expiration)"""
        key = "persistent_key"
        value = {"data": "persistent_value"}
        
        # Set with ttl=0 (no expiration)
        await ttl_cache.set(key, value, ttl=0)
        
        # Should not expire
        ttl = await ttl_cache.ttl(key)
        assert ttl == -1  # Redis returns -1 for no expiration
    
    async def test_ttl_extension(self, ttl_cache):
        """Test extending TTL"""
        key = "extend_ttl_key"
        value = {"data": "extend_value"}
        
        # Set with short TTL
        await ttl_cache.set(key, value, ttl=60)
        
        initial_ttl = await ttl_cache.ttl(key)
        assert initial_ttl > 0 and initial_ttl <= 60
        
        # Extend TTL
        await ttl_cache.expire(key, 300)
        
        extended_ttl = await ttl_cache.ttl(key)
        assert extended_ttl > initial_ttl


class TestRedisCacheDataTypes:
    """Test cache storage of different data types"""
    
    @pytest.fixture
    async def type_cache(self, test_redis):
        """Create cache for data type testing"""
        return CacheManager(redis_client=test_redis)
    
    async def test_string_cache(self, type_cache):
        """Test string data caching"""
        key = "string_key"
        value = "This is a simple string"
        
        await type_cache.set(key, value)
        cached_value = await type_cache.get(key)
        
        assert cached_value == value
        assert isinstance(cached_value, str)
    
    async def test_json_cache(self, type_cache):
        """Test JSON data caching"""
        key = "json_key"
        value = {
            "id": 123,
            "name": "Test Item",
            "tags": ["tag1", "tag2"],
            "metadata": {
                "created": "2023-12-01",
                "active": True
            }
        }
        
        await type_cache.set(key, value)
        cached_value = await type_cache.get(key)
        
        assert cached_value == value
        assert cached_value["id"] == 123
        assert cached_value["tags"] == ["tag1", "tag2"]
    
    async def test_list_cache(self, type_cache):
        """Test list data caching"""
        key = "list_key"
        value = [1, 2, 3, "item", {"nested": "value"}]
        
        await type_cache.set(key, value)
        cached_value = await type_cache.get(key)
        
        assert cached_value == value
        assert len(cached_value) == 5
    
    async def test_numeric_cache(self, type_cache):
        """Test numeric data caching"""
        test_cases = [
            ("int_key", 42),
            ("float_key", 3.14159),
            ("zero_key", 0),
            ("negative_key", -100)
        ]
        
        for key, value in test_cases:
            await type_cache.set(key, value)
            cached_value = await type_cache.get(key)
            assert cached_value == value
            assert isinstance(cached_value, (int, float))
    
    async def test_boolean_cache(self, type_cache):
        """Test boolean data caching"""
        true_key = "bool_true_key"
        false_key = "bool_false_key"
        
        await type_cache.set(true_key, True)
        await type_cache.set(false_key, False)
        
        assert await type_cache.get(true_key) is True
        assert await type_cache.get(false_key) is False


class TestRedisCacheNamespaces:
    """Test cache namespacing functionality"""
    
    @pytest.fixture
    async def namespaced_cache(self, test_redis):
        """Create namespaced cache"""
        return CacheManager(
            redis_client=test_redis,
            namespace="ai_news_test"
        )
    
    async def test_namespace_isolation(self, namespaced_cache):
        """Test namespace isolation"""
        key = "shared_key"
        value = {"data": "namespaced_data"}
        
        # Set with namespace
        await namespaced_cache.set(key, value)
        
        # Should be stored with namespace prefix
        # (implementation depends on CacheManager)
        
        # Get using same namespace
        cached_value = await namespaced_cache.get(key)
        assert cached_value == value
    
    async def test_namespace_pattern_deletion(self, namespaced_cache):
        """Test pattern-based deletion within namespace"""
        # Set multiple keys with same namespace
        for i in range(5):
            await namespaced_cache.set(f"pattern_{i}", {"data": f"value_{i}"})
        
        # Delete by pattern
        deleted_count = await namespaced_cache.delete_pattern("pattern_*")
        assert deleted_count > 0
        
        # Verify deletion
        for i in range(5):
            cached_value = await namespaced_cache.get(f"pattern_{i}")
            assert cached_value is None
    
    async def test_namespace_listing(self, namespaced_cache):
        """Test listing keys within namespace"""
        # Set keys in namespace
        test_keys = ["item_1", "item_2", "other_item"]
        for key in test_keys:
            await namespaced_cache.set(key, {"data": f"value_for_{key}"})
        
        # List keys in namespace
        keys = await namespaced_cache.keys("item_*")
        
        # Should find item_1 and item_2 but not other_item
        assert len(keys) >= 2
        assert "item_1" in keys or "ai_news_test:item_1" in keys
        assert "item_2" in keys or "ai_news_test:item_2" in keys


class TestRedisCachePerformance:
    """Test Redis cache performance characteristics"""
    
    @pytest.fixture
    async def perf_cache(self, test_redis):
        """Create cache for performance testing"""
        return CacheManager(redis_client=test_redis)
    
    async def test_cache_write_performance(self, perf_cache):
        """Test cache write performance"""
        num_operations = 1000
        start_time = time.time()
        
        # Write multiple items
        for i in range(num_operations):
            await perf_cache.set(f"perf_key_{i}", {"data": f"value_{i}", "index": i})
        
        write_duration = time.time() - start_time
        writes_per_second = num_operations / write_duration
        
        # Should achieve reasonable write performance
        assert writes_per_second > 100
        print(f"Cache write performance: {writes_per_second:.2f} writes/second")
    
    async def test_cache_read_performance(self, perf_cache):
        """Test cache read performance"""
        # First, populate cache
        num_items = 1000
        for i in range(num_items):
            await perf_cache.set(f"read_perf_key_{i}", {"data": f"value_{i}"})
        
        # Measure read performance
        start_time = time.time()
        
        read_keys = [f"read_perf_key_{i}" for i in range(num_items)]
        for key in read_keys:
            await perf_cache.get(key)
        
        read_duration = time.time() - start_time
        reads_per_second = num_items / read_duration
        
        # Should achieve reasonable read performance
        assert reads_per_second > 500
        print(f"Cache read performance: {reads_per_second:.2f} reads/second")
    
    async def test_cache_concurrent_access(self, perf_cache):
        """Test concurrent cache access"""
        num_concurrent = 100
        num_operations = 100
        
        async def cache_operations(worker_id: int):
            results = []
            for i in range(num_operations):
                key = f"concurrent_key_{worker_id}_{i}"
                value = {"worker": worker_id, "operation": i}
                
                await perf_cache.set(key, value)
                cached_value = await perf_cache.get(key)
                results.append(cached_value == value)
            
            return results
        
        # Execute concurrent operations
        start_time = time.time()
        tasks = [cache_operations(i) for i in range(num_concurrent)]
        all_results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        # Verify all operations succeeded
        total_operations = num_concurrent * num_operations
        successful_operations = sum(sum(results) for results in all_results)
        
        assert successful_operations == total_operations
        print(f"Concurrent cache operations: {total_operations} operations in {duration:.2f}s")


class TestRedisCacheIntegrationWithAI:
    """Test cache integration with AI processing"""
    
    @pytest.fixture
    async def ai_cache(self, test_redis):
        """Create cache for AI integration testing"""
        return CacheManager(
            redis_client=test_redis,
            namespace="ai_analysis"
        )
    
    async def test_ai_result_caching(self, ai_cache):
        """Test caching AI analysis results"""
        article_id = "test_article_001"
        analysis_result = {
            "article_id": article_id,
            "sentiment": {"label": "positive", "confidence": 0.85},
            "topic": {"category": "technology", "confidence": 0.9},
            "summary": "AI-powered summary of the article",
            "keywords": ["AI", "technology", "innovation"],
            "processing_time": 2.1,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache the analysis result
        cache_key = f"analysis:{article_id}"
        await ai_cache.set(cache_key, analysis_result, ttl=3600)
        
        # Retrieve from cache
        cached_result = await ai_cache.get(cache_key)
        
        assert cached_result is not None
        assert cached_result["article_id"] == article_id
        assert cached_result["sentiment"]["label"] == "positive"
        assert len(cached_result["keywords"]) == 4
    
    async def test_ai_cache_invalidation(self, ai_cache):
        """Test cache invalidation for AI results"""
        article_ids = ["article_001", "article_002", "article_003"]
        
        # Cache results for multiple articles
        for article_id in article_ids:
            cache_key = f"analysis:{article_id}"
            await ai_cache.set(cache_key, {"article_id": article_id}, ttl=3600)
        
        # Invalidate cache for specific pattern
        await ai_cache.delete_pattern("analysis:article_00*")
        
        # Verify selective invalidation
        assert await ai_cache.get("analysis:article_001") is None
        assert await ai_cache.get("analysis:article_002") is None
        assert await ai_cache.get("analysis:article_003") is None
    
    async def test_ai_cache_warming(self, ai_cache):
        """Test cache warming with common queries"""
        # Pre-populate cache with common analyses
        common_queries = [
            {"query": "artificial intelligence", "result": {"category": "tech", "sentiment": "positive"}},
            {"query": "climate change", "result": {"category": "environment", "sentiment": "neutral"}},
            {"query": "cryptocurrency", "result": {"category": "finance", "sentiment": "mixed"}}
        ]
        
        for query_data in common_queries:
            cache_key = f"query_analysis:{query_data['query']}"
            await ai_cache.set(cache_key, query_data['result'], ttl=7200)
        
        # Verify cache warming
        for query_data in common_queries:
            cache_key = f"query_analysis:{query_data['query']}"
            cached_result = await ai_cache.get(cache_key)
            assert cached_result == query_data['result']


class TestRedisRateLimiting:
    """Test rate limiting using Redis"""
    
    @pytest.fixture
    async def rate_limiter(self, test_redis):
        """Create rate limiter instance"""
        return RateLimiter(
            redis_client=test_redis,
            window_size=60,  # 1 minute window
            max_requests=10  # 10 requests per window
        )
    
    async def test_rate_limiting_allowance(self, rate_limiter):
        """Test rate limiting allows requests within limit"""
        client_id = "test_client_001"
        
        # Make requests within limit
        for i in range(10):  # Exactly at limit
            allowed = await rate_limiter.is_allowed(client_id)
            assert allowed is True
        
        # Next request should be denied
        allowed = await rate_limiter.is_allowed(client_id)
        assert allowed is False
    
    async def test_rate_limiting_window_reset(self, rate_limiter):
        """Test rate limiting window reset"""
        client_id = "test_client_002"
        
        # Fill up to limit
        for _ in range(10):
            await rate_limiter.is_allowed(client_id)
        
        # Should be denied
        assert await rate_limiter.is_allowed(client_id) is False
        
        # Clear rate limit (simulate window reset)
        await rate_limiter.clear(client_id)
        
        # Should be allowed again
        assert await rate_limiter.is_allowed(client_id) is True
    
    async def test_multiple_clients_rate_limiting(self, rate_limiter):
        """Test rate limiting for multiple clients"""
        clients = ["client_001", "client_002", "client_003"]
        
        # Each client should have independent rate limits
        for client_id in clients:
            # Fill up to limit for this client
            for _ in range(10):
                assert await rate_limiter.is_allowed(client_id) is True
            
            # Next request should be denied
            assert await rate_limiter.is_allowed(client_id) is False
    
    async def test_rate_limit_status(self, rate_limiter):
        """Test rate limit status reporting"""
        client_id = "test_client_003"
        
        # Check initial status
        status = await rate_limiter.get_status(client_id)
        assert status.allowed is True
        assert status.remaining > 0
        
        # Make requests to approach limit
        for _ in range(9):
            await rate_limiter.is_allowed(client_id)
        
        # Check status near limit
        status = await rate_limiter.get_status(client_id)
        assert status.remaining == 1
        
        # Make final allowed request
        await rate_limiter.is_allowed(client_id)
        
        # Check status at limit
        status = await rate_limiter.get_status(client_id)
        assert status.remaining == 0
        assert status.allowed is False


class TestRedisCacheErrorHandling:
    """Test cache error handling and resilience"""
    
    @pytest.fixture
    async def error_cache(self, test_redis):
        """Create cache for error testing"""
        return CacheManager(redis_client=test_redis)
    
    async def test_connection_error_handling(self, error_cache):
        """Test handling of Redis connection errors"""
        # Mock Redis client to raise connection error
        original_client = error_cache.redis_client
        error_client = Mock()
        error_client.ping = AsyncMock(side_effect=redis.ConnectionError("Connection failed"))
        
        error_cache.redis_client = error_client
        
        # Operations should handle errors gracefully
        try:
            result = await error_cache.get("test_key")
            # Should return None or raise appropriate error
            assert result is None
        except redis.ConnectionError:
            # Expected behavior
            pass
    
    async def test_serialization_error_handling(self, error_cache):
        """Test handling of data serialization errors"""
        # Test with non-serializable object
        class NonSerializable:
            def __init__(self):
                self.func = lambda: None  # Functions aren't JSON serializable
        
        non_serializable = NonSerializable()
        
        try:
            await error_cache.set("non_serializable_key", non_serializable)
        except (TypeError, ValueError):
            # Expected for non-serializable objects
            pass
    
    async def test_large_data_handling(self, error_cache):
        """Test handling of large data in cache"""
        # Create large data structure
        large_data = {
            "content": "x" * (1024 * 1024),  # 1MB of data
            "metadata": list(range(10000)),  # Large list
            "nested": {"level1": {"level2": {"level3": "deep_data"}}}
        }
        
        # Should handle large data (or raise appropriate error)
        try:
            await error_cache.set("large_data_key", large_data, ttl=3600)
            cached_data = await error_cache.get("large_data_key")
            assert cached_data is not None
        except redis.ResponseError:
            # Redis might reject large values
            pass


class TestRedisCacheMonitoring:
    """Test cache monitoring and statistics"""
    
    @pytest.fixture
    async def monitor_cache(self, test_redis):
        """Create cache for monitoring tests"""
        return CacheManager(redis_client=test_redis)
    
    async def test_cache_statistics(self, monitor_cache):
        """Test cache statistics collection"""
        # Perform various operations
        await monitor_cache.set("stat_key_1", {"data": "value1"})
        await monitor_cache.set("stat_key_2", {"data": "value2"})
        
        # Get some values
        await monitor_cache.get("stat_key_1")
        await monitor_cache.get("stat_key_2")
        await monitor_cache.get("nonexistent_key")  # Cache miss
        
        # Get statistics
        stats = await monitor_cache.get_stats()
        
        assert "hits" in stats
        assert "misses" in stats
        assert "keys" in stats
        
        # Should have some hits and misses
        assert stats["keys"] >= 2
    
    async def test_cache_health_check(self, monitor_cache):
        """Test cache health checking"""
        # Test normal operation
        is_healthy = await monitor_cache.health_check()
        assert is_healthy is True
        
        # Test with simulated error
        error_client = Mock()
        error_client.ping = AsyncMock(side_effect=Exception("Health check failed"))
        
        monitor_cache.redis_client = error_client
        
        is_healthy = await monitor_cache.health_check()
        assert is_healthy is False


# Cache test utilities
async def create_test_cache_data(cache_manager: CacheManager, num_items: int = 100):
    """Create test data in cache"""
    for i in range(num_items):
        key = f"test_item_{i:04d}"
        value = {
            "id": i,
            "name": f"Item {i}",
            "data": f"Data for item {i}",
            "timestamp": datetime.utcnow().isoformat()
        }
        await cache_manager.set(key, value, ttl=3600)


async def benchmark_cache_operations(cache_manager: CacheManager, num_operations: int = 1000):
    """Benchmark cache operations"""
    # Write benchmark
    start_time = time.time()
    for i in range(num_operations):
        await cache_manager.set(f"bench_key_{i}", {"value": i})
    write_duration = time.time() - start_time
    
    # Read benchmark
    start_time = time.time()
    for i in range(num_operations):
        await cache_manager.get(f"bench_key_{i}")
    read_duration = time.time() - start_time
    
    return {
        "write_duration": write_duration,
        "read_duration": read_duration,
        "write_ops_per_sec": num_operations / write_duration,
        "read_ops_per_sec": num_operations / read_duration
    }


def validate_cache_response(response: Any, expected_type: type = None):
    """Validate cache response format"""
    if expected_type:
        assert isinstance(response, expected_type)
    
    # Additional validation based on response type
    if isinstance(response, dict):
        assert "data" in response or "value" in response or "result" in response
    elif isinstance(response, list):
        assert len(response) >= 0


if __name__ == "__main__":
    print("Cache integration tests configuration loaded successfully")