"""
Unit tests for NewsAPI client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any


class TestNewsAPIClient:
    """Test suite for NewsAPI client"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.NEWSAPI_KEY = "test_newsapi_key"
        
        # Mock response data
        self.mock_articles_response = {
            "status": "ok",
            "totalResults": 20,
            "articles": [
                {
                    "source": {"id": "bbc-news", "name": "BBC News"},
                    "author": "John Doe",
                    "title": "Test Article 1",
                    "description": "Test description 1",
                    "url": "https://example.com/article1",
                    "urlToImage": "https://example.com/image1.jpg",
                    "publishedAt": "2023-12-01T10:00:00Z",
                    "content": "Test content 1"
                },
                {
                    "source": {"id": "cnn", "name": "CNN"},
                    "author": "Jane Smith",
                    "title": "Test Article 2",
                    "description": "Test description 2", 
                    "url": "https://example.com/article2",
                    "urlToImage": "https://example.com/image2.jpg",
                    "publishedAt": "2023-12-01T11:00:00Z",
                    "content": "Test content 2"
                }
            ]
        }
        
        self.mock_sources_response = {
            "status": "ok",
            "sources": [
                {
                    "id": "bbc-news",
                    "name": "BBC News",
                    "description": "BBC News source",
                    "url": "https://bbc.com/news",
                    "category": "general",
                    "language": "en",
                    "country": "gb"
                },
                {
                    "id": "cnn",
                    "name": "CNN",
                    "description": "CNN source",
                    "url": "https://cnn.com",
                    "category": "general",
                    "language": "en",
                    "country": "us"
                }
            ]
        }

    @pytest.fixture
    def newsapi_client(self):
        """Create NewsAPI client instance for testing"""
        # This would be the actual client class
        # Mock implementation for testing
        from app.services.newsapi_client import NewsAPIClient
        return NewsAPIClient(api_key=self.mock_config.NEWSAPI_KEY)

    @pytest.mark.asyncio
    async def test_fetch_articles_success(self, newsapi_client):
        """Test successful article fetching"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_articles_response
            mock_get.return_value = mock_response
            
            result = await newsapi_client.fetch_articles(
                query="technology",
                from_date=datetime(2023, 12, 1),
                to_date=datetime(2023, 12, 1),
                page_size=20
            )
            
            assert len(result) == 2
            assert result[0]["title"] == "Test Article 1"
            assert result[1]["title"] == "Test Article 2"
            assert all("source" in article for article in result)

    @pytest.mark.asyncio
    async def test_fetch_articles_api_error(self, newsapi_client):
        """Test API error handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "status": "error",
                "code": "parametersMissing",
                "message": "The 'q' parameter is required."
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await newsapi_client.fetch_articles(query="")
            
            assert "parametersMissing" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_articles_rate_limit(self, newsapi_client):
        """Test rate limit handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "status": "error",
                "code": "rateLimited",
                "message": "API calls quota exceeded."
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await newsapi_client.fetch_articles(query="test")
            
            assert "rateLimited" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fetch_articles_network_error(self, newsapi_client):
        """Test network error handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Connection timeout")
            
            with pytest.raises(Exception):
                await newsapi_client.fetch_articles(query="test")

    @pytest.mark.asyncio
    async def test_fetch_sources_success(self, newsapi_client):
        """Test successful sources fetching"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_sources_response
            mock_get.return_value = mock_response
            
            result = await newsapi_client.fetch_sources(category="general", country="us")
            
            assert len(result) == 2
            assert result[0]["id"] == "bbc-news"
            assert result[1]["id"] == "cnn"

    @pytest.mark.asyncio
    async def test_transform_article_data(self, newsapi_client):
        """Test article data transformation"""
        raw_article = self.mock_articles_response["articles"][0]
        transformed = newsapi_client.transform_article(raw_article)
        
        assert "id" in transformed
        assert "title" in transformed
        assert "content" in transformed
        assert "url" in transformed
        assert "published_at" in transformed
        assert "source" in transformed
        assert "api_source_id" in transformed
        assert "api_name" in transformed

    @pytest.mark.asyncio
    async def test_transform_article_missing_fields(self, newsapi_client):
        """Test article transformation with missing fields"""
        incomplete_article = {
            "title": "Incomplete Article",
            "url": "https://example.com/incomplete",
            # Missing other fields
        }
        
        transformed = newsapi_client.transform_article(incomplete_article)
        
        assert transformed["title"] == "Incomplete Article"
        assert transformed["url"] == "https://example.com/incomplete"
        assert transformed["content"] is None or transformed["content"] == ""
        assert transformed["author"] is None or transformed["author"] == ""

    def test_generate_content_hash(self, newsapi_client):
        """Test content hash generation for deduplication"""
        content = "This is a test article content"
        title = "Test Article Title"
        
        hash_result = newsapi_client.generate_content_hash(title, content)
        
        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 hex digest length
        assert hash_result == newsapi_client.generate_content_hash(title, content)  # Same input = same hash

    def test_validate_response(self, newsapi_client):
        """Test response validation"""
        # Valid response
        valid_response = self.mock_articles_response
        assert newsapi_client.validate_response(valid_response) is True
        
        # Invalid response - missing status
        invalid_response = {"articles": []}
        assert newsapi_client.validate_response(invalid_response) is False
        
        # Invalid response - error status
        error_response = {
            "status": "error",
            "code": "apiKeyInvalid",
            "message": "API key provided is invalid"
        }
        assert newsapi_client.validate_response(error_response) is False

    @pytest.mark.asyncio
    async def test_paginated_fetch(self, newsapi_client):
        """Test pagination handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock paginated responses
            page1_response = {
                "status": "ok",
                "totalResults": 50,
                "articles": [{"title": f"Article {i}", "url": f"https://example.com/{i}"} 
                           for i in range(1, 21)]
            }
            page2_response = {
                "status": "ok", 
                "totalResults": 50,
                "articles": [{"title": f"Article {i}", "url": f"https://example.com/{i}"} 
                           for i in range(21, 41)]
            }
            
            mock_get.side_effect = [
                Mock(status_code=200, json=lambda: page1_response),
                Mock(status_code=200, json=lambda: page2_response)
            ]
            
            result = await newsapi_client.fetch_articles(
                query="test", 
                page_size=20, 
                max_pages=2
            )
            
            assert len(result) == 40
            assert result[0]["title"] == "Article 1"
            assert result[19]["title"] == "Article 20"
            assert result[20]["title"] == "Article 21"
            assert result[39]["title"] == "Article 40"

    @pytest.mark.asyncio
    async def test_get_top_headlines(self, newsapi_client):
        """Test top headlines endpoint"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_articles_response
            mock_get.return_value = mock_response
            
            result = await newsapi_client.get_top_headlines(
                country="us",
                category="technology",
                page_size=20
            )
            
            assert len(result) == 2
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "top-headlines" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_everything(self, newsapi_client):
        """Test search everything endpoint"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_articles_response
            mock_get.return_value = mock_response
            
            result = await newsapi_client.search_everything(
                query="artificial intelligence",
                from_date=datetime(2023, 12, 1),
                to_date=datetime(2023, 12, 1),
                language="en",
                sort_by="publishedAt"
            )
            
            assert len(result) == 2
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "everything" in call_args[0][0]