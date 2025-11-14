# Guía de Cobertura de Código - AI News Aggregator

## Objetivos de Cobertura

### Targets de Cobertura

| Componente | Unit Tests | Integration Tests | E2E Tests | Overall |
|------------|------------|-------------------|-----------|---------|
| **Core Services** | 95% | 90% | 100% | 95% |
| **API Endpoints** | 90% | 85% | 100% | 90% |
| **Database Layer** | 85% | 90% | 95% | 90% |
| **Frontend Components** | 90% | 80% | 100% | 90% |
| **Utility Functions** | 95% | 75% | 90% | 95% |
| **Business Logic** | 95% | 85% | 100% | 95% |
| **Error Handling** | 90% | 80% | 100% | 90% |

### Métricas de Calidad

- **Branch Coverage**: ≥85%
- **Function Coverage**: ≥90%
- **Line Coverage**: ≥85%
- **Statement Coverage**: ≥85%
- **Mutation Score**: ≥70% (opcional con Stryker)

## Backend Coverage (pytest-cov)

### Configuración de Coverage

#### pytest.ini
```ini
[tool:pytest]
addopts = 
    --cov=app
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
    --cov-branch
    --cov-contexts=test

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    api: API tests
    database: Database tests
    external: Tests using external services
    async: Async tests
    coverage: Tests for coverage verification
```

#### pyproject.toml
```toml
[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/migrations/*", 
    "*/venv/*",
    "*/env/*",
    "*/__pycache__/*",
    "*/alembic/*",
    "*/conftest.py",
    "*/main.py",  # Entry point
]

branch = true
contexts = ["test", "unit", "integration"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
    "TYPE_CHECKING",
    "except ImportError:",
    "# Needed for Python 3.7/3.8 compatibility",
]

show_missing = true
precision = 2
fail_under = 80
skip_covered = true

[tool.coverage.html]
directory = "htmlcov"
title = "AI News Aggregator Coverage Report"

[tool.coverage.xml]
output = "coverage.xml"

[tool.coverage.paths]
source = [
    "app/",
    "*/site-packages/app/",
]
```

### Ejecutar Coverage Analysis

#### Análisis Básico
```bash
# Ejecutar tests con coverage
cd backend
pytest tests/ --cov=app --cov-report=term

# Coverage con reporte HTML
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Coverage con exclusion de archivos
pytest tests/ --cov=app --cov-report=html \
    --cov-omit="*/migrations/*,*/tests/*,*/venv/*"

# Coverage mínimo
pytest tests/ --cov=app --cov-fail-under=85
```

#### Coverage Detallado
```bash
# Coverage con missing lines
pytest tests/ --cov=app --cov-report=term-missing

# Coverage branch-by-branch
pytest tests/ --cov=app --cov-branch --cov-report=term

# Coverage específico por módulo
pytest tests/services/ --cov=app.services --cov-report=html

# Coverage con contexts
pytest tests/ --cov=app --cov-contexts=test,unit,integration
```

#### Reportes Avanzados
```bash
# Combinación de reportes
pytest tests/ \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-report=xml:coverage.xml \
    --cov-fail-under=80

# Coverage con sorting por coverage
pytest tests/ --cov=app --cov-report=term --cov-report-sort=cover

# Coverage con filter por test type
pytest tests/ -m unit --cov=app --cov-report=term
pytest tests/ -m integration --cov=app --cov-report=term
```

### Scripts de Coverage

#### coverage-check.py
```python
#!/usr/bin/env python3
"""
Script para verificar coverage y generar reportes
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd):
    """Run shell command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def check_coverage():
    """Check coverage thresholds"""
    print("🔍 Checking coverage...")
    
    # Run coverage report
    cmd = "pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=85"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode != 0:
        print("❌ Coverage below threshold!")
        print(stderr)
        return False
    
    print("✅ Coverage meets threshold")
    return True

def generate_reports():
    """Generate all coverage reports"""
    print("📊 Generating coverage reports...")
    
    cmd = """
    pytest tests/ \
        --cov=app \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml \
        --cov-report=json:coverage.json
    """
    
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode == 0:
        print("✅ Reports generated:")
        print("  - Terminal: Coverage shown above")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")
        print("  - JSON: coverage.json")
    else:
        print("❌ Error generating reports:")
        print(stderr)
    
    return returncode == 0

def analyze_coverage():
    """Analyze coverage gaps"""
    print("📈 Analyzing coverage gaps...")
    
    # Parse coverage.json
    try:
        import json
        with open('coverage.json', 'r') as f:
            coverage_data = json.load(f)
        
        totals = coverage_data['totals']
        files = coverage_data['files']
        
        print(f"Overall Coverage: {totals['percent_covered']:.1f}%")
        print(f"Lines Covered: {totals['covered_lines']}/{totals['num_statements']}")
        print(f"Branches Covered: {totals['num_branches']}/{totals['num_branches']}")
        
        # Find files with low coverage
        low_coverage_files = []
        for filepath, file_data in files.items():
            coverage_percent = (file_data['summary']['covered_lines'] / 
                              file_data['summary']['num_statements'] * 100) if file_data['summary']['num_statements'] > 0 else 0
            
            if coverage_percent < 80:
                low_coverage_files.append((filepath, coverage_percent))
        
        if low_coverage_files:
            print("\n⚠️  Files with low coverage (<80%):")
            for filepath, coverage in sorted(low_coverage_files, key=lambda x: x[1]):
                print(f"  {filepath}: {coverage:.1f}%")
        
    except FileNotFoundError:
        print("⚠️  coverage.json not found. Run tests with --cov-report=json first.")
    except Exception as e:
        print(f"❌ Error analyzing coverage: {e}")

if __name__ == "__main__":
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent / "backend"
    os.chdir(backend_dir)
    
    # Check coverage thresholds
    if not check_coverage():
        sys.exit(1)
    
    # Generate detailed reports
    generate_reports()
    
    # Analyze gaps
    analyze_coverage()
    
    print("\n🎉 Coverage analysis complete!")
```

## Frontend Coverage (Vitest)

### Configuración de Coverage

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
      provider: 'v8', // or 'c8'
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/coverage/**',
        '**/dist/**',
        '**/build/**',
        'src/main.tsx',
        'src/App.tsx' // Often just a wrapper
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 85,
          lines: 85,
          statements: 85
        },
        perFile: {
          branches: 75,
          functions: 80,
          lines: 80,
          statements: 80
        }
      },
      reportsDirectory: './coverage',
      reportOnFailure: true
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

### Ejecutar Frontend Coverage

#### Comandos Básicos
```bash
cd frontend/ai-news-frontend

# Tests con coverage
npm test -- --coverage

# Coverage con reportes específicos
npm test -- --coverage --reporter=verbose

# Coverage con threshold checking
npm test -- --coverage --reporter=verbose --check-coverage

# Coverage solo para archivos fuente
npm test -- --coverage --coverage.include="src/**/*"
```

#### Coverage Avanzado
```bash
# Coverage con exclude
npm test -- --coverage --coverage.exclude="src/test/**,src/**/*.d.ts"

# Coverage con multiple reporters
npm test -- --coverage \
  --reporter=html \
  --reporter=json \
  --reporter=lcov \
  --reporter=text-summary

# Coverage con custom thresholds
npm test -- --coverage \
  --coverage.thresholds.lines=80 \
  --coverage.thresholds.functions=85 \
  --coverage.thresholds.branches=75

# Coverage de un archivo específico
npm test src/components/NewsCard.test.tsx -- --coverage
```

### Scripts de Frontend Coverage

#### coverage-analysis.js
```javascript
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

function runCoverage() {
  console.log('🔍 Running coverage analysis...');
  
  try {
    // Run tests with coverage
    execSync('npm test -- --coverage --reporter=json --outputFile=coverage.json', {
      stdio: 'inherit',
      cwd: path.resolve(__dirname, '../ai-news-frontend')
    });
    
    // Parse coverage data
    const coveragePath = path.join(__dirname, '../ai-news-frontend/coverage/coverage.json');
    
    if (fs.existsSync(coveragePath)) {
      const coverageData = JSON.parse(fs.readFileSync(coveragePath, 'utf8'));
      
      console.log('📊 Coverage Summary:');
      console.log(`Overall: ${coverageData.total.lines.pct}%`);
      console.log(`Functions: ${coverageData.total.functions.pct}%`);
      console.log(`Statements: ${coverageData.total.statements.pct}%`);
      console.log(`Branches: ${coverageData.total.branches.pct}%`);
      
      // Find low coverage files
      const lowCoverageFiles = [];
      for (const [file, data] of Object.entries(coverageData)) {
        if (typeof data === 'object' && data.total) {
          const avgCoverage = (
            data.total.lines.pct + 
            data.total.functions.pct + 
            data.total.statements.pct + 
            data.total.branches.pct
          ) / 4;
          
          if (avgCoverage < 80) {
            lowCoverageFiles.push({ file, coverage: avgCoverage });
          }
        }
      }
      
      if (lowCoverageFiles.length > 0) {
        console.log('\n⚠️  Files with low coverage (<80%):');
        lowCoverageFiles
          .sort((a, b) => a.coverage - b.coverage)
          .forEach(({ file, coverage }) => {
            console.log(`  ${file}: ${coverage.toFixed(1)}%`);
          });
      }
    }
    
  } catch (error) {
    console.error('❌ Coverage analysis failed:', error.message);
    process.exit(1);
  }
}

function generateReports() {
  console.log('📋 Generating coverage reports...');
  
  const commands = [
    'npm test -- --coverage --reporter=html',
    'npm test -- --coverage --reporter=lcov',
    'npm test -- --coverage --reporter=text-summary'
  ];
  
  commands.forEach(command => {
    try {
      execSync(command, { 
        stdio: 'inherit',
        cwd: path.resolve(__dirname, '../ai-news-frontend')
      });
    } catch (error) {
      console.error(`❌ Command failed: ${command}`);
    }
  });
  
  console.log('✅ Reports generated:');
  console.log('  - HTML: coverage/index.html');
  console.log('  - LCOV: coverage/lcov.info');
  console.log('  - Summary: shown above');
}

if (require.main === module) {
  runCoverage();
  generateReports();
}

module.exports = { runCoverage, generateReports };
```

## Coverage por Tipo de Test

### Unit Tests Coverage
```bash
# Backend unit tests coverage
cd backend
pytest tests/unit/ --cov=app --cov-report=term

# Frontend unit tests coverage  
cd frontend/ai-news-frontend
npm test src/__tests__/ -- --coverage

# Unit test specific coverage
pytest tests/services/ --cov=app.services --cov-omit="*/tests/*"
```

### Integration Tests Coverage
```bash
# Backend integration tests
cd backend
pytest tests/integration/ --cov=app --cov-report=term

# Frontend integration tests
cd frontend/ai-news-frontend
npm test src/integration/ -- --coverage
```

### End-to-End Coverage
```javascript
// e2e/coverage.js - Coverage en E2E tests
import { test, expect } from '@playwright/test';

test.describe('E2E Coverage', () => {
  test('Complete user journey', async ({ page }) => {
    // Navigate through key user flows to ensure routes/components are covered
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('AI News Aggregator');
    
    await page.click('[data-testid="search-button"]');
    await page.fill('[data-testid="search-input"]', 'technology');
    await page.press('[data-testid="search-input"]', 'Enter');
    
    await expect(page.locator('[data-testid="news-card"]')).toHaveCount.greaterThan(0);
    
    // Check code coverage after navigation
    const coverage = await page.evaluate(() => window.__coverage__);
    expect(coverage).toBeTruthy();
  });
});
```

## Coverage Dashboards

### Coverage Tracking Script
```python
#!/usr/bin/env python3
"""
Coverage tracking y trending
"""

import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import matplotlib.pyplot as plt
import pandas as pd

class CoverageTracker:
    def __init__(self, data_file='coverage_history.json'):
        self.data_file = data_file
        self.history = self.load_history()
    
    def load_history(self):
        """Load coverage history"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_history(self):
        """Save coverage history"""
        with open(self.data_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def collect_coverage(self):
        """Collect current coverage metrics"""
        # Backend coverage
        backend_result = subprocess.run([
            'pytest', 'backend/tests/', 
            '--cov=app', '--cov-report=json:backend_coverage.json', 
            '--quiet'
        ], capture_output=True, text=True)
        
        # Frontend coverage
        frontend_result = subprocess.run([
            'npm', 'test', '--', '--coverage', '--reporter=json', 
            '--outputFile=frontend_coverage.json'
        ], cwd='frontend/ai-news-frontend', capture_output=True, text=True)
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'backend_coverage': self.parse_backend_coverage(),
            'frontend_coverage': self.parse_frontend_coverage()
        }
        
        self.history.append(metrics)
        self.save_history()
        return metrics
    
    def parse_backend_coverage(self):
        """Parse backend coverage JSON"""
        try:
            with open('backend_coverage.json', 'r') as f:
                data = json.load(f)
                return {
                    'lines': data['totals']['percent_covered'],
                    'functions': data['totals']['percent_covered'],
                    'statements': data['totals']['percent_covered'],
                    'branches': data['totals']['percent_covered']
                }
        except:
            return None
    
    def parse_frontend_coverage(self):
        """Parse frontend coverage JSON"""
        try:
            with open('frontend/ai-news-frontend/coverage/coverage.json', 'r') as f:
                data = json.load(f)
                return {
                    'lines': data['total']['lines']['pct'],
                    'functions': data['total']['functions']['pct'],
                    'statements': data['total']['statements']['pct'],
                    'branches': data['total']['branches']['pct']
                }
        except:
            return None
    
    def generate_report(self):
        """Generate coverage trend report"""
        if len(self.history) < 2:
            print("Insufficient data for trending")
            return
        
        df = pd.DataFrame(self.history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create trend plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Backend trends
        if df['backend_coverage'].notna().any():
            backend_data = df[df['backend_coverage'].notna()]
            axes[0,0].plot(backend_data['timestamp'], backend_data['backend_coverage'].apply(lambda x: x['lines']))
            axes[0,0].set_title('Backend Coverage Trend')
            axes[0,0].set_ylabel('Coverage %')
            axes[0,0].tick_params(axis='x', rotation=45)
        
        # Frontend trends
        if df['frontend_coverage'].notna().any():
            frontend_data = df[df['frontend_coverage'].notna()]
            axes[0,1].plot(frontend_data['timestamp'], frontend_data['frontend_coverage'].apply(lambda x: x['lines']))
            axes[0,1].set_title('Frontend Coverage Trend')
            axes[0,1].set_ylabel('Coverage %')
            axes[0,1].tick_params(axis='x', rotation=45)
        
        # Overall trend
        axes[1,0].plot(df['timestamp'], df.apply(lambda row: 
            (row['backend_coverage']['lines'] + row['frontend_coverage']['lines']) / 2 
            if row['backend_coverage'] and row['frontend_coverage'] 
            else None, axis=1))
        axes[1,0].set_title('Overall Coverage Trend')
        axes[1,0].set_ylabel('Coverage %')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # Coverage by component
        latest = self.history[-1]
        components = []
        coverages = []
        
        if latest['backend_coverage']:
            components.append('Backend')
            coverages.append(latest['backend_coverage']['lines'])
        
        if latest['frontend_coverage']:
            components.append('Frontend')
            coverages.append(latest['frontend_coverage']['lines'])
        
        axes[1,1].bar(components, coverages)
        axes[1,1].set_title('Latest Coverage by Component')
        axes[1,1].set_ylabel('Coverage %')
        
        plt.tight_layout()
        plt.savefig('coverage_trends.png', dpi=300, bbox_inches='tight')
        print("📊 Coverage trends saved to coverage_trends.png")
    
    def check_thresholds(self):
        """Check if coverage meets thresholds"""
        if not self.history:
            return
        
        latest = self.history[-1]
        alerts = []
        
        # Backend thresholds
        if latest['backend_coverage']:
            if latest['backend_coverage']['lines'] < 80:
                alerts.append(f"Backend lines coverage: {latest['backend_coverage']['lines']:.1f}% < 80%")
            if latest['backend_coverage']['branches'] < 75:
                alerts.append(f"Backend branches coverage: {latest['backend_coverage']['branches']:.1f}% < 75%")
        
        # Frontend thresholds
        if latest['frontend_coverage']:
            if latest['frontend_coverage']['lines'] < 85:
                alerts.append(f"Frontend lines coverage: {latest['frontend_coverage']['lines']:.1f}% < 85%")
            if latest['frontend_coverage']['functions'] < 85:
                alerts.append(f"Frontend functions coverage: {latest['frontend_coverage']['functions']:.1f}% < 85%")
        
        if alerts:
            print("⚠️  Coverage alerts:")
            for alert in alerts:
                print(f"  {alert}")
            return False
        else:
            print("✅ All coverage thresholds met")
            return True

if __name__ == "__main__":
    tracker = CoverageTracker()
    
    print("🔍 Collecting coverage metrics...")
    metrics = tracker.collect_coverage()
    
    print("\n📊 Current Coverage:")
    if metrics['backend_coverage']:
        print(f"Backend: {metrics['backend_coverage']['lines']:.1f}%")
    if metrics['frontend_coverage']:
        print(f"Frontend: {metrics['frontend_coverage']['lines']:.1f}%")
    
    print("\n🎯 Checking thresholds...")
    tracker.check_thresholds()
    
    print("\n📈 Generating trends report...")
    tracker.generate_report()
```

### Coverage Integration con GitHub

#### .github/workflows/coverage.yml
```yaml
name: Coverage Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  coverage-analysis:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        cd frontend/ai-news-frontend && npm ci
    
    - name: Run coverage collection
      run: |
        python scripts/coverage_tracker.py
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage
    
    - name: Upload frontend coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/ai-news-frontend/coverage/lcov.info
        flags: frontend
        name: frontend-coverage
    
    - name: Comment PR with coverage
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request'
      with:
        script: |
          const fs = require('fs');
          const coverage = JSON.parse(fs.readFileSync('coverage_history.json', 'utf8'));
          const latest = coverage[coverage.length - 1];
          
          let comment = `## 📊 Coverage Report\n\n`;
          
          if (latest.backend_coverage) {
            comment += `**Backend:** ${latest.backend_coverage.lines.toFixed(1)}%\n`;
          }
          
          if (latest.frontend_coverage) {
            comment += `**Frontend:** ${latest.frontend_coverage.lines.toFixed(1)}%\n`;
          }
          
          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

## Mejores Prácticas de Coverage

### Writing Testable Code

#### 1. Functions Pequeñas y Específicas
```python
# ❌ Bad - Function too complex
def process_articles(articles):
    # 50+ lines of complex logic
    pass

# ✅ Good - Small, focused functions
def validate_article(article):
    # Simple validation logic
    pass

def extract_keywords(article):
    # Simple extraction logic  
    pass

def save_article(article):
    # Simple save logic
    pass
```

#### 2. Dependency Injection
```python
# ✅ Good - Testable with dependencies injected
class NewsService:
    def __init__(self, api_client=None, db_client=None, cache_client=None):
        self.api_client = api_client or NewsAPIClient()
        self.db_client = db_client or DatabaseClient()
        self.cache_client = cache_client or CacheClient()
```

#### 3. Pure Functions
```python
# ✅ Good - Pure functions are easy to test
def calculate_reading_time(content):
    word_count = len(content.split())
    return word_count // 200  # 200 words per minute

# ❌ Bad - Functions with side effects
def send_email(user, message):
    # Sends email as side effect - harder to test
    smtp_server.send(user.email, message)
```

### Coverage Anti-Patterns

#### 1. Testing Getters/Setters
```python
# ❌ Don't test trivial getters/setters
class User:
    def __init__(self, name):
        self.name = name
    
    @property
    def name(self):
        return self._name
    
    @name.setter  
    def name(self, value):
        self._name = value

# Test like this only if there's actual logic
def test_user_name_setter():
    user = User("John")
    assert user.name == "John"
    
    user.name = "Jane"
    assert user.name == "Jane"
```

#### 2. Coverage-Driven Testing
```python
# ❌ Don't write tests just to hit coverage targets
def complex_function():
    if some_condition:  # Add test just for this branch
        do_something()
    else:
        pass  # Don't add empty else branch

# ✅ Do focus on meaningful scenarios
def complex_function():
    if valid_data(data):
        return process_data(data)
    else:
        raise InvalidDataError("Data validation failed")
```

#### 3. Ignoring Error Handling
```python
# ✅ Test both success and error scenarios
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def test_divide():
    assert divide(10, 2) == 5
    
    with pytest.raises(ValueError):
        divide(10, 0)
```

### Coverage Exclusions

#### Archivos a Excluir
```python
# Exclude patterns in coverage configuration
exclude_patterns = [
    "*/tests/*",           # Test files
    "*/migrations/*",      # Database migrations
    "*/conftest.py",       # Pytest configuration
    "*/main.py",           # Entry points
    "*/settings.py",       # Configuration files
    "*/__init__.py",       # Package init files (often just imports)
    "*/urls.py",           # URL routing (often auto-generated)
    "*/admin.py",          # Django admin (if applicable)
]
```

#### Líneas de Código a Excluir
```python
# Use pragma comments to exclude specific lines
def debug_function():
    if settings.DEBUG:  # pragma: no cover
        print("Debug mode enabled")
    
    try:
        risky_operation()
    except Exception as e:  # pragma: no cover
        # Error handling that's hard to test
        logger.error(f"Unexpected error: {e}")
        raise

class Config:  # pragma: no cover
    """Configuration class - tested via integration tests"""
    pass
```

## Coverage en CI/CD

### GitHub Actions Integration

#### Full Coverage Pipeline
```yaml
name: Full Coverage Analysis

on: [push, pull_request]

jobs:
  backend-coverage:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install coverage pytest-cov
    
    - name: Run tests with coverage
      run: |
        cd backend
        pytest tests/ \
          --cov=app \
          --cov-report=xml \
          --cov-report=html \
          --cov-fail-under=80
    
    - name: Upload to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        flags: backend
        name: backend-coverage
    
    - name: Upload coverage artifacts
      uses: actions/upload-artifact@v3
      with:
        name: backend-coverage-report
        path: backend/htmlcov/

  frontend-coverage:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd frontend/ai-news-frontend
        npm ci
    
    - name: Run tests with coverage
      run: |
        cd frontend/ai-news-frontend
        npm test -- --coverage --reporter=json --outputFile=coverage.json
    
    - name: Upload to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/ai-news-frontend/coverage/lcov.info
        flags: frontend
        name: frontend-coverage
    
    - name: Upload coverage artifacts
      uses: actions/upload-artifact@v3
      with:
        name: frontend-coverage-report
        path: frontend/ai-news-frontend/coverage/
```

---

Esta guía debe mantenerse actualizada y servir como referencia para mantener alta cobertura de código sin caer en los anti-patrones de testing.
