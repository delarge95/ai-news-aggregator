# Estrategia de Testing - AI News Aggregator

## Visión General

Esta estrategia define la metodología de testing para el AI News Aggregator, un sistema completo de agregación de noticias con backend Python/FastAPI y frontend React/TypeScript.

## Arquitectura de Testing

### Componentes del Sistema

```
AI News Aggregator
├── Backend (Python/FastAPI)
│   ├── API Endpoints (/users, /articles, /analytics)
│   ├── Servicios (NewsAPI, Guardian, NYTimes)
│   ├── Base de Datos (PostgreSQL)
│   ├── Cache (Redis)
│   ├── Tareas Asíncronas (Celery)
│   └── Sistema de Búsqueda
└── Frontend (React/TypeScript)
    ├── Componentes UI
    ├── Hooks Personalizados
    ├── Servicios API
    └── Estado Global
```

### Filosofía de Testing

1. **Testing en Pirámide**
   - 70% Tests Unitarios
   - 20% Tests de Integración
   - 10% Tests End-to-End

2. **Principios Fundamentales**
   - **Aislamiento**: Cada test es independiente
   - **Confiabilidad**: Tests deterministas sin flakiness
   - **Mantenibilidad**: Fácil comprensión y modificación
   - **Cobertura**: Múltiples niveles de testing

## Tipos de Testing

### 1. Tests Unitarios

#### Backend (Python/pytest)
- **Scope**: Funciones y métodos individuales
- **Mocking**: httpx, SQLAlchemy, Redis, Celery
- **Cobertura mínima**: 80%
- **Ubicación**: `backend/tests/services/`, `backend/tests/unit/`

```python
@pytest.mark.asyncio
async def test_newsapi_client_fetch():
    """Test unitario para cliente NewsAPI"""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_data
        mock_get.return_value = mock_response
        
        client = NewsAPIClient(api_key="test")
        result = await client.fetch_articles(query="tech")
        
        assert len(result) > 0
        assert result[0].title == "Test Article"
```

#### Frontend (Vitest/Jest)
- **Scope**: Componentes React, hooks, utilidades
- **Mocking**: APIs, contextos, hooks
- **Cobertura mínima**: 75%
- **Ubicación**: `frontend/src/__tests__/`, `frontend/ai-news-frontend/src/__tests__/`

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { NewsCard } from '../components/NewsCard';

describe('NewsCard', () => {
  it('should display article title and content', () => {
    const mockArticle = {
      title: 'Test Article',
      content: 'Test content...',
      publishedAt: '2023-01-01T00:00:00Z'
    };
    
    render(<NewsCard article={mockArticle} />);
    
    expect(screen.getByText('Test Article')).toBeInTheDocument();
    expect(screen.getByText('Test content...')).toBeInTheDocument();
  });
});
```

### 2. Tests de Integración

#### Backend API Testing
- **Scope**: Endpoints API completos
- **Database**: PostgreSQL con datos de prueba
- **Cache**: Redis en modo test
- **External APIs**: Mock responses
- **Ubicación**: `backend/tests/integration/`

```python
@pytest.mark.asyncio
async def test_user_registration_flow():
    """Test de integración para registro de usuario"""
    client = TestClient()
    
    # Registro
    response = await client.post("/users/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    
    # Login
    login_response = await client.post("/users/login", json={
        "email": "test@example.com", 
        "password": "password123"
    })
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
```

#### Frontend Integration Testing
- **Scope**: Flujos completos de UI
- **API**: Mock del backend
- **Estado**: Testing de Redux/Context
- **Ubicación**: `frontend/src/integration/`

```typescript
import { renderWithProviders } from '../test-utils';
import { NewsDashboard } from '../components/NewsDashboard';

describe('NewsDashboard Integration', () => {
  it('should load and display articles', async () => {
    const { store } = renderWithProviders(<NewsDashboard />);
    
    // Esperar que se carguen los artículos
    await waitFor(() => {
      expect(store.getState().articles.loading).toBe(false);
    });
    
    expect(screen.getByText('Latest News')).toBeInTheDocument();
  });
});
```

### 3. Tests End-to-End (E2E)

#### Playwright Testing
- **Scope**: Flujos completos de usuario
- **Browsers**: Chrome, Firefox, Safari
- **Ubicación**: `e2e/tests/`

```typescript
import { test, expect } from '@playwright/test';

test('User can search and read articles', async ({ page }) => {
  await page.goto('/');
  
  // Buscar artículos
  await page.fill('[data-testid="search-input"]', 'technology');
  await page.click('[data-testid="search-button"]');
  
  // Verificar resultados
  await expect(page.locator('[data-testid="news-card"]')).toHaveCount.greaterThan(0);
  
  // Abrir artículo
  await page.click('[data-testid="news-card"]:first-child');
  
  // Verificar contenido
  await expect(page.locator('[data-testid="article-content"]')).toBeVisible();
});
```

#### Cypress Testing (Alternativa)
```javascript
describe('News Aggregator E2E', () => {
  it('should load homepage and display latest articles', () => {
    cy.visit('/');
    cy.contains('Latest News');
    cy.get('[data-cy="article-list"]').should('be.visible');
  });
});
```

## Configuración de Testing

### Backend Setup

#### Dependencias (requirements.txt)
```txt
# Testing Framework
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-mock==3.12.0
pytest-cov==4.1.0
pytest-xdist==3.5.0
pytest-html==3.2.0

# Mocking
httpx==0.25.2
responses==0.24.1
factory-boy==3.3.0

# Database Testing
pytest-postgresql==5.0.0
pytest-redis==3.0.0

# Code Quality
black==23.11.0
isort==5.12.0
flake8==6.1.0
mypy==1.7.1
```

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    api: API tests
    database: Database tests
    external: Tests using external services
    async: Async tests
```

#### conftest.py
```python
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncpg

# Database Fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_database():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    yield session

# HTTP Client Fixtures
@pytest.fixture
async def mock_httpx_client():
    """Mock httpx AsyncClient"""
    with patch('httpx.AsyncClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        yield mock_client

# Service Fixtures
@pytest.fixture
def mock_newsapi_client():
    """Mock NewsAPI client"""
    client = Mock()
    client.fetch_articles = AsyncMock(return_value=[])
    return client

@pytest.fixture
def sample_articles():
    """Sample articles for testing"""
    return [
        {
            "id": 1,
            "title": "Test Article 1",
            "content": "Test content 1",
            "published_at": "2023-01-01T00:00:00Z",
            "source": "Test Source"
        },
        {
            "id": 2,
            "title": "Test Article 2",
            "content": "Test content 2", 
            "published_at": "2023-01-02T00:00:00Z",
            "source": "Another Source"
        }
    ]
```

### Frontend Setup

#### package.json Scripts
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:watch": "vitest --watch",
    "test:run": "vitest --run",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "type-check": "tsc --noEmit"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.1.4",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^14.5.1",
    "@types/jest": "^29.5.8",
    "@typescript-eslint/eslint-plugin": "^6.11.0",
    "@typescript-eslint/parser": "^6.11.0",
    "@vitest/ui": "^0.34.6",
    "@vitest/coverage-c8": "^0.33.0",
    "@playwright/test": "^1.40.0",
    "jsdom": "^22.1.0",
    "typescript": "^5.2.2",
    "vite": "^4.4.5",
    "vitest": "^0.34.6"
  }
}
```

#### vitest.config.ts
```typescript
/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'c8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**'
      ]
    },
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
```

#### src/test/setup.ts
```typescript
import '@testing-library/jest-dom'
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe() { return null }
  disconnect() { return null }
  unobserve() { return null }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  observe() { return null }
  disconnect() { return null }
  unobserve() { return null }
}

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Cleanup after each test
afterEach(() => {
  cleanup()
})
```

## Estrategias de Mocking

### External APIs
```python
# backend/tests/mocks/api_responses.py
NEWSAPI_SUCCESS_RESPONSE = {
    "status": "ok",
    "totalResults": 38,
    "articles": [{
        "source": {"id": "techcrunch", "name": "TechCrunch"},
        "author": "John Doe",
        "title": "AI Revolution in Tech",
        "description": "Latest developments in AI technology",
        "url": "https://example.com/article1",
        "urlToImage": "https://example.com/image1.jpg",
        "publishedAt": "2023-11-06T10:00:00Z",
        "content": "Full article content..."
    }]
}
```

### Database Testing
```python
# Usar PostgreSQL en memoria o Docker container
@pytest.fixture(scope="session")
def test_database():
    """Create test database"""
    # Setup logic for test database
    yield test_db
    # Cleanup logic
```

## Métricas y Reportes

### Cobertura de Código

#### Backend (pytest-cov)
```bash
# Ejecutar tests con cobertura
pytest --cov=app --cov-report=html --cov-report=term

# Métricas mínimas requeridas
# - Cobertura general: 80%
# - Nuevas funcionalidades: 90%
# - Core business logic: 95%
```

#### Frontend (vitest --coverage)
```bash
# Tests con cobertura
vitest --coverage

# Reportes HTML en coverage/
open coverage/index.html
```

### Calidad de Tests

#### Static Analysis
```bash
# Backend
flake8 backend/tests/
black --check backend/tests/
isort --check-only backend/tests/
mypy backend/tests/

# Frontend  
npm run lint
npm run type-check
```

#### Test Metrics
- **Test Duration**: < 100ms unit tests, < 2s integration tests
- **Flakiness Rate**: < 1%
- **Mutation Score**: > 70% (optional con Stryker)
- **Test Density**: 1 test per 10 lines of code

## Herramientas de Testing

### Desarrollo
- **pytest**: Framework de testing principal
- **Vitest**: Testing framework para React
- **Testing Library**: Testing utilities para componentes
- **Playwright**: E2E testing
- **MSW**: API mocking para frontend

### CI/CD Integration
- **GitHub Actions**: Pipeline de CI/CD
- **pytest-html**: Reportes HTML
- **Codecov**: Análisis de cobertura
- **SonarCloud**: Calidad de código
- **Percy**: Visual regression testing

### Performance Testing
- **pytest-benchmark**: Benchmarking de rendimiento
- **k6**: Load testing
- **Lighthouse**: Performance auditing
- **Web Vitals**: Core Web Vitals monitoring

## Mejores Prácticas

### Writing Tests
1. **Naming**: `test_[what]_[scenario]_[expected]`
2. **Structure**: Arrange, Act, Assert
3. **Isolation**: Tests independientes y paralelizables
4. **Readability**: Código autoexplicativo con nombres claros

### Mocking Strategy
1. **Mock at boundaries**: APIs externas, base de datos
2. **Test the contract**: Verificar interacciones
3. **Avoid over-mocking**: No mock todo
4. **Keep mocks simple**: Mocks específicos y claros

### Test Data Management
1. **Factories**: Use factory-boy para generar datos
2. **Fixtures**: Reutilizar datos comunes
3. **Seeding**: Datos determinísticos
4. **Cleanup**: Limpieza automática

### Continuous Testing
1. **Pre-commit hooks**: Run tests before commit
2. **Branch protection**: Require tests to pass
3. **Fast feedback**: Tests rápidos en desarrollo
4. **Slow tests**: Ejecutar en CI nocturno

## Escalabilidad y Mantenimiento

### Parallel Execution
```bash
# Backend
pytest -n auto  # Usar todos los CPUs disponibles

# Frontend  
vitest --run --threads  # Tests paralelos
```

### Test Organization
```
tests/
├── unit/           # Tests unitarios
├── integration/    # Tests de integración  
├── e2e/           # Tests end-to-end
├── fixtures/      # Datos y fixtures compartidos
├── mocks/         # Mocks reutilizables
├── helpers/       # Utilidades de testing
└── conftest.py    # Configuración global
```

### Maintenance
1. **Test refactoring**: Limpieza regular de tests
2. **Performance monitoring**: Tiempo de ejecución
3. **Coverage trends**: Seguimiento de cobertura
4. **Documentation**: Documentar casos complejos

## Roadmap de Testing

### Fase 1 (Actual)
- ✅ Setup básico de testing framework
- ✅ Tests unitarios core services
- ✅ Mocking de external APIs
- ✅ Configuración CI básica

### Fase 2 (Próximo)
- 🔄 Tests de integración API
- 🔄 E2E tests con Playwright
- 🔄 Performance testing
- 🔄 Visual regression testing

### Fase 3 (Futuro)
- 📋 Contract testing (Pact)
- 📋 Chaos engineering
- 📋 Property-based testing
- 📋 Security testing
- 📋 Accessibility testing

---

Esta estrategia debe evolucionar con el proyecto, adaptándose a nuevas necesidades y manteniendo siempre la calidad como prioridad absoluta.
