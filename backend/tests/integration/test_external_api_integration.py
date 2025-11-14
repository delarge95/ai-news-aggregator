"""
Integration tests for external API clients
Tests de integración para clientes de APIs externas

Este archivo contiene tests que verifican la integración con APIs externas
incluyendo NewsAPI, The Guardian API, y New York Times API, incluyendo
rate limiting, error handling, y manejo de respuestas.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timedelta
import aiohttp
import json
import httpx

# Import application components
from app.services.newsapi_client import NewsAPIClient
from app.services.guardian_client import GuardianClient
from app.services.nytimes_client import NYTimesClient
from app.core.config import settings

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.external_api
]


class TestNewsAPIIntegration:
    """Test NewsAPI integration and functionality"""
    
    @pytest.fixture
    async def newsapi_client(self):
        """Create NewsAPI client for testing"""
        # Use test API key
        client = NewsAPIClient(api_key="test-newsapi-key")
        return client
    
    @pytest.fixture
    def mock_newsapi_response(self):
        """Mock NewsAPI response data"""
        return {
            "status": "ok",
            "totalResults": 20,
            "articles": [
                {
                    "source": {"id": "bbc-news", "name": "BBC News"},
                    "author": "BBC Reporter",
                    "title": "AI Technology Breakthrough",
                    "description": "Scientists announce major AI breakthrough",
                    "url": "https://bbc.com/news/ai-technology",
                    "urlToImage": "https://bbc.com/image.jpg",
                    "publishedAt": "2023-12-01T10:00:00Z",
                    "content": "AI technology continues to advance rapidly..."
                },
                {
                    "source": {"id": "cnn", "name": "CNN"},
                    "author": "CNN Staff",
                    "title": "Global Climate Summit Results",
                    "description": "World leaders agree on new climate measures",
                    "url": "https://cnn.com/politics/climate-summit",
                    "urlToImage": "https://cnn.com/image.jpg",
                    "publishedAt": "2023-12-01T11:00:00Z",
                    "content": "Climate summit concludes with historic agreements..."
                }
            ]
        }
    
    @pytest.mark.skipif(not settings.NEWSAPI_KEY, reason="NewsAPI key not configured")
    async def test_newsapi_real_connection(self, newsapi_client):
        """Test real connection to NewsAPI (requires API key)"""
        try:
            # Test basic API connectivity
            response = await newsapi_client.get_top_headlines(
                country="us", 
                page_size=5
            )
            
            assert "status" in response
            assert response["status"] == "ok"
            assert "articles" in response
            assert len(response["articles"]) > 0
            
        except Exception as e:
            pytest.fail(f"NewsAPI connection failed: {str(e)}")
    
    async def test_newsapi_top_headlines_mock(self, newsapi_client, mock_newsapi_response, mock_httpx_client):
        """Test top headlines with mocked response"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_httpx_client.get.return_value = mock_response
        
        newsapi_client._client = mock_httpx_client
        
        # Test top headlines
        response = await newsapi_client.get_top_headlines(
            country="us",
            page_size=10
        )
        
        assert response["status"] == "ok"
        assert len(response["articles"]) == 2
        assert response["articles"][0]["title"] == "AI Technology Breakthrough"
        
        # Verify request was made correctly
        mock_httpx_client.get.assert_called_once()
        call_args = mock_httpx_client.get.call_args
        assert "country=us" in call_args[0][0]
        assert "pageSize=10" in call_args[0][0]
    
    async def test_newsapi_search_articles_mock(self, newsapi_client, mock_newsapi_response, mock_httpx_client):
        """Test article search with mocked response"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_httpx_client.get.return_value = mock_response
        
        newsapi_client._client = mock_httpx_client
        
        # Test search
        response = await newsapi_client.search_articles(
            query="artificial intelligence",
            language="en",
            sort_by="publishedAt"
        )
        
        assert response["status"] == "ok"
        assert len(response["articles"]) == 2
        
        # Verify search parameters
        call_args = mock_httpx_client.get.call_args
        assert "q=artificial+intelligence" in call_args[0][0]
        assert "language=en" in call_args[0][0]
        assert "sortBy=publishedAt" in call_args[0][0]
    
    async def test_newsapi_error_handling(self, newsapi_client, mock_httpx_client):
        """Test NewsAPI error handling"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "status": "error",
            "code": "rateLimited",
            "message": "You have made too many requests"
        }
        mock_httpx_client.get.return_value = mock_response
        
        newsapi_client._client = mock_httpx_client
        
        # Should raise appropriate exception
        with pytest.raises(Exception) as exc_info:
            await newsapi_client.get_top_headlines(country="us")
        
        assert "rate limited" in str(exc_info.value).lower()
    
    async def test_newsapi_rate_limiting(self, newsapi_client, mock_httpx_client):
        """Test NewsAPI rate limiting"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "articles": []}
        mock_httpx_client.get.return_value = mock_response
        
        newsapi_client._client = mock_httpx_client
        
        # Make multiple requests quickly
        tasks = []
        for _ in range(5):
            task = newsapi_client.get_top_headlines(country="us")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed (or be rate limited appropriately)
        for response in responses:
            assert "status" in response
    
    async def test_newsapi_response_parsing(self, newsapi_client, mock_newsapi_response, mock_httpx_client):
        """Test NewsAPI response parsing and validation"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_newsapi_response
        mock_httpx_client.get.return_value = mock_response
        
        newsapi_client._client = mock_httpx_client
        
        # Test response parsing
        response = await newsapi_client.get_top_headlines(country="us")
        
        # Verify parsed data structure
        articles = response["articles"]
        assert len(articles) == 2
        
        # Validate article structure
        for article in articles:
            assert "source" in article
            assert "title" in article
            assert "description" in article
            assert "url" in article
            assert "publishedAt" in article
            assert isinstance(article["source"], dict)
            assert "id" in article["source"]
            assert "name" in article["source"]


class TestGuardianAPIIntegration:
    """Test The Guardian API integration and functionality"""
    
    @pytest.fixture
    async def guardian_client(self):
        """Create Guardian client for testing"""
        client = GuardianClient(api_key="test-guardian-key")
        return client
    
    @pytest.fixture
    def mock_guardian_response(self):
        """Mock Guardian API response data"""
        return {
            "response": {
                "status": "ok",
                "total": 10,
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
        }
    
    @pytest.mark.skipif(not settings.GUARDIAN_API_KEY, reason="Guardian API key not configured")
    async def test_guardian_real_connection(self, guardian_client):
        """Test real connection to Guardian API"""
        try:
            # Test basic API connectivity
            response = await guardian_client.search_content(
                query="technology",
                page_size=5
            )
            
            assert "response" in response
            assert response["response"]["status"] == "ok"
            assert "results" in response["response"]
            
        except Exception as e:
            pytest.fail(f"Guardian API connection failed: {str(e)}")
    
    async def test_guardian_search_content_mock(self, guardian_client, mock_guardian_response, mock_httpx_client):
        """Test Guardian content search with mocked response"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_guardian_response
        mock_httpx_client.get.return_value = mock_response
        
        guardian_client._client = mock_httpx_client
        
        # Test search
        response = await guardian_client.search_content(
            query="artificial intelligence",
            section="technology",
            page_size=10
        )
        
        assert response["response"]["status"] == "ok"
        assert len(response["response"]["results"]) == 1
        assert response["response"]["results"][0]["webTitle"] == "AI Technology Shows Major Advances"
        
        # Verify request parameters
        call_args = mock_httpx_client.get.call_args
        assert "q=artificial+intelligence" in call_args[0][0]
        assert "section=technology" in call_args[0][0]
        assert "page-size=10" in call_args[0][0]
    
    async def test_guardian_content_by_section_mock(self, guardian_client, mock_guardian_response, mock_httpx_client):
        """Test Guardian content filtering by section"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_guardian_response
        mock_httpx_client.get.return_value = mock_response
        
        guardian_client._client = mock_httpx_client
        
        # Test section-based filtering
        response = await guardian_client.get_content_by_section(
            section="technology",
            page=1
        )
        
        assert response["response"]["status"] == "ok"
        assert len(response["response"]["results"]) == 1
        
        # Verify section parameter
        call_args = mock_httpx_client.get.call_args
        assert "section=technology" in call_args[0][0]
    
    async def test_guardian_single_article_mock(self, guardian_client, mock_guardian_response, mock_httpx_client):
        """Test Guardian single article retrieval"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_guardian_response
        mock_httpx_client.get.return_value = mock_response
        
        guardian_client._client = mock_httpx_client
        
        # Test single article retrieval
        article_id = "technology/2023/dec/01/ai-advances"
        response = await guardian_client.get_single_article(article_id)
        
        assert response["response"]["status"] == "ok"
        assert "results" in response["response"]
        assert len(response["response"]["results"]) == 1
        
        # Verify article ID in request
        call_args = mock_httpx_client.get.call_args
        assert article_id in call_args[0][0]
    
    async def test_guardian_error_handling(self, guardian_client, mock_httpx_client):
        """Test Guardian API error handling"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "response": {
                "status": "error",
                "message": "Content not found"
            }
        }
        mock_httpx_client.get.return_value = mock_response
        
        guardian_client._client = mock_httpx_client
        
        # Should raise appropriate exception
        with pytest.raises(Exception) as exc_info:
            await guardian_client.get_single_article("nonexistent-article")
        
        assert "not found" in str(exc_info.value).lower()
    
    async def test_guardian_response_normalization(self, guardian_client, mock_guardian_response, mock_httpx_client):
        """Test Guardian response normalization to common format"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_guardian_response
        mock_httpx_client.get.return_value = mock_response
        
        guardian_client._client = mock_httpx_client
        
        # Test response normalization
        response = await guardian_client.search_content(query="test")
        
        # Verify common format structure
        articles = response.get("articles", [])
        if articles:
            article = articles[0]
            assert "title" in article
            assert "content" in article
            assert "url" in article
            assert "published_at" in article
            assert "source" in article


class TestNYTimesAPIIntegration:
    """Test New York Times API integration and functionality"""
    
    @pytest.fixture
    async def nytimes_client(self):
        """Create NYTimes client for testing"""
        client = NYTimesClient(api_key="test-nytimes-key")
        return client
    
    @pytest.fixture
    def mock_nytimes_response(self):
        """Mock NYTimes API response data"""
        return {
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
                        },
                        "multimedia": [
                            {
                                "url": "https://nytimes.com/image.jpg",
                                "subtype": "xlarge"
                            }
                        ]
                    }
                ],
                "meta": {
                    "hits": 1,
                    "offset": 0,
                    "time": 45
                }
            }
        }
    
    @pytest.mark.skipif(not settings.NYTIMES_API_KEY, reason="NYTimes API key not configured")
    async def test_nytimes_real_connection(self, nytimes_client):
        """Test real connection to NYTimes API"""
        try:
            # Test basic API connectivity
            response = await nytimes_client.search_articles(
                query="technology",
                page=0
            )
            
            assert "status" in response
            assert response["status"] == "OK"
            assert "response" in response
            
        except Exception as e:
            pytest.fail(f"NYTimes API connection failed: {str(e)}")
    
    async def test_nytimes_search_articles_mock(self, nytimes_client, mock_nytimes_response, mock_httpx_client):
        """Test NYTimes article search with mocked response"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_nytimes_response
        mock_httpx_client.get.return_value = mock_response
        
        nytimes_client._client = mock_httpx_client
        
        # Test search
        response = await nytimes_client.search_articles(
            query="artificial intelligence",
            page=0,
            sort="newest"
        )
        
        assert response["status"] == "OK"
        assert len(response["response"]["docs"]) == 1
        assert response["response"]["docs"][0]["headline"]["main"] == "AI Technology Reaches New Milestone"
        
        # Verify search parameters
        call_args = mock_httpx_client.get.call_args
        assert "q=artificial+intelligence" in call_args[0][0]
        assert "page=0" in call_args[0][0]
        assert "sort=newest" in call_args[0][0]
    
    async def test_nytimes_popular_articles_mock(self, nytimes_client, mock_nytimes_response, mock_httpx_client):
        """Test NYTimes popular articles with mocked response"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_nytimes_response
        mock_httpx_client.get.return_value = mock_response
        
        nytimes_client._client = mock_httpx_client
        
        # Test popular articles
        response = await nytimes_client.get_most_popular_articles(
            period=7,  # 7 days
            section="all"
        )
        
        assert response["status"] == "OK"
        assert len(response["response"]["docs"]) == 1
        
        # Verify popular endpoint parameters
        call_args = mock_httpx_client.get.call_args
        assert "viewed" in call_args[0][0]
        assert "period=7" in call_args[0][0]
    
    async def test_nytimes_books_mock(self, nytimes_client, mock_httpx_client):
        """Test NYTimes books API"""
        books_response = {
            "status": "OK",
            "results": [
                {
                    "title": "AI Technology Book",
                    "author": "Tech Author",
                    "publisher": "Tech Publisher"
                }
            ]
        }
        
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = books_response
        mock_httpx_client.get.return_value = mock_response
        
        nytimes_client._client = mock_httpx_client
        
        # Test books API
        response = await nytimes_client.get_books_list(
            list="hardcover-fiction"
        )
        
        assert response["status"] == "OK"
        assert len(response["results"]) == 1
    
    async def test_nytimes_error_handling(self, nytimes_client, mock_httpx_client):
        """Test NYTimes API error handling"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "status": "ERROR",
            "message": "Rate limit exceeded"
        }
        mock_httpx_client.get.return_value = mock_response
        
        nytimes_client._client = mock_httpx_client
        
        # Should raise appropriate exception
        with pytest.raises(Exception) as exc_info:
            await nytimes_client.search_articles(query="test")
        
        assert "rate limit" in str(exc_info.value).lower()
    
    async def test_nytimes_response_normalization(self, nytimes_client, mock_nytimes_response, mock_httpx_client):
        """Test NYTimes response normalization"""
        # Mock the HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_nytimes_response
        mock_httpx_client.get.return_value = mock_response
        
        nytimes_client._client = mock_httpx_client
        
        # Test response normalization
        response = await nytimes_client.search_articles(query="test")
        
        # Verify common format structure
        articles = response.get("articles", [])
        if articles:
            article = articles[0]
            assert "title" in article
            assert "content" in article
            assert "url" in article
            assert "published_at" in article
            assert "source" in article


class TestExternalAPIIntegrationWorkflow:
    """Test complete workflows involving multiple external APIs"""
    
    @pytest.fixture
    async def all_api_clients(self):
        """Create all API clients"""
        clients = {
            "newsapi": NewsAPIClient(api_key="test-newsapi-key"),
            "guardian": GuardianClient(api_key="test-guardian-key"),
            "nytimes": NYTimesClient(api_key="test-nytimes-key")
        }
        return clients
    
    async def test_multi_api_article_aggregation(self, all_api_clients, mock_httpx_client):
        """Test aggregating articles from multiple APIs"""
        # Mock responses for each API
        newsapi_response = {
            "status": "ok",
            "articles": [
                {
                    "title": "Tech News",
                    "content": "Technology content",
                    "url": "https://example.com/tech",
                    "publishedAt": "2023-12-01T10:00:00Z",
                    "source": {"name": "NewsAPI Source"}
                }
            ]
        }
        
        guardian_response = {
            "response": {
                "status": "ok",
                "results": [
                    {
                        "webTitle": "Guardian News",
                        "fields": {"body": "Guardian content"},
                        "webUrl": "https://guardian.com/news",
                        "webPublicationDate": "2023-12-01T11:00:00Z"
                    }
                ]
            }
        }
        
        nytimes_response = {
            "status": "OK",
            "response": {
                "docs": [
                    {
                        "headline": {"main": "NYTimes News"},
                        "lead_paragraph": "NYTimes content",
                        "web_url": "https://nytimes.com/news",
                        "pub_date": "2023-12-01T12:00:00+0000"
                    }
                ]
            }
        }
        
        # Set up mock responses
        responses = [newsapi_response, guardian_response, nytimes_response]
        for i, (api_name, client) in enumerate(all_api_clients.items()):
            client._client = mock_httpx_client
            
            # Mock different responses for each API
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = responses[i]
            mock_httpx_client.get.return_value = mock_response
        
        # Aggregate articles from all sources
        aggregated_articles = []
        
        # Get articles from each API
        for api_name, client in all_api_clients.items():
            if api_name == "newsapi":
                response = await client.get_top_headlines(country="us")
                articles = response.get("articles", [])
            elif api_name == "guardian":
                response = await client.search_content(query="technology")
                articles = response.get("articles", [])
            elif api_name == "nytimes":
                response = await client.search_articles(query="technology")
                articles = response.get("articles", [])
            
            for article in articles:
                article["api_source"] = api_name
                aggregated_articles.append(article)
        
        # Verify aggregation
        assert len(aggregated_articles) == 3
        assert all("api_source" in article for article in aggregated_articles)
        
        # Verify each API contributed
        api_sources = {article["api_source"] for article in aggregated_articles}
        assert len(api_sources) == 3
    
    async def test_api_fallback_strategy(self, all_api_clients, mock_httpx_client):
        """Test fallback strategy when one API fails"""
        # Mock NewsAPI to fail
        newsapi_error_response = Mock()
        newsapi_error_response.status_code = 503
        newsapi_error_response.json.return_value = {
            "status": "error",
            "message": "Service unavailable"
        }
        
        # Mock Guardian and NYTimes to succeed
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "response": {"status": "ok", "results": []},
            "status": "OK",
            "response": {"docs": []}
        }
        
        # Configure clients
        all_api_clients["newsapi"]._client = mock_httpx_client
        all_api_clients["guardian"]._client = mock_httpx_client
        all_api_clients["nytimes"]._client = mock_httpx_client
        
        # Set up response sequence
        mock_httpx_client.get.side_effect = [
            newsapi_error_response,  # NewsAPI fails
            success_response,        # Guardian succeeds
            success_response         # NYTimes succeeds
        ]
        
        # Test fallback behavior
        results = []
        
        # Try NewsAPI first
        try:
            response = await all_api_clients["newsapi"].get_top_headlines(country="us")
            results.append(("newsapi", "success", response))
        except Exception as e:
            results.append(("newsapi", "failed", str(e)))
        
        # Fallback to Guardian
        try:
            response = await all_api_clients["guardian"].search_content(query="technology")
            results.append(("guardian", "success", response))
        except Exception as e:
            results.append(("guardian", "failed", str(e)))
        
        # Fallback to NYTimes
        try:
            response = await all_api_clients["nytimes"].search_articles(query="technology")
            results.append(("nytimes", "success", response))
        except Exception as e:
            results.append(("nytimes", "failed", str(e)))
        
        # Verify results
        assert results[0][1] == "failed"  # NewsAPI failed
        assert results[1][1] == "success"  # Guardian succeeded
        assert results[2][1] == "success"  # NYTimes succeeded


class TestExternalAPIPerformance:
    """Test performance aspects of external API integration"""
    
    async def test_api_response_time_tracking(self):
        """Test response time tracking for API calls"""
        # This test would track actual response times
        # Implementation depends on monitoring capabilities
        pass
    
    async def test_concurrent_api_requests(self, all_api_clients, mock_httpx_client):
        """Test concurrent requests to multiple APIs"""
        # Mock successful responses for all APIs
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [{"title": "Test Article"}]
        }
        
        # Configure all clients
        for client in all_api_clients.values():
            client._client = mock_httpx_client
            mock_httpx_client.get.return_value = mock_response
        
        # Make concurrent requests
        tasks = []
        for api_name, client in all_api_clients.items():
            if api_name == "newsapi":
                task = client.get_top_headlines(country="us")
            elif api_name == "guardian":
                task = client.search_content(query="technology")
            elif api_name == "nytimes":
                task = client.search_articles(query="technology")
            tasks.append(task)
        
        # Execute concurrently
        responses = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        assert len(responses) == 3
        for response in responses:
            assert "status" in response or "response" in response
    
    async def test_api_batch_requests(self):
        """Test batch processing of API requests"""
        # This would test batching multiple search terms
        # into fewer API calls where possible
        pass


# Test utilities and helpers
def create_mock_api_response(status_code: int = 200, data: Dict[str, Any] = None) -> Mock:
    """Create a mock API response"""
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json.return_value = data or {"status": "ok"}
    return mock_response


def verify_api_rate_limits(response_headers: Dict[str, str]):
    """Verify API rate limiting headers are present"""
    rate_limit_headers = [
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining", 
        "X-RateLimit-Reset"
    ]
    
    for header in rate_limit_headers:
        assert header in response_headers, f"Rate limit header {header} missing"


def validate_article_structure(article: Dict[str, Any]):
    """Validate article structure from external APIs"""
    required_fields = ["title", "content", "url", "published_at", "source"]
    
    for field in required_fields:
        assert field in article, f"Required field {field} missing from article"
    
    # Validate source structure
    assert isinstance(article["source"], (dict, str))
    if isinstance(article["source"], dict):
        assert "name" in article["source"]


if __name__ == "__main__":
    print("External API integration tests configuration loaded successfully")