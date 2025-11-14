"""
Integration tests for complete API workflows
Tests de integración para flujos completos de API

Este archivo contiene tests que verifican flujos completos de la API,
incluyendo autenticación, operaciones CRUD, paginación, búsqueda,
y manejo de errores a nivel de API.
"""

import asyncio
import json
import pytest
from typing import Dict, List, Any
from unittest.mock import AsyncMock, Mock, patch
from httpx import AsyncClient
from fastapi import status

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio
]


class TestAPIAuthentication:
    """Test API authentication workflows"""
    
    async def test_api_key_authentication(self, test_client: AsyncClient):
        """Test API key authentication"""
        # Test without API key
        response = await test_client.get("/api/v1/articles/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with invalid API key
        headers = {"Authorization": "Bearer invalid-key"}
        response = await test_client.get("/api/v1/articles/", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test with valid API key (if configured)
        if hasattr(self, 'valid_api_key'):
            headers = {"Authorization": f"Bearer {self.valid_api_key}"}
            response = await test_client.get("/api/v1/articles/", headers=headers)
            assert response.status_code == status.HTTP_200_OK
    
    async def test_rate_limiting_headers(self, test_client: AsyncClient):
        """Test rate limiting headers are present"""
        response = await test_client.get("/api/v1/articles/")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
    
    async def test_cors_headers(self, test_client: AsyncClient):
        """Test CORS headers for cross-origin requests"""
        response = await test_client.options("/api/v1/articles/")
        assert response.status_code in [200, 204]
        assert "access-control-allow-origin" in response.headers.get("access-control-allow-headers", "")


class TestAPIArticlesWorkflow:
    """Test complete article management workflow"""
    
    @pytest.fixture
    async def sample_article_data(self):
        """Sample article data for testing"""
        return {
            "title": "Test Article for Integration",
            "content": "This is a test article content for integration testing.",
            "description": "Test description",
            "url": "https://example.com/test-article",
            "author": "Test Author",
            "source": {
                "id": "test-source",
                "name": "Test Source"
            }
        }
    
    async def test_full_article_lifecycle(self, test_client: AsyncClient, sample_article_data: Dict[str, Any]):
        """Test complete article CRUD lifecycle"""
        
        # CREATE - Add new article
        response = await test_client.post("/api/v1/articles/", json=sample_article_data)
        assert response.status_code == status.HTTP_201_CREATED
        
        article = response.json()
        article_id = article["id"]
        assert article["title"] == sample_article_data["title"]
        assert article["status"] == "pending"
        
        # READ - Get article by ID
        response = await test_client.get(f"/api/v1/articles/{article_id}")
        assert response.status_code == status.HTTP_200_OK
        
        retrieved_article = response.json()
        assert retrieved_article["id"] == article_id
        assert retrieved_article["title"] == sample_article_data["title"]
        
        # UPDATE - Update article
        update_data = {
            "title": "Updated Test Article",
            "status": "processed"
        }
        response = await test_client.put(f"/api/v1/articles/{article_id}", json=update_data)
        assert response.status_code == status.HTTP_200_OK
        
        updated_article = response.json()
        assert updated_article["title"] == update_data["title"]
        assert updated_article["status"] == update_data["status"]
        
        # DELETE - Delete article
        response = await test_client.delete(f"/api/v1/articles/{article_id}")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        response = await test_client.get(f"/api/v1/articles/{article_id}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_article_search_and_filters(self, test_client: AsyncClient, sample_articles: List[Dict[str, Any]]):
        """Test article search and filtering capabilities"""
        
        # Add test articles
        for article_data in sample_articles:
            await test_client.post("/api/v1/articles/", json=article_data)
        
        # Test keyword search
        response = await test_client.get("/api/v1/articles/search?q=AI")
        assert response.status_code == status.HTTP_200_OK
        
        search_results = response.json()
        assert isinstance(search_results["items"], list)
        assert len(search_results["items"]) > 0
        
        # Test date range filtering
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow()
        
        response = await test_client.get(
            f"/api/v1/articles/",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test source filtering
        response = await test_client.get(
            "/api/v1/articles/",
            params={"source": "test-source"}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Test sentiment filtering
        response = await test_client.get(
            "/api/v1/articles/",
            params={"sentiment": "positive"}
        )
        assert response.status_code == status.HTTP_200_OK
    
    async def test_article_pagination(self, test_client: AsyncClient, sample_articles: List[Dict[str, Any]]):
        """Test article pagination functionality"""
        
        # Add test articles
        for article_data in sample_articles:
            await test_client.post("/api/v1/articles/", json=article_data)
        
        # Test first page
        response = await test_client.get("/api/v1/articles/?page=1&size=2")
        assert response.status_code == status.HTTP_200_OK
        
        page1 = response.json()
        assert "items" in page1
        assert "page" in page1
        assert "size" in page1
        assert "total" in page1
        assert page1["items"][0]["page"] == 1
        assert page1["items"][0]["size"] == 2
        
        # Test second page
        response = await test_client.get("/api/v1/articles/?page=2&size=2")
        assert response.status_code == status.HTTP_200_OK
        
        page2 = response.json()
        assert page2["page"] == 2
        assert len(page2["items"]) <= 2
        
        # Test invalid page parameters
        response = await test_client.get("/api/v1/articles/?page=0&size=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    async def test_article_bulk_operations(self, test_client: AsyncClient, sample_articles: List[Dict[str, Any]]):
        """Test bulk article operations"""
        
        # Add multiple articles
        response = await test_client.post("/api/v1/articles/bulk", json=sample_articles)
        assert response.status_code == status.HTTP_201_CREATED
        
        result = response.json()
        assert "created_count" in result
        assert result["created_count"] == len(sample_articles)
        
        # Test bulk update
        bulk_update_data = {
            "status": "processed",
            "filter": {"status": "pending"}
        }
        response = await test_client.put("/api/v1/articles/bulk", json=bulk_update_data)
        assert response.status_code == status.HTTP_200_OK
        
        # Test bulk delete
        response = await test_client.delete("/api/v1/articles/bulk", json={"filter": {"status": "processed"}})
        assert response.status_code == status.HTTP_200_OK
        
        delete_result = response.json()
        assert "deleted_count" in delete_result


class TestAPIAnalyticsWorkflow:
    """Test analytics API workflow"""
    
    async def test_analytics_summary(self, test_client: AsyncClient):
        """Test analytics summary endpoint"""
        response = await test_client.get("/api/v1/analytics/summary")
        assert response.status_code == status.HTTP_200_OK
        
        summary = response.json()
        assert "total_articles" in summary
        assert "sentiment_distribution" in summary
        assert "topic_distribution" in summary
        assert "daily_stats" in summary
    
    async def test_analytics_trending(self, test_client: AsyncClient):
        """Test trending topics endpoint"""
        response = await test_client.get("/api/v1/analytics/trending")
        assert response.status_code == status.HTTP_200_OK
        
        trending = response.json()
        assert "trending_topics" in trending
        assert "trending_keywords" in trending
        assert isinstance(trending["trending_topics"], list)
    
    async def test_analytics_performance(self, test_client: AsyncClient):
        """Test performance metrics endpoint"""
        response = await test_client.get("/api/v1/analytics/performance")
        assert response.status_code == status.HTTP_200_OK
        
        performance = response.json()
        assert "api_response_times" in performance
        assert "ai_processing_times" in performance
        assert "error_rates" in performance


class TestAPIErrorHandling:
    """Test API error handling"""
    
    async def test_validation_errors(self, test_client: AsyncClient):
        """Test validation error responses"""
        # Test missing required fields
        invalid_data = {"title": "Only title"}
        response = await test_client.post("/api/v1/articles/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        error_detail = response.json()
        assert "detail" in error_detail
        assert isinstance(error_detail["detail"], list)
    
    async def test_not_found_errors(self, test_client: AsyncClient):
        """Test 404 error responses"""
        response = await test_client.get("/api/v1/articles/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    async def test_rate_limit_errors(self, test_client: AsyncClient):
        """Test rate limit exceeded responses"""
        # Make rapid requests to trigger rate limiting
        tasks = []
        for _ in range(150):  # Exceed typical rate limits
            task = test_client.get("/api/v1/articles/")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # At least some requests should be rate limited
        rate_limited_count = sum(
            1 for response in responses 
            if not isinstance(response, Exception) and response.status_code == 429
        )
        assert rate_limited_count > 0
    
    async def test_server_errors(self, test_client: AsyncClient):
        """Test 5xx server error responses"""
        with patch('app.services.news_service.NewsService.get_articles') as mock_service:
            mock_service.side_effect = Exception("Database connection failed")
            
            response = await test_client.get("/api/v1/articles/")
            assert response.status_code >= 500


class TestAPIContentNegotiation:
    """Test API content negotiation and response formats"""
    
    async def test_json_response_format(self, test_client: AsyncClient):
        """Test JSON response format"""
        response = await test_client.get("/api/v1/articles/")
        assert response.status_code == status.HTTP_200_OK
        
        # Verify JSON structure
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert "pagination" in data
    
    async def test_xml_response_format(self, test_client: AsyncClient):
        """Test XML response format (if supported)"""
        response = await test_client.get(
            "/api/v1/articles/",
            headers={"Accept": "application/xml"}
        )
        # Should either return XML or 406 Not Acceptable
        assert response.status_code in [200, 406]
    
    async def test_caching_headers(self, test_client: AsyncClient):
        """Test HTTP caching headers"""
        response = await test_client.get("/api/v1/articles/")
        assert response.status_code == 200
        
        # Check for cache headers
        cache_headers = ["etag", "last-modified", "cache-control"]
        for header in cache_headers:
            # Headers might be present or absent depending on implementation
            assert header in response.headers or header.upper() in response.headers


class TestAPIConcurrency:
    """Test API concurrent request handling"""
    
    async def test_concurrent_article_requests(self, test_client: AsyncClient):
        """Test handling of concurrent article requests"""
        # Make multiple concurrent requests
        tasks = []
        for i in range(10):
            task = test_client.get(f"/api/v1/articles/?page={i % 3 + 1}")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Responses should be different (different pages)
        response_data = [response.json() for response in responses]
        unique_pages = set(page["pagination"]["page"] for page in response_data if "pagination" in page)
        assert len(unique_pages) > 1
    
    async def test_concurrent_search_requests(self, test_client: AsyncClient):
        """Test concurrent search requests"""
        search_terms = ["AI", "technology", "news", "science", "sports"]
        
        tasks = []
        for term in search_terms:
            task = test_client.get(f"/api/v1/articles/search?q={term}")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All searches should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Verify different results for different terms
        search_results = [response.json() for response in responses]
        result_counts = [len(result.get("items", [])) for result in search_results]
        assert any(count > 0 for count in result_counts)


class TestAPIHealthCheck:
    """Test API health check endpoints"""
    
    async def test_health_endpoint(self, test_client: AsyncClient):
        """Test health check endpoint"""
        response = await test_client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        
        health_data = response.json()
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "timestamp" in health_data
        assert "version" in health_data
    
    async def test_readiness_endpoint(self, test_client: AsyncClient):
        """Test readiness probe endpoint"""
        response = await test_client.get("/ready")
        assert response.status_code == status.HTTP_200_OK
        
        readiness_data = response.json()
        assert "ready" in readiness_data
        assert "checks" in readiness_data
    
    async def test_liveness_endpoint(self, test_client: AsyncClient):
        """Test liveness probe endpoint"""
        response = await test_client.get("/live")
        assert response.status_code == status.HTTP_200_OK
        
        liveness_data = response.json()
        assert "alive" in liveness_data


# Utility functions for integration tests
def create_test_api_client() -> AsyncClient:
    """Create a test API client with proper configuration"""
    # This would typically create a client with test-specific configuration
    # such as test database URL, mocked services, etc.
    pass


def verify_api_response_structure(response_data: Dict[str, Any], expected_fields: List[str]):
    """Verify that API response contains expected fields"""
    for field in expected_fields:
        assert field in response_data, f"Expected field '{field}' not found in response"


def assert_paginated_response(response_data: Dict[str, Any]):
    """Assert that response follows pagination format"""
    required_fields = ["items", "pagination"]
    verify_api_response_structure(response_data, required_fields)
    
    pagination = response_data["pagination"]
    assert "page" in pagination
    assert "size" in pagination
    assert "total" in pagination
    assert "pages" in pagination


if __name__ == "__main__":
    # Run basic smoke test
    import sys
    sys.path.append("/workspace/ai-news-aggregator/backend")
    
    print("Integration API tests configuration loaded successfully")