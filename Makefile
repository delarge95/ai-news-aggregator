# Makefile for AI News Aggregator
# Comprehensive build, test, and deployment automation

.PHONY: help install dev test test-unit test-integration test-coverage test-e2e lint format type-check security clean build run stop logs monitor

# Default target
help: ## Show this help message
	@echo "🤖 AI News Aggregator - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Testing Commands:"
	@echo "  test-coverage        Run full test suite with coverage"
	@echo "  test-unit           Run only unit tests"
	@echo "  test-integration    Run only integration tests"
	@echo "  test-e2e            Run end-to-end tests"
	@echo ""
	@echo "Development Commands:"
	@echo "  install             Install dependencies"
	@echo "  dev-backend         Start backend in development mode"
	@echo "  dev-frontend        Start frontend in development mode"
	@echo "  dev                 Start both backend and frontend"

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[0;33m
BLUE = \033[0;34m
PURPLE = \033[0;35m
CYAN = \033[0;36m
NC = \033[0m # No Color

# Project paths
PROJECT_ROOT = $(dir $(CURDIR))
BACKEND_DIR = backend
FRONTEND_DIR = frontend/ai-news-frontend
COVERAGE_DIR = htmlcov
REPORTS_DIR = reports

# Python and Node versions
PYTHON = python3
PYTEST = pytest
COVERAGE = coverage
NODE = node
PNPM = pnpm
PYTEST_ARGS = --cov=app --cov-report=term-missing --cov-report=html:$(COVERAGE_DIR) --cov-report=xml:$(PROJECT_ROOT)/$(REPORTS_DIR)/coverage.xml --cov-report=json:$(PROJECT_ROOT)/$(REPORTS_DIR)/coverage.json --cov-fail-under=80 --cov-branch

# =============================================================================
# DEPENDENCIES AND SETUP
# =============================================================================

install: ## Install all dependencies (backend and frontend)
	@echo "$(BLUE)📦 Installing dependencies...$(NC)"
	@echo "$(YELLOW)Installing backend dependencies...$(NC)"
	$(MAKE) install-backend
	@echo "$(YELLOW)Installing frontend dependencies...$(NC)"
	$(MAKE) install-frontend

install-backend: ## Install backend dependencies
	@echo "$(CYAN)🐍 Installing Python dependencies...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install --upgrade pip
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install pytest-cov pytest-asyncio pytest-xdist pytest-timeout

install-frontend: ## Install frontend dependencies
	@echo "$(CYAN)⚛️  Installing Node.js dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) install --prefer-offline

# =============================================================================
# DEVELOPMENT SERVERS
# =============================================================================

dev-backend: ## Start backend development server
	@echo "$(GREEN)🚀 Starting backend development server...$(NC)"
	cd $(BACKEND_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start frontend development server
	@echo "$(GREEN)🎨 Starting frontend development server...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) run dev

dev: ## Start both backend and frontend in development mode
	@echo "$(GREEN)🚀 Starting full development environment...$(NC)"
	@echo "$(BLUE)Backend: http://localhost:8000$(NC)"
	@echo "$(BLUE)Frontend: http://localhost:3000$(NC)"
	@echo "$(BLUE)API Docs: http://localhost:8000/docs$(NC)"
	@make dev-backend &
	@make dev-frontend

# =============================================================================
# TESTING
# =============================================================================

test: test-coverage ## Run all tests with coverage (alias)

test-coverage: ## Run full test suite with comprehensive coverage
	@echo "$(BLUE)🧪 Running comprehensive test suite with coverage...$(NC)"
	@mkdir -p $(REPORTS_DIR)
	@echo "$(CYAN)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) $(PYTEST_ARGS) -v --tb=short --durations=10
	@echo "$(GREEN)✅ Backend tests completed$(NC)"
	@echo "$(CYAN)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) test --coverage --watchAll=false
	@echo "$(GREEN)✅ Frontend tests completed$(NC)"
	@echo "$(GREEN)📊 Coverage reports generated in $(COVERAGE_DIR) and $(REPORTS_DIR)/$(NC)"

test-unit: ## Run only unit tests (fast, isolated)
	@echo "$(BLUE)🔬 Running unit tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) -m "not integration and not slow" --cov=app --cov-report=term-missing -x
	@echo "$(GREEN)✅ Unit tests completed$(NC)"

test-integration: ## Run only integration tests
	@echo "$(BLUE)🔗 Running integration tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) -m integration --cov=app --cov-append -v
	@echo "$(GREEN)✅ Integration tests completed$(NC)"

test-performance: ## Run performance tests
	@echo "$(BLUE)⚡ Running performance tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) -m performance --cov=app --cov-append --durations=0 -v
	@echo "$(GREEN)✅ Performance tests completed$(NC)"

test-e2e: ## Run end-to-end tests
	@echo "$(GREEN)🎭 Running end-to-end tests...$(NC)"
	@echo "$(YELLOW)E2E tests require application to be running$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) -m e2e -v

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)👀 Running tests in watch mode...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) $(PYTEST_ARGS) --cov-append --lf --ff -x

test-parallel: ## Run tests in parallel (requires pytest-xdist)
	@echo "$(BLUE)🚀 Running tests in parallel...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) $(PYTEST_ARGS) -n auto -v

# Frontend specific testing
test-frontend: ## Run frontend tests
	@echo "$(BLUE)⚛️  Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) test --coverage --watchAll=false

test-frontend-watch: ## Run frontend tests in watch mode
	@echo "$(BLUE)👀 Running frontend tests in watch mode...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) test

# =============================================================================
# COVERAGE COMMANDS
# =============================================================================

coverage-report: ## Generate and display coverage report
	@echo "$(BLUE)📊 Generating coverage report...$(NC)"
	cd $(BACKEND_DIR) && $(COVERAGE) report --show-missing --fail-under=80
	@echo "$(CYAN)📁 HTML report: file://$(PROJECT_ROOT)/$(COVERAGE_DIR)/index.html$(NC)"

coverage-html: ## Generate HTML coverage report
	@echo "$(BLUE)📄 Generating HTML coverage report...$(NC)"
	cd $(BACKEND_DIR) && $(COVERAGE) html --title="AI News Aggregator - Coverage Report"
	@echo "$(GREEN)✅ HTML report generated: $(COVERAGE_DIR)/index.html$(NC)"

coverage-xml: ## Generate XML coverage report
	@echo "$(BLUE)📄 Generating XML coverage report...$(NC)"
	cd $(BACKEND_DIR) && $(COVERAGE) xml
	@echo "$(GREEN)✅ XML report generated: $(REPORTS_DIR)/coverage.xml$(NC)"

coverage-json: ## Generate JSON coverage report
	@echo "$(BLUE)📄 Generating JSON coverage report...$(NC)"
	cd $(BACKEND_DIR) && $(COVERAGE) json
	@echo "$(GREEN)✅ JSON report generated: $(PROJECT_ROOT)/$(REPORTS_DIR)/coverage.json$(NC)"

coverage-serve: ## Serve HTML coverage report in browser
	@echo "$(BLUE)🌐 Serving coverage report...$(NC)"
	@echo "$(CYAN)Open: http://localhost:8001$(NC)"
	cd $(PROJECT_ROOT) && python3 -m http.server 8001 --directory $(COVERAGE_DIR)

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: lint-backend lint-frontend ## Run all linting checks

lint-backend: ## Lint backend code
	@echo "$(BLUE)🔍 Linting backend code...$(NC)"
	cd $(BACKEND_DIR) && python -m flake8 app/ --max-line-length=88 --exclude=__pycache__,venv,.venv,migrations
	cd $(BACKEND_DIR) && python -m black --check app/ tests/
	cd $(BACKEND_DIR) && python -m isort --check-only app/ tests/
	@echo "$(GREEN)✅ Backend linting passed$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(BLUE)🔍 Linting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) run lint
	@echo "$(GREEN)✅ Frontend linting passed$(NC)"

format: format-backend format-frontend ## Format all code

format-backend: ## Format backend code
	@echo "$(BLUE)🎨 Formatting backend code...$(NC)"
	cd $(BACKEND_DIR) && python -m black app/ tests/
	cd $(BACKEND_DIR) && python -m isort app/ tests/
	@echo "$(GREEN)✅ Backend code formatted$(NC)"

format-frontend: ## Format frontend code
	@echo "$(BLUE)🎨 Formatting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) run format
	@echo "$(GREEN)✅ Frontend code formatted$(NC)"

type-check: ## Run type checking
	@echo "$(BLUE)🔍 Running type checks...$(NC)"
	cd $(BACKEND_DIR) && python -m mypy app/ --ignore-missing-imports
	cd $(FRONTEND_DIR) && $(PNPM) run type-check
	@echo "$(GREEN)✅ Type checks passed$(NC)"

security: ## Run security checks
	@echo "$(BLUE)🔒 Running security checks...$(NC)"
	cd $(BACKEND_DIR) && python -m safety check
	cd $(FRONTEND_DIR) && $(PNPM) audit
	@echo "$(GREEN)✅ Security checks passed$(NC)"

# =============================================================================
# BUILD AND DEPLOYMENT
# =============================================================================

build: build-backend build-frontend ## Build all components

build-backend: ## Build backend Docker image
	@echo "$(BLUE)🐳 Building backend Docker image...$(NC)"
	docker build -t ai-news-backend $(BACKEND_DIR)/
	@echo "$(GREEN)✅ Backend image built$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(BLUE)⚛️  Building frontend for production...$(NC)"
	cd $(FRONTEND_DIR) && $(PNPM) run build
	@echo "$(GREEN)✅ Frontend built$(NC)"

# =============================================================================
# CONTAINER MANAGEMENT
# =============================================================================

up: ## Start all services with Docker Compose
	@echo "$(GREEN)🚀 Starting services...$(NC)"
	docker-compose up -d

down: ## Stop all services
	@echo "$(RED)🛑 Stopping services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(YELLOW)🔄 Restarting services...$(NC)"
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f db

logs-redis: ## Show Redis logs
	docker-compose logs -f redis

# =============================================================================
# UTILITIES
# =============================================================================

clean: ## Clean build artifacts and cache
	@echo "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	rm -rf $(PROJECT_ROOT)/$(COVERAGE_DIR)
	rm -rf $(PROJECT_ROOT)/$(REPORTS_DIR)
	rm -rf $(BACKEND_DIR)/.pytest_cache
	rm -rf $(BACKEND_DIR)/__pycache__
	rm -rf $(BACKEND_DIR)/.coverage
	rm -rf $(BACKEND_DIR)/htmlcov
	rm -rf $(BACKEND_DIR)/coverage.xml
	rm -rf $(BACKEND_DIR)/coverage.json
	cd $(FRONTEND_DIR) && rm -rf dist node_modules/.vite
	@echo "$(GREEN)✅ Cleaned all artifacts$(NC)"

monitor: ## Show system resource usage
	@echo "$(BLUE)📊 System monitoring...$(NC)"
	@echo "Docker containers:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Disk usage:"
	@du -sh $(PROJECT_ROOT)/$(BACKEND_DIR) $(PROJECT_ROOT)/$(FRONTEND_DIR) 2>/dev/null || echo "Disk usage check skipped"

# =============================================================================
# CI/CD HELPERS
# =============================================================================

ci-test: ## Run tests for CI environment (minimal output)
	@echo "$(BLUE)🤖 Running CI tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) $(PYTEST_ARGS) --tb=line -q
	@echo "$(GREEN)✅ CI tests passed$(NC)"

ci-install: ## Install dependencies for CI
	@echo "$(BLUE)🤖 Installing CI dependencies...$(NC)"
	$(MAKE) install-backend
	@echo "$(GREEN)✅ CI dependencies installed$(NC)"

# Database helpers
db-migrate: ## Run database migrations
	@echo "$(BLUE)📊 Running database migrations...$(NC)"
	cd $(BACKEND_DIR) && alembic upgrade head

db-reset: ## Reset database (development only)
	@echo "$(RED)⚠️  Resetting database...$(NC)"
	cd $(BACKEND_DIR) && alembic downgrade base && alembic upgrade head
	@echo "$(GREEN)✅ Database reset$(NC)"

# Health checks
health-check: ## Check if all services are healthy
	@echo "$(BLUE)🏥 Checking service health...$(NC)"
	@curl -s http://localhost:8000/health || echo "Backend not responding"
	@curl -s http://localhost:3000 || echo "Frontend not responding"
	@echo "$(GREEN)✅ Health check completed$(NC)"

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)📚 Generating documentation...$(NC)"
	cd $(BACKEND_DIR) && python -m pydoc -w app
	@echo "$(GREEN)✅ Documentation generated$(NC)"

# Quick test for PR validation
pr-check: format lint test-unit security ## Run all checks for PR validation
	@echo "$(GREEN)✅ All PR checks passed$(NC)"

# =============================================================================
# DOCKER PRODUCTION COMMANDS
# =============================================================================

# Initialize production environment
prod-init: ## Initialize production Docker environment
	@echo "$(BLUE)🚀 Initializing production environment...$(NC)"
	chmod +x init-docker-prod.sh deploy-prod.sh
	./init-docker-prod.sh
	@echo "$(GREEN)✅ Production environment initialized$(NC)"

# Production deployment
prod-deploy: prod-init ## Full production deployment
	@echo "$(BLUE)🚀 Deploying to production...$(NC)"
	chmod +x deploy-prod.sh
	./deploy-prod.sh deploy
	@echo "$(GREEN)✅ Production deployment completed$(NC)"

prod-build: ## Build production Docker images
	@echo "$(BLUE)🐳 Building production images...$(NC)"
	./deploy-prod.sh build
	@echo "$(GREEN)✅ Production images built$(NC)"

prod-start: ## Start production services
	@echo "$(BLUE)🚀 Starting production services...$(NC)"
	./deploy-prod.sh start
	@echo "$(GREEN)✅ Production services started$(NC)"

prod-stop: ## Stop production services
	@echo "$(RED)🛑 Stopping production services...$(NC)"
	./deploy-prod.sh stop
	@echo "$(GREEN)✅ Production services stopped$(NC)"

prod-restart: ## Restart production services
	@echo "$(YELLOW)🔄 Restarting production services...$(NC)"
	./deploy-prod.sh restart
	@echo "$(GREEN)✅ Production services restarted$(NC)"

prod-status: ## Show production service status
	@echo "$(BLUE)📊 Production service status...$(NC)"
	./deploy-prod.sh status

prod-logs: ## Show production service logs
	@echo "$(BLUE)📋 Production service logs...$(NC)"
	./deploy-prod.sh logs

prod-health: ## Check production service health
	@echo "$(BLUE)🏥 Checking production health...$(NC)"
	./deploy-prod.sh health
	@echo "$(GREEN)✅ Production health check completed$(NC)"

prod-cleanup: ## Clean up production Docker resources
	@echo "$(YELLOW)🧹 Cleaning up production resources...$(NC)"
	./deploy-prod.sh cleanup
	@echo "$(GREEN)✅ Production cleanup completed$(NC)"

# Development Docker commands
dev-up: ## Start development environment with Docker
	@echo "$(BLUE)🚀 Starting development environment...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d
	@echo "$(GREEN)✅ Development environment started$(NC)"

dev-down: ## Stop development environment
	@echo "$(RED)🛑 Stopping development environment...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.override.yml down
	@echo "$(GREEN)✅ Development environment stopped$(NC)"

dev-logs: ## Show development service logs
	@echo "$(BLUE)📋 Development service logs...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f

# Quick deployment helpers
prod-quick: prod-build prod-start prod-health ## Quick production deployment (build + start + health check)
	@echo "$(GREEN)🚀 Quick production deployment completed$(NC)"

dev-quick: dev-up dev-status ## Quick development setup
	@echo "$(GREEN)🚀 Quick development setup completed$(NC)"