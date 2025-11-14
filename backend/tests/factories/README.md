# Test Data Factories System

Sistema completo de factories y fixtures para testing del AI News Aggregator.

## 📋 Descripción

Este sistema proporciona una manera consistente y reutilizable de generar datos de prueba para todos los componentes del sistema AI News Aggregator. Incluye:

- **Factories**: Generadores de datos para modelos de base de datos
- **Fixtures**: Datos preconfigurados para pytest
- **Mock APIs**: Simulación de APIs externas
- **Data Loaders**: Carga sistemática de datasets de prueba
- **Ejemplos**: Casos de uso y patrones de testing

## 🏗️ Estructura

```
tests/factories/
├── __init__.py              # Exports principales
├── article_factory.py       # Factories para artículos
├── user_factory.py          # Factories para usuarios
├── source_factory.py        # Factories para fuentes
├── analysis_factory.py      # Factories para análisis IA
├── test_data_loader.py      # Loader de datos de prueba
├── mock_external_apis.py    # Mock APIs externas
├── fixtures.py              # Pytest fixtures
├── examples.py              # Ejemplos de uso
└── README.md               # Esta documentación
```

## 🚀 Uso Básico

### 1. Crear datos individuales

```python
from tests.factories import ArticleFactory, UserFactory, SourceFactory

# Crear usuario
user = UserFactory()
db_session.add(user)
db_session.flush()

# Crear fuente
source = SourceFactory(spanish=True)  # Fuente española
db_session.add(source)
db_session.flush()

# Crear artículo
article = ArticleFactory(
    source=source,
    processed=True,
    tech_related=True
)
db_session.add(article)
db_session.flush()
```

### 2. Usar fixtures de pytest

```python
def test_article_creation(sample_article, admin_user):
    assert sample_article.id is not None
    assert sample_article.source is not None
    assert admin_user.is_superuser is True

def test_user_preferences(user_with_preferences):
    user = user_with_preferences
    assert user.preferences is not None
    assert len(user.preferences.preferred_topics) > 0
```

### 3. Crear datasets completos

```python
from tests.factories import TestDataLoader

def test_with_complete_data(db_session):
    loader = TestDataLoader(db_session)
    
    # Cargar datos básicos
    result = loader.load_basic_data(
        num_users=10,
        num_sources=5,
        num_articles_per_source=3
    )
    
    assert result['users_count'] == 10
    assert result['articles_count'] == 15
```

### 4. Mock de APIs externas

```python
from tests.factories import MockAPIContext

def test_with_external_api():
    with MockAPIContext(['newsapi']) as mock_manager:
        # Tu código que usa NewsAPI
        newsapi = mock_manager.get_api('newsapi')
        response = newsapi.get_top_headlines(country='es')
        
        assert response.success
        assert response.status_code == 200
```

## 📊 Models Soportados

### User
- `UserFactory`: Usuario básico
- `UserFactory(admin=True)`: Usuario administrador
- `UserFactory(moderator=True)`: Usuario moderador
- `UserFactory(inactive=True)`: Usuario inactivo

### UserPreference
- `UserPreferenceFactory`: Preferencias con valores por defecto
- `UserPreferenceFactory(strict_preferences=True)`: Preferencias estrictas
- `UserPreferenceFactory(positive_only=True)`: Solo noticias positivas

### UserBookmark
- `UserBookmarkFactory`: Marcador básico
- `UserBookmarkFactory(with_notes=True)`: Con notas
- `UserBookmarkFactory(with_tags=True)`: Con tags

### Source
- `SourceFactory`: Fuente básica
- `SourceFactory(spanish=True)`: Fuente española
- `SourceFactory(highly_credible=True)`: Alta credibilidad
- `SourceFactory(tech_focused=True)`: Enfoque tecnológico

### Article
- `ArticleFactory`: Artículo básico
- `ArticleFactory(processed=True)`: Procesado por IA
- `ArticleFactory(unprocessed=True)`: Sin procesar
- `ArticleFactory(tech_related=True)`: Sobre tecnología
- `ArticleFactory(positive_sentiment=True)`: Sentimiento positivo

### ArticleAnalysis
- `ArticleAnalysisFactory`: Análisis básico
- `ArticleAnalysisFactory(analysis_type='sentiment')`: Análisis de sentimiento
- `ArticleAnalysisFactory(high_confidence=True)`: Alta confianza

### AnalysisTask
- `AnalysisTaskFactory`: Tarea básica
- `AnalysisTaskFactory(pending=True)`: Tarea pendiente
- `AnalysisTaskFactory(completed=True)`: Tarea completada
- `AnalysisTaskFactory(failed=True)`: Tarea fallida

## 🔧 Features Avanzadas

### Context Managers

```python
# Datos de prueba con cleanup automático
with TestDataContext(db_session, data_level='advanced') as test_data:
    # Usar datos de prueba
    assert test_data['articles_count'] > 0
# Los datos se limpian automáticamente

# Mock de APIs con cleanup automático
with MockAPIContext(['newsapi', 'guardian']):
    # APIs están mockeadas
    pass
# Los mocks se desactivan automáticamente
```

### Factories de Conjuntos

```python
from tests.factories import UserSetFactory, SourceSetFactory, AnalysisSetFactory

# Crear conjunto de usuarios balanceado
users = UserSetFactory.create_user_set(
    normal_users=5,
    admins=1,
    moderators=2,
    inactive_users=1
)

# Crear conjunto de fuentes balanceado
sources = SourceSetFactory.create_news_source_set(
    high_credibility=3,
    medium_credibility=4,
    low_credibility=2,
    inactive=1,
    include_spanish=True,
    include_english=True
)

# Crear análisis completo para artículo
analyses = AnalysisSetFactory.create_complete_article_analysis(article)
```

### Loading de Datos Complejo

```python
def test_advanced_scenario(db_session):
    loader = TestDataLoader(db_session)
    
    # Cargar datos avanzados
    result = loader.load_advanced_test_data()
    
    # Cargar artículos duplicados
    source = loader.loaded_data['sources'][0]
    duplicates = loader.create_duplicate_articles(source, num_duplicates=3)
    
    # Verificar datos cargados
    summary = loader.get_data_summary()
    assert summary['users'] > 0
    assert summary['articles'] > 0
    assert summary['analysis_results'] > 0
```

## 🧪 Testing Patterns

### Unit Testing
```python
def test_user_factory():
    user = UserFactory()
    assert user.id is not None
    assert user.username is not None
    assert user.email is not None
    assert user.hashed_password is not None
```

### Integration Testing
```python
def test_user_article_relationship(db_session, sample_user, sample_articles):
    # Crear marcador
    bookmark = UserBookmarkFactory(user=sample_user, article=sample_articles[0])
    db_session.add(bookmark)
    db_session.flush()
    
    # Verificar relación
    assert bookmark.user == sample_user
    assert bookmark.article == sample_articles[0]
```

### Performance Testing
```python
def test_bulk_creation_performance(db_session, sample_sources):
    import time
    
    start_time = time.time()
    
    # Crear muchos artículos
    articles = ArticleFactory.create_batch(100, source=sample_sources[0])
    db_session.add_all(articles)
    db_session.flush()
    
    creation_time = time.time() - start_time
    assert creation_time < 5.0  # Debe crear 100 artículos en menos de 5 segundos
```

### Parametrized Testing
```python
@pytest.mark.parametrize("article_trait,expected_processed", [
    ("processed", True),
    ("unprocessed", False),
    ("failed", True)
])
def test_article_states(db_session, sample_source, article_trait, expected_processed):
    article = ArticleFactory(source=sample_source, **{article_trait: True})
    db_session.add(article)
    db_session.flush()
    
    if expected_processed:
        assert article.processed_at is not None
    else:
        assert article.processed_at is None
```

## 🔄 Utilities

### Limpieza de Datos
```python
from tests.factories import cleanup_test_data

def cleanup_after_test(db_session):
    cleanup_test_data(db_session)
    # Todos los datos de prueba son eliminados
```

### Funciones de Conveniencia
```python
from tests.factories import quick_test_data, comprehensive_test_data

# Testing rápido
quick_data = quick_test_data(db_session)

# Testing exhaustivo
comprehensive_data = comprehensive_test_data(db_session)
```

### Exportar Datos de Prueba
```python
def test_export_test_data(db_session):
    loader = TestDataLoader(db_session)
    loader.load_basic_data(num_users=5, num_sources=3)
    
    # Exportar a JSON
    loader.export_test_data('test_data_export.json')
```

## 🏃‍♂️ Running Tests

### Ejecutar todos los tests
```bash
cd ai-news-aggregator/backend
pytest tests/ -v
```

### Ejecutar tests específicos de factories
```bash
pytest tests/factories/ -v
```

### Ejecutar tests con coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Ejecutar tests de performance
```bash
pytest tests/ -m "performance" -v
```

## 🔍 Debugging

### Verificar datos generados
```python
def debug_generated_data(db_session):
    user = UserFactory()
    print(f"User ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Role: {user.role}")
    
    source = SourceFactory()
    print(f"Source ID: {source.id}")
    print(f"Source Name: {source.name}")
    print(f"Source Credibility: {source.credibility_score}")
```

### Logging de factories
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Esto mostrará detalles de la generación de datos
user = UserFactory()
article = ArticleFactory()
```

## 📚 Ejemplos Completos

Ver el archivo `examples.py` para ejemplos detallados de todos los patrones de uso, incluyendo:

- Testing básico de cada modelo
- Testing de relaciones entre modelos
- Testing de servicios con datos de prueba
- Testing de rendimiento
- Testing de integración
- Testing parametrizado

## 🎯 Best Practices

1. **Usar fixtures para datos comunes**: Los fixtures proporcionan datos preconfigurados y consistentes
2. **Limpiar datos después de tests**: Usar cleanup automático o manual
3. **Usar traits para características específicas**: Los traits permiten crear datos con propiedades específicas
4. **Mockear APIs externas**: Siempre usar MockAPIContext para APIs externas
5. **Usar context managers para limpieza automática**: TestDataContext maneja cleanup automáticamente
6. **Parametrizar tests para cobertura**: Usar parámetros para probar diferentes escenarios
7. **Documentar factories complejas**: Añadir docstrings para factories especializadas

## 🛠️ Extensión

Para añadir nuevas factories:

1. Crear factory en el archivo apropiado
2. Añadir traits según sea necesario
3. Actualizar `__init__.py` con exports
4. Añadir fixtures relacionadas en `fixtures.py`
5. Documentar en `examples.py`

## 📞 Soporte

Para preguntas o problemas con el sistema de factories:

1. Revisar `examples.py` para patrones de uso
2. Verificar la documentación de factory-boy
3. Consultar los tests existentes para ejemplos
4. Revisar los logs de generación para debugging