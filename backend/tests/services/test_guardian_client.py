"""
Unit tests for Guardian API client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any


class TestGuardianClient:
    """Test suite for Guardian API client"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.GUARDIAN_API_KEY = "test_guardian_api_key"
        
        # Mock response data
        self.mock_search_response = {
            "response": {
                "status": "ok",
                "total": 20,
                "startIndex": 1,
                "pageSize": 10,
                "currentPage": 1,
                "pages": 2,
                "orderBy": "newest",
                "results": [
                    {
                        "id": "technology/2023/dec/01/test-article-1",
                        "type": "article",
                        "sectionId": "technology",
                        "sectionName": "Technology",
                        "webPublicationDate": "2023-12-01T10:00:00Z",
                        "webTitle": "Test Guardian Article 1",
                        "webUrl": "https://theguardian.com/technology/2023/dec/01/test-article-1",
                        "apiUrl": "https://content.guardianapis.com/technology/2023/dec/01/test-article-1",
                        "fields": {
                            "headline": "Test Guardian Article 1 Headline",
                            "standfirst": "Test Guardian standfirst",
                            "trailText": "Test trail text",
                            "byline": "John Guardian",
                            "body": "Test Guardian body content",
                            "thumbnail": "https://example.com/guardian-thumbnail-1.jpg",
                            "wordcount": "1500",
                            "commentable": "true",
                            "shortUrl": "https://gu.com/p/test1"
                        },
                        "tags": [
                            {
                                "id": "technology/artificial-intelligence",
                                "type": "keyword",
                                "title": "Artificial Intelligence",
                                "webTitle": "Artificial Intelligence",
                                "webUrl": "https://theguardian.com/technology/artificial-intelligence",
                                "apiUrl": "https://content.guardianapis.com/technology/artificial-intelligence",
                                "sectionId": "technology",
                                "sectionName": "Technology"
                            }
                        ]
                    },
                    {
                        "id": "politics/2023/dec/01/test-article-2",
                        "type": "article",
                        "sectionId": "politics",
                        "sectionName": "Politics",
                        "webPublicationDate": "2023-12-01T11:00:00Z",
                        "webTitle": "Test Guardian Article 2",
                        "webUrl": "https://theguardian.com/politics/2023/dec/01/test-article-2",
                        "apiUrl": "https://content.guardianapis.com/politics/2023/dec/01/test-article-2",
                        "fields": {
                            "headline": "Test Guardian Article 2 Headline",
                            "standfirst": "Test politics standfirst",
                            "trailText": "Politics trail text",
                            "byline": "Jane Guardian",
                            "body": "Test politics body content",
                            "thumbnail": "https://example.com/guardian-thumbnail-2.jpg"
                        }
                    }
                ]
            }
        }

        self.mock_content_response = {
            "response": {
                "status": "ok",
                "content": {
                    "id": "technology/2023/dec/01/test-article-1",
                    "type": "article",
                    "sectionId": "technology",
                    "sectionName": "Technology",
                    "webPublicationDate": "2023-12-01T10:00:00Z",
                    "webTitle": "Test Guardian Article 1 Full Content",
                    "webUrl": "https://theguardian.com/technology/2023/dec/01/test-article-1",
                    "apiUrl": "https://content.guardianapis.com/technology/2023/dec/01/test-article-1",
                    "fields": {
                        "headline": "Test Guardian Article 1 Headline",
                        "standfirst": "Test Guardian standfirst",
                        "trailText": "Test trail text",
                        "byline": "John Guardian",
                        "body": "Full Guardian body content with rich text formatting",
                        "thumbnail": "https://example.com/guardian-thumbnail-full.jpg",
                        "wordcount": "2000"
                    }
                }
            }
        }

    @pytest.fixture
    def guardian_client(self):
        """Create Guardian client instance for testing"""
        from app.services.guardian_client import GuardianAPIClient
        return GuardianAPIClient(api_key=self.mock_config.GUARDIAN_API_KEY)

    @pytest.mark.asyncio
    async def test_search_articles_success(self, guardian_client):
        """Test successful article search"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_search_response
            mock_get.return_value = mock_response
            
            result = await guardian_client.search_articles(
                query="artificial intelligence",
                section="technology",
                from_date=datetime(2023, 12, 1),
                to_date=datetime(2023, 12, 1),
                page_size=10
            )
            
            assert len(result) == 2
            assert result[0]["title"] == "Test Guardian Article 1"
            assert result[0]["api_source_id"] == "technology/2023/dec/01/test-article-1"
            assert result[0]["api_name"] == "guardian"

    @pytest.mark.asyncio
    async def test_search_articles_with_fields(self, guardian_client):
        """Test article search with specific fields"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_search_response
            mock_get.return_value = mock_response
            
            result = await guardian_client.search_articles(
                query="technology",
                fields=["headline", "standfirst", "body", "byline"]
            )
            
            # Verify that the request included requested fields
            call_args = mock_get.call_args
            assert "fields" in call_args[1]["params"]
            fields_param = call_args[1]["params"]["fields"]
            assert "headline" in fields_param
            assert "standfirst" in fields_param
            assert "body" in fields_param

    @pytest.mark.asyncio
    async def test_search_articles_api_error(self, guardian_client):
        """Test API error handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "response": {
                    "status": "error",
                    "message": "Invalid parameters",
                    "statusCode": 400
                }
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await guardian_client.search_articles(query="")
            
            assert "Invalid parameters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_articles_rate_limit(self, guardian_client):
        """Test rate limit handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "response": {
                    "status": "error",
                    "message": "Rate limit exceeded",
                    "statusCode": 429
                }
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await guardian_client.search_articles(query="test")
            
            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_article_content_success(self, guardian_client):
        """Test successful full article content retrieval"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_content_response
            mock_get.return_value = mock_response
            
            article_id = "technology/2023/dec/01/test-article-1"
            result = await guardian_client.get_article_content(
                article_id,
                fields=["body", "headline", "byline"]
            )
            
            assert "content" in result
            assert result["content"]["id"] == article_id
            assert result["content"]["webTitle"] == "Test Guardian Article 1 Full Content"
            assert "body" in result["content"]["fields"]

    @pytest.mark.asyncio
    async def test_get_article_content_not_found(self, guardian_client):
        """Test article not found error"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {
                "response": {
                    "status": "error",
                    "message": "Content not found",
                    "statusCode": 404
                }
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await guardian_client.get_article_content("invalid/article/id")
            
            assert "Content not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transform_search_result(self, guardian_client):
        """Test transformation of search result to standard format"""
        raw_result = self.mock_search_response["response"]["results"][0]
        transformed = guardian_client.transform_article(raw_result)
        
        assert "id" in transformed
        assert "title" in transformed
        assert "content" in transformed
        assert "url" in transformed
        assert "published_at" in transformed
        assert "author" in transformed
        assert "api_source_id" in transformed
        assert "api_name" in transformed
        assert transformed["api_name"] == "guardian"
        assert transformed["api_source_id"] == "technology/2023/dec/01/test-article-1"

    @pytest.mark.asyncio
    async def test_transform_content_response(self, guardian_client):
        """Test transformation of content response"""
        content_data = self.mock_content_response["response"]["content"]
        transformed = guardian_client.transform_content_response(content_data)
        
        assert "id" in transformed
        assert "content" in transformed
        assert "fields" in transformed
        assert transformed["fields"]["headline"] == "Test Guardian Article 1 Headline"
        assert transformed["fields"]["body"] == "Full Guardian body content with rich text formatting"

    def test_build_search_url(self, guardian_client):
        """Test URL building for search requests"""
        params = {
            "q": "artificial intelligence",
            "section": "technology",
            "from-date": "2023-12-01",
            "to-date": "2023-12-01",
            "page-size": "10",
            "order-by": "newest",
            "api-key": "test_key"
        }
        
        url = guardian_client.build_search_url(params)
        expected_url = "https://content.guardianapis.com/search"
        assert expected_url in url
        assert "q=artificial+intelligence" in url
        assert "section=technology" in url

    @pytest.mark.asyncio
    async def test_get_tag_info(self, guardian_client):
        """Test tag information extraction"""
        raw_result = self.mock_search_response["response"]["results"][0]
        tags = guardian_client.extract_tags(raw_result)
        
        assert len(tags) == 1
        assert tags[0]["id"] == "technology/artificial-intelligence"
        assert tags[0]["type"] == "keyword"
        assert tags[0]["title"] == "Artificial Intelligence"
        assert tags[0]["sectionId"] == "technology"

    @pytest.mark.asyncio
    async def test_parse_publication_date(self, guardian_client):
        """Test publication date parsing"""
        date_string = "2023-12-01T10:00:00Z"
        parsed_date = guardian_client.parse_publication_date(date_string)
        
        assert isinstance(parsed_date, datetime)
        assert parsed_date.year == 2023
        assert parsed_date.month == 12
        assert parsed_date.day == 1
        assert parsed_date.hour == 10

    @pytest.mark.asyncio
    async def test_extract_section_info(self, guardian_client):
        """Test section information extraction"""
        raw_result = self.mock_search_response["response"]["results"][0]
        section_info = guardian_client.extract_section_info(raw_result)
        
        assert section_info["section_id"] == "technology"
        assert section_info["section_name"] == "Technology"

    @pytest.mark.asyncio
    async def test_build_content_url(self, guardian_client):
        """Test content URL building"""
        article_id = "technology/2023/dec/01/test-article-1"
        url = guardian_client.build_content_url(
            article_id,
            fields=["body", "headline"],
            api_key="test_key"
        )
        
        expected_url = f"https://content.guardianapis.com/{article_id}"
        assert expected_url in url
        assert "fields=body%2Cheadline" in url
        assert "api-key=test_key" in url

    @pytest.mark.asyncio
    async def test_validate_search_response(self, guardian_client):
        """Test search response validation"""
        # Valid response
        valid_response = self.mock_search_response
        assert guardian_client.validate_search_response(valid_response) is True
        
        # Invalid response - missing response field
        invalid_response = {"status": "ok"}
        assert guardian_client.validate_search_response(invalid_response) is False
        
        # Invalid response - error status
        error_response = {
            "response": {
                "status": "error",
                "message": "Invalid API key"
            }
        }
        assert guardian_client.validate_search_response(error_response) is False

    @pytest.mark.asyncio
    async def test_paginated_search(self, guardian_client):
        """Test pagination handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock multiple pages
            page_responses = []
            for page in [1, 2]:
                page_response = {
                    "response": {
                        "status": "ok",
                        "total": 40,
                        "currentPage": page,
                        "pages": 4,
                        "results": [
                            {
                                "id": f"test/article/{page}-{i}",
                                "webTitle": f"Test Article {page}-{i}",
                                "webUrl": f"https://theguardian.com/test/{page}-{i}",
                                "webPublicationDate": "2023-12-01T10:00:00Z"
                            }
                            for i in range(10)
                        ]
                    }
                }
                page_responses.append(Mock(status_code=200, json=lambda: page_response))
            
            mock_get.side_effect = page_responses
            
            result = await guardian_client.search_articles(
                query="test",
                page_size=10,
                max_pages=2
            )
            
            assert len(result) == 20
            assert result[0]["title"] == "Test Article 1-0"
            assert result[19]["title"] == "Test Article 2-9"

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, guardian_client):
        """Test network timeout handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(Exception):
                await guardian_client.search_articles(query="test")

    @pytest.mark.asyncio
    async def test_handle_quota_exceeded(self, guardian_client):
        """Test quota exceeded handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "response": {
                    "status": "error",
                    "message": "Your quota has been exceeded",
                    "statusCode": 429
                }
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await guardian_client.search_articles(query="test")
            
            assert "quota" in str(exc_info.value).lower()