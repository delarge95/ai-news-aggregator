"""
Unit tests for NYTimes API client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any


class TestNYTimesClient:
    """Test suite for NYTimes API client"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        # Mock configuration
        self.mock_config = Mock()
        self.mock_config.NYTIMES_API_KEY = "test_nytimes_api_key"
        
        # Mock response data
        self.mock_search_response = {
            "status": "OK",
            "copyright": "Copyright (c) 2023 The New York Times Company. All Rights Reserved.",
            "response": {
                "docs": [
                    {
                        "web_url": "https://www.nytimes.com/2023/12/01/technology/test-article-1.html",
                        "snippet": "Test NYTimes article snippet 1",
                        "lead_paragraph": "Test lead paragraph for NYTimes article 1",
                        "abstract": "Test abstract for NYTimes article 1",
                        "print_page": "1",
                        "source": ["The New York Times"],
                        "multimedia": [
                            {
                                "url": "https://example.com/image1.jpg",
                                "format": "Standard Thumbnail",
                                "height": 150,
                                "width": 150,
                                "type": "image"
                            }
                        ],
                        "headline": {
                            "main": "Test NYTimes Article 1",
                            "kicker": "Technology",
                            "print_headline": "Test NYTimes Print Headline 1",
                            "content_kicker": "Technology Kicker",
                            "seo": "SEO headline",
                            "sub": "Sub headline"
                        },
                        "pub_date": "2023-12-01T10:00:00+0000",
                        "document_type": "article",
                        "news_desk": "Technology",
                        "section_name": "Technology",
                        "subsection_name": "Artificial Intelligence",
                        "byline": {
                            "original": "By John NYTimes",
                            "person": [
                                {
                                    "firstname": "John",
                                    "lastname": "NYTimes",
                                    "rank": 1,
                                    "role": "reported",
                                    "organization": ""
                                }
                            ],
                            "organization": None
                        },
                        "keywords": [
                            {
                                "name": "subject",
                                "value": "Artificial Intelligence",
                                "rank": 1,
                                "major": "N"
                            },
                            {
                                "name": "organizations",
                                "value": "NYTimes",
                                "rank": 2,
                                "major": "N"
                            }
                        ],
                        "web_url": "https://www.nytimes.com/2023/12/01/technology/test-article-1.html",
                        "api_url": "https://api.nytimes.com/svc/search/v2/articlesearch.json"
                    },
                    {
                        "web_url": "https://www.nytimes.com/2023/12/01/politics/test-article-2.html",
                        "snippet": "Test NYTimes article snippet 2",
                        "lead_paragraph": "Test lead paragraph for NYTimes article 2",
                        "abstract": "Test abstract for NYTimes article 2",
                        "source": ["The New York Times"],
                        "headline": {
                            "main": "Test NYTimes Article 2",
                            "kicker": "Politics",
                            "print_headline": "Test NYTimes Print Headline 2"
                        },
                        "pub_date": "2023-12-01T11:00:00+0000",
                        "document_type": "article",
                        "news_desk": "Politics",
                        "section_name": "Politics",
                        "byline": {
                            "original": "By Jane NYTimes",
                            "person": [
                                {
                                    "firstname": "Jane",
                                    "lastname": "NYTimes",
                                    "rank": 1,
                                    "role": "reported"
                                }
                            ]
                        },
                        "web_url": "https://www.nytimes.com/2023/12/01/politics/test-article-2.html"
                    }
                ],
                "meta": {
                    "hits": 20,
                    "offset": 0,
                    "time": 145,
                    "params": {
                        "q": "artificial intelligence"
                    }
                }
            }
        }

        self.mock_article_response = {
            "status": "OK",
            "response": {
                "docs": [
                    {
                        "web_url": "https://www.nytimes.com/2023/12/01/technology/test-article-1.html",
                        "snippet": "Test NYTimes article snippet 1",
                        "lead_paragraph": "Test lead paragraph for NYTimes article 1",
                        "abstract": "Test abstract for NYTimes article 1",
                        "source": ["The New York Times"],
                        "headline": {
                            "main": "Test NYTimes Article 1 Full",
                            "print_headline": "Test NYTimes Print Headline 1"
                        },
                        "pub_date": "2023-12-01T10:00:00+0000",
                        "document_type": "article",
                        "news_desk": "Technology",
                        "section_name": "Technology",
                        "subsection_name": "Artificial Intelligence",
                        "byline": {
                            "original": "By John NYTimes",
                            "person": [
                                {
                                    "firstname": "John",
                                    "lastname": "NYTimes",
                                    "rank": 1,
                                    "role": "reported"
                                }
                            ]
                        },
                        "keywords": [
                            {
                                "name": "subject",
                                "value": "Artificial Intelligence",
                                "rank": 1
                            }
                        ],
                        "multimedia": [
                            {
                                "url": "https://example.com/full-article-image.jpg",
                                "format": "Large",
                                "height": 600,
                                "width": 600,
                                "type": "image"
                            }
                        ]
                    }
                ]
            }
        }

    @pytest.fixture
    def nytimes_client(self):
        """Create NYTimes client instance for testing"""
        from app.services.nytimes_client import NYTimesAPIClient
        return NYTimesAPIClient(api_key=self.mock_config.NYTIMES_API_KEY)

    @pytest.mark.asyncio
    async def test_search_articles_success(self, nytimes_client):
        """Test successful article search"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_search_response
            mock_get.return_value = mock_response
            
            result = await nytimes_client.search_articles(
                query="artificial intelligence",
                begin_date=datetime(2023, 12, 1).strftime("%Y%m%d"),
                end_date=datetime(2023, 12, 1).strftime("%Y%m%d"),
                page=0,
                sort="newest"
            )
            
            assert len(result) == 2
            assert result[0]["title"] == "Test NYTimes Article 1"
            assert result[0]["api_source_id"] is not None
            assert result[0]["api_name"] == "nytimes"
            assert "artificial intelligence" in result[0]["snippet"].lower()

    @pytest.mark.asyncio
    async def test_search_articles_with_filters(self, nytimes_client):
        """Test article search with various filters"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_search_response
            mock_get.return_value = mock_response
            
            result = await nytimes_client.search_articles(
                query="technology",
                news_desk="Technology",
                section_name="Technology",
                begin_date=datetime(2023, 12, 1).strftime("%Y%m%d"),
                end_date=datetime(2023, 12, 1).strftime("%Y%m%d")
            )
            
            # Verify that the request included filters
            call_args = mock_get.call_args
            assert "news_desk" in call_args[1]["params"]
            assert "section_name" in call_args[1]["params"]

    @pytest.mark.asyncio
    async def test_search_articles_api_error(self, nytimes_client):
        """Test API error handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "status": "ERROR",
                "message": "Invalid parameters",
                "response": {}
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await nytimes_client.search_articles(query="")
            
            assert "Invalid parameters" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_search_articles_quota_exceeded(self, nytimes_client):
        """Test quota exceeded handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "status": "ERROR",
                "message": "Rate limit exceeded",
                "response": {}
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await nytimes_client.search_articles(query="test")
            
            assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_article_success(self, nytimes_client):
        """Test successful single article retrieval"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_article_response
            mock_get.return_value = mock_response
            
            article_url = "https://www.nytimes.com/2023/12/01/technology/test-article-1.html"
            result = await nytimes_client.get_article(article_url)
            
            assert "docs" in result
            assert len(result["docs"]) == 1
            assert result["docs"][0]["web_url"] == article_url
            assert result["docs"][0]["headline"]["main"] == "Test NYTimes Article 1 Full"

    @pytest.mark.asyncio
    async def test_get_article_not_found(self, nytimes_client):
        """Test article not found handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "OK",
                "response": {"docs": []}
            }
            mock_get.return_value = mock_response
            
            result = await nytimes_client.get_article("https://invalid-url.com")
            assert len(result["docs"]) == 0

    @pytest.mark.asyncio
    async def test_transform_article(self, nytimes_client):
        """Test article data transformation"""
        raw_doc = self.mock_search_response["response"]["docs"][0]
        transformed = nytimes_client.transform_article(raw_doc)
        
        assert "id" in transformed
        assert "title" in transformed
        assert "content" in transformed
        assert "url" in transformed
        assert "published_at" in transformed
        assert "author" in transformed
        assert "api_source_id" in transformed
        assert "api_name" in transformed
        assert transformed["api_name"] == "nytimes"
        assert transformed["content"] == "Test lead paragraph for NYTimes article 1"
        assert transformed["author"] == "John NYTimes"

    @pytest.mark.asyncio
    async def test_extract_keywords(self, nytimes_client):
        """Test keyword extraction from article"""
        raw_doc = self.mock_search_response["response"]["docs"][0]
        keywords = nytimes_client.extract_keywords(raw_doc)
        
        assert len(keywords) == 2
        keyword_values = [k["value"] for k in keywords]
        assert "Artificial Intelligence" in keyword_values
        assert "NYTimes" in keyword_values

    @pytest.mark.asyncio
    async def test_extract_multimedia(self, nytimes_client):
        """Test multimedia extraction from article"""
        raw_doc = self.mock_search_response["response"]["docs"][0]
        multimedia = nytimes_client.extract_multimedia(raw_doc)
        
        assert len(multimedia) == 1
        assert multimedia[0]["url"] == "https://example.com/image1.jpg"
        assert multimedia[0]["type"] == "image"
        assert multimedia[0]["format"] == "Standard Thumbnail"

    @pytest.mark.asyncio
    async def test_parse_date(self, nytimes_client):
        """Test date parsing from NYTimes format"""
        date_string = "2023-12-01T10:00:00+0000"
        parsed_date = nytimes_client.parse_pub_date(date_string)
        
        assert isinstance(parsed_date, datetime)
        assert parsed_date.year == 2023
        assert parsed_date.month == 12
        assert parsed_date.day == 1
        assert parsed_date.hour == 10
        assert parsed_date.minute == 0

    @pytest.mark.asyncio
    async def test_build_search_url(self, nytimes_client):
        """Test URL building for search requests"""
        params = {
            "q": "artificial intelligence",
            "begin_date": "20231201",
            "end_date": "20231201",
            "api-key": "test_key"
        }
        
        url = nytimes_client.build_search_url(params)
        expected_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        assert expected_url in url
        assert "q=artificial+intelligence" in url
        assert "begin_date=20231201" in url

    @pytest.mark.asyncio
    async def test_build_article_url(self, nytimes_client):
        """Test URL building for single article retrieval"""
        article_url = "https://www.nytimes.com/2023/12/01/technology/test-article-1.html"
        built_url = nytimes_client.build_article_url(
            article_url,
            api_key="test_key"
        )
        
        expected_base = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        assert expected_base in built_url
        assert "fq=web_url" in built_url

    @pytest.mark.asyncio
    async def test_validate_search_response(self, nytimes_client):
        """Test search response validation"""
        # Valid response
        valid_response = self.mock_search_response
        assert nytimes_client.validate_search_response(valid_response) is True
        
        # Invalid response - missing response field
        invalid_response = {"status": "OK"}
        assert nytimes_client.validate_search_response(invalid_response) is False
        
        # Invalid response - error status
        error_response = {
            "status": "ERROR",
            "message": "Invalid API key",
            "response": {}
        }
        assert nytimes_client.validate_search_response(error_response) is False

    @pytest.mark.asyncio
    async def test_paginated_search(self, nytimes_client):
        """Test pagination handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            # Mock multiple pages
            page_responses = []
            for page in [0, 1]:
                page_response = {
                    "status": "OK",
                    "response": {
                        "docs": [
                            {
                                "web_url": f"https://www.nytimes.com/test-{page}-{i}.html",
                                "headline": {"main": f"Test Article {page}-{i}"},
                                "pub_date": "2023-12-01T10:00:00+0000",
                                "snippet": f"Snippet for article {page}-{i}"
                            }
                            for i in range(10)
                        ],
                        "meta": {"hits": 20, "offset": page * 10}
                    }
                }
                page_responses.append(Mock(status_code=200, json=lambda: page_response))
            
            mock_get.side_effect = page_responses
            
            result = await nytimes_client.search_articles(
                query="test",
                page_size=10,
                max_pages=2
            )
            
            assert len(result) == 20
            assert result[0]["title"] == "Test Article 0-0"
            assert result[19]["title"] == "Test Article 1-9"

    @pytest.mark.asyncio
    async def test_extract_byline_info(self, nytimes_client):
        """Test byline information extraction"""
        raw_doc = self.mock_search_response["response"]["docs"][0]
        byline = nytimes_client.extract_byline_info(raw_doc)
        
        assert byline["original"] == "By John NYTimes"
        assert byline["author"] == "John NYTimes"
        assert len(byline["person"]) == 1
        assert byline["person"][0]["firstname"] == "John"
        assert byline["person"][0]["lastname"] == "NYTimes"

    @pytest.mark.asyncio
    async def test_extract_section_info(self, nytimes_client):
        """Test section information extraction"""
        raw_doc = self.mock_search_response["response"]["docs"][0]
        section_info = nytimes_client.extract_section_info(raw_doc)
        
        assert section_info["section_name"] == "Technology"
        assert section_info["subsection_name"] == "Artificial Intelligence"
        assert section_info["news_desk"] == "Technology"

    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, nytimes_client):
        """Test network timeout handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")
            
            with pytest.raises(Exception):
                await nytimes_client.search_articles(query="test")

    @pytest.mark.asyncio
    async def test_handle_api_key_error(self, nytimes_client):
        """Test API key error handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "status": "ERROR",
                "message": "Invalid API key",
                "response": {}
            }
            mock_get.return_value = mock_response
            
            with pytest.raises(Exception) as exc_info:
                await nytimes_client.search_articles(query="test")
            
            assert "Invalid API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, nytimes_client):
        """Test empty query handling"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.mock_search_response
            mock_get.return_value = mock_response
            
            # Empty query should still work (gets all articles)
            result = await nytimes_client.search_articles(query="")
            assert isinstance(result, list)
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_popular_articles(self, nytimes_client):
        """Test popular articles endpoint (if implemented)"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "OK",
                "results": [
                    {
                        "title": "Popular Article 1",
                        "url": "https://nytimes.com/popular-1",
                        "abstract": "Popular article abstract"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            result = await nytimes_client.get_popular_articles(period="1")
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_build_multimedia_url(self, nytimes_client):
        """Test multimedia URL building"""
        multimedia = self.mock_search_response["response"]["docs"][0]["multimedia"][0]
        built_url = nytimes_client.build_multimedia_url(multimedia)
        
        expected_base = "https://example.com/"
        assert expected_base in built_url
        assert multimedia["url"] in built_url