# Tests de Integración - AI News Aggregator

Este directorio contiene los tests de integración para el proyecto AI News Aggregator, verificando la interacción entre diferentes componentes del sistema.

## Archivos de Tests

### 1. test_api_integration.py
**Flujos completos de API**
- Autenticación y autorización
- Operaciones CRUD completas de artículos
- Búsqueda y filtrado de contenido
- Paginación de resultados
- Operaciones en lote (bulk operations)
- Analytics y métricas de API
- Manejo de errores y códigos de estado HTTP
- Content negotiation (JSON/XML)
- Concurrencia de requests
- Health checks (/health, /ready, /live)

### 2. test_database_integration.py
**Operaciones CRUD de Base de Datos**
- Conexión y configuración de BD
- Transacciones y rollback
- Operaciones concurrentes
- CRUD completo para Articles, Sources, Users
- Análisis de artículos y preferencias de usuario
- Optimización de queries y paginación
- Constraints de integridad (FK, unique, check)
- Migraciones y versionado de schema
- Índices y performance

### 3. test_external_api_integration.py
**Integración con APIs Externas**
- **NewsAPI**: Top headlines, búsqueda de artículos, rate limiting
- **The Guardian API**: Búsqueda de contenido, artículos por sección
- **New York Times API**: Búsqueda, artículos populares, libros
- Manejo de errores de APIs externas
- Rate limiting y retry logic
- Normalización de respuestas
- Estrategias de fallback
- Requests concurrentes
- Aggregación multi-API

### 4. test_ai_integration.py
**Integración con IA y Celery**
- **OpenAI API**: Análisis de sentimientos, clasificación de temas, resumenes
- **AIProcessor**: Pipeline completo de análisis de IA
- **AIMonitor**: Monitoreo y métricas de IA
- **Celery Tasks**: Tareas asíncronas para procesamiento de artículos
- Batch processing de artículos
- Cache de resultados de IA
- Timeouts y manejo de errores
- Cost tracking y performance monitoring
- Error recovery y retry mechanisms

### 5. test_cache_integration.py
**Sistema de Cache Redis**
- Operaciones básicas: set, get, delete, exists
- Gestión de TTL y expiración
- Diferentes tipos de datos (strings, JSON, lists, números)
- Namespacing y aislamiento
- Performance y concurrencia
- Integración con AI processing
- Rate limiting con Redis
- Manejo de errores y resiliencia
- Monitoreo y estadísticas

## Configuración de Tests

### Variables de Entorno para Tests
```bash
# Database
TESTING=true
DATABASE_URL=sqlite+aiosqlite:///:memory:

# Redis
REDIS_URL=redis://localhost:6379/15

# External APIs (opcionales para tests reales)
NEWSAPI_KEY=test-newsapi-key
GUARDIAN_API_KEY=test-guardian-key
NYTIMES_API_KEY=test-nytimes-key

# OpenAI
OPENAI_API_KEY=test-openai-key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/15
CELERY_RESULT_BACKEND=redis://localhost:6379/15
```

### Markers de Tests
Los tests utilizan markers de pytest para categorización:

```python
@pytest.mark.integration      # Tests de integración
@pytest.mark.asyncio         # Tests asíncronos
@pytest.mark.database        # Tests que requieren BD
@pytest.mark.external_api    # Tests con APIs externas
@pytest.mark.ai             # Tests de IA
@pytest.mark.celery         # Tests de Celery
@pytest.mark.redis          # Tests de Redis
@pytest.mark.slow           # Tests lentos
```

## Ejecución de Tests

### Ejecutar todos los tests de integración
```bash
# Desde el directorio backend
cd ai-news-aggregator/backend
python -m pytest tests/integration/ -v --tb=short
```

### Ejecutar tests específicos por categoría
```bash
# Solo tests de API
pytest tests/integration/test_api_integration.py -v

# Solo tests de base de datos
pytest tests/integration/test_database_integration.py -v -m database

# Solo tests de APIs externas
pytest tests/integration/test_external_api_integration.py -v -m external_api

# Solo tests de IA
pytest tests/integration/test_ai_integration.py -v -m ai

# Solo tests de cache
pytest tests/integration/test_cache_integration.py -v -m redis
```

### Ejecutar tests con cobertura
```bash
# Instalar coverage si no está disponible
pip install pytest-cov

# Ejecutar con cobertura
pytest tests/integration/ --cov=app --cov-report=html --cov-report=term
```

### Tests con servicios reales
```bash
# Habilitar tests con APIs reales (requiere claves válidas)
ENABLE_API_TESTS=1 pytest tests/integration/test_external_api_integration.py -v

# Tests de integración completa
pytest tests/integration/ -v --run-slow
```

## Fixtures y Configuración

### Fixtures Disponibles
- `test_client`: Cliente HTTP asíncrono para tests de API
- `test_redis`: Cliente Redis para tests de cache
- `test_db_session`: Sesión de BD con rollback automático
- `sample_articles`: Datos de ejemplo de artículos
- `mock_httpx_client`: Cliente HTTP mockeado
- `mock_openai_client`: Cliente OpenAI mockeado

### Limpieza Automática
Los tests incluyen limpieza automática:
- Base de datos: rollback de transacciones
- Redis: limpieza de cache de tests
- APIs mockeadas: reset de estados
- Archivos temporales: eliminación automática

## Patrones de Testing

### 1. Setup-Exercise-Verify
```python
async def test_example(test_client):
    # Setup: preparar datos
    article_data = {"title": "Test", "content": "Content"}
    
    # Exercise: ejecutar operación
    response = await test_client.post("/api/v1/articles/", json=article_data)
    
    # Verify: verificar resultados
    assert response.status_code == 201
    assert response.json()["title"] == "Test"
```

### 2. Test de Integración Completa
```python
async def test_full_workflow(test_client, test_redis, sample_articles):
    # 1. Crear artículos via API
    # 2. Procesar con IA
    # 3. Verificar cache
    # 4. Consultar via API
    # 5. Verificar resultados
    pass
```

### 3. Test de Manejo de Errores
```python
async def test_error_handling(test_client):
    # Test con datos inválidos
    # Test con servicios no disponibles
    # Test de rate limiting
    # Test de timeouts
    pass
```

## Configuración de CI/CD

### GitHub Actions
```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run integration tests
        env:
          REDIS_URL: redis://localhost:6379/15
        run: |
          pytest tests/integration/ -v --tb=short
```

### Docker Compose para Tests
```yaml
version: '3.8'
services:
  redis-test:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --save "" --appendonly no
  
  test-runner:
    build: .
    command: pytest tests/integration/ -v
    environment:
      REDIS_URL: redis://redis-test:6379/15
    depends_on:
      - redis-test
```

## Mejores Prácticas

### 1. Aislamiento de Tests
- Cada test debe ser independiente
- Usar fixtures para setup/teardown
- Mockear dependencias externas
- Base de datos limpia por test

### 2. Datos de Test
- Usar datos realistas pero genéricos
- Evitar datos reales o sensibles
- Fixtures reutilizables
- Seeds para reproducibilidad

### 3. Performance
- Tests paralelos cuando sea posible
- Mock para operaciones lentas
- Timeouts apropiados
- Cleanup eficiente

### 4. Mantenibilidad
- Nombres descriptivos de tests
- Comentarios explicativos
- Estructura modular
- Constants para valores mágicos

## Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión Redis
```bash
# Verificar que Redis esté ejecutándose
redis-cli ping

# Limpiar cache de tests
redis-cli FLUSHDB 15
```

#### 2. Error de Base de Datos
```bash
# Verificar configuración de BD
python -c "from app.db.database import engine; print('DB OK')"
```

#### 3. Tests Lentos
```bash
# Ejecutar solo tests rápidos
pytest tests/integration/ -m "not slow"

# Parallel execution
pip install pytest-xdist
pytest tests/integration/ -n auto
```

#### 4. APIs Externas
```bash
# Tests sin APIs reales (mockeadas)
pytest tests/integration/ -m "not requires_api_key"

# Verificar configuración de APIs
python -c "from app.core.config import settings; print(settings.NEWSAPI_KEY)"
```

## Contribución

Para agregar nuevos tests de integración:

1. Crear archivo `test_[feature]_integration.py`
2. Importar fixtures necesarias de `conftest.py`
3. Usar markers apropiados (`@pytest.mark.integration`)
4. Seguir patrones establecidos
5. Documentar complejidad y dependencias
6. Agregar a CI/CD pipeline

## Métricas de Calidad

- **Coverage objetivo**: >80%
- **Tiempo de ejecución**: <5 minutos
- **Tests paralelos**: Habilitados
- **Services externos**: Mockeados por defecto
- **Deps de CI**: Redis, PostgreSQL (opcional)