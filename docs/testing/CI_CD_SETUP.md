# Configuración CI/CD - AI News Aggregator

## Overview del Pipeline

Este documento describe la configuración completa de CI/CD para el AI News Aggregator usando GitHub Actions.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Development   │───▶│   Pull Request   │───▶│   Main Branch   │
│   Branch        │    │   Validation     │    │   Integration   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Local Dev     │    │   Automated      │    │   Deployment    │
│   Testing       │    │   Testing        │    │   Pipeline      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Workflows de GitHub Actions

### 1. CI - Continuous Integration

**.github/workflows/ci.yml**
```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: '3.11'
  NODE_VERSION: '18'

jobs:
  # ========================================================================
  # BACKEND TESTING
  # ========================================================================
  backend-tests:
    name: Backend Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-type: [unit, integration, security]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_newsaggregator
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ env.PYTHON_VERSION }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
        pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-html pytest-xdist

    - name: Set up test environment
      run: |
        cd backend
        # Create test database
        createdb -h localhost -p 5432 -U postgres test_newsaggregator
        # Run migrations
        alembic upgrade head
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_newsaggregator
        REDIS_URL: redis://localhost:6379

    - name: Run backend tests
      run: |
        cd backend
        case "${{ matrix.test-type }}" in
          "unit")
            pytest tests/ -v --cov=app --cov-report=xml --cov-report=html --junit-xml=results.xml -m unit
            ;;
          "integration")
            pytest tests/integration/ -v --cov=app --cov-report=xml --cov-report=html --junit-xml=results.xml -m integration
            ;;
          "security")
            bandit -r app/ -f json -o bandit-report.json
            safety check --json --output safety-report.json
            ;;
        esac
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_newsaggregator
        REDIS_URL: redis://localhost:6379
        NEWSAPI_KEY: ${{ secrets.NEWSAPI_KEY }}
        GUARDIAN_API_KEY: ${{ secrets.GUARDIAN_API_KEY }}

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend-${{ matrix.test-type }}
        name: backend-${{ matrix.test-type }}
        fail_ci_if_error: false

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: backend-test-results-${{ matrix.test-type }}
        path: |
          backend/results.xml
          backend/htmlcov/
          backend/bandit-report.json
          backend/safety-report.json

  # ========================================================================
  # FRONTEND TESTING  
  # ========================================================================
  frontend-tests:
    name: Frontend Tests
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}
        cache: 'npm'
        cache-dependency-path: frontend/ai-news-frontend/package-lock.json

    - name: Install dependencies
      run: |
        cd frontend/ai-news-frontend
        npm ci

    - name: Run type checking
      run: |
        cd frontend/ai-news-frontend
        npm run type-check

    - name: Run linting
      run: |
        cd frontend/ai-news-frontend
        npm run lint

    - name: Run unit tests
      run: |
        cd frontend/ai-news-frontend
        npm test -- --coverage --reporter=junit --outputFile=results.xml

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/ai-news-frontend/coverage/lcov.info
        flags: frontend
        name: frontend-coverage

    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: frontend-test-results
        path: |
          frontend/ai-news-frontend/results.xml
          frontend/ai-news-frontend/coverage/

  # ========================================================================
  # E2E TESTING
  # ========================================================================
  e2e-tests:
    name: E2E Tests
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    if: github.event_name == 'pull_request'
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_newsaggregator
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}

    - name: Install backend dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Install frontend dependencies
      run: |
        cd frontend/ai-news-frontend
        npm ci

    - name: Install Playwright
      run: |
        cd frontend/ai-news-frontend
        npx playwright install --with-deps

    - name: Build frontend
      run: |
        cd frontend/ai-news-frontend
        npm run build

    - name: Start backend
      run: |
        cd backend
        uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 10
      env:
        DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_newsaggregator
        REDIS_URL: redis://localhost:6379

    - name: Start frontend preview
      run: |
        cd frontend/ai-news-frontend
        npm run preview -- --host 0.0.0.0 --port 3000 &
        sleep 5

    - name: Run E2E tests
      run: |
        cd frontend/ai-news-frontend
        npx playwright test --reporter=junit --output=e2e-results.xml

    - name: Upload E2E results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: e2e-test-results
        path: |
          frontend/ai-news-frontend/e2e-results.xml
          frontend/ai-news-frontend/test-results/

  # ========================================================================
  # CODE QUALITY
  # ========================================================================
  code-quality:
    name: Code Quality
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ env.NODE_VERSION }}

    - name: Install Python dependencies
      run: |
        pip install flake8 black isort mypy bandit safety

    - name: Install Node dependencies
      run: |
        cd frontend/ai-news-frontend
        npm ci

    - name: Python linting
      run: |
        cd backend
        flake8 app/ tests/
        black --check app/ tests/
        isort --check-only app/ tests/
        mypy app/ --ignore-missing-imports

    - name: Node.js linting
      run: |
        cd frontend/ai-news-frontend
        npm run lint

    - name: Security scanning
      run: |
        cd backend
        bandit -r app/ -f json -o bandit-report.json
        safety check --json --output safety-report.json

    - name: Upload quality reports
      uses: actions/upload-artifact@v3
      with:
        name: quality-reports
        path: |
          backend/bandit-report.json
          backend/safety-report.json

  # ========================================================================
  # MERGE CHECK
  # ========================================================================
  merge-check:
    name: Merge Check
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests, e2e-tests, code-quality]
    if: github.event_name == 'pull_request'
    
    steps:
    - name: Check test results
      run: |
        echo "All tests passed successfully"
        echo "Backend tests: ✅"
        echo "Frontend tests: ✅" 
        echo "E2E tests: ✅"
        echo "Code quality: ✅"
```

### 2. CD - Continuous Deployment

**.github/workflows/cd.yml**
```yaml
name: CD Pipeline

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  # ========================================================================
  # DOCKER BUILD
  # ========================================================================
  docker-build:
    name: Build Docker Images
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to Docker Hub
      uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Build and push backend
      uses: docker/build-push-action@v5
      with:
        context: ./backend
        file: ./backend/Dockerfile
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/ai-news-backend:latest
          ${{ secrets.DOCKER_USERNAME }}/ai-news-backend:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Build and push frontend
      uses: docker/build-push-action@v5
      with:
        context: ./frontend
        file: ./frontend/Dockerfile
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/ai-news-frontend:latest
          ${{ secrets.DOCKER_USERNAME }}/ai-news-frontend:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # ========================================================================
  # DEPLOY TO STAGING
  # ========================================================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: docker-build
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Deploy to staging
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.STAGING_HOST }}
        username: ${{ secrets.STAGING_USER }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          cd /opt/ai-news-aggregator
          
          # Pull latest images
          docker-compose pull backend frontend
          
          # Deploy with zero downtime
          docker-compose up -d --remove-orphans
          
          # Wait for services to be healthy
          timeout 300 bash -c 'until curl -f http://localhost:8000/health; do echo "Waiting for backend..."; sleep 5; done'
          timeout 300 bash -c 'until curl -f http://localhost:3000/health; do echo "Waiting for frontend..."; sleep 5; done'
          
          # Run smoke tests
          python scripts/smoke_tests.py --environment=staging

  # ========================================================================
  # STAGING TESTS
  # ========================================================================
  staging-tests:
    name: Staging Tests
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment: staging
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run staging smoke tests
      run: |
        python scripts/run_smoke_tests.py \
          --base-url ${{ secrets.STAGING_URL }} \
          --api-url ${{ secrets.STAGING_API_URL }}

    - name: Performance testing
      run: |
        python scripts/performance_tests.py \
          --base-url ${{ secrets.STAGING_URL }} \
          --load-test-duration=300s

  # ========================================================================
  # DEPLOY TO PRODUCTION
  # ========================================================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [docker-build, staging-tests]
    environment: production
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Deploy to production
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USER }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/ai-news-aggregator/production
          
          # Backup current deployment
          docker-compose exec -T postgres pg_dumpall > backup_$(date +%Y%m%d_%H%M%S).sql
          
          # Deploy new version
          docker-compose pull backend frontend
          docker-compose up -d --remove-orphans
          
          # Health check
          python scripts/health_check.py --environment=production
          
          # Run database migrations
          docker-compose exec backend alembic upgrade head

  # ========================================================================
  # POST DEPLOYMENT
  # ========================================================================
  post-deployment:
    name: Post-deployment Tasks
    runs-on: ubuntu-latest
    needs: deploy-production
    
    steps:
    - name: Production smoke tests
      run: |
        python scripts/run_smoke_tests.py \
          --base-url ${{ secrets.PRODUCTION_URL }} \
          --api-url ${{ secrets.PRODUCTION_API_URL }} \
          --environment=production

    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        message: |
          🚀 AI News Aggregator deployment completed!
          Environment: Production
          Commit: ${{ github.sha }}
          Branch: ${{ github.ref_name }}
      if: always()
```

### 3. Security Scanning

**.github/workflows/security.yml**
```yaml
name: Security Scanning

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday 2 AM
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    name: Security Scanning
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-results.sarif'

    - name: Run CodeQL Analysis
      uses: github/codeql-action/init@v2
      with:
        languages: 'python, javascript'

    - name: Autobuild
      uses: github/codeql-action/autobuild@v2

    - name: Perform CodeQL Analysis
      uses: github/codeql-action/analyze@v2

    - name: Docker security scan
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'python:3.11-slim'
        format: 'sarif'
        output: 'docker-trivy-results.sarif'
```

## Environments y Secrets

### Repository Secrets

**Backend API Keys:**
- `NEWSAPI_KEY`: API key para NewsAPI
- `GUARDIAN_API_KEY`: API key para The Guardian
- `NYTIMES_API_KEY`: API key para NYTimes
- `OPENAI_API_KEY`: API key para OpenAI

**Database:**
- `DATABASE_URL`: Production database URL
- `TEST_DATABASE_URL`: Test database URL

**Docker:**
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password

**Deployment:**
- `STAGING_HOST`: Staging server hostname
- `STAGING_USER`: Staging server user
- `STAGING_SSH_KEY`: Staging server SSH key
- `PRODUCTION_HOST`: Production server hostname
- `PRODUCTION_USER`: Production server user
- `PRODUCTION_SSH_KEY`: Production server SSH key

**Monitoring:**
- `SLACK_WEBHOOK`: Slack webhook for notifications
- `SENTRY_DSN`: Sentry DSN for error tracking

### GitHub Environments

```yaml
# Environment Protection Rules

staging:
  deployment_branches:
    - main
  required_reviewers:
    - "@team-leads"
  wait_timer: 0

production:
  deployment_branches:
    - main
  required_reviewers:
    - "@engineering-manager"
  wait_timer: 3600  # 1 hour
  environment_variables:
    - ENVIRONMENT=production
```

## Scripts de Deployment

### Smoke Tests Script

**scripts/smoke_tests.py**
```python
#!/usr/bin/env python3
"""
Smoke tests para verificar que el deployment funciona correctamente
"""

import requests
import time
import sys

def test_health_endpoint(base_url):
    """Test health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint OK")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_api_endpoints(api_url):
    """Test API endpoints"""
    endpoints = [
        "/users/health",
        "/articles/health", 
        "/analytics/health"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{api_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} OK")
            else:
                print(f"❌ {endpoint} failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {endpoint} error: {e}")
            return False
    
    return True

def test_frontend(base_url):
    """Test frontend loading"""
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200 and "AI News Aggregator" in response.text:
            print("✅ Frontend OK")
            return True
        else:
            print(f"❌ Frontend failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:3000"
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    print(f"🧪 Running smoke tests...")
    print(f"Frontend: {base_url}")
    print(f"API: {api_url}")
    
    # Wait for services to start
    print("⏳ Waiting for services to start...")
    time.sleep(30)
    
    tests = [
        test_frontend(base_url),
        test_health_endpoint(base_url),
        test_api_endpoints(api_url)
    ]
    
    if all(tests):
        print("🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print("💥 Smoke tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Performance Tests Script

**scripts/performance_tests.py**
```python
#!/usr/bin/env python3
"""
Performance tests para verificar que el deployment cumple SLAs
"""

import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_api_performance(api_url, duration=60):
    """Test API performance under load"""
    start_time = time.time()
    request_count = 0
    error_count = 0
    response_times = []
    
    def make_request():
        nonlocal request_count, error_count
        try:
            request_start = time.time()
            response = requests.get(f"{api_url}/articles")
            request_time = time.time() - request_start
            
            if response.status_code == 200:
                request_count += 1
                response_times.append(request_time)
                return True
            else:
                error_count += 1
                return False
        except Exception:
            error_count += 1
            return False
    
    # Run load test
    with ThreadPoolExecutor(max_workers=10) as executor:
        while time.time() - start_time < duration:
            futures = [executor.submit(make_request) for _ in range(10)]
            
            for future in as_completed(futures):
                future.result()
    
    # Calculate metrics
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    error_rate = error_count / (request_count + error_count) * 100
    
    print(f"📊 Performance Results:")
    print(f"  Total requests: {request_count}")
    print(f"  Error count: {error_count}")
    print(f"  Error rate: {error_rate:.2f}%")
    print(f"  Avg response time: {avg_response_time:.3f}s")
    print(f"  Max response time: {max_response_time:.3f}s")
    
    # Check SLA compliance
    if error_rate > 1:  # Less than 1% error rate
        print("❌ Error rate SLA violated (>1%)")
        return False
    
    if avg_response_time > 2.0:  # Less than 2s average
        print("❌ Response time SLA violated (>2s)")
        return False
    
    print("✅ Performance SLAs met")
    return True

if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    test_api_performance(api_url, duration)
```

## Monitoring y Alertas

### GitHub Actions Badges

```markdown
<!-- README.md -->

![CI](https://github.com/username/ai-news-aggregator/workflows/CI%20Pipeline/badge.svg)
![CD](https://github.com/username/ai-news-aggregator/workflows/CD%20Pipeline/badge.svg)
![Security](https://github.com/username/ai-news-aggregator/workflows/Security%20Scanning/badge.svg)
[![codecov](https://codecov.io/gh/username/ai-news-aggregator/branch/main/graph/badge.svg)](https://codecov.io/gh/username/ai-news-aggregator)
```

### Custom Workflow Status

```yaml
# .github/workflows/custom-status.yml
name: Custom Status

on:
  workflow_run:
    workflows: ["CI Pipeline"]
    types: [completed]

jobs:
  update-status:
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    steps:
      - name: Update commit status
        uses: octokit/request-action@v2.x
        with:
          route: POST /repos/{owner}/{repo}/statuses/{sha}
          owner: ${{ github.repository_owner }}
          repo: ${{ github.event.repository.name }}
          sha: ${{ github.event.workflow_run.head_sha }}
          state: success
          context: 'Custom Tests'
          description: 'All tests passed successfully'
```

## Troubleshooting

### Common Issues

1. **Database Connection Timeouts**
   ```yaml
   # Add longer timeout in CI
   services:
     postgres:
       options: >-
         --health-cmd pg_isready
         --health-interval 10s
         --health-timeout 10s
         --health-retries 20  # Increased from default 5
   ```

2. **Node.js Memory Issues**
   ```yaml
   # Increase Node.js memory
   - name: Run tests
     run: |
       cd frontend/ai-news-frontend
       NODE_OPTIONS="--max-old-space-size=4096" npm test
   ```

3. **Docker Build Cache Issues**
   ```yaml
   # Use GitHub cache
   - name: Build and push
     uses: docker/build-push-action@v5
     with:
       cache-from: type=gha
       cache-to: type=gha,mode=max
   ```

### Debugging Actions

```yaml
# Add debug step
- name: Debug
  if: failure()
  run: |
    echo "Workflow failed. Debugging..."
    env
    docker ps
    docker logs container_name || true
```

---

Esta configuración proporciona un pipeline CI/CD completo, robusto y escalable para el AI News Aggregator.
