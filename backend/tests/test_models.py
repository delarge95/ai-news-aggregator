"""
Test Suite for SQLAlchemy Models
Comprehensive tests for all database models including:
- Article, Source, User, UserPreference, UserBookmark
- TrendingTopic, ArticleAnalysis, AnalysisTask
- Relationships, constraints, and validation
"""

import pytest
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    Base, Article, Source, User, UserPreference, UserBookmark,
    TrendingTopic, ArticleAnalysis, AnalysisTask, 
    ProcessingStatus, AnalysisTaskStatus
)


class TestSourceModel:
    """Test suite for Source model"""
    
    def test_source_creation(self, source_factory):
        """Test Source model creation"""
        source = source_factory(
            name="Test Source",
            url="https://example.com",
            api_name="newsapi",
            country="US",
            language="en"
        )
        
        assert source.name == "Test Source"
        assert source.url == "https://example.com"
        assert source.api_name == "newsapi"
        assert source.country == "US"
        assert source.language == "en"
        assert source.credibility_score == 0.0
        assert source.is_active is True
        assert source.rate_limit_per_hour == 100
        assert source.created_at is not None
        assert source.updated_at is not None
    
    def test_source_unique_constraint(self, test_db_session, source_factory):
        """Test Source unique constraints"""
        source1 = source_factory(name="Unique Source", api_name="newsapi")
        source2 = source_factory(name="Unique Source", api_name="guardian")
        
        # First source should be created successfully
        test_db_session.add(source1)
        test_db_session.commit()
        
        # Second source with same name should fail due to unique constraint
        test_db_session.add(source2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_source_relationships(self, article_factory, source_factory, test_db_session):
        """Test Source relationships with Article"""
        source = source_factory(name="Test Source")
        article = article_factory(title="Test Article", source_id=source.id)
        
        test_db_session.add(source)
        test_db_session.add(article)
        test_db_session.commit()
        
        # Test relationship
        assert source.articles == [article]
        assert article.source == source
    
    def test_source_rate_limit_tracking(self, source_factory):
        """Test Source rate limit information tracking"""
        source = source_factory(
            rate_limit_per_hour=50,
            rate_limit_info={
                "remaining_calls": 45,
                "reset_time": "2023-12-01T11:00:00Z",
                "total_calls_made": 5
            }
        )
        
        assert source.rate_limit_per_hour == 50
        assert source.rate_limit_info["remaining_calls"] == 45
        assert source.rate_limit_info["total_calls_made"] == 5


class TestArticleModel:
    """Test suite for Article model"""
    
    def test_article_creation(self, article_factory):
        """Test Article model creation"""
        article = article_factory(
            title="Test Article",
            content="Test content",
            url="https://example.com/test",
            sentiment_score=0.8,
            sentiment_label="positive",
            bias_score=0.3,
            topic_tags=["technology", "AI"],
            relevance_score=0.9
        )
        
        assert article.title == "Test Article"
        assert article.content == "Test content"
        assert article.url == "https://example.com/test"
        assert article.sentiment_score == 0.8
        assert article.sentiment_label == "positive"
        assert article.bias_score == 0.3
        assert article.topic_tags == ["technology", "AI"]
        assert article.relevance_score == 0.9
        assert article.processing_status == ProcessingStatus.PENDING
        assert article.created_at is not None
        assert article.updated_at is not None
    
    def test_article_unique_url_constraint(self, article_factory, test_db_session):
        """Test Article unique URL constraint"""
        article1 = article_factory(url="https://example.com/unique")
        article2 = article_factory(url="https://example.com/unique")
        
        # First article should be created
        test_db_session.add(article1)
        test_db_session.commit()
        
        # Second article with same URL should fail
        test_db_session.add(article2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_article_duplicate_detection(self, article_factory, test_db_session):
        """Test Article duplicate detection fields"""
        article1 = article_factory(
            title="Original Article",
            content_hash="abc123",
            duplicate_group_id=uuid4()
        )
        article2 = article_factory(
            title="Duplicate Article",
            content_hash="abc123",
            duplicate_group_id=article1.duplicate_group_id
        )
        
        test_db_session.add_all([article1, article2])
        test_db_session.commit()
        
        assert article1.content_hash == article2.content_hash
        assert article1.duplicate_group_id == article2.duplicate_group_id
    
    def test_article_processing_status_enum(self, article_factory):
        """Test Article processing status enum values"""
        statuses = [
            ProcessingStatus.PENDING,
            ProcessingStatus.PROCESSING,
            ProcessingStatus.COMPLETED,
            ProcessingStatus.FAILED,
            ProcessingStatus.SKIPPED
        ]
        
        for status in statuses:
            article = article_factory(processing_status=status)
            assert article.processing_status == status
    
    def test_article_sentiment_validation(self, article_factory):
        """Test Article sentiment score validation"""
        # Valid sentiment scores
        article1 = article_factory(sentiment_score=-1.0)
        article2 = article_factory(sentiment_score=0.0)
        article3 = article_factory(sentiment_score=1.0)
        
        assert article1.sentiment_score == -1.0
        assert article2.sentiment_score == 0.0
        assert article3.sentiment_score == 1.0
    
    def test_article_bias_validation(self, article_factory):
        """Test Article bias score validation"""
        # Valid bias scores
        article1 = article_factory(bias_score=0.0)
        article2 = article_factory(bias_score=0.5)
        article3 = article_factory(bias_score=1.0)
        
        assert article1.bias_score == 0.0
        assert article2.bias_score == 0.5
        assert article3.bias_score == 1.0
    
    def test_article_relationships(self, article_factory, source_factory, test_db_session):
        """Test Article relationships"""
        source = source_factory(name="Test Source")
        article = article_factory(title="Test Article", source_id=source.id)
        
        test_db_session.add(source)
        test_db_session.add(article)
        test_db_session.commit()
        
        assert article.source == source
        assert source.articles == [article]


class TestUserModel:
    """Test suite for User model"""
    
    def test_user_creation(self, user_factory):
        """Test User model creation"""
        user = user_factory(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            role="user"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "user"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.hashed_password == "hashed_password"
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_user_unique_constraints(self, user_factory, test_db_session):
        """Test User unique constraints"""
        user1 = user_factory(username="unique_user", email="unique@example.com")
        user2 = user_factory(username="unique_user", email="different@example.com")
        user3 = user_factory(username="different_user", email="unique@example.com")
        
        # First user should be created
        test_db_session.add(user1)
        test_db_session.commit()
        
        # User with same username should fail
        test_db_session.add(user2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
        
        # User with same email should fail
        test_db_session.rollback()
        test_db_session.add(user3)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_user_roles(self, user_factory):
        """Test User role validation"""
        roles = ["user", "admin", "moderator"]
        
        for role in roles:
            user = user_factory(role=role)
            assert user.role == role
    
    def test_user_admin_status(self, user_factory):
        """Test User admin status"""
        regular_user = user_factory(role="user", is_superuser=False)
        admin_user = user_factory(role="admin", is_superuser=True)
        
        assert regular_user.is_superuser is False
        assert admin_user.is_superuser is True


class TestUserPreferenceModel:
    """Test suite for UserPreference model"""
    
    def test_user_preference_creation(self, user_factory, test_db_session):
        """Test UserPreference model creation"""
        user = user_factory()
        preference = UserPreference(
            user_id=user.id,
            preferred_sources=["source1", "source2"],
            blocked_sources=["blocked_source"],
            preferred_topics=["technology", "AI"],
            ignored_topics=["politics"],
            sentiment_preference="positive",
            reading_level="mixed",
            notification_frequency="daily",
            language="en",
            timezone="UTC"
        )
        
        test_db_session.add(user)
        test_db_session.add(preference)
        test_db_session.commit()
        
        assert preference.user_id == user.id
        assert preference.preferred_sources == ["source1", "source2"]
        assert preference.blocked_sources == ["blocked_source"]
        assert preference.preferred_topics == ["technology", "AI"]
        assert preference.sentiment_preference == "positive"
        assert preference.language == "en"
        assert preference.timezone == "UTC"
    
    def test_user_preference_user_relationship(self, user_factory, test_db_session):
        """Test UserPreference user relationship"""
        user = user_factory()
        preference = UserPreference(user_id=user.id)
        
        test_db_session.add(user)
        test_db_session.add(preference)
        test_db_session.commit()
        
        assert preference.user == user
        assert user.preferences == preference
    
    def test_user_preference_unique_constraint(self, user_factory, test_db_session):
        """Test UserPreference unique constraint with user"""
        user = user_factory()
        pref1 = UserPreference(user_id=user.id)
        pref2 = UserPreference(user_id=user.id)
        
        # First preference should be created
        test_db_session.add(user)
        test_db_session.add(pref1)
        test_db_session.commit()
        
        # Second preference for same user should fail
        test_db_session.add(pref2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestUserBookmarkModel:
    """Test suite for UserBookmark model"""
    
    def test_user_bookmark_creation(self, user_factory, article_factory, test_db_session):
        """Test UserBookmark model creation"""
        user = user_factory()
        article = article_factory()
        
        bookmark = UserBookmark(
            user_id=user.id,
            article_id=article.id,
            title="Bookmarked Article",
            url="https://example.com/bookmarked",
            notes="Important article to read",
            tags=["important", "technology"]
        )
        
        test_db_session.add_all([user, article, bookmark])
        test_db_session.commit()
        
        assert bookmark.user_id == user.id
        assert bookmark.article_id == article.id
        assert bookmark.title == "Bookmarked Article"
        assert bookmark.notes == "Important article to read"
        assert bookmark.tags == ["important", "technology"]
        assert bookmark.created_at is not None
    
    def test_user_bookmark_relationships(self, user_factory, article_factory, test_db_session):
        """Test UserBookmark relationships"""
        user = user_factory()
        article = article_factory()
        bookmark = UserBookmark(
            user_id=user.id,
            article_id=article.id,
            title="Bookmarked",
            url="https://example.com/bookmarked"
        )
        
        test_db_session.add_all([user, article, bookmark])
        test_db_session.commit()
        
        assert bookmark.user == user
        assert bookmark.article == article
        assert bookmark in user.bookmarks
    
    def test_user_bookmark_unique_constraint(self, user_factory, article_factory, test_db_session):
        """Test UserBookmark unique constraint"""
        user = user_factory()
        article = article_factory()
        bookmark1 = UserBookmark(
            user_id=user.id,
            article_id=article.id,
            title="First Bookmark",
            url="https://example.com/first"
        )
        bookmark2 = UserBookmark(
            user_id=user.id,
            article_id=article.id,
            title="Second Bookmark",
            url="https://example.com/second"
        )
        
        # First bookmark should be created
        test_db_session.add_all([user, article, bookmark1])
        test_db_session.commit()
        
        # Second bookmark for same user/article should fail
        test_db_session.add(bookmark2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()


class TestTrendingTopicModel:
    """Test suite for TrendingTopic model"""
    
    def test_trending_topic_creation(self, trending_topic_factory):
        """Test TrendingTopic model creation"""
        topic = trending_topic_factory(
            topic="Artificial Intelligence",
            topic_category="technology",
            trend_score=0.85,
            article_count=150,
            sources_count=25,
            time_period="24h"
        )
        
        assert topic.topic == "Artificial Intelligence"
        assert topic.topic_category == "technology"
        assert topic.trend_score == 0.85
        assert topic.article_count == 150
        assert topic.sources_count == 25
        assert topic.time_period == "24h"
        assert topic.date_recorded is not None
        assert topic.trend_metadata is None
    
    def test_trending_topic_metadata(self, trending_topic_factory):
        """Test TrendingTopic metadata storage"""
        topic = trending_topic_factory(
            trend_metadata={
                "growth_rate": 0.15,
                "peak_hour": "14:00",
                "peak_day": "Monday",
                "related_terms": ["AI", "machine learning", "neural networks"]
            }
        )
        
        assert topic.trend_metadata["growth_rate"] == 0.15
        assert topic.trend_metadata["peak_hour"] == "14:00"
        assert "AI" in topic.trend_metadata["related_terms"]
    
    def test_trending_topic_time_periods(self, trending_topic_factory):
        """Test different time periods for trending topics"""
        periods = ["1h", "6h", "24h", "7d"]
        
        for period in periods:
            topic = trending_topic_factory(time_period=period)
            assert topic.time_period == period


class TestArticleAnalysisModel:
    """Test suite for ArticleAnalysis model"""
    
    def test_article_analysis_creation(self, article_factory, test_db_session):
        """Test ArticleAnalysis model creation"""
        article = article_factory()
        
        analysis = ArticleAnalysis(
            article_id=article.id,
            analysis_type="sentiment",
            analysis_data={
                "label": "positive",
                "confidence": 0.85,
                "scores": {"positive": 0.7, "neutral": 0.2, "negative": 0.1}
            },
            model_used="gpt-3.5-turbo",
            confidence_score=0.85
        )
        
        test_db_session.add_all([article, analysis])
        test_db_session.commit()
        
        assert analysis.article_id == article.id
        assert analysis.analysis_type == "sentiment"
        assert analysis.model_used == "gpt-3.5-turbo"
        assert analysis.confidence_score == 0.85
        assert analysis.processed_at is not None
    
    def test_article_analysis_types(self, article_factory, test_db_session):
        """Test different analysis types"""
        article = article_factory()
        analysis_types = ["sentiment", "summary", "bias", "topics"]
        
        test_db_session.add(article)
        test_db_session.commit()
        
        for analysis_type in analysis_types:
            analysis = ArticleAnalysis(
                article_id=article.id,
                analysis_type=analysis_type,
                analysis_data={"type": analysis_type}
            )
            test_db_session.add(analysis)
            test_db_session.commit()
            
            assert analysis.analysis_type == analysis_type
            test_db_session.rollback()
    
    def test_article_analysis_unique_constraint(self, article_factory, test_db_session):
        """Test ArticleAnalysis unique constraint"""
        article = article_factory()
        analysis1 = ArticleAnalysis(
            article_id=article.id,
            analysis_type="sentiment",
            analysis_data={"type": "sentiment"}
        )
        analysis2 = ArticleAnalysis(
            article_id=article.id,
            analysis_type="sentiment",
            analysis_data={"type": "sentiment"}
        )
        
        # First analysis should be created
        test_db_session.add_all([article, analysis1])
        test_db_session.commit()
        
        # Second analysis with same article/type should fail
        test_db_session.add(analysis2)
        with pytest.raises(IntegrityError):
            test_db_session.commit()
    
    def test_article_analysis_relationships(self, article_factory, test_db_session):
        """Test ArticleAnalysis relationships"""
        article = article_factory()
        analysis = ArticleAnalysis(
            article_id=article.id,
            analysis_type="sentiment",
            analysis_data={"label": "positive"}
        )
        
        test_db_session.add_all([article, analysis])
        test_db_session.commit()
        
        assert analysis.article == article
        assert analysis in article.analysis_results


class TestAnalysisTaskModel:
    """Test suite for AnalysisTask model"""
    
    def test_analysis_task_creation(self, analysis_task_factory, article_factory, test_db_session):
        """Test AnalysisTask model creation"""
        article = article_factory()
        
        task = analysis_task_factory(
            task_type="sentiment",
            task_name="Sentiment Analysis Task",
            article_id=article.id,
            status=AnalysisTaskStatus.PENDING,
            priority=3,
            max_retries=3,
            model_name="gpt-3.5-turbo",
            input_data={"text": "Test content for analysis"},
            scheduled_at=datetime.utcnow()
        )
        
        test_db_session.add_all([article, task])
        test_db_session.commit()
        
        assert task.task_type == "sentiment"
        assert task.task_name == "Sentiment Analysis Task"
        assert task.article_id == article.id
        assert task.status == AnalysisTaskStatus.PENDING
        assert task.priority == 3
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.model_name == "gpt-3.5-turbo"
        assert task.input_data["text"] == "Test content for analysis"
    
    def test_analysis_task_status_enum(self, analysis_task_factory):
        """Test AnalysisTask status enum values"""
        statuses = [
            AnalysisTaskStatus.PENDING,
            AnalysisTaskStatus.RUNNING,
            AnalysisTaskStatus.COMPLETED,
            AnalysisTaskStatus.FAILED,
            AnalysisTaskStatus.CANCELLED
        ]
        
        for status in statuses:
            task = analysis_task_factory(status=status)
            assert task.status == status
    
    def test_analysis_task_task_types(self, analysis_task_factory):
        """Test different analysis task types"""
        task_types = ["sentiment", "summary", "topics", "relevance", "bias"]
        
        for task_type in task_types:
            task = analysis_task_factory(task_type=task_type)
            assert task.task_type == task_type
    
    def test_analysis_task_error_handling(self, analysis_task_factory):
        """Test AnalysisTask error handling fields"""
        task = analysis_task_factory(
            error_message="API rate limit exceeded",
            error_code="RATE_LIMIT_EXCEEDED",
            stack_trace="Traceback (most recent call last)...",
            retry_count=2
        )
        
        assert task.error_message == "API rate limit exceeded"
        assert task.error_code == "RATE_LIMIT_EXCEEDED"
        assert task.stack_trace is not None
        assert task.retry_count == 2
    
    def test_analysis_task_worker_tracking(self, analysis_task_factory):
        """Test AnalysisTask worker tracking"""
        task = analysis_task_factory(
            worker_id="worker-001",
            task_metadata={
                "cpu_usage": 0.45,
                "memory_usage": "128MB",
                "processing_time": 2.5
            }
        )
        
        assert task.worker_id == "worker-001"
        assert task.task_metadata["cpu_usage"] == 0.45
        assert task.task_metadata["processing_time"] == 2.5
    
    def test_analysis_task_timing(self, analysis_task_factory):
        """Test AnalysisTask timing fields"""
        task = analysis_task_factory(
            scheduled_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            processing_duration_ms=2500
        )
        
        assert task.scheduled_at is not None
        assert task.started_at is not None
        assert task.completed_at is not None
        assert task.processing_duration_ms == 2500


class TestDatabaseIndexes:
    """Test suite for database indexes"""
    
    def test_source_indexes(self, test_db_engine):
        """Test Source model indexes"""
        inspector = inspect(test_db_engine)
        indexes = inspector.get_indexes('sources')
        index_names = [idx['name'] for idx in indexes]
        
        assert 'idx_sources_api_name' in index_names
        assert 'idx_sources_api_source_id' in index_names
        assert 'idx_sources_is_active' in index_names
    
    def test_article_indexes(self, test_db_engine):
        """Test Article model indexes"""
        inspector = inspect(test_db_engine)
        indexes = inspector.get_indexes('articles')
        index_names = [idx['name'] for idx in indexes]
        
        assert 'idx_articles_source_id' in index_names
        assert 'idx_articles_published_at' in index_names
        assert 'idx_articles_url' in index_names
        assert 'idx_articles_sentiment_score' in index_names
        assert 'idx_articles_sentiment_label' in index_names
        assert 'idx_articles_ai_processed_at' in index_names
        assert 'idx_articles_processing_status' in index_names
        assert 'idx_articles_duplicate_group_hash' in index_names
    
    def test_analysis_task_indexes(self, test_db_engine):
        """Test AnalysisTask model indexes"""
        inspector = inspect(test_db_engine)
        indexes = inspector.get_indexes('analysis_tasks')
        index_names = [idx['name'] for idx in indexes]
        
        assert 'idx_analysis_tasks_status' in index_names
        assert 'idx_analysis_tasks_task_type' in index_names
        assert 'idx_analysis_tasks_scheduled_at' in index_names
        assert 'idx_analysis_tasks_priority' in index_names
        assert 'idx_analysis_tasks_article_id' in index_names
        assert 'idx_analysis_tasks_worker_id' in index_names
        assert 'idx_analysis_tasks_status_priority' in index_names
    
    def test_trending_topic_indexes(self, test_db_engine):
        """Test TrendingTopic model indexes"""
        inspector = inspect(test_db_engine)
        indexes = inspector.get_indexes('trending_topics')
        index_names = [idx['name'] for idx in indexes]
        
        assert 'idx_trending_topic_date' in index_names
        assert 'idx_trending_topic_category' in index_names
        assert 'idx_trending_topic_score' in index_names


class TestModelDataTypes:
    """Test suite for model data types and validation"""
    
    def test_uuid_fields(self, user_factory, article_factory, source_factory):
        """Test UUID field generation"""
        user = user_factory()
        article = article_factory()
        source = source_factory()
        
        # All UUID fields should be valid UUIDs
        assert isinstance(user.id, str) and len(user.id) == 36
        assert isinstance(article.id, str) and len(article.id) == 36
        assert isinstance(source.id, str) and len(source.id) == 36
    
    def test_json_fields(self, user_factory, article_factory, test_db_session):
        """Test JSON field storage and retrieval"""
        user = user_factory()
        preference = UserPreference(
            user_id=user.id,
            preferred_sources=["source1", "source2"],
            topic_tags=["AI", "technology"]
        )
        
        article = article_factory(
            topic_tags=["technology", "AI"],
            rate_limit_info={"remaining": 50, "total": 100}
        )
        
        test_db_session.add_all([user, preference, article])
        test_db_session.commit()
        
        # Verify JSON fields are stored correctly
        assert isinstance(preference.preferred_sources, list)
        assert preference.preferred_sources == ["source1", "source2"]
        assert isinstance(article.topic_tags, list)
        assert article.topic_tags == ["technology", "AI"]
        assert isinstance(article.rate_limit_info, dict)
    
    def test_datetime_fields(self, user_factory, article_factory):
        """Test datetime field handling"""
        user = user_factory()
        article = article_factory()
        
        # All datetime fields should be datetime objects or None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert isinstance(article.created_at, datetime)
        assert isinstance(article.updated_at, datetime)
        assert isinstance(article.published_at, (datetime, type(None)))
    
    def test_enum_fields(self, article_factory):
        """Test enum field handling"""
        article = article_factory()
        
        # Enum fields should be enum instances
        assert isinstance(article.processing_status, ProcessingStatus)
        
        # Test different enum values
        for status in ProcessingStatus:
            article.processing_status = status
            assert article.processing_status == status


class TestModelFactoryIntegration:
    """Integration tests for factory patterns with models"""
    
    def test_factory_integration_with_database(self, article_factory, source_factory, test_db_session):
        """Test that factory-created models work with database operations"""
        # Create source and article using factories
        source = source_factory(name="Integration Test Source")
        article = article_factory(
            title="Integration Test Article",
            source_id=source.id
        )
        
        # Add to database
        test_db_session.add_all([source, article])
        test_db_session.commit()
        
        # Retrieve from database
        retrieved_source = test_db_session.query(Source).filter_by(name="Integration Test Source").first()
        retrieved_article = test_db_session.query(Article).filter_by(title="Integration Test Article").first()
        
        assert retrieved_source is not None
        assert retrieved_article is not None
        assert retrieved_article.source == retrieved_source
        assert retrieved_source.articles == [retrieved_article]
    
    def test_factory_with_relationships(self, user_factory, article_factory, test_db_session):
        """Test factory pattern with complex relationships"""
        # Create user, article, and bookmark using factories
        user = user_factory(username="relationship_test_user")
        article = article_factory(title="Relationship Test Article")
        bookmark = UserBookmark(
            user_id=user.id,
            article_id=article.id,
            title="Bookmarked Article",
            url="https://example.com/bookmarked"
        )
        
        # Add to database
        test_db_session.add_all([user, article, bookmark])
        test_db_session.commit()
        
        # Test relationships
        assert user.preferences is None  # No preferences created
        assert len(user.bookmarks) == 1
        assert user.bookmarks[0] == bookmark
        assert bookmark.user == user
        assert bookmark.article == article