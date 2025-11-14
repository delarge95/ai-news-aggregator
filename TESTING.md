# 🧪 Testing & Coverage System

Comprehensive testing and coverage reporting system for AI News Aggregator.

## 📊 Coverage Configuration

### Backend (.coveragerc)
- **Source**: `app/` directory
- **Coverage Threshold**: 80% minimum
- **Branch Coverage**: Enabled
- **Parallel Execution**: Supported
- **Excludes**: Tests, migrations, configuration files

### Frontend (vitest.config.ts)
- **Source**: `src/` directory  
- **Coverage Threshold**: 80% minimum
- **Providers**: V8 coverage provider
- **Excludes**: Tests, configs, types, generated files

## 🏗️ Testing Stack

### Backend Testing
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-xdist**: Parallel execution
- **pytest-timeout**: Test timeout management
- **pytest-html**: HTML test reports
- **pytest-json-report**: JSON test reports

### Frontend Testing
- **Vitest**: Test runner (Vite-compatible)
- **React Testing Library**: Component testing
- **@testing-library/jest-dom**: Custom matchers
- **@testing-library/user-event**: User interaction simulation
- **Happy DOM**: Lightweight DOM implementation
- **jsdom**: JavaScript DOM implementation
- **MSW**: Mock Service Worker for API mocking

### Code Quality Tools
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **Black**: Python code formatting
- **isort**: Python import sorting
- **MyPy**: Python type checking
- **Safety**: Security vulnerability scanning
- **Flake8**: Python linting

## 🚀 Quick Start

### Install Dependencies
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend/ai-news-frontend
pnpm install
```

### Run Tests
```bash
# Full test suite with coverage
make test-coverage

# Backend only
cd backend
pytest --cov=app --cov-report=html

# Frontend only
cd frontend/ai-news-frontend
pnpm test --coverage
```

## 📋 Available Commands

### Make Commands
| Command | Description |
|---------|-------------|
| `make test-coverage` | Full test suite with coverage |
| `make test-unit` | Unit tests only |
| `make test-integration` | Integration tests only |
| `make test-performance` | Performance tests |
| `make test-watch` | Tests in watch mode |
| `make test-parallel` | Tests in parallel |
| `make coverage-report` | Generate coverage report |
| `make coverage-html` | Generate HTML coverage report |
| `make coverage-serve` | Serve coverage report |
| `make lint` | Run all linting |
| `make format` | Format all code |
| `make type-check` | Type checking |
| `make security` | Security scanning |

### Backend Test Scripts
```bash
# Basic test runner
./run_tests.sh

# With coverage
./run_tests.sh --coverage

# Verbose output
./run_tests.sh --coverage --verbose

# Skip slow tests
./run_tests.sh --skip-slow

# Parallel execution
./run_tests.sh --parallel

# Custom test path
./run_tests.sh --test-path tests/services
```

### Frontend Test Scripts
```bash
pnpm test                 # Run tests in watch mode
pnpm test:run            # Run tests once
pnpm test:coverage       # Run with coverage
pnpm test:ui             # Run with UI
```

## 📊 Coverage Reports

### Report Locations
- **Backend HTML**: `backend/htmlcov/index.html`
- **Backend XML**: `reports/coverage.xml`
- **Backend JSON**: `reports/coverage.json`
- **Frontend HTML**: `frontend/ai-news-frontend/coverage/index.html`

### Viewing Reports
```bash
# Serve coverage report locally
make coverage-serve

# Or open directly
open backend/htmlcov/index.html
open frontend/ai-news-frontend/coverage/index.html
```

### Coverage Thresholds
- **Backend**: 80% minimum line/branch coverage
- **Frontend**: 80% minimum line/branch coverage
- **Global**: Enforced across all modules

## 🔧 Test Configuration

### Backend (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
addopts = 
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
    --cov-branch
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests
    redis: Tests requiring Redis
    openai: Tests requiring OpenAI
    celery: Tests requiring Celery
```

### Frontend (vitest.config.ts)
```typescript
export default defineConfig({
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      reporter: ['text', 'json', 'html', 'lcov'],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
      },
    },
  },
})
```

## 🎯 Test Categories

### Unit Tests
- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1s each)
- **Coverage**: High (100% target)
- **Examples**: Utility functions, pure components

```bash
make test-unit
# or
pytest -m "not integration and not slow"
```

### Integration Tests
- **Purpose**: Test component interactions
- **Speed**: Medium (1-10s each)
- **Coverage**: Focus on critical paths
- **Examples**: API endpoints, database operations

```bash
make test-integration
# or
pytest -m integration
```

### Performance Tests
- **Purpose**: Test under load and stress
- **Speed**: Slow (10s+ each)
- **Coverage**: Critical performance metrics
- **Examples**: Database queries, AI processing

```bash
make test-performance
# or
pytest -m performance
```

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Speed**: Slow (30s+ each)
- **Coverage**: User journey validation
- **Examples**: Full article processing pipeline

```bash
make test-e2e
# or
pytest -m e2e
```

## 🏗️ CI/CD Integration

### GitHub Actions
The CI pipeline includes:
1. **Backend Testing** (pytest + coverage)
2. **Frontend Testing** (Vitest + coverage)
3. **Code Quality** (ESLint, Prettier, Black)
4. **Security Scanning** (Safety audit)
5. **Build Testing** (Docker build)
6. **Coverage Reporting** (Codecov integration)

### Workflow Features
- **Parallel Execution**: Backend and frontend tests run concurrently
- **Coverage Upload**: Reports sent to Codecov
- **Artifact Storage**: Test results and reports preserved
- **Slack Notifications**: Build status notifications
- **Coverage Badges**: Auto-generated for README

### Environment Variables
```yaml
# Required secrets
OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

# Test environment
DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
REDIS_URL: redis://localhost:6379/15
TESTING: true
```

## 📈 Coverage Tracking

### Codecov Integration
- **Backend Flag**: Tracks Python code coverage
- **Frontend Flag**: Tracks TypeScript/React coverage
- **Pull Request Comments**: Coverage changes in PR
- **Coverage Reports**: Detailed breakdowns by file

### Coverage Badge
```markdown
[![Coverage Status](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://codecov.io/gh/your-username/ai-news-aggregator)
```

### Coverage Reports
- **Terminal**: Real-time coverage during tests
- **HTML**: Interactive coverage browser
- **XML**: CI/CD integration format
- **JSON**: Programmatic access

## 🔍 Code Quality Checks

### Linting
```bash
# Backend
cd backend
flake8 app/ --max-line-length=88

# Frontend  
cd frontend/ai-news-frontend
eslint src/ --ext .ts,.tsx
```

### Formatting
```bash
# Backend
cd backend
black app/ tests/
isort app/ tests/

# Frontend
cd frontend/ai-news-frontend
prettier --write src/
```

### Type Checking
```bash
# Backend
cd backend
mypy app/ --ignore-missing-imports

# Frontend
cd frontend/ai-news-frontend
tsc --noEmit
```

### Security Scanning
```bash
# Backend dependencies
cd backend
safety check

# Frontend dependencies
cd frontend/ai-news-frontend
pnpm audit
```

## 🐛 Debugging Tests

### Common Issues

#### Test Timeouts
```bash
# Increase timeout for slow tests
pytest --timeout=60 tests/slow_test.py
```

#### Coverage Issues
```bash
# Run with more verbose coverage
pytest --cov=app --cov-report=term-missing --cov-verbose

# Check coverage exclusions
coverage report --show-missing
```

#### Parallel Test Issues
```bash
# Run tests sequentially if parallel fails
pytest -n 0
```

### Debug Commands
```bash
# Run specific test file
pytest tests/test_specific.py -v

# Run with pdb on failure
pytest --pdb tests/test_specific.py

# Run with coverage for single file
pytest tests/test_specific.py --cov=app --cov-report=html

# Generate HTML report for debugging
pytest --cov=app --cov-report=html:debug-coverage
```

## 📚 Best Practices

### Writing Tests
1. **Use descriptive test names**: `test_should_return_user_by_id_when_user_exists`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: APIs, databases, file system
4. **Test edge cases**: Empty inputs, error conditions
5. **Keep tests independent**: No shared state between tests

### Coverage Goals
1. **Aim for 80%+ coverage**: Minimum threshold requirement
2. **Focus on business logic**: Core functionality over utilities
3. **Avoid testing third-party code**: Focus on your implementation
4. **Test error paths**: Ensure proper error handling

### Test Organization
```
tests/
├── conftest.py           # Shared fixtures
├── unit/                 # Unit tests
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/          # Integration tests
│   ├── test_api.py
│   └── test_database.py
├── performance/          # Performance tests
│   └── test_load.py
└── e2e/                  # End-to-end tests
    └── test_workflows.py
```

## 🆘 Troubleshooting

### Common Errors

#### Import Errors
```python
# Add to conftest.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
```

#### Coverage Not Generated
```bash
# Check coverage configuration
coverage debug config

# Verify source paths
coverage report --show-missing
```

#### Async Test Issues
```python
# Use pytest-asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

#### Database Test Issues
```python
# Use in-memory SQLite for tests
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine
```

### Getting Help
1. **Check test logs**: `reports/test-output.log`
2. **Review coverage reports**: HTML reports show uncovered lines
3. **Run in verbose mode**: `pytest -v`
4. **Check CI logs**: GitHub Actions provides detailed logs
5. **Use debugger**: `pytest --pdb` on failure

---

For more information, see individual component documentation:
- [Backend Testing Guide](backend/tests/README.md)
- [Frontend Testing Guide](frontend/ai-news-frontend/src/test/README.md)
- [Coverage Configuration](.coveragerc)
- [GitHub Actions Workflow](.github/workflows/test-coverage.yml)