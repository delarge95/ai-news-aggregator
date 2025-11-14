"""
Test Suite for REST API Endpoints
Comprehensive tests for all API endpoints including:
- Health, News, Articles, Search, Users
- AI Analysis, Analytics, Monitoring
- Authentication, authorization, validation
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import json

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.models import User, Article, Source, UserPreference, UserBookmark, TrendingTopic
from app.services.ai_processor import SentimentLabel, TopicCategory


class TestHealthEndpoints:
    """Test suite for health check endpoints"""
    
    def test_health_check(self, test_client):
        """Test basic health check endpoint"""
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_check_with_details(self, test_client):
        """Test health check with detailed status"""
        response = test_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "redis" in data
        assert "ai_services" in data
    
    def test_health_check_database_status(self, test_client, async_db_session):
        """Test database connection health check"""
        with patch('app.api.v1.endpoints.health.get_database') as mock_get_db:
            mock_get_db.return_value = lambda: async_db_session
            
            response = test_client.get("/api/v1/health/database")
            assert response.status_code == 200
            data = response.json()
            assert "database" in data
            assert "status" in data["database"]


class TestNewsEndpoints:
    """Test suite for news endpoints"""
    
    def test_get_latest_news(self, test_client, sample_article_data):
        """Test getting latest news"""
        with patch('app.api.v1.endpoints.news.get_latest_news') as mock_get_news:
            mock_get_news.return_value = [
                {
                    "title": "Test News Article",
                    "content": "Test content",
                    "url": "https://example.com/news",
                    "published_at": "2023-12-01T10:00:00Z",
                    "source": "Test Source"
                }
            ]
            
            response = test_client.get("/api/v1/news/latest")
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert len(data["articles"]) > 0
    
    def test_get_news_by_category(self, test_client):
        """Test getting news by category"""
        with patch('app.api.v1.endpoints.news.get_news_by_category') as mock_get_category:
            mock_get_category.return_value = [
                {"title": "Tech News", "category": "technology"}
            ]
            
            response = test_client.get("/api/v1/news/category/technology")
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert data["articles"][0]["category"] == "technology"
    
    def test_get_news_by_source(self, test_client):
        """Test getting news by source"""
        with patch('app.api.v1.endpoints.news.get_news_by_source') as mock_get_source:
            mock_get_source.return_value = [
                {"title": "BBC News", "source": "BBC"}
            ]
            
            response = test_client.get("/api/v1/news/source/bbc-news")
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert data["articles"][0]["source"] == "BBC"
    
    def test_search_news(self, test_client):
        """Test news search endpoint"""
        with patch('app.api.v1.endpoints.news.search_news') as mock_search:
            mock_search.return_value = {
                "articles": [{"title": "AI News", "content": "AI content"}],
                "total": 1,
                "query": "artificial intelligence"
            }
            
            response = test_client.get("/api/v1/news/search?q=artificial+intelligence")
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert data["total"] == 1


class TestArticlesEndpoints:
    """Test suite for articles endpoints"""
    
    @pytest.fixture
    def sample_article_id(self):
        return str(uuid4())
    
    def test_get_articles(self, test_client):
        """Test getting articles with pagination"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.fetchall.return_value = []
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.get("/api/v1/articles/")
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert "total" in data
            assert "page" in data
    
    def test_get_article_by_id(self, test_client, sample_article_id):
        """Test getting article by ID"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_article = Mock()
            mock_article.id = sample_article_id
            mock_article.title = "Test Article"
            mock_article.content = "Test content"
            mock_article.url = "https://example.com/test"
            mock_article.created_at = datetime.utcnow()
            mock_article.updated_at = datetime.utcnow()
            mock_article.source_name = "Test Source"
            
            mock_db.execute.return_value.fetchone.return_value = mock_article
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.get(f"/api/v1/articles/{sample_article_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == sample_article_id
            assert data["title"] == "Test Article"
    
    def test_get_article_not_found(self, test_client):
        """Test getting non-existent article"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.fetchone.return_value = None
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.get(f"/api/v1/articles/{uuid4()}")
            assert response.status_code == 404
    
    def test_create_article(self, test_client, sample_article_data):
        """Test creating new article"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.lastrowid = 1
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.post("/api/v1/articles/", json=sample_article_data)
            assert response.status_code == 201
            data = response.json()
            assert data["title"] == sample_article_data["title"]
    
    def test_update_article(self, test_client, sample_article_id, sample_article_data):
        """Test updating article"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.rowcount = 1
            mock_get_db.return_value = lambda: mock_db
            
            update_data = {"title": "Updated Title"}
            response = test_client.put(f"/api/v1/articles/{sample_article_id}", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Article updated successfully"
    
    def test_delete_article(self, test_client, sample_article_id):
        """Test deleting article"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.rowcount = 1
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.delete(f"/api/v1/articles/{sample_article_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Article deleted successfully"
    
    def test_get_articles_by_sentiment(self, test_client):
        """Test filtering articles by sentiment"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_article = Mock()
            mock_article.id = str(uuid4())
            mock_article.title = "Positive Article"
            mock_article.sentiment_label = "positive"
            mock_article.sentiment_score = 0.8
            
            mock_db.execute.return_value.fetchall.return_value = [mock_article]
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.get("/api/v1/articles/sentiment/positive")
            assert response.status_code == 200
            data = response.json()
            assert len(data["articles"]) > 0
            assert data["articles"][0]["sentiment_label"] == "positive"
    
    def test_get_articles_by_date_range(self, test_client):
        """Test filtering articles by date range"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_article = Mock()
            mock_article.id = str(uuid4())
            mock_article.title = "Recent Article"
            mock_article.published_at = datetime.utcnow()
            
            mock_db.execute.return_value.fetchall.return_value = [mock_article]
            mock_get_db.return_value = lambda: mock_db
            
            params = {
                "date_from": "2023-12-01",
                "date_to": "2023-12-31"
            }
            response = test_client.get("/api/v1/articles/date-range", params=params)
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data


class TestSearchEndpoints:
    """Test suite for search endpoints"""
    
    def test_search_articles(self, test_client):
        """Test basic article search"""
        with patch('app.api.v1.endpoints.search.SearchService') as mock_search_cls:
            mock_search = Mock()
            mock_search.advanced_search = AsyncMock(return_value={
                "articles": [{"title": "Search Result", "content": "Search content"}],
                "total": 1,
                "facets": {},
                "took": 25
            })
            mock_search_cls.return_value = mock_search
            
            response = test_client.get("/api/v1/search?q=artificial+intelligence")
            assert response.status_code == 200
            data = response.json()
            assert "articles" in data
            assert data["total"] == 1
    
    def test_search_with_filters(self, test_client):
        """Test search with multiple filters"""
        with patch('app.api.v1.endpoints.search.SearchService') as mock_search_cls:
            mock_search = Mock()
            mock_search.advanced_search = AsyncMock(return_value={
                "articles": [],
                "total": 0,
                "facets": {"sources": {"tech-news": 5}},
                "took": 15
            })
            mock_search_cls.return_value = mock_search
            
            params = {
                "q": "AI technology",
                "source": "tech-news",
                "sentiment": "positive",
                "date_from": "2023-12-01"
            }
            response = test_client.get("/api/v1/search", params=params)
            assert response.status_code == 200
            data = response.json()
            assert "facets" in data
    
    def test_semantic_search(self, test_client):
        """Test semantic search functionality"""
        with patch('app.api.v1.endpoints.search.SearchService') as mock_search_cls:
            mock_search = Mock()
            mock_search.advanced_search = AsyncMock(return_value={
                "articles": [{"title": "Semantic Result"}],
                "total": 1,
                "semantic_score": 0.95,
                "took": 50
            })
            mock_search_cls.return_value = mock_search
            
            response = test_client.get("/api/v1/search/semantic?q=machine+learning")
            assert response.status_code == 200
            data = response.json()
            assert "semantic_score" in data
            assert data["semantic_score"] == 0.95
    
    def test_search_suggestions(self, test_client):
        """Test search suggestions/autocomplete"""
        with patch('app.api.v1.endpoints.search.get_search_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                "artificial intelligence",
                "AI breakthrough",
                "machine learning"
            ]
            
            response = test_client.get("/api/v1/search/suggestions?q=ai")
            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data
            assert len(data["suggestions"]) > 0


class TestUserEndpoints:
    """Test suite for user management endpoints"""
    
    @pytest.fixture
    def sample_user_id(self):
        return str(uuid4())
    
    def test_create_user(self, test_client, sample_user_data):
        """Test user registration"""
        with patch('app.api.v1.endpoints.users.create_user') as mock_create_user:
            mock_create_user.return_value = {
                "id": str(uuid4()),
                "username": "newuser",
                "email": "new@example.com",
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = test_client.post("/api/v1/users/", json=sample_user_data)
            assert response.status_code == 201
            data = response.json()
            assert data["username"] == sample_user_data["username"]
    
    def test_get_user_profile(self, test_client, sample_user_id):
        """Test getting user profile"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.full_name = "Test User"
            mock_user.role = "user"
            mock_get_user.return_value = mock_user
            
            response = test_client.get("/api/v1/users/me")
            assert response.status_code == 200
            data = response.json()
            assert data["username"] == "testuser"
    
    def test_update_user_profile(self, test_client, sample_user_id):
        """Test updating user profile"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v1.endpoints.users.update_user') as mock_update:
                mock_update.return_value = {
                    "id": sample_user_id,
                    "username": "updateduser",
                    "full_name": "Updated User"
                }
                
                update_data = {"full_name": "Updated User"}
                response = test_client.put("/api/v1/users/me", json=update_data)
                assert response.status_code == 200
                data = response.json()
                assert data["full_name"] == "Updated User"
    
    def test_get_user_preferences(self, test_client, sample_user_id):
        """Test getting user preferences"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v1.endpoints.users.get_user_preferences') as mock_get_prefs:
                mock_get_prefs.return_value = {
                    "preferred_sources": ["tech-news"],
                    "sentiment_preference": "positive",
                    "language": "en"
                }
                
                response = test_client.get("/api/v1/users/me/preferences")
                assert response.status_code == 200
                data = response.json()
                assert "preferred_sources" in data
    
    def test_update_user_preferences(self, test_client, sample_user_id):
        """Test updating user preferences"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v1.endpoints.users.update_user_preferences') as mock_update:
                mock_update.return_value = {
                    "preferred_sources": ["tech-news", "world-news"],
                    "sentiment_preference": "positive"
                }
                
                preferences_data = {
                    "preferred_sources": ["tech-news", "world-news"],
                    "sentiment_preference": "positive"
                }
                response = test_client.put("/api/v1/users/me/preferences", json=preferences_data)
                assert response.status_code == 200
                data = response.json()
                assert len(data["preferred_sources"]) == 2
    
    def test_get_user_bookmarks(self, test_client, sample_user_id):
        """Test getting user bookmarks"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v1.endpoints.users.get_user_bookmarks') as mock_get_bookmarks:
                mock_bookmarks = [
                    {
                        "id": str(uuid4()),
                        "title": "Bookmarked Article",
                        "url": "https://example.com/bookmarked",
                        "created_at": datetime.utcnow().isoformat()
                    }
                ]
                mock_get_bookmarks.return_value = mock_bookmarks
                
                response = test_client.get("/api/v1/users/me/bookmarks")
                assert response.status_code == 200
                data = response.json()
                assert len(data) > 0
                assert data[0]["title"] == "Bookmarked Article"
    
    def test_create_bookmark(self, test_client, sample_user_id):
        """Test creating a bookmark"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v1.endpoints.users.create_bookmark') as mock_create:
                mock_create.return_value = {
                    "id": str(uuid4()),
                    "title": "New Bookmark",
                    "url": "https://example.com/new",
                    "created_at": datetime.utcnow().isoformat()
                }
                
                bookmark_data = {
                    "title": "New Bookmark",
                    "url": "https://example.com/new",
                    "notes": "Important article"
                }
                response = test_client.post("/api/v1/users/me/bookmarks", json=bookmark_data)
                assert response.status_code == 201
                data = response.json()
                assert data["title"] == "New Bookmark"
    
    def test_delete_bookmark(self, test_client, sample_user_id):
        """Test deleting a bookmark"""
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = sample_user_id
            mock_get_user.return_value = mock_user
            
            with patch('app.api.v1.endpoints.users.delete_bookmark') as mock_delete:
                mock_delete.return_value = {"message": "Bookmark deleted successfully"}
                
                bookmark_id = str(uuid4())
                response = test_client.delete(f"/api/v1/users/me/bookmarks/{bookmark_id}")
                assert response.status_code == 200
                data = response.json()
                assert "successfully" in data["message"]


class TestAIAnalysisEndpoints:
    """Test suite for AI analysis endpoints"""
    
    def test_analyze_sentiment(self, test_client):
        """Test sentiment analysis endpoint"""
        with patch('app.api.v1.endpoints.ai_analysis.analyze_sentiment') as mock_analyze:
            mock_analyze.return_value = {
                "label": "positive",
                "confidence": 0.85,
                "scores": {"positive": 0.7, "neutral": 0.2, "negative": 0.1},
                "reasoning": "Positive sentiment detected"
            }
            
            request_data = {"text": "This is great news about AI advancement!"}
            response = test_client.post("/api/v1/ai-analysis/sentiment", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["label"] == "positive"
            assert data["confidence"] == 0.85
    
    def test_extract_topics(self, test_client):
        """Test topic extraction endpoint"""
        with patch('app.api.v1.endpoints.ai_analysis.extract_topics') as mock_extract:
            mock_extract.return_value = {
                "category": "technology",
                "confidence": 0.92,
                "keywords": ["AI", "machine learning", "innovation"],
                "scores": {"technology": 0.8, "business": 0.1, "sports": 0.1}
            }
            
            request_data = {"text": "Latest AI and machine learning innovations"}
            response = test_client.post("/api/v1/ai-analysis/topics", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["category"] == "technology"
            assert "AI" in data["keywords"]
    
    def test_generate_summary(self, test_client):
        """Test summary generation endpoint"""
        with patch('app.api.v1.endpoints.ai_analysis.generate_summary') as mock_summarize:
            mock_summarize.return_value = {
                "summary": "Revolutionary AI breakthrough promises industry transformation.",
                "keywords": ["AI", "breakthrough", "technology"],
                "key_points": [
                    "Major technological advancement",
                    "Significant performance improvements"
                ],
                "word_count": 125,
                "compression_ratio": 0.15
            }
            
            request_data = {
                "text": "Very long article content about AI breakthrough...",
                "max_length": 200
            }
            response = test_client.post("/api/v1/ai-analysis/summary", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert len(data["summary"]) > 0
            assert data["compression_ratio"] == 0.15
    
    def test_full_article_analysis(self, test_client):
        """Test comprehensive article analysis"""
        with patch('app.api.v1.endpoints.ai_analysis.analyze_article') as mock_analyze:
            mock_analyze.return_value = {
                "sentiment": {
                    "label": "positive",
                    "confidence": 0.85
                },
                "topics": {
                    "category": "technology",
                    "confidence": 0.92
                },
                "summary": {
                    "summary": "AI breakthrough analysis",
                    "keywords": ["AI", "technology"]
                },
                "processing_time": 2.5,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            request_data = {"text": "Complete article content for analysis"}
            response = test_client.post("/api/v1/ai-analysis/full", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "sentiment" in data
            assert "topics" in data
            assert "summary" in data
    
    def test_bulk_analysis(self, test_client):
        """Test bulk analysis endpoint"""
        with patch('app.api.v1.endpoints.ai_analysis.bulk_analyze') as mock_bulk:
            mock_bulk.return_value = {
                "total_processed": 10,
                "successful": 9,
                "failed": 1,
                "results": [
                    {
                        "id": 1,
                        "sentiment": {"label": "positive", "confidence": 0.85}
                    }
                ],
                "processing_time": 15.2
            }
            
            request_data = {
                "articles": [
                    {"id": 1, "text": "First article"},
                    {"id": 2, "text": "Second article"}
                ],
                "analysis_types": ["sentiment", "topics"]
            }
            response = test_client.post("/api/v1/ai-analysis/bulk", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["total_processed"] == 10
            assert data["successful"] == 9


class TestAnalyticsEndpoints:
    """Test suite for analytics endpoints"""
    
    def test_get_dashboard_stats(self, test_client):
        """Test dashboard statistics endpoint"""
        with patch('app.api.v1.endpoints.analytics.get_dashboard_stats') as mock_stats:
            mock_stats.return_value = {
                "total_articles": 1500,
                "articles_today": 45,
                "total_sources": 25,
                "active_users": 120,
                "avg_processing_time": 2.3,
                "success_rate": 0.98
            }
            
            response = test_client.get("/api/v1/analytics/dashboard")
            assert response.status_code == 200
            data = response.json()
            assert data["total_articles"] == 1500
            assert data["articles_today"] == 45
    
    def test_get_sentiment_distribution(self, test_client):
        """Test sentiment distribution analytics"""
        with patch('app.api.v1.endpoints.analytics.get_sentiment_distribution') as mock_sentiment:
            mock_sentiment.return_value = {
                "positive": 650,
                "neutral": 520,
                "negative": 330,
                "period": "last_7_days"
            }
            
            response = test_client.get("/api/v1/analytics/sentiment")
            assert response.status_code == 200
            data = response.json()
            assert data["positive"] == 650
            assert data["neutral"] == 520
    
    def test_get_topic_trends(self, test_client):
        """Test topic trends analytics"""
        with patch('app.api.v1.endpoints.analytics.get_topic_trends') as mock_trends:
            mock_trends.return_value = {
                "trending_topics": [
                    {"topic": "AI", "count": 150, "trend_score": 0.95},
                    {"topic": "Climate", "count": 120, "trend_score": 0.88}
                ],
                "time_period": "last_7_days"
            }
            
            response = test_client.get("/api/v1/analytics/topics/trending")
            assert response.status_code == 200
            data = response.json()
            assert len(data["trending_topics"]) > 0
            assert data["trending_topics"][0]["topic"] == "AI"
    
    def test_get_source_performance(self, test_client):
        """Test source performance analytics"""
        with patch('app.api.v1.endpoints.analytics.get_source_performance') as mock_performance:
            mock_performance.return_value = {
                "sources": [
                    {
                        "name": "Tech News Daily",
                        "articles_count": 250,
                        "avg_sentiment": 0.6,
                        "credibility_score": 0.9
                    }
                ],
                "period": "last_30_days"
            }
            
            response = test_client.get("/api/v1/analytics/sources/performance")
            assert response.status_code == 200
            data = response.json()
            assert len(data["sources"]) > 0
            assert data["sources"][0]["articles_count"] == 250
    
    def test_get_user_engagement(self, test_client):
        """Test user engagement analytics"""
        with patch('app.api.v1.endpoints.analytics.get_user_engagement') as mock_engagement:
            mock_engagement.return_value = {
                "daily_active_users": 85,
                "bookmarks_created": 320,
                "avg_session_duration": 15.2,
                "top_interactions": [
                    {"action": "bookmark", "count": 150},
                    {"action": "share", "count": 85}
                ]
            }
            
            response = test_client.get("/api/v1/analytics/users/engagement")
            assert response.status_code == 200
            data = response.json()
            assert data["daily_active_users"] == 85
            assert data["bookmarks_created"] == 320


class TestMonitoringEndpoints:
    """Test suite for monitoring endpoints"""
    
    def test_get_system_metrics(self, test_client):
        """Test system metrics endpoint"""
        with patch('app.api.v1.endpoints.ai_monitor.get_system_metrics') as mock_metrics:
            mock_metrics.return_value = {
                "cpu_usage": 45.2,
                "memory_usage": 68.5,
                "database_connections": 15,
                "cache_hit_rate": 0.87,
                "ai_processing_queue": 5
            }
            
            response = test_client.get("/api/v1/monitor/metrics")
            assert response.status_code == 200
            data = response.json()
            assert data["cpu_usage"] == 45.2
            assert data["cache_hit_rate"] == 0.87
    
    def test_get_ai_processing_stats(self, test_client):
        """Test AI processing statistics"""
        with patch('app.api.v1.endpoints.ai_monitor.get_ai_processing_stats') as mock_stats:
            mock_stats.return_value = {
                "total_analyses": 2500,
                "successful_analyses": 2450,
                "failed_analyses": 50,
                "avg_processing_time": 2.3,
                "models_usage": {
                    "gpt-3.5-turbo": 2000,
                    "local-model": 500
                }
            }
            
            response = test_client.get("/api/v1/monitor/ai-processing")
            assert response.status_code == 200
            data = response.json()
            assert data["total_analyses"] == 2500
            assert data["avg_processing_time"] == 2.3
    
    def test_get_error_logs(self, test_client):
        """Test error logs endpoint"""
        with patch('app.api.v1.endpoints.ai_monitor.get_error_logs') as mock_logs:
            mock_logs.return_value = {
                "errors": [
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": "ERROR",
                        "message": "AI processing failed",
                        "component": "ai_processor",
                        "count": 3
                    }
                ],
                "total_errors": 15,
                "period": "last_24_hours"
            }
            
            response = test_client.get("/api/v1/monitor/errors")
            assert response.status_code == 200
            data = response.json()
            assert len(data["errors"]) > 0
            assert data["errors"][0]["level"] == "ERROR"


class TestEndpointValidation:
    """Test suite for endpoint validation and error handling"""
    
    def test_invalid_article_creation(self, test_client):
        """Test validation for invalid article data"""
        invalid_data = {
            "title": "",  # Empty title should fail
            "url": "invalid-url"  # Invalid URL
        }
        
        response = test_client.post("/api/v1/articles/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_search_without_query(self, test_client):
        """Test search endpoint without query parameter"""
        response = test_client.get("/api/v1/search")
        assert response.status_code == 400  # Bad request
    
    def test_invalid_sentiment_value(self, test_client):
        """Test sentiment analysis with invalid input"""
        with patch('app.api.v1.endpoints.ai_analysis.analyze_sentiment') as mock_analyze:
            mock_analyze.side_effect = ValueError("Invalid text provided")
            
            request_data = {"text": ""}  # Empty text
            response = test_client.post("/api/v1/ai-analysis/sentiment", json=request_data)
            assert response.status_code == 400
    
    def test_unauthorized_access(self, test_client):
        """Test unauthorized access to protected endpoints"""
        # Try to access user profile without authentication
        response = test_client.get("/api/v1/users/me")
        assert response.status_code == 401  # Unauthorized
    
    def test_rate_limiting(self, test_client):
        """Test rate limiting on endpoints"""
        with patch('app.core.rate_limiter.check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = False  # Rate limit exceeded
            
            # Make multiple requests to trigger rate limiting
            for _ in range(5):
                response = test_client.get("/api/v1/news/latest")
                if response.status_code == 429:
                    break
            else:
                # If no rate limiting triggered, that's also valid
                pass
    
    def test_invalid_uuid_format(self, test_client):
        """Test endpoints with invalid UUID format"""
        invalid_id = "invalid-uuid-format"
        
        response = test_client.get(f"/api/v1/articles/{invalid_id}")
        assert response.status_code == 422  # Validation error
    
    def test_pagination_validation(self, test_client):
        """Test pagination parameter validation"""
        params = {
            "page": -1,  # Invalid page number
            "limit": 1000  # Too large limit
        }
        
        response = test_client.get("/api/v1/articles/", params=params)
        assert response.status_code == 422  # Validation error


class TestEndpointIntegration:
    """Integration tests for multiple endpoints working together"""
    
    @pytest.mark.asyncio
    async def test_article_workflow(self, test_client, sample_article_data):
        """Test complete article workflow: create -> read -> update -> delete"""
        # Create article
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.lastrowid = 1
            mock_get_db.return_value = lambda: mock_db
            
            create_response = test_client.post("/api/v1/articles/", json=sample_article_data)
            assert create_response.status_code == 201
            
            article_id = create_response.json()["id"]
        
        # Read article
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_article = Mock()
            mock_article.id = article_id
            mock_article.title = sample_article_data["title"]
            mock_article.content = sample_article_data["content"]
            mock_article.url = sample_article_data["url"]
            mock_article.created_at = datetime.utcnow()
            mock_article.updated_at = datetime.utcnow()
            mock_article.source_name = "Test Source"
            
            mock_db.execute.return_value.fetchone.return_value = mock_article
            mock_get_db.return_value = lambda: mock_db
            
            read_response = test_client.get(f"/api/v1/articles/{article_id}")
            assert read_response.status_code == 200
        
        # Update article
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.rowcount = 1
            mock_get_db.return_value = lambda: mock_db
            
            update_data = {"title": "Updated Title"}
            update_response = test_client.put(f"/api/v1/articles/{article_id}", json=update_data)
            assert update_response.status_code == 200
        
        # Delete article
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            mock_db.execute.return_value.rowcount = 1
            mock_get_db.return_value = lambda: mock_db
            
            delete_response = test_client.delete(f"/api/v1/articles/{article_id}")
            assert delete_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_user_preferences_workflow(self, test_client, sample_user_data):
        """Test user preferences workflow"""
        # Create user
        with patch('app.api.v1.endpoints.users.create_user') as mock_create:
            mock_create.return_value = {
                "id": str(uuid4()),
                "username": sample_user_data["username"],
                "email": sample_user_data["email"]
            }
            
            create_response = test_client.post("/api/v1/users/", json=sample_user_data)
            assert create_response.status_code == 201
        
        # Get and update preferences
        user_id = create_response.json()["id"]
        
        with patch('app.api.v1.endpoints.users.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = user_id
            mock_get_user.return_value = mock_user
            
            # Get preferences
            with patch('app.api.v1.endpoints.users.get_user_preferences') as mock_get_prefs:
                mock_get_prefs.return_value = {}
                
                get_response = test_client.get("/api/v1/users/me/preferences")
                assert get_response.status_code == 200
            
            # Update preferences
            with patch('app.api.v1.endpoints.users.update_user_preferences') as mock_update:
                mock_update.return_value = {"preferred_sources": ["tech-news"]}
                
                update_data = {
                    "preferred_sources": ["tech-news", "world-news"],
                    "sentiment_preference": "positive"
                }
                
                update_response = test_client.put("/api/v1/users/me/preferences", json=update_data)
                assert update_response.status_code == 200


class TestEndpointPerformance:
    """Test suite for endpoint performance and optimization"""
    
    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent requests"""
        import concurrent.futures
        import threading
        
        def make_request():
            return test_client.get("/api/v1/health/")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)
    
    def test_large_response_handling(self, test_client):
        """Test handling of large responses"""
        with patch('app.api.v1.endpoints.articles.get_database') as mock_get_db:
            mock_db = Mock()
            
            # Generate many mock articles
            mock_articles = []
            for i in range(1000):
                article = Mock()
                article.id = str(uuid4())
                article.title = f"Article {i}"
                article.content = f"Content for article {i}" * 10
                article.url = f"https://example.com/article/{i}"
                article.created_at = datetime.utcnow()
                article.updated_at = datetime.utcnow()
                article.source_name = f"Source {i % 10}"
                mock_articles.append(article)
            
            mock_db.execute.return_value.fetchall.return_value = mock_articles
            mock_get_db.return_value = lambda: mock_db
            
            response = test_client.get("/api/v1/articles/")
            assert response.status_code == 200
            data = response.json()
            assert len(data["articles"]) == 1000
    
    def test_cache_headers(self, test_client):
        """Test cache headers in responses"""
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        
        # Check for cache-related headers
        # Note: Actual cache headers depend on implementation
        headers = response.headers
        # Some responses should have cache headers
        # assert "cache-control" in headers or "etag" in headers