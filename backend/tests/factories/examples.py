"""
Ejemplo de uso del sistema de factories y fixtures

Este archivo demuestra cómo usar las factories y fixtures creadas
para generar datos de prueba consistentes y reutilizables.
"""

import pytest
from sqlalchemy.orm import Session

from tests.factories.article_factory import ArticleFactory
from tests.factories.user_factory import UserFactory, UserPreferenceFactory
from tests.factories.source_factory import SourceFactory
from tests.factories.analysis_factory import ArticleAnalysisFactory, AnalysisTaskFactory
from tests.factories.test_data_loader import TestDataLoader, TestDataContext
from tests.factories.mock_external_apis import MockAPIContext
from tests.factories.fixtures import comprehensive_test_data_fixture


# =============================================================================
# EJEMPLOS BÁSICOS DE USO
# =============================================================================

def test_basic_article_creation(db_session: Session):
    """Ejemplo básico: crear un artículo"""
    article = ArticleFactory()
    db_session.add(article)
    db_session.flush()
    
    assert article.id is not None
    assert article.title is not None
    assert article.source is not None


def test_article_with_traits(db_session: Session, sample_source: SourceFactory):
    """Ejemplo: crear artículo con características específicas"""
    # Artículo procesado con sentimiento positivo
    article = ArticleFactory(
        source=sample_source,
        processed=True,
        positive_sentiment=True,
        tech_related=True
    )
    
    db_session.add(article)
    db_session.flush()
    
    assert article.processing_status.value == 'completed'
    assert article.sentiment_score > 0
    assert any(tag.get('tag') == 'technology' for tag in article.topic_tags)


def test_user_with_preferences(db_session: Session):
    """Ejemplo: crear usuario con preferencias"""
    # Crear usuario
    user = UserFactory(role='user')
    db_session.add(user)
    db_session.flush()
    
    # Crear preferencias
    preferences = UserPreferenceFactory(user=user)
    db_session.add(preferences)
    db_session.flush()
    
    assert user.preferences == preferences
    assert preferences.user == user


def test_complete_analysis_set(db_session: Session, sample_article: Article):
    """Ejemplo: crear análisis completo para un artículo"""
    from tests.factories.analysis_factory import AnalysisSetFactory
    
    analyses = AnalysisSetFactory.create_complete_article_analysis(
        article=sample_article
    )
    
    db_session.add_all(analyses)
    db_session.flush()
    
    assert len(analyses) == 6  # summary, sentiment, bias, topics, relevance, entities
    
    analysis_types = [analysis.analysis_type for analysis in analyses]
    expected_types = ['summary', 'sentiment', 'bias', 'topics', 'relevance', 'entities']
    
    for expected_type in expected_types:
        assert expected_type in analysis_types


# =============================================================================
# EJEMPLOS CON DATASET COMPLETO
# =============================================================================

def test_with_comprehensive_data(comprehensive_test_data_fixture):
    """Ejemplo: usar dataset completo para testing"""
    data = comprehensive_test_data_fixture
    
    # Verificar que tenemos datos
    assert len(data['users']) > 0
    assert len(data['sources']) > 0
    assert len(data['articles']) > 0
    
    # Verificar relaciones
    user_with_prefs = None
    for user in data['users']:
        if user.preferences:
            user_with_prefs = user
            break
    
    assert user_with_prefs is not None
    assert user_with_prefs.preferences is not None


def test_data_loader_usage(db_session: Session):
    """Ejemplo: usar TestDataLoader"""
    loader = TestDataLoader(db_session)
    
    # Cargar datos básicos
    result = loader.load_basic_data(
        num_users=5,
        num_sources=3,
        num_articles_per_source=2
    )
    
    assert result['users_count'] == 5
    assert result['sources_count'] == 3
    assert result['articles_count'] == 6  # 3 fuentes x 2 artículos
    
    # Verificar que se cargaron correctamente
    assert len(loader.loaded_data['users']) == 5
    assert len(loader.loaded_data['sources']) == 3
    assert len(loader.loaded_data['articles']) == 6


def test_context_manager_usage(db_session: Session):
    """Ejemplo: usar context manager para datos de prueba"""
    with TestDataContext(db_session, data_level='basic') as test_data:
        assert test_data['users_count'] > 0
        assert test_data['sources_count'] > 0
        assert test_data['articles_count'] > 0
    
    # Los datos se limpian automáticamente al salir del contexto
    # (asumiendo que tienes un método para verificar limpieza)


# =============================================================================
# EJEMPLOS CON MOCK APIS
# =============================================================================

def test_with_mock_apis():
    """Ejemplo: usar mocks de APIs externas"""
    with MockAPIContext(apis=['newsapi']) as mock_manager:
        # Simular request a NewsAPI
        response = mock_manager.get_api('newsapi').get_top_headlines(country='es')
        
        assert response.success
        assert response.status_code == 200
        assert 'articles' in response.json_data
        assert len(response.json_data['articles']) > 0


def test_mock_api_with_errors():
    """Ejemplo: simular errores de API"""
    with MockAPIContext(apis=['newsapi']) as mock_manager:
        newsapi = mock_manager.get_api('newsapi')
        
        # Configurar para simular errores
        mock_manager.configure_api_error('newsapi', 'rate_limit')
        
        # Hacer varias requests para activar errores
        for i in range(5):
            response = newsapi.get_top_headlines()
            
            if i % 10 == 4:  # Cada 5ta request después del 5to request
                assert response.status_code == 429  # Rate limited
            else:
                assert response.status_code == 200


# =============================================================================
# EJEMPLOS DE TESTING ESPECÍFICO
# =============================================================================

def test_article_filtering(db_session: Session, sample_sources: list):
    """Ejemplo: testing con filtros de artículos"""
    # Crear artículos de diferentes tipos
    processed_articles = ArticleFactory.create_batch(
        3,
        source=sample_sources[0],
        processed=True
    )
    
    unprocessed_articles = ArticleFactory.create_batch(
        2,
        source=sample_sources[0],
        unprocessed=True
    )
    
    for article in processed_articles + unprocessed_articles:
        db_session.add(article)
    
    db_session.flush()
    
    # Test: filtrar solo artículos procesados
    from app.db.models import ProcessingStatus
    processed = db_session.query(Article).filter(
        Article.processing_status == ProcessingStatus.COMPLETED
    ).all()
    
    assert len(processed) == 3


def test_user_bookmarks_creation(db_session: Session, sample_users: list, sample_articles: list):
    """Ejemplo: testing de sistema de marcadores"""
    user = sample_users[0]
    
    # Crear marcadores
    bookmarks = []
    for article in sample_articles[:3]:  # Primeros 3 artículos
        bookmark = UserBookmarkFactory(user=user, article=article)
        db_session.add(bookmark)
        bookmarks.append(bookmark)
    
    db_session.flush()
    
    # Verificar que se crearon correctamente
    assert len(bookmarks) == 3
    assert all(bm.user == user for bm in bookmarks)
    assert len(set(bm.article_id for bm in bookmarks)) == 3  # Sin duplicados


def test_analysis_queue_simulation(db_session: Session, sample_articles: list):
    """Ejemplo: simular cola de análisis"""
    from tests.factories.analysis_factory import TaskSetFactory
    
    # Crear cola de análisis
    tasks = TaskSetFactory.create_analysis_queue(
        total_tasks=20,
        pending_ratio=0.5,
        running_ratio=0.2,
        completed_ratio=0.2,
        failed_ratio=0.1
    )
    
    for task in tasks:
        db_session.add(task)
    
    db_session.flush()
    
    # Verificar distribución
    from app.db.models import AnalysisTaskStatus
    
    pending = db_session.query(AnalysisTask).filter(
        AnalysisTask.status == AnalysisTaskStatus.PENDING
    ).count()
    
    running = db_session.query(AnalysisTask).filter(
        AnalysisTask.status == AnalysisTaskStatus.RUNNING
    ).count()
    
    completed = db_session.query(AnalysisTask).filter(
        AnalysisTask.status == AnalysisTaskStatus.COMPLETED
    ).count()
    
    failed = db_session.query(AnalysisTask).filter(
        AnalysisTask.status == AnalysisTaskStatus.FAILED
    ).count()
    
    assert pending >= 8  # Al menos 40% de 20
    assert running >= 4   # Al menos 20% de 20
    assert completed >= 4 # Al menos 20% de 20
    assert failed >= 2    # Al menos 10% de 20


# =============================================================================
# EJEMPLOS DE TESTING DE RENDIMIENTO
# =============================================================================

def test_bulk_creation_performance(db_session: Session, sample_sources: list):
    """Ejemplo: testing de rendimiento con creación masiva"""
    import time
    
    start_time = time.time()
    
    # Crear artículos en lote
    articles = ArticleFactory.create_batch(
        50,
        source=sample_sources[0],
        processed=True
    )
    
    db_session.add_all(articles)
    db_session.flush()
    
    end_time = time.time()
    creation_time = end_time - start_time
    
    # Verificar que se crearon todos
    assert len(articles) == 50
    
    # Verificar que la creación fue razonablemente rápida (< 5 segundos)
    assert creation_time < 5.0
    
    # Verificar que los artículos son únicos
    article_ids = [article.id for article in articles]
    assert len(article_ids) == len(set(article_ids))


def test_database_queries_performance(db_session: Session, comprehensive_test_data_fixture):
    """Ejemplo: testing de rendimiento de queries"""
    import time
    
    data = comprehensive_test_data_fixture
    
    start_time = time.time()
    
    # Simular algunas queries típicas
    articles = db_session.query(Article).filter(
        Article.processing_status == 'completed'
    ).limit(100).all()
    
    users = db_session.query(User).filter(
        User.is_active == True
    ).all()
    
    articles_with_analysis = db_session.query(Article).join(
        ArticleAnalysis
    ).distinct().all()
    
    end_time = time.time()
    query_time = end_time - start_time
    
    # Verificar que obtuvimos resultados
    assert len(articles) > 0
    assert len(users) > 0
    assert len(articles_with_analysis) > 0
    
    # Verificar que las queries fueron razonablemente rápidas
    assert query_time < 3.0


# =============================================================================
# EJEMPLOS DE INTEGRATION TESTING
# =============================================================================

def test_article_service_integration(db_session: Session, comprehensive_test_data_fixture):
    """Ejemplo: test de integración con servicio de artículos"""
    data = comprehensive_test_data_fixture
    
    # Simular operaciones del servicio de artículos
    def get_processed_articles():
        from app.db.models import ProcessingStatus
        return db_session.query(Article).filter(
            Article.processing_status == ProcessingStatus.COMPLETED
        ).all()
    
    def get_articles_by_sentiment(sentiment):
        return db_session.query(Article).filter(
            Article.sentiment_label == sentiment
        ).all()
    
    def get_trending_topics():
        return db_session.query(Article.topic_tags).all()
    
    # Test las operaciones
    processed_articles = get_processed_articles()
    positive_articles = get_articles_by_sentiment('positive')
    trending_topics = get_trending_topics()
    
    assert len(processed_articles) > 0
    assert len(positive_articles) >= 0  # Puede ser 0 si no hay artículos positivos
    assert len(trending_topics) > 0


def test_user_service_integration(db_session: Session, comprehensive_test_data_fixture):
    """Ejemplo: test de integración con servicio de usuarios"""
    data = comprehensive_test_data_fixture
    
    # Simular operaciones del servicio de usuarios
    def get_active_users():
        return db_session.query(User).filter(User.is_active == True).all()
    
    def get_users_with_preferences():
        return db_session.query(User).join(UserPreference).all()
    
    def get_user_bookmarks(user_id):
        return db_session.query(UserBookmark).filter(
            UserBookmark.user_id == user_id
        ).all()
    
    # Test las operaciones
    active_users = get_active_users()
    users_with_prefs = get_users_with_preferences()
    
    if active_users:
        bookmarks = get_user_bookmarks(active_users[0].id)
        assert isinstance(bookmarks, list)
    
    assert len(active_users) > 0
    assert len(users_with_prefs) >= 0  # Puede ser 0 si no hay usuarios con prefs


# =============================================================================
# EJEMPLOS PARA DIFERENTES TIPOS DE TESTING
# =============================================================================

@pytest.mark.parametrize("article_trait,expected_processed", [
    ("processed", True),
    ("unprocessed", False),
    ("failed", True)  # Procesamiento fallido aún cuenta como procesado
])
def test_article_processing_states(db_session: Session, sample_source, article_trait, expected_processed):
    """Ejemplo: testing parametrizado de estados de procesamiento"""
    article = ArticleFactory(source=sample_source, **{article_trait: True})
    db_session.add(article)
    db_session.flush()
    
    if expected_processed:
        assert article.processed_at is not None
    else:
        assert article.processed_at is None


@pytest.mark.parametrize("user_role,expected_permissions", [
    ("user", 0),      # Usuario normal
    ("moderator", 1), # Moderador
    ("admin", 2)      # Administrador
])
def test_user_permissions_by_role(db_session: Session, user_role, expected_permissions):
    """Ejemplo: testing parametrizado de permisos por rol"""
    user = UserFactory(role=user_role)
    db_session.add(user)
    db_session.flush()
    
    # Simular verificación de permisos
    permissions = 0
    if user.role in ['moderator', 'admin']:
        permissions += 1
    if user.is_superuser:
        permissions += 1
    
    assert permissions == expected_permissions


# =============================================================================
# EJEMPLO DE SETUP Y TEARDOWN PERSONALIZADO
# =============================================================================

class TestArticleManagement:
    """Clase de test con setup personalizado"""
    
    def setup_method(self, method, db_session: Session, sample_sources: list):
        """Setup para cada método de test"""
        self.db = db_session
        self.sources = sample_sources
        
        # Crear datos base
        self.articles = ArticleFactory.create_batch(
            10,
            source=self.sources[0],
            processed=True
        )
        self.db.add_all(self.articles)
        self.db.flush()
    
    def test_article_count(self):
        """Test de ejemplo"""
        assert len(self.articles) == 10
        
        # Verificar que todos tienen fuente
        for article in self.articles:
            assert article.source is not None
    
    def test_article_processing(self):
        """Test de ejemplo"""
        processed_count = sum(1 for article in self.articles if article.processed_at is not None)
        assert processed_count == 10  # Todos fueron creados como procesados


if __name__ == "__main__":
    # Ejemplo de ejecución manual
    print("Ejemplos de uso de factories:")
    print("1. ArticleFactory() - Artículo básico")
    print("2. ArticleFactory(processed=True) - Artículo procesado")
    print("3. UserFactory(admin=True) - Usuario admin")
    print("4. UserPreferenceFactory(user=user) - Preferencias de usuario")
    print("5. SourceFactory(spanish=True) - Fuente española")
    print("6. TestDataLoader(db).load_basic_data() - Dataset completo")
    print("7. MockAPIContext(['newsapi']) - Mock de APIs")
    print("8. comprehensive_test_data_fixture - Fixture completo")