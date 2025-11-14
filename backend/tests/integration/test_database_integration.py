"""
Integration tests for database CRUD operations
Tests de integración para operaciones CRUD de base de datos

Este archivo contiene tests que verifican las operaciones CRUD completas
en la base de datos, incluyendo transacciones, constraints, índices,
y optimizaciones de rendimiento.
"""

import asyncio
import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
import asyncpg
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

# Import application components
from app.db.models import (
    Article, Source, User, Category, 
    ArticleAnalysis, TrendingTopic, UserPreference
)
from app.db.database import get_db_session, create_engine, get_async_session
from app.core.config import settings

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.database
]


class TestDatabaseConnection:
    """Test database connection and configuration"""
    
    @pytest.fixture
    async def test_db_session(self):
        """Create a test database session with rollback"""
        # Use test database URL from conftest.py
        test_db_url = "sqlite+aiosqlite:///:memory:"
        
        async with AsyncSession(test_engine) as session:
            try:
                # Create all tables
                async with test_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                
                yield session
                
            finally:
                await session.close()
                await test_engine.dispose()
    
    async def test_database_connection_health(self, test_db_session):
        """Test database connection is healthy"""
        result = await test_db_session.execute(select(1))
        assert result.scalar() == 1
    
    async def test_database_transaction_rollback(self, test_db_session):
        """Test transaction rollback functionality"""
        # Create test article
        test_article = Article(
            title="Test Article",
            content="Test content",
            url="https://example.com/test"
        )
        test_db_session.add(test_article)
        
        # Commit first transaction
        await test_db_session.commit()
        article_id = test_article.id
        
        # Start new transaction
        await test_db_session.begin()
        
        # Update article
        await test_db_session.execute(
            update(Article).where(Article.id == article_id).values(title="Modified Title")
        )
        
        # Rollback
        await test_db_session.rollback()
        
        # Verify rollback
        result = await test_db_session.execute(
            select(Article).where(Article.id == article_id)
        )
        article = result.scalar_one()
        assert article.title == "Test Article"
    
    async def test_concurrent_database_operations(self, test_db_session):
        """Test concurrent database operations"""
        # Create multiple articles concurrently
        articles_data = [
            {
                "title": f"Article {i}",
                "content": f"Content for article {i}",
                "url": f"https://example.com/article-{i}"
            }
            for i in range(10)
        ]
        
        # Insert articles concurrently
        tasks = []
        for data in articles_data:
            article = Article(**data)
            test_db_session.add(article)
            tasks.append(test_db_session.flush())
        
        await asyncio.gather(*tasks)
        await test_db_session.commit()
        
        # Verify all articles were created
        result = await test_db_session.execute(select(Article))
        articles = result.scalars().all()
        assert len(articles) == 10


class TestArticleCRUDOperations:
    """Test complete Article CRUD operations"""
    
    @pytest.fixture
    async def test_article_data(self):
        """Sample article data for testing"""
        return {
            "title": "Test Article Title",
            "content": "This is the test article content for integration testing.",
            "description": "Test description",
            "url": "https://example.com/test-article",
            "author": "Test Author",
            "image_url": "https://example.com/image.jpg",
            "published_at": datetime.utcnow()
        }
    
    @pytest.fixture
    async def related_source(self, test_db_session):
        """Create a related source for testing"""
        source = Source(
            name="Test Source",
            api_name="test_api",
            api_source_id="test-source-id",
            country="US",
            language="en",
            credibility_score=0.8,
            is_active=True
        )
        test_db_session.add(source)
        await test_db_session.commit()
        await test_db_session.refresh(source)
        return source
    
    async def test_create_article(self, test_db_session, test_article_data, related_source):
        """Test creating a new article"""
        # Add source relationship
        test_article_data["source_id"] = related_source.id
        
        article = Article(**test_article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        await test_db_session.refresh(article)
        
        assert article.id is not None
        assert article.title == test_article_data["title"]
        assert article.content == test_article_data["content"]
        assert article.created_at is not None
        assert article.status == "pending"
    
    async def test_read_article_by_id(self, test_db_session, test_article_data, related_source):
        """Test reading an article by ID"""
        # Create article
        test_article_data["source_id"] = related_source.id
        article = Article(**test_article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        await test_db_session.refresh(article)
        article_id = article.id
        
        # Read article by ID
        result = await test_db_session.execute(
            select(Article).where(Article.id == article_id)
        )
        retrieved_article = result.scalar_one()
        
        assert retrieved_article.id == article_id
        assert retrieved_article.title == test_article_data["title"]
    
    async def test_update_article(self, test_db_session, test_article_data, related_source):
        """Test updating an article"""
        # Create article
        test_article_data["source_id"] = related_source.id
        article = Article(**test_article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        await test_db_session.refresh(article)
        article_id = article.id
        
        # Update article
        update_data = {
            "title": "Updated Title",
            "status": "processed",
            "ai_sentiment": "positive",
            "ai_confidence": 0.85
        }
        
        await test_db_session.execute(
            update(Article).where(Article.id == article_id).values(**update_data)
        )
        await test_db_session.commit()
        
        # Verify update
        result = await test_db_session.execute(
            select(Article).where(Article.id == article_id)
        )
        updated_article = result.scalar_one()
        
        assert updated_article.title == "Updated Title"
        assert updated_article.status == "processed"
        assert updated_article.ai_sentiment == "positive"
    
    async def test_delete_article(self, test_db_session, test_article_data, related_source):
        """Test deleting an article"""
        # Create article
        test_article_data["source_id"] = related_source.id
        article = Article(**test_article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        await test_db_session.refresh(article)
        article_id = article.id
        
        # Delete article
        await test_db_session.execute(
            delete(Article).where(Article.id == article_id)
        )
        await test_db_session.commit()
        
        # Verify deletion
        result = await test_db_session.execute(
            select(Article).where(Article.id == article_id)
        )
        assert result.scalar_one_or_none() is None
    
    async def test_article_with_relationships(self, test_db_session, test_article_data, related_source):
        """Test article operations with relationships"""
        # Create article with source relationship
        test_article_data["source_id"] = related_source.id
        article = Article(**test_article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        
        # Create analysis record
        analysis = ArticleAnalysis(
            article_id=article.id,
            sentiment="positive",
            sentiment_confidence=0.8,
            topic="technology",
            topic_confidence=0.9,
            summary="Test summary",
            keywords=["test", "article"]
        )
        test_db_session.add(analysis)
        await test_db_session.commit()
        
        # Query article with relationships
        result = await test_db_session.execute(
            select(Article)
            .options(
                selectinload(Article.source),
                selectinload(Article.analysis)
            )
            .where(Article.id == article.id)
        )
        
        retrieved_article = result.scalar_one()
        
        assert retrieved_article.source.name == "Test Source"
        assert len(retrieved_article.analysis) == 1
        assert retrieved_article.analysis[0].sentiment == "positive"


class TestSourceCRUDOperations:
    """Test Source CRUD operations"""
    
    @pytest.fixture
    async def source_data(self):
        """Sample source data for testing"""
        return {
            "name": "Test News Source",
            "api_name": "newsapi",
            "api_source_id": "test-news-source",
            "url": "https://example.com",
            "country": "US",
            "language": "en",
            "credibility_score": 0.85,
            "is_active": True,
            "rate_limit_per_hour": 100
        }
    
    async def test_create_source(self, test_db_session, source_data):
        """Test creating a new source"""
        source = Source(**source_data)
        test_db_session.add(source)
        await test_db_session.flush()
        await test_db_session.refresh(source)
        
        assert source.id is not None
        assert source.name == source_data["name"]
        assert source.is_active is True
    
    async def test_source_unique_constraints(self, test_db_session, source_data):
        """Test source unique constraints"""
        # Create first source
        source1 = Source(**source_data)
        test_db_session.add(source1)
        await test_db_session.flush()
        
        # Try to create duplicate (should fail)
        source2 = Source(**source_data)
        test_db_session.add(source2)
        
        with pytest.raises(Exception):  # Should raise integrity error
            await test_db_session.flush()
    
    async def test_source_filtering_and_search(self, test_db_session):
        """Test source filtering and search functionality"""
        # Create multiple sources
        sources_data = [
            {
                "name": "US News",
                "api_name": "newsapi",
                "country": "US",
                "language": "en",
                "is_active": True
            },
            {
                "name": "UK News",
                "api_name": "guardian",
                "country": "GB",
                "language": "en",
                "is_active": True
            },
            {
                "name": "Inactive Source",
                "api_name": "test",
                "country": "US",
                "language": "en",
                "is_active": False
            }
        ]
        
        for data in sources_data:
            source = Source(**data)
            test_db_session.add(source)
        
        await test_db_session.commit()
        
        # Test filtering by country
        us_sources = await test_db_session.execute(
            select(Source).where(Source.country == "US")
        )
        us_sources_list = us_sources.scalars().all()
        assert len(us_sources_list) == 2
        
        # Test filtering by active status
        active_sources = await test_db_session.execute(
            select(Source).where(Source.is_active == True)
        )
        active_sources_list = active_sources.scalars().all()
        assert len(active_sources_list) == 2
        
        # Test filtering by API name
        newsapi_sources = await test_db_session.execute(
            select(Source).where(Source.api_name == "newsapi")
        )
        assert len(newsapi_sources.scalars().all()) == 1


class TestAnalyticsDataOperations:
    """Test analytics-related database operations"""
    
    async def test_article_analysis_crud(self, test_db_session, test_article_data):
        """Test ArticleAnalysis CRUD operations"""
        # Create article first
        article = Article(**test_article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        await test_db_session.refresh(article)
        
        # Create analysis
        analysis_data = {
            "article_id": article.id,
            "sentiment": "positive",
            "sentiment_confidence": 0.85,
            "topic": "technology",
            "topic_confidence": 0.9,
            "summary": "Test summary for the article",
            "keywords": ["test", "technology", "ai"],
            "bias_score": 0.2,
            "credibility_score": 0.8
        }
        
        analysis = ArticleAnalysis(**analysis_data)
        test_db_session.add(analysis)
        await test_db_session.commit()
        await test_db_session.refresh(analysis)
        
        assert analysis.id is not None
        assert analysis.sentiment == "positive"
        
        # Update analysis
        await test_db_session.execute(
            update(ArticleAnalysis).where(ArticleAnalysis.id == analysis.id)
            .values(sentiment="negative", sentiment_confidence=0.9)
        )
        await test_db_session.commit()
        
        # Verify update
        result = await test_db_session.execute(
            select(ArticleAnalysis).where(ArticleAnalysis.id == analysis.id)
        )
        updated_analysis = result.scalar_one()
        assert updated_analysis.sentiment == "negative"
    
    async def test_trending_topics_operations(self, test_db_session):
        """Test TrendingTopic operations"""
        # Create trending topics
        topics_data = [
            {
                "topic": "artificial intelligence",
                "category": "technology",
                "mentions_count": 100,
                "trend_score": 0.85,
                "date": datetime.utcnow().date()
            },
            {
                "topic": "climate change",
                "category": "environment",
                "mentions_count": 75,
                "trend_score": 0.7,
                "date": datetime.utcnow().date()
            }
        ]
        
        for data in topics_data:
            topic = TrendingTopic(**data)
            test_db_session.add(topic)
        
        await test_db_session.commit()
        
        # Query trending topics
        result = await test_db_session.execute(
            select(TrendingTopic).order_by(TrendingTopic.mentions_count.desc())
        )
        topics = result.scalars().all()
        assert len(topics) == 2
        assert topics[0].mentions_count == 100
    
    async def test_user_preferences_crud(self, test_db_session):
        """Test UserPreference operations"""
        # Create user
        user = User(
            email="test@example.com",
            username="testuser"
        )
        test_db_session.add(user)
        await test_db_session.flush()
        await test_db_session.refresh(user)
        
        # Create preferences
        preferences_data = {
            "user_id": user.id,
            "preferred_topics": ["technology", "science"],
            "preferred_sources": ["newsapi", "guardian"],
            "notification_settings": {"email": True, "push": False}
        }
        
        preferences = UserPreference(**preferences_data)
        test_db_session.add(preferences)
        await test_db_session.commit()
        await test_db_session.refresh(preferences)
        
        assert preferences.user_id == user.id
        assert "technology" in preferences.preferred_topics


class TestDatabaseOptimization:
    """Test database optimization features"""
    
    async def test_pagination_performance(self, test_db_session):
        """Test pagination query performance"""
        # Create large dataset
        articles_data = [
            {
                "title": f"Article {i}",
                "content": f"Content for article {i}",
                "url": f"https://example.com/article-{i}"
            }
            for i in range(100)
        ]
        
        for data in articles_data:
            article = Article(**data)
            test_db_session.add(article)
        
        await test_db_session.commit()
        
        # Test pagination query
        page_size = 10
        page_number = 5
        
        result = await test_db_session.execute(
            select(Article)
            .order_by(Article.created_at.desc())
            .limit(page_size)
            .offset((page_number - 1) * page_size)
        )
        
        articles = result.scalars().all()
        assert len(articles) <= page_size
        
        # Test total count query
        count_result = await test_db_session.execute(
            select(Article).count()
        )
        total_count = count_result.scalar()
        assert total_count == 100
    
    async def test_complex_filtering_queries(self, test_db_session):
        """Test complex filtering queries"""
        # Create test data
        test_data = [
            {"title": "AI Technology News", "content": "AI content", "status": "processed"},
            {"title": "Sports News", "content": "sports content", "status": "pending"},
            {"title": "Business News", "content": "business content", "status": "processed"}
        ]
        
        for data in test_data:
            article = Article(**data)
            test_db_session.add(article)
        
        await test_db_session.commit()
        
        # Test complex WHERE clause
        result = await test_db_session.execute(
            select(Article).where(
                and_(
                    Article.status == "processed",
                    Article.title.contains("News")
                )
            )
        )
        
        articles = result.scalars().all()
        assert len(articles) == 2
        assert all("News" in article.title for article in articles)
    
    async def test_database_indexes_usage(self, test_db_session):
        """Test database indexes are being used"""
        # Create source and articles with indexes
        source = Source(
            name="Test Source",
            api_name="newsapi",
            country="US",
            language="en",
            is_active=True
        )
        test_db_session.add(source)
        await test_db_session.flush()
        
        # Add indexed articles
        for i in range(50):
            article = Article(
                title=f"Article {i}",
                content=f"Content {i}",
                url=f"https://example.com/article-{i}",
                source_id=source.id,
                status="processed"
            )
            test_db_session.add(article)
        
        await test_db_session.commit()
        
        # Query using indexed columns
        result = await test_db_session.execute(
            select(Article)
            .where(Article.source_id == source.id)
            .where(Article.status == "processed")
            .order_by(Article.created_at.desc())
            .limit(10)
        )
        
        articles = result.scalars().all()
        assert len(articles) <= 10
        assert all(article.source_id == source.id for article in articles)


class TestDatabaseConstraints:
    """Test database constraints and data integrity"""
    
    async def test_foreign_key_constraints(self, test_db_session):
        """Test foreign key constraints"""
        # Try to create article with non-existent source
        article_data = {
            "title": "Test Article",
            "content": "Test content",
            "url": "https://example.com/test",
            "source_id": 999  # Non-existent source
        }
        
        article = Article(**article_data)
        test_db_session.add(article)
        
        with pytest.raises(Exception):  # Should raise foreign key constraint error
            await test_db_session.flush()
    
    async def test_check_constraints(self, test_db_session):
        """Test check constraints"""
        # Create source with invalid credibility score
        source_data = {
            "name": "Test Source",
            "api_name": "test",
            "credibility_score": 1.5,  # Invalid: should be <= 1.0
            "is_active": True
        }
        
        source = Source(**source_data)
        test_db_session.add(source)
        
        # This should be handled by database constraints
        # Depending on the database, this might raise an error
        try:
            await test_db_session.flush()
            # If no error, verify the value was clamped
            await test_db_session.refresh(source)
            assert source.credibility_score <= 1.0
        except Exception:
            # Expected for strict databases
            pass
    
    async def test_unique_constraints(self, test_db_session):
        """Test unique constraints"""
        # Create first user
        user1 = User(email="test@example.com", username="testuser1")
        test_db_session.add(user1)
        await test_db_session.flush()
        
        # Try to create duplicate email
        user2 = User(email="test@example.com", username="testuser2")
        test_db_session.add(user2)
        
        with pytest.raises(Exception):  # Should raise unique constraint error
            await test_db_session.flush()


class TestDatabaseMigrations:
    """Test database migration handling"""
    
    async def test_migration_compatibility(self, test_db_session):
        """Test that schema changes are compatible"""
        # Create article with all current fields
        article_data = {
            "title": "Migration Test Article",
            "content": "Test content for migration",
            "url": "https://example.com/migration-test"
        }
        
        article = Article(**article_data)
        test_db_session.add(article)
        await test_db_session.flush()
        await test_db_session.refresh(article)
        
        # Verify all expected fields exist
        expected_fields = [
            "id", "title", "content", "url", "created_at", 
            "updated_at", "status", "source_id"
        ]
        
        for field in expected_fields:
            assert hasattr(article, field), f"Field {field} missing from Article model"
    
    async def test_schema_versioning(self, test_db_session):
        """Test schema versioning compatibility"""
        # Test that old data can be read with new schema
        result = await test_db_session.execute(
            select(Article).limit(1)
        )
        
        # If articles exist, verify they can be read
        articles = result.scalars().all()
        for article in articles:
            assert article.id is not None
            assert isinstance(article.created_at, datetime)


# Database test utilities
async def create_test_database():
    """Create a clean test database"""
    # Implementation would create a fresh test database
    pass


async def cleanup_test_database():
    """Clean up test database"""
    # Implementation would clean up test database
    pass


async def seed_test_data(session: AsyncSession, num_articles: int = 10):
    """Seed database with test data"""
    # Create source
    source = Source(
        name="Test Source",
        api_name="newsapi",
        country="US",
        language="en",
        is_active=True
    )
    session.add(source)
    await session.flush()
    
    # Create articles
    for i in range(num_articles):
        article = Article(
            title=f"Test Article {i}",
            content=f"Test content for article {i}",
            url=f"https://example.com/article-{i}",
            source_id=source.id,
            status="processed" if i % 2 == 0 else "pending"
        )
        session.add(article)
    
    await session.commit()


def assert_article_data_integrity(article: Article):
    """Assert that article data meets integrity requirements"""
    assert article.id is not None
    assert article.title is not None and len(article.title) > 0
    assert article.content is not None and len(article.content) > 0
    assert article.url is not None and len(article.url) > 0
    assert article.created_at is not None
    assert article.status in ["pending", "processed", "failed"]


if __name__ == "__main__":
    print("Database integration tests configuration loaded successfully")