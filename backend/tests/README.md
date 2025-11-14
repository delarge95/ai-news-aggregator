# AI News Aggregator - Comprehensive Test Suite

Este directorio contiene una suite completa de tests unitarios para el backend del AI News Aggregator, implementando mejores prácticas de testing con pytest, coverage, mocking de APIs externas y factory patterns.

## 📋 Contenido de la Suite de Tests

### Archivos Principales

- **`conftest.py`** - Configuración de pytest con fixtures comprehensivas
- **`test_models.py`** - Tests para todos los modelos SQLAlchemy
- **`test_services.py`** - Tests para servicios (news_service, ai_processor, search_service)
- **`test_endpoints.py`** - Tests para todos los endpoints REST
- **`test_utils.py`** - Tests para utilidades y middleware

### Tests de Servicios Existentes

```
tests/services/
├── __init__.py
├── test_newsapi_client.py     # Tests para cliente NewsAPI
├── test_guardian_client.py    # Tests para cliente Guardian
├── test_nytimes_client.py     # Tests para cliente NYTimes
├── test_deduplication.py      # Tests para algoritmos de deduplicación
├── test_rate_limiter.py       # Tests para sistema de rate limiting
├── test_ai_processor.py       # Tests para procesador de IA
├── test_ai_monitor.py         # Tests para monitoreo de IA
└── test_search_service.py     # Tests para servicio de búsqueda
```

## 🚀 Uso Rápido

### Ejecutar Todos los Tests

```bash
# Ejecutar tests completos con coverage usando script principal
./run_comprehensive_tests.sh

# Ejecutar solo tests rápidos (unit tests)
pytest tests/ -m "unit or not slow" -v

# Ejecutar con coverage y report HTML
pytest tests/ --cov=app --cov-report=html:htmlcov --cov-report=term-missing
```

### Ejecutar Categorías Específicas

```bash
# Solo tests unitarios
pytest tests/ -m unit -v

# Tests de integración
pytest tests/ -m integration -v

# Tests de performance
pytest tests/ -m performance -v

# Tests que requieren Redis
pytest tests/ -m redis -v

# Tests que requieren APIs externas
pytest tests/ -m api --enable-api-tests

# Tests de servicios existentes
pytest tests/services/ -v
```

### Ejecutar Tests Específicos

```bash
# Test un archivo específico
pytest tests/test_models.py -v

# Test una clase específica
pytest tests/test_models.py::TestArticleModel -v

# Test un método específico
pytest tests/test_models.py::TestArticleModel::test_article_creation -v

# Tests con patrón
pytest tests/ -k "test_article" -v
```

## 📊 Coverage y Reporting

### Generar Coverage Report

```bash
# Coverage con múltiples formatos
pytest tests/ --cov=app --cov-report=html:htmlcov --cov-report=xml:coverage.xml

# Abrir report HTML
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Reportes Disponibles

- **`htmlcov/index.html`** - Report HTML interactivo
- **`coverage.xml`** - Report XML para CI/CD
- **`coverage.json`** - Report JSON para herramientas
- **`test_reports/report.html`** - Report HTML de pytest

## 🏗️ Arquitectura de Tests

### Test Models (`test_models.py`)

Tests comprehensivos para todos los modelos SQLAlchemy:

- **Source Model** - Creación, relaciones, constraints, rate limiting
- **Article Model** - Validación, duplicados, sentiment analysis, processing status
- **User Model** - Autenticación, roles, constraints únicos
- **UserPreference Model** - Configuraciones JSON, relaciones
- **UserBookmark Model** - Constraints únicos, relaciones
- **TrendingTopic Model** - Metadata, time periods
- **ArticleAnalysis Model** - Cache de análisis, unique constraints
- **AnalysisTask Model** - Estados async, tracking, error handling

### Test Services (`test_services.py`)

Tests para la capa de servicios:

- **NewsService** - Factory pattern, rate limiting, error handling, circuit breaker
- **AIProcessor** - Análisis completo, caching, fallbacks, OpenAI integration
- **SearchService** - Full-text search, semantic search, facets, performance optimization
- **News API Clients** - NewsAPI, Guardian, NYTimes clients with error handling
- **DatabaseOptimizer** - Query optimization, cleanup, statistics
- **AIMonitor** - Performance tracking, alerting, metrics collection

### Test Endpoints (`test_endpoints.py`)

Tests para todos los endpoints REST:

- **Health Endpoints** - Health checks, database status, system metrics
- **News Endpoints** - Latest news, categories, sources, search
- **Articles Endpoints** - CRUD operations, filtering, pagination, sentiment
- **Search Endpoints** - Advanced search, semantic search, suggestions
- **User Endpoints** - Profile, preferences, bookmarks, authentication
- **AI Analysis Endpoints** - Sentiment, topics, summary, bulk analysis
- **Analytics Endpoints** - Dashboard stats, trends, performance, engagement
- **Monitoring Endpoints** - System metrics, error logs, AI processing stats

### Test Utils (`test_utils.py`)

Tests para utilidades:

- **RedisCacheManager** - Cache operations, error handling, connection management
- **RateLimitManager** - Rate limiting, burst limits, time windows, persistence
- **PaginationHelper** - Page calculations, validation, memory efficiency
- **SearchUtils** - Text normalization, keyword extraction, scoring, fuzzy matching
- **TextNormalizer** - Text cleaning, stopwords, stemming, language detection
- **DeduplicationUtils** - Content hashing, similarity detection, grouping
- **ConfigManager** - Config loading, validation, environment override
- **Middleware** - Request logging, security headers, CORS

## 🔧 Fixtures y Factory Patterns

### Database Fixtures

```python
@pytest.fixture
async def async_db_session(async_test_db_engine):
    """Async database session for testing"""
    async_session = sessionmaker(
        async_test_db_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
```

### Factory Patterns

```python
@pytest.fixture
def article_factory():
    """Factory for creating test articles"""
    def _create_article(title="Test Article", content="Test content", **kwargs):
        article = Article(
            title=title,
            content=content,
            processing_status=ProcessingStatus.PENDING,
            **kwargs
        )
        return article
    return _create_article
```

### Mock Services

```python
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    client = Mock()
    client.chat.completions.create = AsyncMock(
        return_value=Mock(choices=[...])
    )
    return client
```

## 📈 Markers y Categorización

### Markers Disponibles

- **`unit`** - Tests unitarios (rápidos, aislados)
- **`integration`** - Tests de integración
- **`performance`** - Tests de performance
- **`slow`** - Tests lentos (excluir por defecto)
- **`redis`** - Tests que requieren Redis
- **`openai`** - Tests que requieren OpenAI API
- **`celery`** - Tests que requieren Celery
- **`api`** - Tests que requieren API keys externas
- **`database`** - Tests que requieren acceso a base de datos
- **`auth`** - Tests de autenticación/autorización

### Uso de Markers

```bash
# Ejecutar solo tests unitarios
pytest -m unit

# Excluir tests lentos
pytest -m "not slow"

# Ejecutar tests de integración o que requieren Redis
pytest -m "integration or redis"

# Ejecutar todos excepto APIs externas
pytest -m "not api"
```

## 🔒 Mocking y Aislamiento

### APIs Externas

```python
# Mock de NewsAPI
with patch('app.services.newsapi_client.httpx.AsyncClient') as mock_client:
    mock_client.get.return_value = Mock(
        status_code=200,
        json.return_value={"articles": [...]}
    )
    # Test logic here
```

### Base de Datos

```python
# Base de datos en memoria para tests
@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
```

### Redis

```python
# Mock de Redis
@pytest.fixture
async def test_redis():
    try:
        # Intentar conexión real a Redis
        redis_client = await redis.from_url("redis://localhost:6379/15")
        yield redis_client
    except:
        # Fallback a mock
        yield Mock(ping=AsyncMock(return_value=True))
```

## 🎯 Validación y Edge Cases

### Validación de Datos

- **Validación de esquemas** con Pydantic
- **Validación de UUIDs** y formatos
- **Validación de rangos** (sentiment scores, bias scores)
- **Validación de enums** (ProcessingStatus, AnalysisTaskStatus)

### Edge Cases

- **Rate limiting** - Manejo de límites de API
- **Timeout handling** - Timeouts en operaciones async
- **Error recovery** - Recuperación de errores de red
- **Resource cleanup** - Limpieza de recursos
- **Memory management** - Gestión de memoria en tests largos

## 🚀 Performance Testing

### Benchmarks

```python
@pytest.mark.performance
def test_search_performance(large_dataset):
    start_time = time.time()
    results = search_service.advanced_search("query", large_dataset)
    execution_time = time.time() - start_time
    
    assert execution_time < 5.0  # Should complete within 5 seconds
```

### Memory Profiling

```python
@pytest.fixture
def memory_profiler():
    import tracemalloc
    
    @contextmanager
    def profile_memory():
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        yield
        
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        for stat in top_stats[:10]:
            print(stat)
        
        tracemalloc.stop()
    
    return profile_memory
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests with coverage
        run: |
          ./run_comprehensive_tests.sh
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 🛠️ Troubleshooting

### Problemas Comunes

#### Tests fallan por dependencias externas

```bash
# Ejecutar solo tests que no requieren servicios externos
pytest tests/ -m "not (redis or openai or api)"
```

#### Coverage bajo el objetivo

```bash
# Verificar cobertura por módulo
coverage report --show-missing

# Generar reporte HTML para análisis
coverage html
```

#### Tests lentos

```bash
# Ejecutar en paralelo
pytest tests/ -n auto

# Excluir tests lentos
pytest tests/ -m "not slow"
```

#### Problemas de base de datos

```bash
# Verificar configuración de base de datos
export DATABASE_URL="sqlite+aiosqlite:///:memory:"

# Limpiar cache de tests
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +
```

## 📚 Documentación Adicional

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session.html)

## 🤝 Contribuir

Para agregar nuevos tests:

1. Seguir la estructura existente
2. Usar fixtures apropiadas
3. Mock servicios externos
4. Agregar coverage
5. Documentar edge cases

---

**¡Suite de Tests Completa para AI News Aggregator!** 🎯✅