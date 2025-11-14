# Guía de Troubleshooting de Tests - AI News Aggregator

## Problemas Comunes y Soluciones

### 🔧 Problemas de Setup y Configuración

#### 1. Dependencies de Testing No Instaladas

**Síntomas:**
```bash
ModuleNotFoundError: No module named 'pytest'
ModuleNotFoundError: No module named 'vitest'
```

**Solución:**
```bash
# Backend
cd backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Frontend  
cd frontend/ai-news-frontend
npm install
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest
```

**Prevención:**
```json
// package.json - Scripts para auto-setup
{
  "scripts": {
    "setup:tests": "pip install -r requirements.txt",
    "test:install": "npm install"
  }
}
```

#### 2. Configuración de Database en Tests

**Síntomas:**
```
sqlalchemy.exc.OperationalError: could not connect to server
psycopg2.OperationalError: could not connect to database
```

**Solución:**
```bash
# Usar Docker para database de testing
docker-compose -f docker-compose.test.yml up -d

# Verificar conexión
psql -h localhost -p 5432 -U postgres -d test_newsaggregator
```

**Configuración en tests:**
```python
# conftest.py
@pytest.fixture(scope="session")
async def test_database():
    """Setup test database"""
    # Create test database
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_newsaggregator"
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()

# Environment variables
DATABASE_URL_TEST = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_newsaggregator"
```

#### 3. Configuración de Redis en Tests

**Síntomas:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Solución:**
```bash
# Iniciar Redis para tests
docker run -d -p 6379:6379 redis:7

# Verificar conexión
redis-cli ping
```

**Configuración:**
```python
# test configuration
REDIS_URL_TEST = "redis://localhost:6379/1"  # Different DB number
```

### 🧪 Problemas con Pytest (Backend)

#### 1. Tests Async No Funcionan

**Síntomas:**
```
RuntimeError: Event loop is closed
```

**Solución:**
```python
# pytest.ini
[tool:pytest]
addopts = 
    --asyncio-mode=auto
    --asyncio-mode=strict

# Test file
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected

# conftest.py
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

#### 2. Tests con Mock No Funcionan

**Síntomas:**
```
AttributeError: 'Mock' object has no attribute 'mock_add_spec'
```

**Solución:**
```python
# ❌ Incorrect
mock_client = Mock()
mock_client.fetch_articles = "some_value"

# ✅ Correct
mock_client = Mock()
mock_client.fetch_articles.return_value = []
mock_client.fetch_articles.side_effect = Exception("Error")

# Para async
mock_client.fetch_articles = AsyncMock(return_value=[])
mock_client.fetch_articles = AsyncMock(side_effect=Exception("Error"))
```

**Patrón correcto:**
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch

@pytest.mark.asyncio
async def test_with_mock():
    with patch('app.services.news_service.NewsAPIClient') as mock_api:
        # Configure mock
        mock_instance = AsyncMock()
        mock_instance.fetch_articles.return_value = [{"title": "Test"}]
        mock_api.return_value = mock_instance
        
        # Test
        service = NewsService(api_client=mock_instance)
        result = await service.fetch_articles("test")
        
        # Assertions
        assert len(result) == 1
        assert result[0]["title"] == "Test"
        mock_instance.fetch_articles.assert_called_once_with("test")
```

#### 3. Tests Lentos o Con Timeouts

**Síntomas:**
```
pytest-timeout: Test timed out after 30.0 seconds
```

**Solución:**
```python
# Configurar timeout
@pytest.mark.timeout(60)  # 1 minute
@pytest.mark.slow  # Mark as slow test
async def test_slow_operation():
    # Test implementation
    pass

# En pytest.ini
[tool:pytest]
timeout = 60
addopts = --timeout=60
markers =
    slow: marks tests as slow
    fast: marks tests as fast
```

**Optimización:**
```python
# Usar fixtures más eficientes
@pytest.fixture
def fast_mock():
    # Return a simple mock instead of complex setup
    return Mock()

# Paralelizar tests
@pytest.mark.parametrize("test_data", test_data_list)
def test_parametrized(test_data):
    # Tests run in parallel
    pass
```

#### 4. Coverage Report Falla

**Síntomas:**
```
coverage.CoverageException: No source for code
```

**Solución:**
```python
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */venv/*
    */migrations/*

[report]
exclude_lines = 
    pragma: no cover
    def __repr__
    if self.debug:
    raise NotImplementedError

# pytest.ini
[tool:pytest]
addopts = 
    --cov=app
    --cov-report=term-missing
    --cov-fail-under=80
```

### ⚛️ Problemas con Vitest (Frontend)

#### 1. Tests de Componentes React Fallan

**Síntomas:**
```
Error: Uncaught [Error: Not implemented: HTMLCanvasElement.getContext("2d")]
```

**Solución:**
```typescript
// src/test/setup.ts
import '@testing-library/jest-dom'

// Mock canvas
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn(),
  putImageData: jest.fn(),
  createImageData: jest.fn(),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  fillText: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  stroke: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  rect: jest.fn(),
  clip: jest.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  observe() { return null }
  disconnect() { return null }
  unobserve() { return null }
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() { return null }
  disconnect() { return null }
  unobserve() { return null }
}

// Mock matchMedia
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
```

#### 2. Hook Testing Con Errores

**Síntomas:**
```
Error: Not supported: could not import a module
```

**Solución:**
```typescript
// ✅ Correct hook testing pattern
import { renderHook, act } from '@testing-library/react';

describe('useCustomHook', () => {
  it('should update state correctly', () => {
    // Arrange
    const { result } = renderHook(() => useCustomHook());
    
    // Act
    act(() => {
      result.current.updateState('new value');
    });
    
    // Assert
    expect(result.current.state).toBe('new value');
  });
});

// ❌ Avoid this pattern
const { result } = renderHook(() => useCustomHook({ dependency: true }));
```

#### 3. Async Tests En Vitest

**Síntomas:**
```
Test has been already finished
```

**Solución:**
```typescript
// ✅ Correct async testing
it('should handle async operation', async () => {
  const { result } = renderHook(() => useAsyncHook());
  
  // Wait for loading to complete
  await waitFor(() => {
    expect(result.current.loading).toBe(false);
  });
  
  expect(result.current.data).toBeDefined();
});

// Using act for async updates
it('should update after async operation', async () => {
  const { result } = renderHook(() => useAsyncHook());
  
  act(async () => {
    await result.current.fetchData();
  });
  
  expect(result.current.data).toBeDefined();
});
```

### 🎭 Problemas con E2E Tests (Playwright)

#### 1. Tests Flaky en E2E

**Síntomas:**
```
Error: Waiting for selector "button": Timeout
```

**Solución:**
```typescript
// Use more robust selectors
await page.getByRole('button', { name: /submit/i }).waitFor();
await page.getByTestId('loading').waitFor({ state: 'hidden' });

// Wait for network to be idle
await page.waitForLoadState('networkidle');

// Add timeouts
await page.waitForSelector('[data-testid="element"]', { 
  timeout: 10000,
  state: 'visible' 
});
```

**Mejores prácticas:**
```typescript
// ✅ Robust E2E test
test('user can complete action', async ({ page }) => {
  await page.goto('/');
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Use test IDs
  await page.getByTestId('search-input').fill('test query');
  await page.getByTestId('search-button').click();
  
  // Wait for results
  await expect(page.getByTestId('search-results')).toBeVisible();
  
  // Take screenshot for debugging
  await page.screenshot({ path: 'test-result.png' });
});
```

#### 2. Manejo de Autenticación en E2E

**Síntomas:**
```
Error: Cannot perform Cookie operation
```

**Solución:**
```typescript
// ✅ Handle authentication properly
test.beforeEach(async ({ page }) => {
  // Login before each test
  await page.goto('/login');
  await page.getByLabel('Email').fill('test@example.com');
  await page.getByLabel('Password').fill('password');
  await page.getByRole('button', { name: 'Login' }).click();
  
  // Wait for redirect
  await page.waitForURL('/dashboard');
});

// Or use storage state
test.use({
  storageState: 'tests/fixtures/auth.json'
});
```

### 🚀 Problemas de Performance

#### 1. Tests Muy Lentos

**Síntomas:**
```
Test execution time: 30+ seconds
```

**Solución:**
```python
# Parallel execution
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers

# Database optimization
@pytest.fixture
async def optimized_db():
    """Use in-memory database for faster tests"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Test implementation
```

```typescript
// Frontend - Parallel tests
// vitest.config.ts
export default defineConfig({
  test: {
    threads: true,  // Enable parallel execution
    maxConcurrency: 4
  }
});
```

#### 2. Memory Leaks en Tests

**Síntomas:**
```
Memory usage keeps increasing
Tests fail with "out of memory"
```

**Solución:**
```python
# Proper cleanup
@pytest.fixture
async def cleanup_test():
    """Ensure cleanup after test"""
    yield
    # Cleanup code
    await some_cleanup_function()

# Use context managers
async with get_database() as db:
    # Test code
    pass  # Automatic cleanup
```

```typescript
// Frontend cleanup
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Reset DOM
document.body.innerHTML = '';
```

### 🐛 Problemas de Debugging

#### 1. Tests Fallan Intermitentemente

**Estrategias de debugging:**
```python
# Add debug output
def test_flaky_functionality():
    print(f"Debug info: {some_variable}")
    
    # Use breakpoints
    import pdb; pdb.set_trace()
    
    # Log state
    logger.info(f"Current state: {some_state}")
    
    assert condition
```

```typescript
// Debug frontend tests
it('should debug state', () => {
  render(<Component />);
  
  // Debug DOM
  screen.debug(); // Prints DOM structure
  
  // Debug specific element
  screen.debug(screen.getByText('content'));
  
  // Debug events
  const user = userEvent.setup({ 
    logger: console,
    advanceTimers: vi.advanceTimersByTime 
  });
});
```

#### 2. Coverage Incorrecta

**Síntomas:**
```
Coverage shows 0% or wrong percentages
```

**Solución:**
```python
# Verify coverage configuration
pytest --cov=app --cov-report=term-missing --cov-verbose

# Exclude problematic files
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    main.py
    settings.py

[report]
skip_covered = false
show_missing = true
```

#### 3. CI/CD Pipeline Fallos

**Problemas comunes:**

1. **Database not available in CI**
```yaml
# Solution in GitHub Actions
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: postgres
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

2. **Node version conflicts**
```yaml
# Solution
- uses: actions/setup-node@v4
  with:
    node-version: '18'
    cache: 'npm'
```

3. **Timeouts en CI**
```yaml
# Increase timeout
- run: pytest tests/ --timeout=300
  timeout-minutes: 10
```

### 🔍 Tools de Debugging

#### 1. Pytest Debugging
```bash
# Verbose output
pytest -v -s

# Drop into debugger on failure
pytest --pdb

# Show local variables
pytest --tb=long

# Capture print statements
pytest -s

# Debug specific test
pytest -k "test_name" -v -s --pdb
```

#### 2. Vitest Debugging
```bash
# Run single test
npm test -- --run component.test.tsx

# Debug mode
npm test -- --inspect-brk

# Verbose output
npm test -- --reporter=verbose

# Update snapshots
npm test -- --update-snapshots
```

#### 3. E2E Debugging
```bash
# Run with browser
npx playwright test --headed

# Debug mode
npx playwright test --debug

# Trace on failure
npx playwright test --trace=on

# Screenshots
npx playwright test --screenshots=on

# Show report
npx playwright show-report
```

### 📊 Monitoreo de Calidad

#### 1. Tracking Test Health
```python
# scripts/test_health_monitor.py
import subprocess
import json
import time
from datetime import datetime

def check_test_health():
    """Monitor test suite health"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_count': 0,
        'failures': 0,
        'duration': 0,
        'coverage': 0
    }
    
    # Run tests and collect metrics
    try:
        result = subprocess.run([
            'pytest', 'tests/', 
            '--tb=no', '--quiet',
            '--json-report', '--json-report-file=test_results.json'
        ], capture_output=True, text=True)
        
        with open('test_results.json', 'r') as f:
            data = json.load(f)
            
        results.update({
            'test_count': data['summary']['total'],
            'failures': data['summary']['failed'],
            'duration': data['summary']['duration'],
            'passed': data['summary']['passed']
        })
        
    except Exception as e:
        results['error'] = str(e)
    
    return results

if __name__ == "__main__":
    health = check_test_health()
    print(json.dumps(health, indent=2))
```

#### 2. Test Performance Monitoring
```python
# Performance tracking
import time
import functools
from typing import Any, Callable

def track_test_performance(func: Callable) -> Callable:
    """Decorator to track test performance"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Log slow tests
        if duration > 5:
            print(f"⚠️  Slow test: {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper

# Usage
@track_test_performance
def test_slow_operation():
    # Test implementation
    pass
```

### 🆘 Patterns de Emergencia

#### 1. Tests Fallan en Producción
```bash
# Skip slow tests in production
pytest -m "not slow" tests/

# Run only critical tests
pytest -m "critical" tests/

# Minimal smoke test
pytest tests/smoke/ -v
```

#### 2. Corrupción de Estado
```python
# Isolate tests completely
@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test"""
    # Rollback transaction
    # Clear cache
    # Reset external services
    yield
    # Cleanup after test

# Fresh state for each test
@pytest.fixture
def fresh_state():
    """Create fresh state for each test"""
    # Return new instance/session
    return create_fresh_state()
```

#### 3. Tests Lentos en CI
```bash
# Parallel execution
pytest -n auto

# Skip integration tests in CI
pytest -m "not integration"

# Use test selection
pytest tests/unit/ --parallel

# Split test suites
pytest tests/ --split 1/3  # First third
pytest tests/ --split 2/3  # Middle third  
pytest tests/ --split 3/3  # Last third
```

### 📋 Checklist de Troubleshooting

#### Cuando tests fallan:

- [ ] **Verificar dependencias**
  - [ ] pip install -r requirements.txt
  - [ ] npm install
  - [ ] Docker services running

- [ ] **Verificar configuración**
  - [ ] pytest.ini configurado
  - [ ] vitest.config.ts correcto
  - [ ] Environment variables set

- [ ] **Verificar base de datos**
  - [ ] Test database existe
  - [ ] Migrations applied
  - [ ] Connection string correcto

- [ ] **Debug step by step**
  - [ ] Run single test
  - [ ] Add debug output
  - [ ] Check logs
  - [ ] Take screenshots

- [ ] **Optimizar performance**
  - [ ] Use fixtures efficiently
  - [ ] Mock external dependencies
  - [ ] Run tests in parallel
  - [ ] Clean up after tests

- [ ] **CI/CD issues**
  - [ ] Check timeouts
  - [ ] Verify resource limits
  - [ ] Check service dependencies
  - [ ] Review logs carefully

---

Esta guía debe consultarse cuando aparezcan problemas en el proceso de testing. Siempre empezar con las soluciones más simples y básicas antes de implementar soluciones más complejas.
