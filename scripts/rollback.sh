#!/bin/bash

# rollback.sh - Script de rollback rápido para AI News Aggregator
# Versión: 1.0.0
# Descripción: Rollback rápido a versión anterior con verificaciones

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "rollback"

# Configuración de rollback
readonly PROJECT_NAME="ai-news-aggregator"
readonly DOCKER_COMPOSE_FILE="docker-compose.yml"
readonly BACKUP_DIR="./backups"
readonly ROLLBACK_TIMEOUT="${ROLLBACK_TIMEOUT:-300}"
readonly VERIFY_AFTER_ROLLBACK="${VERIFY_AFTER_ROLLBACK:-true}"

# Funciones principales
main() {
    local target_version="${1:-latest}"
    local verify="${2:-true}"
    
    case "$target_version" in
        "latest") rollback_to_latest ;;
        "list") list_available_backups ;;
        "help"|"-h"|"--help") usage ;;
        *) rollback_to_specific "$target_version" ;;
    esac
}

rollback_to_latest() {
    log_info "🔄 Iniciando rollback al backup más reciente..."
    
    local backup_info
    backup_info=$(get_latest_backup_info)
    
    if [[ -z "$backup_info" ]]; then
        log_error "No se encontraron backups disponibles"
        exit 1
    fi
    
    local backup_path
    backup_path=$(echo "$backup_info" | cut -d'|' -f1)
    local backup_timestamp
    backup_timestamp=$(echo "$backup_info" | cut -d'|' -f2)
    
    log_info "Rollback a backup: $(basename "$backup_path") ($backup_timestamp)"
    
    execute_rollback "$backup_path" "$backup_timestamp"
}

rollback_to_specific() {
    local target_version="$1"
    
    log_info "🔄 Iniciando rollback a versión específica: $target_version"
    
    # Buscar backup por timestamp o nombre
    local backup_path
    backup_path=$(find_backup_by_timestamp "$target_version")
    
    if [[ -z "$backup_path" ]]; then
        log_error "Backup no encontrado para: $target_version"
        log_info "Usa '$0 list' para ver backups disponibles"
        exit 1
    fi
    
    local backup_timestamp
    backup_timestamp=$(basename "$backup_path" | sed 's/pre_deployment_//')
    
    log_info "Rollback a backup: $(basename "$backup_path")"
    
    execute_rollback "$backup_path" "$backup_timestamp"
}

execute_rollback() {
    local backup_path="$1"
    local backup_timestamp="$2"
    local rollback_start_time
    
    rollback_start_time=$(date +%s)
    
    # Verificar que el backup existe y es válido
    validate_backup "$backup_path"
    
    # Crear backup de emergencia del estado actual
    create_emergency_backup
    
    # Detener servicios actuales
    log_info "Deteniendo servicios actuales..."
    graceful_shutdown
    
    # Restaurar desde backup
    restore_from_backup "$backup_path"
    
    # Reiniciar servicios
    restart_services
    
    # Verificar rollback
    if [[ "$VERIFY_AFTER_ROLLBACK" == "true" ]]; then
        if ! verify_rollback; then
            log_error "❌ Verificación de rollback fallida"
            if [[ "${AUTO_RETRY_ROLLBACK:-false}" == "true" ]]; then
                log_warn "Intentando rollback automático..."
                rollback_to_latest
            fi
            exit 1
        fi
    fi
    
    local rollback_end_time
    rollback_end_time=$(date +%s)
    local rollback_duration=$((rollback_end_time - rollback_start_time))
    
    log_success "✅ Rollback completado exitosamente en ${rollback_duration}s"
    log_metric "rollback_duration" "$rollback_duration"
    log_deployment_event "rollback_completed" "{\"timestamp\":\"$backup_timestamp\",\"duration\":$rollback_duration}"
}

validate_backup() {
    local backup_path="$1"
    
    log_info "Validando backup: $backup_path"
    
    # Verificar que el directorio existe
    if [[ ! -d "$backup_path" ]]; then
        log_error "Directorio de backup no encontrado: $backup_path"
        exit 1
    fi
    
    # Verificar estructura esperada
    local required_files=("database_backup.sql" "metadata.json")
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$backup_path/$file" ]]; then
            log_warn "Archivo faltante en backup: $file"
        fi
    done
    
    # Verificar metadatos
    if [[ -f "$backup_path/metadata.json" ]]; then
        local backup_env
        backup_env=$(jq -r '.environment // "unknown"' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
        local backup_version
        backup_version=$(jq -r '.version // "unknown"' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
        
        log_info "Backup info:"
        log_info "  Entorno: $backup_env"
        log_info "  Versión: $backup_version"
        log_info "  Timestamp: $backup_timestamp"
    fi
    
    log_success "Backup validado"
}

create_emergency_backup() {
    log_info "Creando backup de emergencia del estado actual..."
    
    local emergency_timestamp
    emergency_timestamp=$(date +%Y%m%d_%H%M%S)
    local emergency_dir="$BACKUP_DIR/emergency_$emergency_timestamp"
    
    mkdir -p "$emergency_dir"
    
    # Backup de base de datos actual
    if docker ps | grep -q "ai_news_postgres"; then
        docker exec ai_news_postgres pg_dump -U postgres ai_news_db > "$emergency_dir/current_database.sql"
        log_success "Backup de emergencia de DB creado"
    fi
    
    # Metadatos del backup de emergencia
    cat > "$emergency_dir/metadata.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "type": "emergency_backup_before_rollback",
    "environment": "${DEPLOY_ENV:-production}",
    "rollback_target": "$backup_timestamp"
}
EOF
    
    log_success "Backup de emergencia creado: $emergency_dir"
}

graceful_shutdown() {
    log_info "Ejecutando apagado graceful de servicios..."
    
    # Detener servicios en orden inverso
    local services=("ai_news_frontend" "ai_news_celery_beat" "ai_news_celery" "ai_news_backend")
    
    for service in "${services[@]}"; do
        if docker ps | grep -q "$service"; then
            log_info "Deteniendo $service..."
            
            # Intentar parada graceful
            if docker exec "$service" ps aux | grep -v grep | grep -q celery; then
                docker exec "$service" pkill -TERM celery || true
                sleep 5
            fi
            
            docker stop "$service" || true
        fi
    done
    
    # Esperar a que todos los contenedores se detengan
    sleep 10
    
    # Forzar eliminación si es necesario
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans --timeout 30 || true
    
    log_success "Servicios detenidos"
}

restore_from_backup() {
    local backup_path="$1"
    
    log_info "Restaurando servicios desde backup..."
    
    # Iniciar servicios de infraestructura primero
    log_info "Iniciando servicios de infraestructura..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis
    
    # Esperar que estén listos
    wait_for_service "postgres" 5432 60
    wait_for_service "redis" 6379 60
    
    # Restaurar base de datos
    if [[ -f "$backup_path/database_backup.sql" ]]; then
        log_info "Restaurando base de datos..."
        
        # Limpiar base de datos actual
        docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || true
        
        # Restaurar datos
        docker exec -i ai_news_postgres psql -U postgres -d ai_news_db < "$backup_path/database_backup.sql"
        
        log_success "Base de datos restaurada"
    fi
    
    # Restaurar código fuente si existe
    if [[ -f "$backup_path/backend_code.tar.gz" ]]; then
        log_info "Restaurando código backend..."
        tar -xzf "$backup_path/backend_code.tar.gz" -C ./backend/ --strip-components=1 2>/dev/null || true
    fi
    
    if [[ -f "$backup_path/frontend_code.tar.gz" ]]; then
        log_info "Restaurando código frontend..."
        tar -xzf "$backup_path/frontend_code.tar.gz" -C ./frontend/ --strip-components=1 2>/dev/null || true
    fi
    
    log_success "Restauración desde backup completada"
}

restart_services() {
    log_info "Reiniciando servicios..."
    
    # Reconstruir imágenes si es necesario
    if [[ "${REBUILD_IMAGES:-false}" == "true" ]]; then
        log_info "Reconstruyendo imágenes Docker..."
        
        docker build -t "${PROJECT_NAME}_backend:latest" ./backend/
        docker build -t "${PROJECT_NAME}_frontend:latest" ./frontend/
    fi
    
    # Iniciar todos los servicios
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_success "Servicios reiniciados"
}

verify_rollback() {
    log_info "Verificando rollback..."
    
    local verification_start_time
    verification_start_time=$(date +%s)
    local verification_failed=0
    
    # Verificar contenedores
    local containers=("ai_news_postgres" "ai_news_redis" "ai_news_backend" "ai_news_celery" "ai_news_celery_beat" "ai_news_frontend")
    
    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            log_success "✅ $container: OK"
        else
            log_error "❌ $container: FAIL"
            ((verification_failed++))
        fi
    done
    
    # Verificar endpoints
    if curl -f -s "http://localhost:8000/health" > /dev/null; then
        log_success "✅ Backend health: OK"
    else
        log_error "❌ Backend health: FAIL"
        ((verification_failed++))
    fi
    
    # Verificar conectividad de BD
    if docker exec ai_news_postgres pg_isready -U postgres > /dev/null; then
        log_success "✅ Database connectivity: OK"
    else
        log_error "❌ Database connectivity: FAIL"
        ((verification_failed++))
    fi
    
    local verification_end_time
    verification_end_time=$(date +%s)
    local verification_duration=$((verification_end_time - verification_start_time))
    
    log_metric "rollback_verification_duration" "$verification_duration"
    
    if [[ $verification_failed -eq 0 ]]; then
        log_success "✅ Verificación de rollback exitosa (${verification_duration}s)"
        return 0
    else
        log_error "❌ Verificación de rollback fallida: $verification_failed errores"
        return 1
    fi
}

get_latest_backup_info() {
    local latest_backup
    
    latest_backup=$(find "$BACKUP_DIR" -name "pre_deployment_*" -type d | sort | tail -1)
    
    if [[ -n "$latest_backup" ]] && [[ -d "$latest_backup" ]]; then
        local backup_timestamp
        backup_timestamp=$(basename "$latest_backup" | sed 's/pre_deployment_//')
        echo "$latest_backup|$backup_timestamp"
    fi
}

find_backup_by_timestamp() {
    local search_term="$1"
    
    # Buscar por timestamp exacto
    local backup_path
    
    backup_path=$(find "$BACKUP_DIR" -name "pre_deployment_${search_term}" -type d | head -1)
    
    if [[ -n "$backup_path" ]]; then
        echo "$backup_path"
        return 0
    fi
    
    # Buscar por coincidencias parciales
    backup_path=$(find "$BACKUP_DIR" -name "pre_deployment_*" -type d | grep "$search_term" | head -1)
    
    if [[ -n "$backup_path" ]]; then
        echo "$backup_path"
        return 0
    fi
    
    echo ""
}

list_available_backups() {
    log_info "📋 Backups disponibles:"
    echo ""
    
    local backups_found=0
    
    find "$BACKUP_DIR" -name "pre_deployment_*" -type d | sort | while read -r backup_path; do
        local backup_name
        backup_name=$(basename "$backup_path")
        local backup_timestamp
        backup_timestamp=$(echo "$backup_name" | sed 's/pre_deployment_//')
        local formatted_date
        formatted_date=$(format_timestamp "$backup_timestamp")
        
        # Verificar si es un backup válido
        local size
        size=$(du -sh "$backup_path" 2>/dev/null | cut -f1 || echo "unknown")
        
        # Verificar metadatos si existen
        local metadata_info=""
        if [[ -f "$backup_path/metadata.json" ]]; then
            local version
            local environment
            version=$(jq -r '.version // "unknown"' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
            environment=$(jq -r '.environment // "unknown"' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
            metadata_info=" [v:$version, env:$environment]"
        fi
        
        printf "  %s (%s) - %s%s\n" "$backup_timestamp" "$formatted_date" "$size" "$metadata_info"
        
        ((backups_found++))
    done
    
    if [[ $backups_found -eq 0 ]]; then
        log_info "No se encontraron backups"
    else
        echo ""
        log_info "Total de backups: $backups_found"
        echo ""
        log_info "Uso: $0 <timestamp> [verify]"
        log_info "Ejemplo: $0 20241106_041606 true"
    fi
}

format_timestamp() {
    local timestamp="$1"
    
    # Formato: YYYYMMDD_HHMMSS -> YYYY-MM-DD HH:MM:SS
    if [[ ${#timestamp} -eq 15 ]] && [[ "$timestamp" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
        local year="${timestamp:0:4}"
        local month="${timestamp:4:2}"
        local day="${timestamp:6:2}"
        local hour="${timestamp:9:2}"
        local minute="${timestamp:11:2}"
        local second="${timestamp:13:2}"
        
        echo "$year-$month-$day $hour:$minute:$second"
    else
        echo "$timestamp"
    fi
}

wait_for_service() {
    local service_name="$1"
    local port="$2"
    local timeout="${3:-60}"
    local start_time
    
    start_time=$(date +%s)
    
    while true; do
        if nc -z localhost "$port" 2>/dev/null; then
            return 0
        fi
        
        if [[ $(($(date +%s) - start_time)) -ge $timeout ]]; then
            log_error "Timeout esperando servicio $service_name"
            return 1
        fi
        
        sleep 2
    done
}

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN] [parámetros]

Acciones:
  latest              - Rollback al backup más reciente
  list                - Listar backups disponibles
  <timestamp>         - Rollback a backup específico
  help                - Mostrar esta ayuda

Parámetros opcionales (solo para rollback):
  verify              - Verificar rollback después de ejecutarlo (default: true)

Variables de entorno:
  VERIFY_AFTER_ROLLBACK - Verificar después del rollback (default: true)
  ROLLBACK_TIMEOUT    - Timeout para verificaciones (default: 300)
  REBUILD_IMAGES      - Reconstruir imágenes durante rollback (default: false)
  AUTO_RETRY_ROLLBACK - Retry automático en caso de fallo (default: false)

Ejemplos:
  $0 latest                    # Rollback al backup más reciente
  $0 20241106_041606          # Rollback a backup específico
  $0 list                      # Ver backups disponibles
  $0 20241106_041606 false    # Rollback sin verificación

Archivos de backup:
  Los backups se almacenan en: $BACKUP_DIR/
  Formato: pre_deployment_YYYYMMDD_HHMMSS/

EOF
}

# Ejecutar función principal
main "$@"