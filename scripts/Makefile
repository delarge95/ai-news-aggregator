# Makefile para AI News Aggregator
# Uso: make [objetivo]

.PHONY: help install deploy health backup rollback migrate scale monitor logs status config clean

# Configuración
PROJECT_NAME := ai-news-aggregator
DOCKER_COMPOSE := docker-compose
OPS_SCRIPT := ./scripts/ops.sh

# Colores para output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Objetivo principal
.DEFAULT_GOAL := help

help: ## Muestra esta ayuda
	@echo "$(CYAN)AI News Aggregator - Makefile$(RESET)"
	@echo ""
	@echo "Uso: make [objetivo]"
	@echo ""
	@echo "Objetivos disponibles:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==============================================================================
# INSTALACIÓN Y CONFIGURACIÓN
# ==============================================================================

install: ## Instalación inicial
	@echo "$(YELLOW)Iniciando instalación...$(RESET)"
	@cp scripts/.env.example .env || true
	@cp scripts/scaling-config.json.example scaling-config.json || true
	@chmod +x scripts/*.sh || true
	@$(OPS_SCRIPT) config
	@echo "$(GREEN)✅ Instalación completada$(RESET)"

setup-dev: ## Configuración para desarrollo
	@echo "$(YELLOW)Configurando entorno de desarrollo...$(RESET)"
	@export DEPLOY_ENV=development
	@export LOG_LEVEL=DEBUG
	@export BACKUP_ENABLED=false
	@export WEB_SERVER=docker
	@echo "$(GREEN)✅ Entorno de desarrollo configurado$(RESET)"

setup-prod: ## Configuración para producción
	@echo "$(YELLOW)Configurando entorno de producción...$(RESET)"
	@export DEPLOY_ENV=production
	@export LOG_LEVEL=WARN
	@export BACKUP_ENABLED=true
	@export WEB_SERVER=nginx
	@export AUTO_ROLLBACK=true
	@echo "$(GREEN)✅ Entorno de producción configurado$(RESET)"

# ==============================================================================
# OPERACIONES BÁSICAS
# ==============================================================================

start: ## Iniciar la aplicación
	@echo "$(YELLOW)Iniciando AI News Aggregator...$(RESET)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Aplicación iniciada$(RESET)"
	@make health

stop: ## Detener la aplicación
	@echo "$(YELLOW)Deteniendo AI News Aggregator...$(RESET)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Aplicación detenida$(RESET)"

restart: ## Reiniciar la aplicación
	@echo "$(YELLOW)Reiniciando AI News Aggregator...$(RESET)"
	@make stop
	@sleep 3
	@make start

build: ## Construir imágenes Docker
	@echo "$(YELLOW)Construyendo imágenes Docker...$(RESET)"
	@$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✅ Imágenes construidas$(RESET)"

# ==============================================================================
# DEPLOYMENT Y ROLLBACK
# ==============================================================================

deploy: ## Deploy completo
	@echo "$(YELLOW)Iniciando deployment...$(RESET)"
	@$(OPS_SCRIPT) deploy

deploy-dry-run: ## Simulación de deployment
	@echo "$(YELLOW)Simulando deployment...$(RESET)"
	@DRY_RUN=true $(OPS_SCRIPT) deploy --dry-run

deploy-backend: ## Deploy solo backend
	@echo "$(YELLOW)Deploying backend...$(RESET)"
	@$(OPS_SCRIPT) deploy --backend-only

deploy-frontend: ## Deploy solo frontend
	@echo "$(YELLOW)Deploying frontend...$(RESET)"
	@$(OPS_SCRIPT) deploy --frontend-only

rollback: ## Rollback al último backup
	@echo "$(YELLOW)Ejecutando rollback...$(RESET)"
	@$(OPS_SCRIPT) rollback

rollback-list: ## Listar backups disponibles
	@echo "$(YELLOW)Backups disponibles:$(RESET)"
	@$(OPS_SCRIPT) rollback --list

# ==============================================================================
# HEALTH CHECKS
# ==============================================================================

health: ## Verificación completa de salud
	@echo "$(YELLOW)Ejecutando health checks...$(RESET)"
	@$(OPS_SCRIPT) health

health-services: ## Verificar solo servicios Docker
	@echo "$(YELLOW)Verificando servicios...$(RESET)"
	@$(OPS_SCRIPT) health services

health-endpoints: ## Verificar solo endpoints
	@echo "$(YELLOW)Verificando endpoints...$(RESET)"
	@$(OPS_SCRIPT) health endpoints

health-database: ## Verificar solo base de datos
	@echo "$(YELLOW)Verificando base de datos...$(RESET)"
	@$(OPS_SCRIPT) health database

health-json: ## Health check con salida JSON
	@echo "$(YELLOW)Health check en formato JSON...$(RESET)"
	@$(OPS_SCRIPT) health --json

# ==============================================================================
# BACKUP Y RESTORE
# ==============================================================================

backup: ## Crear backup completo
	@echo "$(YELLOW)Creando backup...$(RESET)"
	@$(OPS_SCRIPT) backup

backup-db: ## Backup solo base de datos
	@echo "$(YELLOW)Creando backup de BD...$(RESET)"
	@$(OPS_SCRIPT) backup database

backup-code: ## Backup solo código
	@echo "$(YELLOW)Creando backup de código...$(RESET)"
	@$(OPS_SCRIPT) backup code

backup-list: ## Listar backups disponibles
	@echo "$(YELLOW)Backups disponibles:$(RESET)"
	@$(OPS_SCRIPT) backup --list

# ==============================================================================
# MIGRACIONES
# ==============================================================================

migrate: ## Ejecutar migraciones
	@echo "$(YELLOW)Ejecutando migraciones...$(RESET)"
	@$(OPS_SCRIPT) migrate

migrate-create: ## Crear nueva migración (requiere descripción)
	@if [ -z "$(DESCRIPTION)" ]; then \
		echo "$(RED)Error: Debe proporcionar DESCRIPTION=$(RESET)"; \
		echo "Uso: make migrate-create DESCRIPTION='descripción_de_la_migración'"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Creando migración: $(DESCRIPTION)$(RESET)"
	@$(OPS_SCRIPT) migrate --create "$(DESCRIPTION)"

migrate-status: ## Ver estado de migraciones
	@echo "$(YELLOW)Estado de migraciones:$(RESET)"
	@$(OPS_SCRIPT) migrate --status

migrate-rollback: ## Rollback de migraciones
	@echo "$(YELLOW)Rollback de migraciones...$(RESET)"
	@$(OPS_SCRIPT) migrate --rollback

# ==============================================================================
# ESCALADO
# ==============================================================================

scale: ## Auto-scaling
	@echo "$(YELLOW)Ejecutando auto-scaling...$(RESET)"
	@$(OPS_SCRIPT) scale auto

scale-up: ## Escalar servicios hacia arriba (requiere SERVICE y REPLICAS)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: Debe proporcionar SERVICE=$(RESET)"; \
		echo "Uso: make scale-up SERVICE=celery_worker REPLICAS=2"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Escalando $(SERVICE) hacia arriba (+$(REPLICAS))...$(RESET)"
	@$(OPS_SCRIPT) scale up $(SERVICE) $(REPLICAS)

scale-down: ## Escalar servicios hacia abajo (requiere SERVICE y REPLICAS)
	@if [ -z "$(SERVICE)" ]; then \
		echo "$(RED)Error: Debe proporcionar SERVICE=$(RESET)"; \
		echo "Uso: make scale-down SERVICE=celery_worker REPLICAS=1"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Escalando $(SERVICE) hacia abajo (-$(REPLICAS))...$(RESET)"
	@$(OPS_SCRIPT) scale down $(SERVICE) $(REPLICAS)

scale-status: ## Ver estado de escalado
	@echo "$(YELLOW)Estado de escalado:$(RESET)"
	@$(OPS_SCRIPT) scale status

# ==============================================================================
# MODO MANTENIMIENTO
# ==============================================================================

maintenance-on: ## Activar modo mantenimiento (requiere TITLE, MESSAGE, ETA)
	@if [ -z "$(TITLE)" ] || [ -z "$(MESSAGE)" ] || [ -z "$(ETA)" ]; then \
		echo "$(RED)Error: Debe proporcionar TITLE, MESSAGE y ETA$(RESET)"; \
		echo "Uso: make maintenance-on TITLE='Mantenimiento' MESSAGE='Actualizando sistema' ETA='30 minutos'"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Activando modo mantenimiento...$(RESET)"
	@$(OPS_SCRIPT) maintenance on "$(TITLE)" "$(MESSAGE)" "$(ETA)"

maintenance-off: ## Desactivar modo mantenimiento
	@echo "$(YELLOW)Desactivando modo mantenimiento...$(RESET)"
	@$(OPS_SCRIPT) maintenance off

maintenance-status: ## Ver estado de mantenimiento
	@echo "$(YELLOW)Estado de mantenimiento:$(RESET)"
	@$(OPS_SCRIPT) maintenance status

# ==============================================================================
# CERTIFICADOS SSL
# ==============================================================================

cert-renew: ## Renovar certificados SSL
	@echo "$(YELLOW)Renovando certificados SSL...$(RESET)"
	@$(OPS_SCRIPT) certificates renew

cert-status: ## Ver estado de certificados
	@echo "$(YELLOW)Estado de certificados:$(RESET)"
	@$(OPS_SCRIPT) certificates status

cert-generate: ## Generar certificados auto-firmados (desarrollo)
	@echo "$(YELLOW)Generando certificados auto-firmados...$(RESET)"
	@$(OPS_SCRIPT) certificates generate development

cert-backup: ## Backup de certificados
	@echo "$(YELLOW)Creando backup de certificados...$(RESET)"
	@$(OPS_SCRIPT) certificates backup

# ==============================================================================
# MONITOREO Y LOGS
# ==============================================================================

logs: ## Ver logs de todos los servicios
	@echo "$(YELLOW)Mostrando logs...$(RESET)"
	@$(OPS_SCRIPT) logs all

logs-backend: ## Ver logs del backend
	@echo "$(YELLOW)Logs del backend:$(RESET)"
	@$(OPS_SCRIPT) logs backend

logs-frontend: ## Ver logs del frontend
	@echo "$(YELLOW)Logs del frontend:$(RESET)"
	@$(OPS_SCRIPT) logs frontend

logs-db: ## Ver logs de la base de datos
	@echo "$(YELLOW)Logs de la base de datos:$(RESET)"
	@$(OPS_SCRIPT) logs postgres

monitor: ## Monitoreo en tiempo real (Ctrl+C para salir)
	@echo "$(YELLOW)Iniciando monitoreo en tiempo real...$(RESET)"
	@$(OPS_SCRIPT) monitor

# ==============================================================================
# ESTADO Y CONFIGURACIÓN
# ==============================================================================

status: ## Ver estado general del sistema
	@echo "$(YELLOW)Estado del sistema:$(RESET)"
	@$(OPS_SCRIPT) status

config: ## Ver configuración actual
	@echo "$(YELLOW)Configuración actual:$(RESET)"
	@$(OPS_SCRIPT) config

list: ## Listar recursos disponibles
	@echo "$(YELLOW)Recursos disponibles:$(RESET)"
	@$(OPS_SCRIPT) list

# ==============================================================================
# UTILIDADES
# ==============================================================================

clean: ## Limpiar recursos temporales
	@echo "$(YELLOW)Limpiando recursos temporales...$(RESET)"
	@$(OPS_SCRIPT) cleanup
	@docker system prune -f
	@echo "$(GREEN)✅ Cleanup completado$(RESET)"

clean-all: clean ## Limpiar todo (incluyendo volúmenes)
	@echo "$(YELLOW)Limpiando todo...$(RESET)"
	@docker system prune -a -f
	@docker volume prune -f
	@echo "$(GREEN)✅ Cleanup completo$(RESET)"

# ==============================================================================
# DOCUMENTACIÓN Y AYUDA
# ==============================================================================

docs: ## Mostrar documentación
	@$(OPS_SCRIPT) docs

help-detailed: ## Ayuda detallada
	@$(OPS_SCRIPT) help

# ==============================================================================
# TESTING
# ==============================================================================

test: ## Ejecutar tests
	@echo "$(YELLOW)Ejecutando tests...$(RESET)"
	@cd backend && python -m pytest tests/ -v

test-integration: ## Ejecutar tests de integración
	@echo "$(YELLOW)Ejecutando tests de integración...$(RESET)"
	@cd backend && python -m pytest tests/integration/ -v

test-performance: ## Ejecutar tests de rendimiento
	@echo "$(YELLOW)Ejecutando tests de rendimiento...$(RESET)"
	@bash tests/performance/run_performance_tests.sh

# ==============================================================================
# DESARROLLO
# ==============================================================================

dev-install: ## Instalar dependencias de desarrollo
	@echo "$(YELLOW)Instalando dependencias de desarrollo...$(RESET)"
	@cd backend && pip install -r requirements-dev.txt
	@cd frontend && npm install
	@echo "$(GREEN)✅ Dependencias instaladas$(RESET)"

dev-setup: dev-install setup-dev ## Setup completo para desarrollo
	@echo "$(GREEN)✅ Entorno de desarrollo listo$(RESET)"

dev-lint: ## Linting del código
	@echo "$(YELLOW)Ejecutando linting...$(RESET)"
	@cd backend && python -m flake8 app/
	@cd frontend && npx eslint src/ --ext .ts,.tsx

dev-format: ## Formatear código
	@echo "$(YELLOW)Formateando código...$(RESET)"
	@cd backend && python -m black app/ && python -m isort app/
	@cd frontend && npx prettier --write src/

# ==============================================================================
# COMANDOS COMPUESTOS
# ==============================================================================

# Deployment completo
deploy-production: backup migrate deploy health ## Deploy completo para producción

# Rollback de emergencia
emergency-rollback: ## Rollback de emergencia
	@echo "$(RED)Ejecutando rollback de emergencia...$(RESET)"
	@$(OPS_SCRIPT) rollback
	@make health

# Preparación para mantenimiento
prepare-maintenance: backup schedule-maintenance ## Preparar para mantenimiento
	@echo "$(GREEN)✅ Preparación para mantenimiento completada$(RESET)"

schedule-maintenance: ## Programar mantenimiento (requiere TIME y DURATION)
	@if [ -z "$(TIME)" ] || [ -z "$(DURATION)" ]; then \
		echo "$(RED)Error: Debe proporcionar TIME y DURATION$(RESET)"; \
		echo "Uso: make schedule-maintenance TIME='02:00' DURATION='1h'"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Programando mantenimiento para $(TIME) (duración: $(DURATION))...$(RESET)"
	@$(OPS_SCRIPT) maintenance schedule "$(TIME)" "$(DURATION)"

# Health check completo con métricas
health-full: health health-json health-metrics ## Health check completo

health-metrics: ## Mostrar métricas de escalado
	@echo "$(YELLOW)Métricas de escalado:$(RESET)"
	@$(OPS_SCRIPT) scale metrics

# ==============================================================================
# INFORMACIÓN DEL PROYECTO
# ==============================================================================

info: ## Mostrar información del proyecto
	@echo "$(CYAN)AI News Aggregator - Información del Proyecto$(RESET)"
	@echo "=========================================="
	@echo "Proyecto: $(PROJECT_NAME)"
	@echo "Docker Compose: $(DOCKER_COMPOSE)"
	@echo "Script de operaciones: $(OPS_SCRIPT)"
	@echo "Entorno actual: $(DEPLOY_ENV:-no configurado}"
	@echo ""
	@echo "Servicios disponibles:"
	@docker-compose config --services 2>/dev/null || echo "docker-compose.yml no encontrado"
	@echo ""
	@echo "Para más información: make docs"

version: ## Mostrar versión
	@echo "$(PROJECT_NAME) v1.0.0"

# ==============================================================================
# OBJETIVOS ESPECIALES
# ==============================================================================

# Instalar herramientas necesarias
install-tools: ## Instalar herramientas necesarias (jq, netcat, etc.)
	@echo "$(YELLOW)Instalando herramientas necesarias...$(RESET)"
	@command -v jq >/dev/null 2>&1 || (echo "Instalando jq..." && apt-get update && apt-get install -y jq)
	@command -v nc >/dev/null 2>&1 || (echo "Instalando netcat..." && apt-get update && apt-get install -y netcat-openbsd)
	@command -v certbot >/dev/null 2>&1 || echo "Certbot no instalado (opcional para SSL)"
	@echo "$(GREEN)✅ Herramientas instaladas$(RESET)"

# Verificar configuración
verify-setup: ## Verificar que todo esté configurado correctamente
	@echo "$(YELLOW)Verificando configuración...$(RESET)"
	@$(OPS_SCRIPT) config
	@echo ""
	@make install-tools
	@echo ""
	@echo "$(GREEN)✅ Configuración verificada$(RESET)"

# Mostrar logs recientes
recent-logs: ## Mostrar logs recientes
	@echo "$(YELLOW)Logs recientes:$(RESET)"
	@find ./logs -name "*.log" -mtime -1 -exec tail -20 {} \; 2>/dev/null || echo "No hay logs recientes"

# ==============================================================================
# LIMPIEZA DE ARCHIVOS OBJETIVO
# ==============================================================================

# Estos archivos no deben ser limpiados automáticamente
.PHONY: all arch clean actual-install

# Solo para evitar conflictos con variables de entorno
.env:
	@echo "$(RED)No se puede eliminar .env$(RESET)"

docker-compose.yml:
	@echo "$(RED)No se puede eliminar docker-compose.yml$(RESET)"

# ==============================================================================
# NOTAS FINALES
# ==============================================================================

# Todos los objetivos están documentados con "## Descripción"
# Los comandos de desarrollo requieren instalación previa de dependencias
# Para desarrollo: make dev-setup
# Para producción: make setup-prod && make deploy-production