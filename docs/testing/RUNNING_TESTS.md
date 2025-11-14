# Guía de Ejecución de Tests - AI News Aggregator

## Comandos Básicos

### Backend (Python/FastAPI)

#### Tests Unitarios
```bash
# Ejecutar todos los tests unitarios
cd backend
pytest tests/ -v

# Ejecutar tests con coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Ejecutar tests específicos por módulo
pytest tests/services/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v

# Tests en paralelo (usar todos los CPUs)
pytest tests/ -n auto

# Ejecutar tests con marcadores específicos
pytest -m unit -v                    # Solo tests unitarios
pytest -m "not slow" -v             # Excluir tests lentos
pytest -m api -v                    # Solo tests de API
pytest -m integration -v            # Solo tests de integración
```

#### Tests de Servicios Específicos
```bash
# Cliente NewsAPI
pytest tests/services/test_newsapi_client.py -v

# Cliente Guardian
pytest tests/services/test_guardian_client.py -v

# Cliente NYTimes  
pytest tests/services/test_nytimes_client.py -v

# Sistema de deduplicación
pytest tests/services/test_deduplication.py -v

# Rate limiting
pytest tests/services/test_rate_limiter.py -v

# Endpoints de usuarios
pytest tests/test_users_endpoints.py -v

# Sistema de paginación
pytest tests/test_pagination.py -v
```

#### Tests con Configuraciones Específicas
```bash
# Tests asíncronos
pytest tests/ -v --asyncio-mode=auto

# Tests con output detallado
pytest tests/ -v -s --tb=long

# Tests con filtro por nombre
pytest -k "test_newsapi" -v
pytest -k "deduplication" -v
pytest -k "user_registration" -v

# Tests con timeout
pytest tests/ --timeout=30

# Tests con debugging
pytest tests/ --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

#### Scripts Personalizados
```bash
# Usar script existente de tests
./backend/run_tests.sh

# Tests con Celery
./backend/start_celery.sh &
pytest tests/services/test_celery_tasks.py -v
```

### Frontend (React/TypeScript)

#### Tests con Vitest
```bash
cd frontend/ai-news-frontend

# Ejecutar todos los tests
npm test
# o
pnpm test
# o
yarn test

# Tests en modo watch (desarrollo)
npm test -- --watch
# o
pnpm test --watch

# Tests con coverage
npm test -- --coverage
# o
pnpm test --coverage

# Tests con UI
npm test -- --ui
# o
pnpm test -- --ui

# Ejecutar tests una vez (CI)
npm test -- --run
# o
pnpm test -- --run
```

#### Tests de Componentes Específicos
```bash
# Tests de componentes
npm test components/NewsCard.test.tsx
npm test components/Navigation.test.tsx

# Tests de hooks
npm test hooks/useNewsSearch.test.ts
npm test hooks/usePagination.test.ts

# Tests de utilidades
npm test utils/api.test.ts
npm test utils/dateHelpers.test.ts

# Tests de servicios
npm test services/newsApi.test.ts
```

#### Configuraciones Específicas
```bash
# Tests con reporter específico
npm test -- --reporter=verbose
npm test -- --reporter=json --outputFile=test-results.json

# Tests con environment específico
npm test -- --env=test

# Tests con máximo workers
npm test -- --workers=4

# Tests con timeout
npm test -- --testTimeout=10000
```

### End-to-End Testing

#### Playwright
```bash
# Instalar Playwright (primera vez)
cd frontend/ai-news-frontend
npx playwright install

# Ejecutar todos los E2E tests
npm run test:e2e
# o
npx playwright test

# E2E tests en modo UI (interactivo)
npm run test:e2e:ui
# o
npx playwright test --ui

# E2E tests en browser específico
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# E2E tests en modo headed (con browser visible)
npx playwright test --headed

# E2E tests con debug
npx playwright test --debug

# E2E tests específicos
npx playwright test tests/homepage.spec.ts
npx playwright test tests/user-flow.spec.ts
```

#### Cypress (Alternativa)
```bash
# Si usas Cypress
npm run cypress:open
npm run cypress:run

# Ejecutar todos los tests
npm run cypress:run --spec "cypress/e2e/**/*.cy.ts"

# Tests en browser específico
npm run cypress:run --browser chrome
npm run cypress:run --browser firefox
```

## Comandos Avanzados

### Análisis de Cobertura

#### Backend Coverage
```bash
# Cobertura detallada con HTML report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# Cobertura solo para módulos específicos
pytest tests/services/ --cov=app.services --cov-report=html

# Cobertura con fallar si baja del mínimo
pytest tests/ --cov=app --cov-fail-under=80

# Cobertura en formato XML (para CI)
pytest tests/ --cov=app --cov-report=xml:coverage.xml

# Cobertura con exclusión de archivos
pytest tests/ --cov=app --cov-report=html --cov-report=exclude=*/migrations/*
```

#### Frontend Coverage
```bash
# Coverage con Vitest
npm test -- --coverage --coverage.include="src/**/*"

# Coverage con exclude
npm test -- --coverage --coverage.exclude="src/test/**,src/**/*.d.ts"

# Coverage en diferentes formatos
npm test -- --coverage --reporter=html --outputFile=coverage.html
npm test -- --coverage --reporter=lcov --outputFile=coverage.lcov

# Coverage con umbrales
npm test -- --coverage --coverage.thresholds.lines=80
```

### Performance Testing

#### Benchmarks
```bash
# Backend benchmarks con pytest-benchmark
pytest tests/benchmarks/ --benchmark-only --benchmark-sort=mean

# Tests de performance específicos
pytest tests/performance/test_api_performance.py -v

# Frontend performance con Lighthouse
npm run lighthouse
# o usar playwright con performance metrics
npx playwright test --project=chromium --trace=on
```

### Análisis de Calidad

#### Backend Quality
```bash
# Linting
flake8 backend/tests/
black --check backend/tests/
isort --check-only backend/tests/

# Type checking
mypy backend/tests/

# Security testing (opcional)
bandit -r backend/tests/

# Complexity analysis (opcional)
radon cc backend/tests/
```

#### Frontend Quality
```bash
# ESLint
npm run lint

# Type checking
npm run type-check

# Bundle analysis
npm run build
npm run analyze

# Accessibility testing (opcional)
npm run a11y
```

### Tests en CI/CD

#### GitHub Actions (local)
```bash
# Simular CI pipeline
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Backend CI
cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml

# Frontend CI  
cd frontend/ai-news-frontend && npm test -- --coverage --reporter=jest-junit
```

## Configuraciones por Entorno

### Tests de Desarrollo
```bash
# Backend
pytest tests/ -v --asyncio-mode=auto -x  # Parar en primer error

# Frontend
npm test -- --watch --reporter=verbose
```

### Tests de Staging
```bash
# Backend
pytest tests/ --cov=app --cov-fail-under=75 -v

# Frontend  
npm test -- --run --coverage --reporter=dot
```

### Tests de Producción
```bash
# Backend - Solo tests críticos
pytest tests/ --mark-skip slow --mark-skip external -v

# Frontend - Tests rápidos
npm test -- --run --testTimeout=5000
```

## Debugging de Tests

### Backend Debugging
```bash
# Tests con debugger Python
pytest tests/services/test_newsapi_client.py --pdb

# Tests con logging detallado
pytest tests/ -v -s --log-cli-level=DEBUG

# Tests con traceback detallado
pytest tests/ --tb=long --tb=auto

# Tests con solo fallas
pytest tests/ --lf  # Last failed
pytest tests/ --ff  # Failed first
```

### Frontend Debugging
```bash
# Tests con debugging de Vitest
npm test -- --inspect-brk --inspect

# Tests con browser opened
npm test -- --browser

# Tests con screenshots en falla
npm test -- --update-snapshots

# Tests con debug de React
npm test -- --inspect --inspect-brk
```

### E2E Debugging
```bash
# Playwright con tracing
npx playwright test --trace=on

# Playwright con screenshots
npx playwright test --screenshots=on

# Playwright con video
npx playwright test --video=on

# Playwright con debug
npx playwright test --debug

# Abrir HTML report
npx playwright show-report
```

## Scripts Útiles

### Script Master de Tests
```bash
#!/bin/bash
# test-runner.sh

set -e

echo "🧪 Running AI News Aggregator Test Suite"

# Backend tests
echo "📡 Testing Backend..."
cd backend
pytest tests/ --cov=app --cov-report=term-missing -q
echo "✅ Backend tests passed"

# Frontend tests
echo "⚛️ Testing Frontend..."
cd ../frontend/ai-news-frontend
npm test -- --coverage --reporter=dot --passWithNoTests
echo "✅ Frontend tests passed"

# E2E tests
echo "🎭 Testing End-to-End..."
npx playwright test --reporter=dot
echo "✅ E2E tests passed"

echo "🎉 All tests passed successfully!"
```

### Script de Validación Pre-commit
```bash
#!/bin/bash
# pre-commit-tests.sh

echo "🔍 Running pre-commit validation..."

# Backend quick tests
echo "Backend unit tests..."
pytest tests/ -x -q

# Frontend quick tests  
echo "Frontend unit tests..."
npm test -- --run --passWithNoTests

# Type checking
echo "Type checking..."
mypy backend/app/
npm run type-check

echo "✅ Pre-commit validation passed"
```

## Troubleshooting Común

### Problemas de Dependencies
```bash
# Backend
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# Frontend
npm install
# o
pnpm install
```

### Problemas de Database
```bash
# Reset test database
docker-compose down
docker-compose up -d postgres redis

# Migrate test database
cd backend
alembic upgrade head
```

### Problemas de Puertos
```bash
# Verificar puertos en uso
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL

# Matar procesos
kill -9 $(lsof -t -i:3000)
```

### Problemas de Cache
```bash
# Limpiar cache de tests
pytest --cache-clear

# Frontend
rm -rf node_modules/.vite
rm -rf node_modules/.cache

# Reinstall dependencies
npm ci
```

## Métricas de Ejecución

### Tiempos de Ejecución Típicos
- **Backend Unit Tests**: ~30-60 segundos
- **Frontend Unit Tests**: ~20-40 segundos  
- **E2E Tests**: ~2-5 minutos
- **Full Test Suite**: ~5-10 minutos

### Targets de Performance
- **Unit Tests**: < 100ms por test
- **Integration Tests**: < 2s por test
- **E2E Tests**: < 30s por escenario
- **Total Suite**: < 10 minutos

---

Esta guía debe mantenerse actualizada con nuevas configuraciones y comandos según evolucione el proyecto.
