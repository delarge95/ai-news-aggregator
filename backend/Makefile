# Makefile for AI News Aggregator Backend
# Comprehensive build and test automation

.PHONY: help install install-dev test test-unit test-integration test-coverage lint format type-check security clean docs

# Default target
help:
	@echo "AI News Aggregator Backend - Build Commands"
	@echo "==========================================="
	@echo ""
	@echo "Installation:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test           Run complete test suite"
	@echo "  test-unit      Run only unit tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-coverage  Run tests with coverage report"
	@echo "  test-performance Run performance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint           Run code linting"
	@echo "  format         Format code automatically"
	@echo "  type-check     Run type checking"
	@echo "  security       Run security analysis"
	@echo ""
	@echo "Build & Clean:"
	@echo "  build          Build package"
	@echo "  clean          Clean build artifacts"
	@echo "  docs           Build documentation"
	@echo ""
	@echo "CI/CD:"
	@echo "  ci             Run CI/CD test suite"
	@echo "  tox            Run tests with tox"
	@echo ""

# Installation targets
install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

install-dev:
	@echo "Installing development dependencies..."
	pip install -r requirements-dev.txt
	pip install -e .

# Testing targets
test:
	@echo "Running complete test suite..."
	./run_comprehensive_tests.sh

test-unit:
	@echo "Running unit tests..."
	pytest tests/ -m unit -v --cov=app --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	pytest tests/ -m integration -v --cov=app --cov-append

test-coverage:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=app --cov-branch --cov-report=html:htmlcov --cov-report=term-missing --cov-report=xml:coverage.xml
	@echo "Coverage report generated in htmlcov/index.html"

test-performance:
	@echo "Running performance tests..."
	pytest tests/ -m performance --benchmark-only --benchmark-json=benchmark.json

test-fast:
	@echo "Running fast tests only..."
	pytest tests/ -m "unit and not slow" -v

# Code quality targets
lint:
	@echo "Running code linting..."
	black --check --diff app/ tests/
	isort --check-only --diff app/ tests/
	flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503

format:
	@echo "Formatting code..."
	black app/ tests/
	isort app/ tests/

type-check:
	@echo "Running type checking..."
	mypy app/ --ignore-missing-imports --show-error-codes

security:
	@echo "Running security analysis..."
	bandit -r app/ -f json -o security-report.json
	safety check --json --output safety-report.json

quality: lint type-check security
	@echo "Running complete quality checks..."

# Build targets
build:
	@echo "Building package..."
	python -m build

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage*
	rm -rf coverage.xml
	rm -rf coverage.json
	rm -rf test_reports/
	rm -rf benchmark.json
	rm -rf benchmark-histogram/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

docs:
	@echo "Building documentation..."
	cd docs && make html

# CI/CD targets
ci:
	@echo "Running CI/CD test suite..."
	pytest tests/ --cov=app --cov-branch --cov-report=xml --cov-report=term-missing --cov-fail-under=80 -v

tox:
	@echo "Running tests with tox..."
	tox

# Development targets
migrate:
	@echo "Running database migrations..."
	alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration name: " name; \
	alembic revision --autogenerate -m "$$name"

run-server:
	@echo "Starting development server..."
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	@echo "Starting Celery worker..."
	celery -A celery_app.celery_app worker --loglevel=info

run-beat:
	@echo "Starting Celery beat..."
	celery -A celery_app.celery_app beat --loglevel=info

# Docker targets
docker-build:
	@echo "Building Docker image..."
	docker build -t ai-news-aggregator .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 ai-news-aggregator

docker-test:
	@echo "Running tests in Docker..."
	docker build -f Dockerfile.test -t ai-news-aggregator-test .
	docker run ai-news-aggregator-test

# Utility targets
shell:
	@echo "Starting Python shell with app context..."
	python -c "from app.main import app; from app.db.database import engine; from app.db.models import Base; Base.metadata.create_all(bind=engine); import IPython; IPython.embed()"

db-shell:
	@echo "Starting database shell..."
	@if command -v sqlite3 >/dev/null 2>&1; then \
		echo "Opening SQLite shell..."; \
		sqlite3 app.db.sqlite3; \
	else \
		echo "sqlite3 not found. Using Python shell instead."; \
		python -c "import sqlite3; conn = sqlite3.connect('app.db.sqlite3'); conn.execute('SELECT * FROM sqlite_master'); conn.close()"; \
	fi

# Benchmark targets
benchmark:
	@echo "Running benchmarks..."
	pytest tests/ -m performance --benchmark-only --benchmark-compare=master

benchmark-save:
	@echo "Saving benchmark baseline..."
	pytest tests/ -m performance --benchmark-only --benchmark-save=baseline

# Environment setup
setup-env:
	@echo "Setting up development environment..."
	cp .env.example .env || echo "No .env.example found, skipping..."
	@echo "Environment file created. Please configure your settings."

# Quick development workflow
dev: format lint test-fast
	@echo "Development workflow completed!"

# Full quality check
full-check: format lint type-check security test-coverage
	@echo "Full quality check completed!"

# Release workflow
prepare-release: clean build test lint type-check security
	@echo "Release preparation completed!"

# Maintenance targets
update-deps:
	@echo "Updating dependencies..."
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt

check-deps:
	@echo "Checking for dependency updates..."
	pip list --outdated

# Monitoring and health checks
health-check:
	@echo "Running health checks..."
	curl -f http://localhost:8000/api/v1/health/ || echo "Server not responding"
	@echo "Database check..."
	python -c "from app.db.database import engine; engine.connect(); print('Database OK')"
	@echo "Redis check..."
	python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); r.ping(); print('Redis OK')" || echo "Redis not available"

# Logging and debugging
logs:
	@echo "Application logs (last 50 lines)..."
	tail -n 50 logs/app.log || echo "No application logs found"

debug:
	@echo "Debug information:"
	@echo "Python version: $$(python --version)"
	@echo "Pip version: $$(pip --version)"
	@echo "Virtual environment: $${VIRTUAL_ENV:-'Not in virtual environment'}"
	@echo "Current directory: $$(pwd)"
	@echo "Environment variables:"
	@env | grep -E "(DATABASE|REDIS|OPENAI|CELERY)" | head -10 || echo "No relevant environment variables found"

# Backup and restore
backup-db:
	@echo "Backing up database..."
	cp app.db.sqlite3 app.db.sqlite3.backup.$(shell date +%Y%m%d_%H%M%S) || echo "No SQLite database to backup"

restore-db:
	@echo "Available database backups:"
	@ls -la app.db.sqlite3.backup.* 2>/dev/null || echo "No backups found"
	@echo "To restore: cp app.db.sqlite3.backup.YYYYMMDD_HHMMSS app.db.sqlite3"

# Performance monitoring
profile:
	@echo "Running performance profiling..."
	python -m cProfile -o profile_output.prof -m pytest tests/ -k "test_search" --tb=no

memory-profile:
	@echo "Running memory profiling..."
	python -m memory_profiler tests/test_services.py

# Feature flags and configuration
show-config:
	@echo "Current configuration:"
	@echo "Testing: $${TESTING:-false}"
	@echo "Debug: $${DEBUG:-false}"
	@echo "Database URL: $${DATABASE_URL:-'not set'}"
	@echo "Redis URL: $${REDIS_URL:-'not set'}"

# Deployment preparation
deploy-check: test lint type-check security
	@echo "Deployment checks completed!"

# Quick start
start: install-dev migrate run-server
	@echo "Development server starting..."

# All-in-one development setup
setup: install-dev setup-env migrate
	@echo "Development environment setup completed!"
	@echo "Run 'make start' to start the development server"