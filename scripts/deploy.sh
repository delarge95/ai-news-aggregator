#!/bin/bash

# deploy.sh - Script de deployment automatizado para AI News Aggregator
# Versión: 1.0.0
# Descripción: Deployment automatizado con verificaciones de salud, backup y rollback

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "deploy"

# Configuración de deployment
readonly PROJECT_NAME="ai-news-aggregator"
readonly DOCKER_COMPOSE_FILE="docker-compose.yml"
readonly BACKEND_DIR="backend"
readonly FRONTEND_DIR="frontend"
readonly DATABASE_DIR="database"

# Variables de entorno
readonly DEPLOY_ENV="${DEPLOY_ENV:-production}"
readonly BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
readonly HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-300}"
readonly ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"
readonly CLEANUP_ENABLED="${CLEANUP_ENABLED:-true}"

# URLs y puertos
readonly BACKEND_PORT="${BACKEND_PORT:-8000}"
readonly FRONTEND_PORT="${FRONTEND_PORT:-3000}"

# Funciones principales
main() {
    local action="${1:-deploy}"
    
    case "$action" in
        "deploy") deploy_application ;;
        "health-check") run_health_checks ;;
        "rollback") rollback_deployment ;;
        "cleanup") cleanup_deployment ;;
        *) usage ;;
    esac
}

deploy_application() {
    log_info "🚀 Iniciando deployment de $PROJECT_NAME"
    
    # Verificar prerrequisitos
    check_prerequisites
    
    # Realizar backup pre-deployment
    if [[ "$BACKUP_ENABLED" == "true" ]]; then
        perform_pre_deployment_backup
    fi
    
    # Ejecutar migrations de base de datos
    run_database_migrations
    
    # Construir y desplegar servicios
    build_and_deploy_services
    
    # Verificar salud de servicios
    if ! run_health_checks; then
        log_error "❌ Verificaciones de salud fallidas"
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            log_warn "Ejecutando rollback automático..."
            rollback_deployment
        fi
        exit 1
    fi
    
    # Cleanup post-deployment
    if [[ "$CLEANUP_ENABLED" == "true" ]]; then
        cleanup_deployment
    fi
    
    log_success "✅ Deployment completado exitosamente"
}

check_prerequisites() {
    log_info "Verificando prerrequisitos..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose no está instalado"
        exit 1
    fi
    
    # Verificar archivos de configuración
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        log_error "Archivo docker-compose.yml no encontrado"
        exit 1
    fi
    
    # Verificar conectividad de red
    if ! ping -c 1 google.com &> /dev/null; then
        log_warn "Problemas de conectividad de red detectados"
    fi
    
    log_success "Prerrequisitos verificados"
}

perform_pre_deployment_backup() {
    log_info "Creando backup pre-deployment..."
    
    local backup_timestamp
    backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="./backups/pre_deployment_$backup_timestamp"
    
    mkdir -p "$backup_dir"
    
    # Backup de base de datos
    if docker ps | grep -q "ai_news_postgres"; then
        docker exec ai_news_postgres pg_dump -U postgres ai_news_db > "$backup_dir/database_backup.sql"
        log_info "✅ Backup de base de datos completado"
    else
        log_warn "Base de datos no encontrada, omitiendo backup"
    fi
    
    # Backup de configuraciones
    cp docker-compose.yml "$backup_dir/" 2>/dev/null || true
    cp -r "$BACKEND_DIR/app/db/migrations/" "$backup_dir/migrations" 2>/dev/null || true
    
    # Backup de código fuente (última versión)
    if [[ -d "$BACKEND_DIR" ]]; then
        tar -czf "$backup_dir/backend_code.tar.gz" -C "$BACKEND_DIR" . 2>/dev/null || true
    fi
    
    if [[ -d "$FRONTEND_DIR" ]]; then
        tar -czf "$backup_dir/frontend_code.tar.gz" -C "$FRONTEND_DIR" . 2>/dev/null || true
    fi
    
    # Crear archivo de metadatos de backup
    cat > "$backup_dir/metadata.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "environment": "$DEPLOY_ENV",
    "services": ["postgres", "redis", "backend", "celery_worker", "celery_beat", "frontend"],
    "backup_type": "pre_deployment"
}
EOF
    
    log_success "Backup creado en: $backup_dir"
    log_deployment_event "backup_created" "{\"path\":\"$backup_dir\",\"timestamp\":\"$(date -Iseconds)\"}"
}

run_database_migrations() {
    log_info "Ejecutando migrations de base de datos..."
    
    local migrations_start_time
    migrations_start_time=$(date +%s)
    
    # Verificar que la base de datos esté disponible
    if ! wait_for_service "postgres" 5432 60; then
        log_error "Base de datos no disponible para migrations"
        exit 1
    fi
    
    # Ejecutar migrations usando el script dedicado
    if [[ -f "$SCRIPT_DIR/migrate-database.sh" ]]; then
        bash "$SCRIPT_DIR/migrate-database.sh"
    else
        log_warn "Script de migrations no encontrado, ejecutando migrations manualmente..."
        
        # Migraciones manuales (ejemplo)
        if [[ -d "$DATABASE_DIR/migrations" ]]; then
            for migration in "$DATABASE_DIR/migrations"/*.sql; do
                if [[ -f "$migration" ]]; then
                    log_info "Aplicando migración: $(basename "$migration")"
                    docker exec -i ai_news_postgres psql -U postgres -d ai_news_db < "$migration"
                fi
            done
        fi
    fi
    
    local migrations_end_time
    migrations_end_time=$(date +%s)
    local migrations_duration=$((migrations_end_time - migrations_start_time))
    
    log_success "Migrations completadas en ${migrations_duration}s"
    log_metric "database_migrations_duration" "$migrations_duration"
}

build_and_deploy_services() {
    log_info "Construyendo y desplegando servicios..."
    
    local deploy_start_time
    deploy_start_time=$(date +%s)
    
    # Detener servicios existentes
    log_info "Deteniendo servicios existentes..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true
    
    # Construir imágenes
    log_info "Construyendo imágenes Docker..."
    
    # Backend
    log_info "Construyendo imagen backend..."
    docker build -t "${PROJECT_NAME}_backend:latest" "$BACKEND_DIR"
    
    # Frontend
    log_info "Construyendo imagen frontend..."
    docker build -t "${PROJECT_NAME}_frontend:latest" "$FRONTEND_DIR"
    
    # Iniciar servicios en orden de dependencias
    log_info "Iniciando servicios..."
    
    # Servicios de infraestructura primero
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis
    
    # Esperar a que estén listos
    log_info "Esperando que la base de datos esté lista..."
    wait_for_service "postgres" 5432 60
    
    log_info "Esperando que Redis esté listo..."
    wait_for_service "redis" 6379 60
    
    # Iniciar servicios de aplicación
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d backend celery_worker celery_beat frontend
    
    local deploy_end_time
    deploy_end_time=$(date +%s)
    local deploy_duration=$((deploy_end_time - deploy_start_time))
    
    log_success "Servicios desplegados en ${deploy_duration}s"
    log_metric "deployment_duration" "$deploy_duration"
    log_deployment_event "services_deployed" "{\"duration\":$deploy_duration,\"timestamp\":\"$(date -Iseconds)\"}"
}

wait_for_service() {
    local service_name="$1"
    local port="$2"
    local timeout="${3:-60}"
    local start_time
    
    start_time=$(date +%s)
    
    log_info "Esperando servicio $service_name en puerto $port..."
    
    while true; do
        if nc -z localhost "$port" 2>/dev/null; then
            log_success "Servicio $service_name disponible"
            return 0
        fi
        
        if [[ $(($(date +%s) - start_time)) -ge $timeout ]]; then
            log_error "Timeout esperando servicio $service_name"
            return 1
        fi
        
        sleep 2
    done
}

run_health_checks() {
    log_info "Ejecutando verificaciones de salud..."
    
    local health_check_start_time
    health_check_start_time=$(date +%s)
    local failed_checks=0
    
    # Verificar servicios Docker
    log_info "Verificando estado de contenedores..."
    local containers=("ai_news_postgres" "ai_news_redis" "ai_news_backend" "ai_news_celery" "ai_news_celery_beat" "ai_news_frontend")
    
    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            if docker inspect "$container" | grep -q '"Status": "running"'; then
                log_success "✅ $container: OK"
            else
                log_error "❌ $container: No ejecutándose"
                ((failed_checks++))
            fi
        else
            log_error "❌ $container: No encontrado"
            ((failed_checks++))
        fi
    done
    
    # Verificar endpoints de salud
    log_info "Verificando endpoints de salud..."
    
    # Backend health endpoint
    if curl -f -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
        log_success "✅ Backend health: OK"
    else
        log_error "❌ Backend health: FAIL"
        ((failed_checks++))
    fi
    
    # Frontend access
    if curl -f -s "http://localhost:$FRONTEND_PORT" > /dev/null; then
        log_success "✅ Frontend access: OK"
    else
        log_error "❌ Frontend access: FAIL"
        ((failed_checks++))
    fi
    
    # Verificar conectividad de base de datos
    if docker exec ai_news_postgres pg_isready -U postgres > /dev/null; then
        log_success "✅ Database connectivity: OK"
    else
        log_error "❌ Database connectivity: FAIL"
        ((failed_checks++))
    fi
    
    # Verificar Redis
    if docker exec ai_news_redis redis-cli ping | grep -q PONG; then
        log_success "✅ Redis connectivity: OK"
    else
        log_error "❌ Redis connectivity: FAIL"
        ((failed_checks++))
    fi
    
    local health_check_end_time
    health_check_end_time=$(date +%s)
    local health_check_duration=$((health_check_end_time - health_check_start_time))
    
    log_metric "health_check_duration" "$health_check_duration"
    
    if [[ $failed_checks -eq 0 ]]; then
        log_success "✅ Todas las verificaciones de salud pasaron (${health_check_duration}s)"
        return 0
    else
        log_error "❌ $failed_checks verificaciones de salud fallaron"
        return 1
    fi
}

rollback_deployment() {
    log_warn "🔄 Iniciando rollback de deployment..."
    
    # Encontrar backup más reciente
    local latest_backup
    latest_backup=$(find ./backups -name "pre_deployment_*" -type d | sort | tail -1)
    
    if [[ -z "$latest_backup" ]] || [[ ! -d "$latest_backup" ]]; then
        log_error "No se encontró backup para rollback"
        exit 1
    fi
    
    log_info "Rollback desde: $latest_backup"
    
    # Detener servicios actuales
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans
    
    # Restaurar base de datos si existe backup
    if [[ -f "$latest_backup/database_backup.sql" ]]; then
        log_info "Restaurando base de datos..."
        
        # Iniciar solo la base de datos
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis
        wait_for_service "postgres" 5432 60
        
        # Restaurar datos
        docker exec -i ai_news_postgres psql -U postgres -d ai_news_db < "$latest_backup/database_backup.sql"
        log_success "Base de datos restaurada"
    fi
    
    # Restaurar código fuente
    if [[ -f "$latest_backup/backend_code.tar.gz" ]]; then
        log_info "Restaurando código backend..."
        tar -xzf "$latest_backup/backend_code.tar.gz" -C "$BACKEND_DIR/"
    fi
    
    if [[ -f "$latest_backup/frontend_code.tar.gz" ]]; then
        log_info "Restaurando código frontend..."
        tar -xzf "$latest_backup/frontend_code.tar.gz" -C "$FRONTEND_DIR/"
    fi
    
    # Reconstruir y reiniciar servicios
    build_and_deploy_services
    
    log_success "✅ Rollback completado"
    log_deployment_event "rollback_completed" "{\"from\":\"$latest_backup\",\"timestamp\":\"$(date -Iseconds)\"}"
}

cleanup_deployment() {
    log_info "Limpiando recursos post-deployment..."
    
    # Limpiar imágenes Docker no utilizadas
    docker image prune -f
    
    # Limpiar volúmenes huérfanos
    docker volume prune -f
    
    # Limpiar logs antiguos
    if [[ -d "./logs" ]]; then
        find ./logs -name "*.log.*.archive.gz" -mtime +7 -delete 2>/dev/null || true
    fi
    
    # Limpiar backups antiguos (mantener últimos 5)
    if [[ -d "./backups" ]]; then
        find ./backups -name "pre_deployment_*" -type d -printf '%T@ %p\n' | \
        sort -n | head -n -5 | cut -d' ' -f2- | xargs rm -rf 2>/dev/null || true
    fi
    
    log_success "Cleanup completado"
}

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN]

Acciones disponibles:
  deploy              - Ejecutar deployment completo
  health-check        - Solo ejecutar verificaciones de salud
  rollback           - Ejecutar rollback al último backup
  cleanup            - Limpiar recursos del deployment

Variables de entorno:
  DEPLOY_ENV         - Entorno de deployment (default: production)
  BACKUP_ENABLED     - Habilitar backup pre-deployment (default: true)
  ROLLBACK_ENABLED   - Habilitar rollback automático (default: true)
  CLEANUP_ENABLED    - Habilitar cleanup post-deployment (default: true)
  BACKEND_PORT       - Puerto del backend (default: 8000)
  FRONTEND_PORT      - Puerto del frontend (default: 3000)

Ejemplos:
  $0 deploy                          # Deployment completo
  DEPLOY_ENV=staging $0 deploy       # Deployment en staging
  BACKUP_ENABLED=false $0 deploy     # Deployment sin backup
  $0 health-check                    # Solo verificar salud
  $0 rollback                        # Rollback al último backup

EOF
}

# Ejecutar función principal
main "$@"