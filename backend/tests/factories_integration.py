"""
Integration between Factories and existing conftest.py

Este archivo integra las factories creadas con el conftest.py existente,
proporcionando una transición suave entre el sistema anterior y el nuevo.
"""

import pytest
from tests.factories import (
    ArticleFactory,
    UserFactory, 
    SourceFactory,
    ArticleAnalysisFactory,
    TestDataLoader,
    MockAPIContext
)

# Importar fixtures existentes del conftest.py original
from app.db.models import Article, User, Source, UserPreference, UserBookmark


# ============================================================================
# ENHANCED FACTORY FIXTURES
# ============================================================================

@pytest.fixture
def enhanced_db_session(test_db_session):
    """Enhanced database session with factory support"""
    # El test_db_session del conftest.py existente ya está disponible
    # Simplemente lo pasamos junto para uso con factories
    return test_db_session


@pytest.fixture
def factory_article(test_db_session, test_source):
    """Article created using factories with existing test infrastructure"""
    from tests.factories.article_factory import ArticleFactory
    from tests.factories.source_factory import SourceFactory
    
    # Convertir source de conftest a factory-compatible format
    source = SourceFactory(
        name=test_source.name,
        url=test_source.url,
        api_name=test_source.api_name
    )
    
    # Si el test_source tiene un ID específico, usarlo
    source.id = test_source.id
    test_db_session.add(source)
    test_db_session.flush()
    
    article = ArticleFactory(source=source, processed=True)
    return article


@pytest.fixture
def factory_user(test_db_session):
    """User created using factories with existing test infrastructure"""
    from tests.factories.user_factory import UserFactory
    
    user = UserFactory(role='user')
    test_db_session.add(user)
    test_db_session.flush()
    return user


@pytest.fixture
def factory_admin_user(test_db_session):
    """Admin user created using factories"""
    from tests.factories.user_factory import AdminUserFactory
    
    admin = AdminUserFactory()
    test_db_session.add(admin)
    test_db_session.flush()
    return admin


@pytest.fixture
def factory_source(test_db_session):
    """Source created using factories"""
    from tests.factories.source_factory import SourceFactory
    
    source = SourceFactory()
    test_db_session.add(source)
    test_db_session.flush()
    return source


@pytest.fixture
def factory_spanish_source(test_db_session):
    """Spanish source created using factories"""
    from tests.factories.source_factory import SpanishSourceFactory
    
    source = SpanishSourceFactory()
    test_db_session.add(source)
    test_db_session.flush()
    return source


# ============================================================================
# HYBRID DATA FIXTURES (combining existing and factory data)
# ============================================================================

@pytest.fixture
def mixed_articles(test_db_session, sample_articles, test_source):
    """Mix of articles from sample_articles fixture and factory articles"""
    
    # Articles from existing conftest fixture
    articles = []
    for article_data in sample_articles[:2]:  # Take first 2 from existing
        article = Article(
            title=article_data["title"],
            content=article_data["content"],
            url=article_data["url"],
            source_id=test_source.id,
            processing_status="completed"
        )
        test_db_session.add(article)
        articles.append(article)
    
    # Add factory-generated articles
    from tests.factories.article_factory import ArticleFactory
    
    factory_articles = [
        ArticleFactory(source=test_source, processed=True),
        ArticleFactory(source=test_source, tech_related=True),
        ArticleFactory(source=test_source, positive_sentiment=True)
    ]
    
    for article in factory_articles:
        test_db_session.add(article)
        articles.append(article)
    
    test_db_session.flush()
    return articles


@pytest.fixture
def mixed_users(test_db_session, mock_current_user):
    """Mix of users from mock fixtures and factory users"""
    users = [mock_current_user]  # From existing conftest
    
    # Add factory users
    from tests.factories.user_factory import UserSetFactory
    
    factory_users = UserSetFactory.create_user_set(
        normal_users=3,
        admins=1,
        moderators=1
    )
    
    for user in factory_users:
        test_db_session.add(user)
        users.append(user)
    
    test_db_session.flush()
    return users


# ============================================================================
# ENHANCED API MOCKS (combining existing and factory mocks)
# ============================================================================

@pytest.fixture
def combined_mock_apis(mock_openai_client, mock_news_api_client, mock_guardian_client, mock_nytimes_client):
    """Combined mock APIs from existing conftest and factory mocks"""
    
    class CombinedMocks:
        def __init__(self):
            self.openai = mock_openai_client
            self.newsapi = mock_news_api_client
            self.guardian = mock_guardian_client
            self.nytimes = mock_nytimes_client
            
        def get_api_response(self, api_name, endpoint='top-headlines'):
            """Get response from specific mocked API"""
            if api_name == 'newsapi':
                return self.newsapi.get.return_value.json.return_value
            elif api_name == 'guardian':
                return self.guardian.get.return_value.json.return_value
            elif api_name == 'nytimes':
                return self.nytimes.get.return_value.json.return_value
            else:
                raise ValueError(f"Unknown API: {api_name}")
    
    return CombinedMocks()


# ============================================================================
# FACTORY-ENHANCED AI PROCESSOR FIXTURES
# ============================================================================

@pytest.fixture
def factory_ai_processor(test_db_session, test_redis, mock_openai_client):
    """AI Processor enhanced with factory-generated test data"""
    from app.services.ai_processor import AIProcessor
    
    # Create sample articles using factories for testing
    source = SourceFactory(api_name='newsapi')
    test_db_session.add(source)
    test_db_session.flush()
    
    test_articles = ArticleFactory.create_batch(5, source=source, processed=True)
    for article in test_articles:
        test_db_session.add(article)
    test_db_session.flush()
    
    # Create processor
    processor = AIProcessor(
        redis_client=test_redis,
        openai_api_key="test-key"
    )
    processor.openai_client = mock_openai_client
    
    return {
        'processor': processor,
        'test_articles': test_articles,
        'test_source': source
    }


# ============================================================================
# ENHANCED DATA LOADERS
# ============================================================================

@pytest.fixture
def enhanced_test_loader(test_db_session):
    """Test data loader that integrates existing and factory data"""
    from tests.factories.test_data_loader import TestDataLoader
    
    class EnhancedTestLoader(TestDataLoader):
        def __init__(self, db_session):
            super().__init__(db_session)
            self.existing_data = {
                'mock_users': [],
                'sample_articles': []
            }
        
        def load_hybrid_data(self, use_factories=True, use_existing=True):
            """Load data using both factory and existing fixtures"""
            
            if use_existing:
                # Add existing sample data from conftest
                # Note: This would need to be adapted based on your specific needs
                pass
            
            if use_factories:
                # Use factory data
                result = self.load_basic_data(
                    num_users=5,
                    num_sources=3,
                    num_articles_per_source=2
                )
                return result
            
            return {'users': 0, 'sources': 0, 'articles': 0}
    
    return EnhancedTestLoader(test_db_session)


# ============================================================================
# INTEGRATION TEST FIXTURES
# ============================================================================

@pytest.fixture
def integration_test_data(test_db_session, mock_current_user, test_source, sample_articles):
    """Comprehensive test data for integration testing"""
    from tests.factories.analysis_factory import ArticleAnalysisFactory
    from tests.factories.user_factory import UserPreferenceFactory
    
    # Add mock user from conftest
    test_db_session.add(mock_current_user)
    test_db_session.flush()
    
    # Add sample articles from conftest
    for article_data in sample_articles:
        article = Article(
            title=article_data["title"],
            content=article_data["content"], 
            url=article_data["url"],
            source_id=test_source.id
        )
        test_db_session.add(article)
    
    # Add factory-generated articles
    articles = ArticleFactory.create_batch(3, source=test_source, processed=True)
    for article in articles:
        test_db_session.add(article)
    
    # Add analysis results for some articles
    for article in articles[:2]:  # First 2 factory articles
        analysis = ArticleAnalysisFactory(article=article, analysis_type='sentiment')
        test_db_session.add(analysis)
    
    # Add user preferences for mock user
    preferences = UserPreferenceFactory(user=mock_current_user)
    test_db_session.add(preferences)
    
    test_db_session.flush()
    
    return {
        'mock_user': mock_current_user,
        'sample_articles_count': len(sample_articles),
        'factory_articles_count': len(articles),
        'analysis_results_count': 2,
        'has_preferences': mock_current_user.preferences is not None
    }


# ============================================================================
# PERFORMANCE TEST FIXTURES
# ============================================================================

@pytest.fixture
def performance_test_data_set(test_db_session):
    """Large dataset for performance testing using factories"""
    from tests.factories.source_factory import SourceSetFactory
    from tests.factories.user_factory import UserSetFactory
    
    # Create sources
    sources = SourceSetFactory.create_news_source_set(
        high_credibility=5,
        medium_credibility=8,
        low_credibility=3,
        inactive=2
    )
    
    for source in sources:
        test_db_session.add(source)
    
    # Create users
    users = UserSetFactory.create_user_set(
        normal_users=20,
        admins=2,
        moderators=3,
        inactive_users=5
    )
    
    for user in users:
        test_db_session.add(user)
    
    # Create many articles
    article_counts = []
    for i, source in enumerate(sources[:10]):  # Use first 10 sources
        count = 20 + (i * 5)  # 20, 25, 30, etc.
        article_counts.append(count)
        
        articles = ArticleFactory.create_batch(count, source=source, processed=True)
        for article in articles:
            test_db_session.add(article)
    
    test_db_session.flush()
    
    return {
        'sources': len(sources),
        'users': len(users),
        'total_articles': sum(article_counts),
        'article_counts_by_source': dict(zip([s.name for s in sources[:10]], article_counts))
    }


# ============================================================================
# MIGRATION HELPERS
# ============================================================================

@pytest.fixture
def migration_helper(test_db_session):
    """Helper for migrating tests from old fixtures to factories"""
    
    class MigrationHelper:
        def __init__(self, db_session):
            self.db = db_session
        
        def create_user_like_existing_mock(self, mock_user):
            """Create factory user similar to existing mock_user"""
            user = UserFactory(
                id=mock_user.id,
                username=mock_user.username,
                email=mock_user.email,
                full_name=mock_user.full_name,
                role=mock_user.role,
                is_active=mock_user.is_active
            )
            self.db.add(user)
            self.db.flush()
            return user
        
        def create_article_like_existing_sample(self, sample_article, source_id):
            """Create factory article similar to existing sample articles"""
            article = ArticleFactory(
                id=sample_article["id"],
                title=sample_article["title"],
                content=sample_article["content"],
                url=sample_article["url"],
                source_id=source_id
            )
            self.db.add(article)
            self.db.flush()
            return article
        
        def compare_data_integrity(self, factory_data, existing_data):
            """Compare data integrity between factory and existing data"""
            from tests.factories.fixtures import data_integrity_checker
            
            checker = data_integrity_checker()
            
            # Basic integrity checks
            if hasattr(factory_data, '__iter__'):
                for item in factory_data:
                    if hasattr(item, 'id') and hasattr(item, 'title'):
                        checker.check_required_fields(item, ['id', 'title'])
            
            return checker.get_report()
    
    return MigrationHelper(test_db_session)


# ============================================================================
# COMPATIBILITY FIXTURES
# ============================================================================

@pytest.fixture
def backward_compatible_fixtures(mock_current_user, sample_articles, test_source):
    """Provide backward compatibility with existing test patterns"""
    
    class BackwardCompatibility:
        def __init__(self):
            self.mock_user = mock_current_user
            self.sample_articles = sample_articles
            self.test_source = test_source
        
        def get_user(self):
            return self.mock_user
        
        def get_articles(self):
            return self.sample_articles
        
        def get_source(self):
            return self.test_source
        
        def has_user_preferences(self):
            # This would need to be implemented based on your specific needs
            return True
        
        def get_user_bookmarks(self):
            # This would need to be implemented based on your specific needs
            return []
    
    return BackwardCompatibility()


# ============================================================================
# DOCUMENTATION FIXTURES
# ============================================================================

@pytest.fixture
def fixture_documentation():
    """Documentation about available fixtures"""
    return {
        "factories": {
            "ArticleFactory": "Generate individual articles with customizable traits",
            "UserFactory": "Generate users with different roles and states",
            "SourceFactory": "Generate news sources with various characteristics",
            "ArticleAnalysisFactory": "Generate AI analysis results",
            "UserPreferenceFactory": "Generate user preferences",
            "UserBookmarkFactory": "Generate user bookmarks"
        },
        "enhanced_fixtures": {
            "factory_article": "Article using factories integrated with existing test infrastructure",
            "factory_user": "User using factories",
            "factory_admin_user": "Admin user using factories",
            "factory_source": "Source using factories",
            "factory_spanish_source": "Spanish source using factories"
        },
        "hybrid_fixtures": {
            "mixed_articles": "Combination of existing and factory-generated articles",
            "mixed_users": "Combination of mock and factory users",
            "integration_test_data": "Comprehensive data for integration testing"
        },
        "utility_fixtures": {
            "combined_mock_apis": "Combined API mocks from existing and factory sources",
            "factory_ai_processor": "AI processor enhanced with factory data",
            "enhanced_test_loader": "Test data loader with hybrid capabilities",
            "performance_test_data_set": "Large dataset for performance testing"
        },
        "migration_helpers": {
            "migration_helper": "Helper for migrating from old fixtures to factories",
            "backward_compatible_fixtures": "Provide compatibility with existing test patterns"
        }
    }