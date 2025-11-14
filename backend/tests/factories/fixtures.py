"""
Pytest Fixtures - Configuración de fixtures reutilizables

Este módulo proporciona fixtures de pytest para testing del sistema,
proporcionando datos de prueba preconfigurados y utilidades de testing.
"""

import pytest
import uuid
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator
from unittest.mock import Mock

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from factory import fuzzy

from app.db.models import Base, User, Source, Article, UserPreference, UserBookmark
from tests.factories.article_factory import ArticleFactory
from tests.factories.user_factory import UserFactory, UserPreferenceFactory
from tests.factories.source_factory import SourceFactory
from tests.factories.analysis_factory import ArticleAnalysisFactory
from tests.factories.test_data_loader import TestDataLoader


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """Motor de base de datos en memoria para testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Crear todas las tablas
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()


@pytest.fixture(scope="session")
def TestSessionLocal(test_engine):
    """Factory para crear sesiones de prueba"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session(TestSessionLocal) -> Generator[Session, None, None]:
    """Sesión de base de datos para testing"""
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        # Rollback de cambios no confirmados
        session.rollback()
        session.close()


# =============================================================================
# USER FIXTURES
# =============================================================================

@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Usuario de ejemplo básico"""
    user = UserFactory()
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Usuario administrador"""
    user = UserFactory(admin=True)
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def moderator_user(db_session: Session) -> User:
    """Usuario moderador"""
    user = UserFactory(moderator=True)
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    """Usuario inactivo"""
    user = UserFactory(inactive=True)
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def sample_users(db_session: Session) -> List[User]:
    """Lista de usuarios de ejemplo"""
    users = [
        UserFactory(role='user'),
        UserFactory(role='user'),
        UserFactory(role='user'),
        UserFactory(admin=True),
        UserFactory(moderator=True),
        UserFactory(inactive=True)
    ]
    
    for user in users:
        db_session.add(user)
    
    db_session.flush()
    return users


@pytest.fixture
def user_with_preferences(db_session: Session, sample_user: User) -> User:
    """Usuario con preferencias configuradas"""
    preferences = UserPreferenceFactory(user=sample_user)
    db_session.add(preferences)
    db_session.flush()
    return sample_user


# =============================================================================
# SOURCE FIXTURES
# =============================================================================

@pytest.fixture
def sample_source(db_session: Session) -> Source:
    """Fuente de noticias de ejemplo"""
    source = SourceFactory()
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture
def high_credibility_source(db_session: Session) -> Source:
    """Fuente de alta credibilidad"""
    source = SourceFactory(highly_credible=True)
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture
def spanish_source(db_session: Session) -> Source:
    """Fuente española"""
    source = SourceFactory(spanish=True)
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture
def english_source(db_session: Session) -> Source:
    """Fuente inglesa"""
    source = SourceFactory(english=True)
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture
def inactive_source(db_session: Session) -> Source:
    """Fuente inactiva"""
    source = SourceFactory(inactive=True)
    db_session.add(source)
    db_session.flush()
    return source


@pytest.fixture
def sample_sources(db_session: Session) -> List[Source]:
    """Lista de fuentes de ejemplo"""
    sources = [
        SourceFactory(),
        SourceFactory(highly_credible=True),
        SourceFactory(spanish=True),
        SourceFactory(english=True),
        SourceFactory(tech_focused=True),
        SourceFactory(sports_focused=True),
        SourceFactory(low_credibility=True),
        SourceFactory(inactive=True)
    ]
    
    for source in sources:
        db_session.add(source)
    
    db_session.flush()
    return sources


# =============================================================================
# ARTICLE FIXTURES
# =============================================================================

@pytest.fixture
def sample_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo de ejemplo"""
    article = ArticleFactory(source=sample_source, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def unprocessed_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo sin procesar"""
    article = ArticleFactory(source=sample_source, unprocessed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def failed_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo con error en procesamiento"""
    article = ArticleFactory(source=sample_source, failed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def tech_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo sobre tecnología"""
    article = ArticleFactory(source=sample_source, tech_related=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def politics_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo político"""
    article = ArticleFactory(source=sample_source, politics_related=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def health_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo de salud"""
    article = ArticleFactory(source=sample_source, health_related=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def recent_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo reciente"""
    article = ArticleFactory(source=sample_source, recent=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def old_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo antiguo"""
    article = ArticleFactory(source=sample_source, old=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def positive_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo con sentimiento positivo"""
    article = ArticleFactory(source=sample_source, positive_sentiment=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def negative_article(db_session: Session, sample_source: Source) -> Article:
    """Artículo con sentimiento negativo"""
    article = ArticleFactory(source=sample_source, negative_sentiment=True, processed=True)
    db_session.add(article)
    db_session.flush()
    return article


@pytest.fixture
def sample_articles(db_session: Session, sample_sources: List[Source]) -> List[Article]:
    """Lista de artículos de ejemplo"""
    articles = []
    
    for source in sample_sources:
        # Crear diferentes tipos de artículos por fuente
        articles.extend([
            ArticleFactory(source=source, processed=True),
            ArticleFactory(source=source, unprocessed=True),
            ArticleFactory(source=source, tech_related=True, processed=True),
            ArticleFactory(source=source, positive_sentiment=True, processed=True),
            ArticleFactory(source=source, recent=True, processed=True)
        ])
    
    for article in articles:
        db_session.add(article)
    
    db_session.flush()
    return articles


# =============================================================================
# ANALYSIS FIXTURES
# =============================================================================

@pytest.fixture
def sample_analysis_result(db_session: Session, sample_article: Article) -> Any:
    """Resultado de análisis de ejemplo"""
    analysis = ArticleAnalysisFactory(article=sample_article, analysis_type='summary')
    db_session.add(analysis)
    db_session.flush()
    return analysis


@pytest.fixture
def sentiment_analysis(db_session: Session, sample_article: Article) -> Any:
    """Análisis de sentimiento"""
    analysis = ArticleAnalysisFactory(article=sample_article, analysis_type='sentiment')
    db_session.add(analysis)
    db_session.flush()
    return analysis


@pytest.fixture
def bias_analysis(db_session: Session, sample_article: Article) -> Any:
    """Análisis de sesgo"""
    analysis = ArticleAnalysisFactory(article=sample_article, analysis_type='bias')
    db_session.add(analysis)
    db_session.flush()
    return analysis


@pytest.fixture
def topic_analysis(db_session: Session, sample_article: Article) -> Any:
    """Análisis de temas"""
    analysis = ArticleAnalysisFactory(article=sample_article, analysis_type='topics')
    db_session.add(analysis)
    db_session.flush()
    return analysis


@pytest.fixture
def complete_analysis(db_session: Session, sample_article: Article) -> List[Any]:
    """Análisis completo de un artículo"""
    analysis_types = ['summary', 'sentiment', 'bias', 'topics', 'relevance', 'entities']
    analyses = []
    
    for analysis_type in analysis_types:
        analysis = ArticleAnalysisFactory(
            article=sample_article,
            analysis_type=analysis_type
        )
        db_session.add(analysis)
        analyses.append(analysis)
    
    db_session.flush()
    return analyses


@pytest.fixture
def sample_analysis_results(db_session: Session, sample_articles: List[Article]) -> List[Any]:
    """Lista de resultados de análisis de ejemplo"""
    analyses = []
    
    for article in sample_articles:
        if article.processing_status.value == 'completed':
            # Solo los artículos procesados tienen análisis
            for analysis_type in ['summary', 'sentiment', 'topics']:
                analysis = ArticleAnalysisFactory(
                    article=article,
                    analysis_type=analysis_type
                )
                db_session.add(analysis)
                analyses.append(analysis)
    
    db_session.flush()
    return analyses


# =============================================================================
# USER PREFERENCES & BOOKMARKS FIXTURES
# =============================================================================

@pytest.fixture
def user_preferences(db_session: Session, sample_user: User) -> UserPreference:
    """Preferencias de usuario"""
    preferences = UserPreferenceFactory(user=sample_user)
    db_session.add(preferences)
    db_session.flush()
    return preferences


@pytest.fixture
def user_bookmark(db_session: Session, sample_user: User, sample_article: Article) -> UserBookmark:
    """Marcador de usuario"""
    bookmark = UserBookmarkFactory(user=sample_user, article=sample_article)
    db_session.add(bookmark)
    db_session.flush()
    return bookmark


@pytest.fixture
def user_bookmarks(db_session: Session, sample_user: User, sample_articles: List[Article]) -> List[UserBookmark]:
    """Lista de marcadores de usuario"""
    bookmarks = []
    
    # Crear 3 marcadores con artículos diferentes
    for article in sample_articles[:3]:
        bookmark = UserBookmarkFactory(
            user=sample_user,
            article=article,
            title=article.title[:100],
            url=article.url
        )
        db_session.add(bookmark)
        bookmarks.append(bookmark)
    
    db_session.flush()
    return bookmarks


# =============================================================================
# COMPREHENSIVE TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def test_articles_fixture(db_session: Session, sample_sources: List[Source]) -> List[Article]:
    """Fixture completo de artículos para testing"""
    articles = []
    
    for source in sample_sources:
        # Crear artículos variados
        articles.extend([
            ArticleFactory(source=source, processed=True),
            ArticleFactory(source=source, unprocessed=True),
            ArticleFactory(source=source, tech_related=True, processed=True),
            ArticleFactory(source=source, politics_related=True, processed=True),
            ArticleFactory(source=source, health_related=True, processed=True),
            ArticleFactory(source=source, recent=True, processed=True),
            ArticleFactory(source=source, positive_sentiment=True, processed=True),
            ArticleFactory(source=source, negative_sentiment=True, processed=True)
        ])
    
    for article in articles:
        db_session.add(article)
    
    db_session.flush()
    return articles


@pytest.fixture
def test_users_fixture(db_session: Session) -> List[User]:
    """Fixture completo de usuarios para testing"""
    users = [
        UserFactory(username='admin', email='admin@test.com', admin=True),
        UserFactory(username='moderator', email='moderator@test.com', moderator=True),
        UserFactory(username='user1', email='user1@test.com'),
        UserFactory(username='user2', email='user2@test.com'),
        UserFactory(username='user3', email='user3@test.com'),
        UserFactory(username='inactive', email='inactive@test.com', inactive=True)
    ]
    
    for user in users:
        db_session.add(user)
    
    db_session.flush()
    return users


@pytest.fixture
def test_sources_fixture(db_session: Session) -> List[Source]:
    """Fixture completo de fuentes para testing"""
    sources = [
        SourceFactory(name='El País', api_name='newsapi', spanish=True),
        SourceFactory(name='BBC News', api_name='guardian', english=True),
        SourceFactory(name='TechCrunch', api_name='newsapi', tech_focused=True),
        SourceFactory(name='Marca', api_name='newsapi', sports_focused=True),
        SourceFactory(name='Reuters', api_name='guardian', highly_credible=True),
        SourceFactory(name='CNN', api_name='newsapi'),
        SourceFactory(name='The Guardian', api_name='guardian'),
        SourceFactory(name='ABC', api_name='newsapi', spanish=True),
        SourceFactory(name='Blog News', api_name='newsapi', low_credibility=True),
        SourceFactory(name='Inactive Source', api_name='newsapi', inactive=True)
    ]
    
    for source in sources:
        db_session.add(source)
    
    db_session.flush()
    return sources


@pytest.fixture
def comprehensive_test_data_fixture(db_session: Session) -> Dict[str, Any]:
    """Fixture completo con todos los datos de prueba"""
    # Crear fuentes
    sources = test_sources_fixture.__wrapped__(db_session)
    
    # Crear usuarios
    users = test_users_fixture.__wrapped__(db_session)
    
    # Crear artículos
    articles = test_articles_fixture.__wrapped__(db_session, sources)
    
    # Crear preferencias para algunos usuarios
    preferences = []
    for user in users[:3]:  # Solo para los primeros 3 usuarios
        if not user.is_superuser:  # No para admin
            pref = UserPreferenceFactory(user=user)
            db_session.add(pref)
            preferences.append(pref)
    
    # Crear marcadores para algunos usuarios
    bookmarks = []
    for user in users[2:5]:  # Para usuarios 2, 3, 4
        for article in articles[:3]:  # Con los primeros 3 artículos
            bookmark = UserBookmarkFactory(
                user=user,
                article=article,
                title=article.title[:100],
                url=article.url
            )
            db_session.add(bookmark)
            bookmarks.append(bookmark)
    
    # Crear análisis para artículos procesados
    analyses = []
    for article in articles:
        if article.processing_status.value == 'completed':
            for analysis_type in ['summary', 'sentiment', 'topics']:
                analysis = ArticleAnalysisFactory(
                    article=article,
                    analysis_type=analysis_type
                )
                db_session.add(analysis)
                analyses.append(analysis)
    
    db_session.flush()
    
    return {
        'users': users,
        'sources': sources,
        'articles': articles,
        'preferences': preferences,
        'bookmarks': bookmarks,
        'analyses': analyses
    }


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def test_data_loader(db_session: Session) -> TestDataLoader:
    """Loader de datos de prueba"""
    return TestDataLoader(db_session)


@pytest.fixture
def mock_api_manager():
    """Gestor de mocks de APIs externas"""
    from tests.factories.mock_external_apis import MockExternalAPIs
    return MockExternalAPIs()


@pytest.fixture
def mock_http_responses():
    """Mock responses para HTTP requests"""
    responses = {
        'newsapi_success': {
            'status': 'ok',
            'totalResults': 38,
            'articles': [
                {
                    'source': {'id': 'bbc-news', 'name': 'BBC News'},
                    'author': 'Test Author',
                    'title': 'Test Article 1',
                    'description': 'Test description',
                    'url': 'https://test.com/article1',
                    'publishedAt': datetime.utcnow().isoformat()
                }
            ]
        },
        'newsapi_error': {
            'status': 'error',
            'code': 'rateLimited',
            'message': 'You have made too many requests recently'
        },
        'guardian_success': {
            'response': {
                'status': 'ok',
                'total': 1234,
                'results': [
                    {
                        'id': 'test-id',
                        'webTitle': 'Guardian Test Article',
                        'webUrl': 'https://test.com/guardian-article',
                        'sectionName': 'News'
                    }
                ]
            }
        }
    }
    return responses


@pytest.fixture
def sample_search_queries():
    """Consultas de búsqueda de ejemplo para testing"""
    return [
        'tecnología',
        'inteligencia artificial',
        'política española',
        'economía',
        'salud pública',
        'cambio climático',
        'deportes',
        'entretenimiento'
    ]


@pytest.fixture
def sample_dates():
    """Fechas de ejemplo para testing"""
    now = datetime.utcnow()
    return {
        'now': now,
        'today': now.date(),
        'yesterday': now.date() - timedelta(days=1),
        'tomorrow': now.date() + timedelta(days=1),
        'last_week': now - timedelta(days=7),
        'last_month': now - timedelta(days=30),
        'custom_date': datetime(2024, 1, 15, 12, 0, 0)
    }


@pytest.fixture
def sample_pagination_data():
    """Datos de paginación de ejemplo"""
    return {
        'current_page': 1,
        'per_page': 20,
        'total_pages': 10,
        'total_items': 200,
        'has_next': True,
        'has_prev': False,
        'next_page': 2,
        'prev_page': None
    }


# =============================================================================
# MOCK AUTHENTICATION FIXTURES
# =============================================================================

@pytest.fixture
def mock_current_user(db_session: Session, sample_user: User) -> User:
    """Mock usuario actual para testing de autenticación"""
    return sample_user


@pytest.fixture
def mock_admin_user(db_session: Session, admin_user: User) -> User:
    """Mock usuario administrador actual"""
    return admin_user


@pytest.fixture
def mock_auth_headers(sample_user: User) -> Dict[str, str]:
    """Headers de autenticación mock para testing"""
    return {
        'Authorization': f'Bearer mock_token_for_user_{sample_user.id}',
        'Content-Type': 'application/json'
    }


# =============================================================================
# PERFORMANCE TESTING FIXTURES
# =============================================================================

@pytest.fixture
def large_article_dataset(db_session: Session, sample_sources: List[Source], large_article_count: int = 100):
    """Dataset grande de artículos para testing de performance"""
    articles = []
    
    for _ in range(large_article_count):
        source = random.choice(sample_sources)
        article = ArticleFactory(source=source, processed=True)
        db_session.add(article)
        articles.append(article)
        
        # Flush cada 20 artículos para evitar problemas de memoria
        if len(articles) % 20 == 0:
            db_session.flush()
    
    db_session.flush()
    return articles


@pytest.fixture
def large_user_dataset(db_session: Session, large_user_count: int = 50) -> List[User]:
    """Dataset grande de usuarios para testing de performance"""
    users = []
    
    for i in range(large_user_count):
        user = UserFactory(
            username=f'user{i}',
            email=f'user{i}@test.com'
        )
        db_session.add(user)
        users.append(user)
        
        # Flush cada 20 usuarios
        if len(users) % 20 == 0:
            db_session.flush()
    
    db_session.flush()
    return users


# =============================================================================
# PARAMETRIZED TEST FIXTURES
# =============================================================================

@pytest.fixture(params=['es', 'en', 'fr'])
def sample_languages(request):
    """Parametrización de idiomas para testing"""
    return request.param


@pytest.fixture(params=['user', 'admin', 'moderator'])
def sample_user_roles(request):
    """Parametrización de roles de usuario"""
    return request.param


@pytest.fixture(params=[
    ('tech_related', 'processed'),
    ('politics_related', 'processed'),
    ('health_related', 'processed'),
    ('sports_related', 'unprocessed')
])
def sample_article_scenarios(request):
    """Parametrización de escenarios de artículos"""
    return request.param


# =============================================================================
# CLEANUP FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data(db_session: Session):
    """Limpieza automática de datos de prueba"""
    yield db_session
    
    # Rollback de cambios no confirmados
    try:
        db_session.rollback()
    except:
        pass


@pytest.fixture(autouse=True)
def reset_sequence_counters():
    """Resetea contadores de secuencias"""
    yield
    
    # Reset Factory counters si es necesario
    try:
        from factory import fuzzy
        fuzzy.FuzzyText._counter = 0
    except:
        pass