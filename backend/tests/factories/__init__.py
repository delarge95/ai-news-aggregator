"""
Test Data Factories for AI News Aggregator

Este módulo proporciona factories para generar datos de prueba consistentes
y realistas para testing del sistema.

Uso básico:
    from tests.factories import ArticleFactory, UserFactory, SourceFactory
    
    # Crear datos individuales
    user = UserFactory()
    source = SourceFactory()
    article = ArticleFactory(source=source)
    
Uso avanzado:
    from tests.factories import TestDataLoader, MockAPIContext
    
    # Cargar dataset completo
    loader = TestDataLoader(db_session)
    result = loader.load_basic_data(num_users=10, num_sources=5)
    
    # Mock de APIs externas
    with MockAPIContext(['newsapi']):
        # Tu código que usa APIs externas aquí
        pass
"""

# Importar todas las factories
from .article_factory import (
    ArticleFactory,
    DuplicateArticleFactory,
    FeaturedArticleFactory,
    ControversialArticleFactory
)

from .user_factory import (
    UserFactory,
    UserPreferenceFactory,
    UserBookmarkFactory,
    UserWithPreferencesFactory,
    AdminUserFactory,
    ModeratorUserFactory,
    InactiveUserFactory,
    UserSetFactory
)

from .source_factory import (
    SourceFactory,
    HighCredibilitySourceFactory,
    LowCredibilitySourceFactory,
    InactiveSourceFactory,
    SpanishSourceFactory,
    EnglishSourceFactory,
    TechSourceFactory,
    SportsSourceFactory,
    NewsAPISourceFactory,
    GuardianSourceFactory,
    NYTimesSourceFactory,
    APIMockSourceFactory,
    SourceSetFactory
)

from .analysis_factory import (
    ArticleAnalysisFactory,
    AnalysisTaskFactory,
    AnalysisSetFactory,
    TaskSetFactory
)

from .test_data_loader import (
    TestDataLoader,
    TestDataContext,
    quick_test_data,
    comprehensive_test_data,
    cleanup_test_data
)

from .mock_external_apis import (
    MockExternalAPIs,
    MockNewsAPI,
    MockGuardianAPI,
    MockNYTimesAPI,
    MockAPIContext,
    mock_all_apis,
    mock_newsapi_only
)

from .fixtures import (
    # Database fixtures
    test_engine,
    TestSessionLocal,
    db_session,
    
    # User fixtures
    sample_user,
    admin_user,
    moderator_user,
    inactive_user,
    sample_users,
    user_with_preferences,
    
    # Source fixtures
    sample_source,
    high_credibility_source,
    spanish_source,
    english_source,
    inactive_source,
    sample_sources,
    
    # Article fixtures
    sample_article,
    unprocessed_article,
    failed_article,
    tech_article,
    politics_article,
    health_article,
    recent_article,
    old_article,
    positive_article,
    negative_article,
    sample_articles,
    
    # Analysis fixtures
    sample_analysis_result,
    sentiment_analysis,
    bias_analysis,
    topic_analysis,
    complete_analysis,
    sample_analysis_results,
    
    # User preferences & bookmarks fixtures
    user_preferences,
    user_bookmark,
    user_bookmarks,
    
    # Comprehensive fixtures
    test_articles_fixture,
    test_users_fixture,
    test_sources_fixture,
    comprehensive_test_data_fixture,
    
    # Utility fixtures
    test_data_loader,
    mock_api_manager,
    mock_http_responses,
    sample_search_queries,
    sample_dates,
    sample_pagination_data,
    
    # Authentication fixtures
    mock_current_user,
    mock_admin_user,
    mock_auth_headers,
    
    # Performance fixtures
    large_article_dataset,
    large_user_dataset,
    
    # Parametrized fixtures
    sample_languages,
    sample_user_roles,
    sample_article_scenarios
)

# Importar examples para referencia
from .examples import *

# Metadata del módulo
__version__ = "1.0.0"
__author__ = "AI News Aggregator Team"
__description__ = "Sistema completo de factories y fixtures para testing"

# Exportar todo lo que esté disponible
__all__ = [
    # Factories principales
    "ArticleFactory",
    "UserFactory",
    "SourceFactory", 
    "UserPreferenceFactory",
    "UserBookmarkFactory",
    "ArticleAnalysisFactory",
    "AnalysisTaskFactory",
    
    # Factories especializadas
    "DuplicateArticleFactory",
    "FeaturedArticleFactory",
    "ControversialArticleFactory",
    "AdminUserFactory",
    "ModeratorUserFactory",
    "InactiveUserFactory",
    "HighCredibilitySourceFactory",
    "LowCredibilitySourceFactory",
    "SpanishSourceFactory",
    "EnglishSourceFactory",
    "TechSourceFactory",
    "SportsSourceFactory",
    
    # Loaders y managers
    "TestDataLoader",
    "TestDataContext",
    "MockExternalAPIs",
    "MockAPIContext",
    
    # Factories de conjuntos
    "UserSetFactory",
    "SourceSetFactory",
    "AnalysisSetFactory",
    "TaskSetFactory",
    
    # Funciones de conveniencia
    "quick_test_data",
    "comprehensive_test_data",
    "cleanup_test_data",
    "mock_all_apis",
    "mock_newsapi_only",
    
    # Fixtures principales
    "db_session",
    "sample_user",
    "admin_user",
    "sample_users",
    "sample_source",
    "sample_sources",
    "sample_article",
    "sample_articles",
    "sample_analysis_results",
    "comprehensive_test_data_fixture",
    
    # Otros fixtures
    "test_data_loader",
    "mock_api_manager",
    "sample_search_queries",
    "mock_auth_headers",
    "large_article_dataset",
    "large_user_dataset",
    
    # Ejemplos
    "examples"
]