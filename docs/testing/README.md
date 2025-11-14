# Documentación de Testing - AI News Aggregator

## 📋 Índice de Documentación

Esta carpeta contiene la documentación completa de testing y CI/CD para el AI News Aggregator, un sistema de agregación de noticias con backend Python/FastAPI y frontend React/TypeScript.

### 📚 Documentos Principales

| Documento | Descripción | Audiencia |
|-----------|-------------|-----------|
| **[TESTING_STRATEGY.md](./TESTING_STRATEGY.md)** | Metodología general de testing, arquitectura de testing, tipos de tests y configuración | Devs, QA, Tech Leads |
| **[RUNNING_TESTS.md](./RUNNING_TESTS.md)** | Comandos y scripts para ejecutar diferentes tipos de tests | Devs, CI/CD |
| **[CI_CD_SETUP.md](./CI_CD_SETUP.md)** | Configuración completa de GitHub Actions para CI/CD | DevOps, Tech Leads |
| **[test_checklist.md](./test_checklist.md)** | Lista de verificación exhaustiva para QA por funcionalidad | QA, Product Owners |
| **[performance_guidelines.md](./performance_guidelines.md)** | Estrategias y herramientas para performance testing | Devs, SRE |
| **[coverage_guidelines.md](./coverage_guidelines.md)** | Guías para mantener alta cobertura de código | Devs, Tech Leads |
| **[troubleshooting_guide.md](./troubleshooting_guide.md)** | Solución de problemas comunes en testing | Devs, Support |

### 💡 Ejemplos Prácticos

| Directorio | Contenido | Ejemplos |
|------------|-----------|----------|
| **[examples/](./examples/)** | Ejemplos reales de código de tests | Tests unitarios, integración, E2E |

## 🎯 Quick Start

### Ejecutar Tests Básicos

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend/ai-news-frontend
npm test

# Con coverage
pytest tests/ --cov=app --cov-report=html
npm test -- --coverage
```

### Verificar Setup

```bash
# Verificar configuración
python -m pytest --version
npm test -- --version

# Verificar dependencias
cd backend && pip install -r requirements.txt
cd frontend/ai-news-frontend && npm install
```

### Ejecutar Test Suite Completo

```bash
# Usar script runner
./test-runner.sh

# O manualmente
cd backend && pytest tests/ --cov=app
cd frontend/ai-news-frontend && npm test -- --coverage
```

## 🏗️ Arquitectura de Testing

```
AI News Aggregator Testing Architecture
├── Backend (Python/FastAPI)
│   ├── Unit Tests (70%)
│   │   ├── Services testing
│   │   ├── API clients testing
│   │   ├── Utilities testing
│   │   └── Database models testing
│   ├── Integration Tests (20%)
│   │   ├── API endpoints testing
│   │   ├── Database integration testing
│   │   ├── External APIs testing
│   │   └── Cache integration testing
│   └── Performance Tests (10%)
│       ├── Load testing
│       ├── Stress testing
│       └── Memory leak testing
├── Frontend (React/TypeScript)
│   ├── Component Tests (60%)
│   ├── Hook Tests (25%)
│   ├── Integration Tests (10%)
│   └── E2E Tests (5%)
└── End-to-End Tests
    ├── User journeys testing
    ├── Cross-browser testing
    └── Accessibility testing
```

## 📊 Métricas Objetivo

| Métrica | Target | Herramientas |
|---------|--------|--------------|
| **Code Coverage** | ≥85% overall | pytest-cov, Vitest coverage |
| **Test Performance** | <2s unit, <10s integration | pytest-timeout |
| **E2E Tests** | <30s per scenario | Playwright |
| **CI Pipeline** | <10min total | GitHub Actions |
| **Branch Coverage** | ≥80% | pytest-cov --cov-branch |

## 🛠️ Herramientas Utilizadas

### Backend Testing Stack
- **pytest**: Framework principal de testing
- **pytest-asyncio**: Soporte para tests asíncronos
- **pytest-mock**: Mocking framework
- **pytest-cov**: Coverage reporting
- **httpx**: HTTP client para API testing
- **factory-boy**: Test data generation

### Frontend Testing Stack
- **Vitest**: Test runner para React
- **Testing Library**: Component testing
- **@testing-library/jest-dom**: DOM assertions
- **@testing-library/user-event**: User interaction simulation

### E2E Testing Stack
- **Playwright**: Cross-browser E2E testing
- **Chromium/Firefox/WebKit**: Browser engines

### Performance Testing
- **k6**: Load testing framework
- **pytest-benchmark**: Performance benchmarking
- **Lighthouse**: Performance auditing

### CI/CD Stack
- **GitHub Actions**: CI/CD pipeline
- **Docker**: Containerization
- **PostgreSQL**: Database testing
- **Redis**: Cache testing

## 🚀 Flujo de Desarrollo

### Para Developers

1. **Antes deCommit**
   ```bash
   ./pre-commit-tests.sh  # Tests rápidos + linting
   ```

2. **Desarrollo Local**
   ```bash
   # Tests en watch mode
   pytest tests/ -v --asyncio-mode=auto --watch
   npm test -- --watch
   ```

3. **Push a Branch**
   ```bash
   git push origin feature/my-feature
   # CI pipeline se ejecuta automáticamente
   ```

### Para QA

1. **Pre-Testing**
   ```bash
   # Verificar checklist
   cat test_checklist.md
   
   # Setup ambiente completo
   ./setup-test-environment.sh
   ```

2. **Testing Manual**
   ```bash
   # Ejecutar suite completa
   ./test-runner.sh
   
   # Tests específicos por funcionalidad
   pytest tests/ -m "user_management"
   npm test -- --testNamePattern="User"
   ```

3. **E2E Testing**
   ```bash
   # Tests end-to-end
   npm run test:e2e
   
   # Con UI interactiva
   npm run test:e2e:ui
   ```

### Para DevOps

1. **CI/CD Pipeline**
   ```bash
   # Los workflows se ejecutan automáticamente
   # Ver .github/workflows/
   ```

2. **Deploy a Staging**
   ```bash
   # Automatic via GitHub Actions
   # Manual deployment si necesario
   ./deploy-staging.sh
   ```

3. **Monitoring**
   ```bash
   # Verificar health de tests
   python scripts/test_health_monitor.py
   ```

## 📈 Performance Benchmarks

### Targets por Componente

| Componente | Response Time | Throughput | Concurrent Users |
|------------|---------------|------------|------------------|
| **Articles API** | <500ms (p95) | 1000 TPS | 10,000 |
| **Search API** | <1000ms (p95) | 500 TPS | 5,000 |
| **User API** | <300ms (p95) | 200 TPS | 2,000 |
| **Frontend** | <2s (FCP) | N/A | N/A |

### Test Execution Times

| Test Type | Target Time | Actual Time |
|-----------|-------------|-------------|
| **Unit Tests** | <1min | ~30-45s |
| **Integration Tests** | <3min | ~2min |
| **E2E Tests** | <5min | ~3-4min |
| **Full Suite** | <10min | ~7-8min |

## 🔍 Troubleshooting Rápido

### Problemas Comunes

1. **Tests fallan inmediatamente**
   ```bash
   # Verificar dependencias
   pip install -r backend/requirements.txt
   npm install
   
   # Verificar servicios
   docker-compose ps
   ```

2. **Coverage muy bajo**
   ```bash
   # Verificar configuración
   pytest --cov=app --cov-report=term-missing
   
   # Tests específicos
   pytest tests/services/ -v --cov=app.services
   ```

3. **Tests muy lentos**
   ```bash
   # Ejecutar en paralelo
   pytest -n auto
   
   # Solo tests unitarios
   pytest tests/ -m unit -v
   ```

4. **CI/CD falla**
   ```bash
   # Verificar logs detallados
   # Usually timeout or dependency issues
   ```

### Scripts de Ayuda

| Script | Descripción |
|--------|-------------|
| `test-runner.sh` | Ejecuta suite completa de tests |
| `setup-test-environment.sh` | Configura ambiente de testing |
| `performance-test.sh` | Ejecuta tests de performance |
| `coverage-report.sh` | Genera reportes de cobertura |
| `troubleshoot-tests.sh` | Diagnostica problemas comunes |

## 📞 Soporte

### Recursos de Ayuda

1. **Documentación Interna**
   - Esta carpeta contiene toda la documentación necesaria
   - Ejemplos prácticos en `examples/`

2. **Herramientas**
   - Pytest: https://docs.pytest.org/
   - Vitest: https://vitest.dev/
   - Playwright: https://playwright.dev/
   - k6: https://k6.io/

3. **Canales de Comunicación**
   - Issues en GitHub
   - Slack: #testing-support
   - Code review comments

### Reporting Issues

Cuando encuentres problemas:

1. **Verificar esta documentación** primero
2. **Ejecutar tests diagnósticos**
   ```bash
   python scripts/troubleshoot-tests.sh
   ```
3. **Crear issue** con:
   - Descripción del problema
   - Pasos para reproducir
   - Logs de error
   - Environment details

## 🔄 Mejora Continua

### Actualizaciones Regulares

- **Semanal**: Review de métricas de tests
- **Mensual**: Actualización de herramientas
- **Quarterly**: Review de estrategia de testing

### Contribución

Para mejorar la documentación:

1. Fork el repository
2. Actualizar documentación
3. Agregar ejemplos
4. Submit pull request

---

**Última actualización**: 2025-11-06  
**Versión**: 1.0.0  
**Mantenedores**: Development Team

---

Esta documentación debe mantenerse actualizada y evolucionar con el proyecto. Es fundamental para mantener la calidad del código y la confianza en el sistema.
