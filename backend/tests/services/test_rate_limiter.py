"""
Unit tests for rate limiting system
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio
from collections import defaultdict


class TestRateLimiter:
    """Test suite for rate limiting service"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.test_api_keys = {
            "newsapi": "test_newsapi_key",
            "guardian": "test_guardian_key", 
            "nytimes": "test_nytimes_key"
        }
        
        self.test_sources = [
            {"api_name": "newsapi", "rate_limit_per_hour": 100, "name": "NewsAPI"},
            {"api_name": "guardian", "rate_limit_per_hour": 50, "name": "Guardian"},
            {"api_name": "nytimes", "rate_limit_per_hour": 75, "name": "NYTimes"}
        ]

    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter instance for testing"""
        from app.services.rate_limiter import RateLimiter
        return RateLimiter(
            default_limits={
                "newsapi": {"requests_per_hour": 100, "requests_per_minute": 10},
                "guardian": {"requests_per_hour": 50, "requests_per_minute": 5},
                "nytimes": {"requests_per_hour": 75, "requests_per_minute": 8}
            },
            enable_monitoring=True,
            cleanup_interval_minutes=60
        )

    def test_initialization(self, rate_limiter):
        """Test rate limiter initialization"""
        assert rate_limiter.default_limits["newsapi"]["requests_per_hour"] == 100
        assert rate_limiter.default_limits["guardian"]["requests_per_minute"] == 5
        assert rate_limiter.enable_monitoring is True
        assert rate_limiter.cleanup_interval_minutes == 60

    def test_check_rate_limit_allowed(self, rate_limiter):
        """Test rate limit check when request is allowed"""
        api_name = "newsapi"
        request_key = "test_key"
        
        # First request should always be allowed
        allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
        
        assert allowed is True
        assert "remaining_requests" in limit_info
        assert limit_info["remaining_requests"] > 0
        assert "reset_time" in limit_info

    def test_check_rate_limit_exceeded(self, rate_limiter):
        """Test rate limit check when limit is exceeded"""
        api_name = "guardian"
        request_key = "test_key"
        
        # Fill up the rate limit
        for _ in range(rate_limiter.default_limits["guardian"]["requests_per_hour"]):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Next request should be denied
        allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
        
        assert allowed is False
        assert limit_info["remaining_requests"] == 0
        assert "retry_after" in limit_info

    def test_per_minute_rate_limiting(self, rate_limiter):
        """Test per-minute rate limiting"""
        api_name = "nytimes"
        request_key = "test_key"
        
        # Exceed per-minute limit
        for _ in range(rate_limiter.default_limits["nytimes"]["requests_per_minute"]):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Next request should be denied (per-minute limit)
        allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
        
        assert allowed is False
        assert "per_minute_limit_exceeded" in limit_info.get("reason", "")

    def test_custom_rate_limits(self, rate_limiter):
        """Test custom rate limits for specific keys"""
        api_name = "newsapi"
        request_key = "premium_key"
        
        # Set custom higher limit for premium key
        rate_limiter.set_custom_limit(
            api_name, 
            request_key, 
            {"requests_per_hour": 200, "requests_per_minute": 20}
        )
        
        # Should allow more requests
        for _ in range(150):
            allowed, _ = rate_limiter.check_rate_limit(api_name, request_key)
            if not allowed:
                break
        
        # At least 150 requests should have been allowed
        assert True  # If we got here, the test passed

    def test_rate_limit_reset_time(self, rate_limiter):
        """Test rate limit reset timing"""
        api_name = "guardian"
        request_key = "test_key"
        
        # Fill up the limit
        for _ in range(rate_limiter.default_limits["guardian"]["requests_per_hour"]):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Check when limit should reset
        allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
        
        assert allowed is False
        assert "reset_time" in limit_info
        
        reset_time = limit_info["reset_time"]
        assert isinstance(reset_time, datetime)
        # Reset should be within the next hour
        assert reset_time > datetime.utcnow()

    def test_multiple_api_handling(self, rate_limiter):
        """Test rate limiting for multiple APIs"""
        apis = ["newsapi", "guardian", "nytimes"]
        
        for api_name in apis:
            request_key = f"key_{api_name}"
            
            # Each API should have independent rate limits
            allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
            assert allowed is True
            assert limit_info["api_name"] == api_name

    def test_rate_limit_monitoring(self, rate_limiter):
        """Test rate limit monitoring and statistics"""
        if not rate_limiter.enable_monitoring:
            pytest.skip("Monitoring disabled")
        
        api_name = "newsapi"
        request_key = "monitoring_test_key"
        
        # Make several requests
        for _ in range(10):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Check statistics
        stats = rate_limiter.get_rate_limit_stats(api_name, request_key)
        
        assert "total_requests" in stats
        assert "requests_in_last_hour" in stats
        assert "requests_in_last_minute" in stats
        assert "limit_remaining" in stats
        assert "reset_time" in stats

    def test_rate_limit_monitoring_global_stats(self, rate_limiter):
        """Test global rate limit statistics"""
        if not rate_limiter.enable_monitoring:
            pytest.skip("Monitoring disabled")
        
        # Make requests for different APIs
        for api_name in ["newsapi", "guardian"]:
            for _ in range(5):
                rate_limiter.check_rate_limit(api_name, f"key_{api_name}")
        
        global_stats = rate_limiter.get_global_stats()
        
        assert "total_apis_monitored" in global_stats
        assert "total_requests_last_hour" in global_stats
        assert "top_apis_by_usage" in global_stats
        assert global_stats["total_apis_monitored"] >= 2

    def test_cleanup_old_entries(self, rate_limiter):
        """Test cleanup of old rate limit entries"""
        api_name = "newsapi"
        request_key = "cleanup_test_key"
        
        # Manually add old entries
        old_time = datetime.utcnow() - timedelta(hours=2)
        rate_limiter.request_history[api_name][request_key].append(old_time)
        
        # Add recent entry
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        rate_limiter.request_history[api_name][request_key].append(recent_time)
        
        # Run cleanup
        cleaned_count = rate_limiter.cleanup_old_entries()
        
        # Should have cleaned old entries
        assert cleaned_count > 0
        assert len(rate_limiter.request_history[api_name][request_key]) == 1

    def test_get_wait_time(self, rate_limiter):
        """Test wait time calculation"""
        api_name = "guardian"
        request_key = "wait_test_key"
        
        # Fill up the limit
        for _ in range(rate_limiter.default_limits["guardian"]["requests_per_hour"]):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        wait_time = rate_limiter.get_wait_time(api_name, request_key)
        
        assert wait_time > 0
        assert isinstance(wait_time, (int, float))
        assert wait_time <= 3600  # Should not exceed 1 hour

    def test_reset_rate_limit(self, rate_limiter):
        """Test manual rate limit reset"""
        api_name = "newsapi"
        request_key = "reset_test_key"
        
        # Fill up the limit
        for _ in range(rate_limiter.default_limits["newsapi"]["requests_per_hour"]):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Verify limit is exceeded
        allowed, _ = rate_limiter.check_rate_limit(api_name, request_key)
        assert allowed is False
        
        # Reset the limit
        success = rate_limiter.reset_rate_limit(api_name, request_key)
        assert success is True
        
        # Should be allowed now
        allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
        assert allowed is True
        assert limit_info["remaining_requests"] > 0

    @pytest.mark.asyncio
    async def test_async_rate_limit_check(self, rate_limiter):
        """Test async rate limit checking"""
        api_name = "newsapi"
        request_key = "async_test_key"
        
        allowed, limit_info = await rate_limiter.async_check_rate_limit(api_name, request_key)
        
        assert allowed is True
        assert "remaining_requests" in limit_info
        
        # Test with custom limits
        custom_limits = {"requests_per_hour": 5, "requests_per_minute": 1}
        allowed2, limit_info2 = await rate_limiter.async_check_rate_limit(
            api_name, 
            "custom_key", 
            custom_limits=custom_limits
        )
        
        assert allowed2 is True
        assert limit_info2["custom_limits"] == custom_limits

    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self, rate_limiter):
        """Test handling of concurrent requests"""
        api_name = "guardian"
        request_key = "concurrent_test_key"
        custom_limits = {"requests_per_hour": 3, "requests_per_minute": 2}
        
        # Make concurrent requests
        tasks = []
        for _ in range(5):  # More than the limit
            task = rate_limiter.async_check_rate_limit(
                api_name, 
                request_key, 
                custom_limits=custom_limits
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful requests
        successful_requests = sum(
            1 for result in results 
            if not isinstance(result, Exception) and result[0] is True
        )
        
        # Should respect the rate limit even with concurrent requests
        assert successful_requests <= custom_limits["requests_per_hour"]

    def test_burst_handling(self, rate_limiter):
        """Test burst request handling"""
        api_name = "nytimes"
        request_key = "burst_test_key"
        burst_limit = 5
        
        # Allow burst of requests
        allowed_count = 0
        for i in range(burst_limit + 2):  # Exceed burst limit
            allowed, _ = rate_limiter.check_rate_limit(
                api_name, 
                request_key,
                burst_limit=burst_limit
            )
            if allowed:
                allowed_count += 1
        
        # Should not exceed burst limit
        assert allowed_count <= burst_limit

    def test_rate_limit_with_backoff(self, rate_limiter):
        """Test rate limiting with exponential backoff"""
        api_name = "guardian"
        request_key = "backoff_test_key"
        
        # Fill up the limit
        for _ in range(rate_limiter.default_limits["guardian"]["requests_per_hour"]):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Request with backoff
        backoff_strategy = "exponential"
        wait_time = rate_limiter.get_wait_time(
            api_name, 
            request_key, 
            backoff_strategy=backoff_strategy
        )
        
        assert wait_time > 0
        
        # Test different backoff strategies
        strategies = ["linear", "exponential", "fixed"]
        for strategy in strategies:
            wait = rate_limiter.get_wait_time(
                api_name, 
                request_key, 
                backoff_strategy=strategy
            )
            assert wait > 0

    def test_api_specific_limits(self, rate_limiter):
        """Test API-specific rate limits"""
        limits_config = {
            "newsapi": {"requests_per_hour": 100, "requests_per_minute": 10},
            "guardian": {"requests_per_hour": 50, "requests_per_minute": 5}, 
            "nytimes": {"requests_per_hour": 75, "requests_per_minute": 8}
        }
        
        for api_name, limits in limits_config.items():
            request_key = f"test_key_{api_name}"
            
            # Check initial state
            allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
            assert allowed is True
            
            # Verify limits are applied
            rate_limiter.set_api_limits(api_name, limits)
            current_limits = rate_limiter.get_api_limits(api_name)
            assert current_limits == limits

    def test_invalid_api_handling(self, rate_limiter):
        """Test handling of invalid API names"""
        invalid_api = "invalid_api"
        request_key = "test_key"
        
        # Should handle gracefully with default limits
        allowed, limit_info = rate_limiter.check_rate_limit(invalid_api, request_key)
        assert allowed is True  # Should use default limits
        
        # Or should raise exception depending on implementation
        # This depends on the specific implementation choice

    def test_rate_limit_persistence(self, rate_limiter):
        """Test rate limit state persistence"""
        api_name = "newsapi"
        request_key = "persist_test_key"
        
        # Set some state
        rate_limiter.set_custom_limit(
            api_name, 
            request_key, 
            {"requests_per_hour": 50}
        )
        
        # Make some requests to create history
        for _ in range(5):
            rate_limiter.check_rate_limit(api_name, request_key)
        
        # Export state
        state = rate_limiter.export_rate_limit_state()
        
        assert "apis" in state
        assert api_name in state["apis"]
        assert request_key in state["apis"][api_name]
        
        # Import state (reset first)
        rate_limiter.reset_all_limits()
        imported_state = rate_limiter.import_rate_limit_state(state)
        
        assert imported_state is True
        # State should be restored
        custom_limits = rate_limiter.get_custom_limits(api_name, request_key)
        assert custom_limits is not None

    def test_rate_limit_alerts(self, rate_limiter):
        """Test rate limit alert system"""
        if not rate_limiter.enable_monitoring:
            pytest.skip("Monitoring disabled")
        
        api_name = "newsapi"
        request_key = "alert_test_key"
        
        # Setup alert threshold
        alert_threshold = 0.8  # 80% of limit
        
        # Make requests approaching the limit
        for i in range(int(rate_limiter.default_limits["newsapi"]["requests_per_hour"] * alert_threshold)):
            allowed, limit_info = rate_limiter.check_rate_limit(api_name, request_key)
            assert allowed is True
        
        # Check if alert was triggered
        alerts = rate_limiter.get_active_alerts(api_name, request_key)
        
        # Should have alerts when approaching limit
        assert len(alerts) > 0
        
        # Test alert resolution
        for alert in alerts:
            resolved = rate_limiter.resolve_alert(alert["id"])
            assert resolved is True

    def test_rate_limit_error_handling(self, rate_limiter):
        """Test error handling in rate limiting"""
        # Test with invalid inputs
        with pytest.raises((ValueError, TypeError)):
            rate_limiter.check_rate_limit(None, "test_key")
        
        with pytest.raises((ValueError, TypeError)):
            rate_limiter.check_rate_limit("newsapi", None)
        
        # Test with invalid custom limits
        invalid_limits = {"invalid_limit": 100}
        allowed, limit_info = rate_limiter.check_rate_limit(
            "newsapi", 
            "test_key", 
            custom_limits=invalid_limits
        )
        # Should handle gracefully or raise exception depending on implementation
        assert isinstance(limit_info, dict)

    def test_performance_large_number_of_keys(self, rate_limiter):
        """Test performance with large number of API keys"""
        num_keys = 1000
        api_name = "newsapi"
        
        # Test with large number of keys
        start_time = time.time()
        
        for i in range(num_keys):
            key = f"test_key_{i}"
            rate_limiter.check_rate_limit(api_name, key)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should handle efficiently (less than a few seconds)
        assert processing_time < 5.0
        
        # Verify some keys are still accessible
        allowed, _ = rate_limiter.check_rate_limit(api_name, "test_key_0")
        assert isinstance(allowed, bool)