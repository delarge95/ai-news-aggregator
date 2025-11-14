#!/bin/bash

# backup-restore.sh - Gestión de backup y restore para AI News Aggregator
# Versión: 1.0.0
# Descripción: Sistema completo de backup y restauración con compresión y verificación

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "backup-restore"

# Configuración de backup
readonly PROJECT_NAME="ai-news-aggregator"
readonly BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-./backups}"
readonly DATABASE_CONTAINER="ai_news_postgres"
readonly DATABASE_NAME="ai_news_db"
readonly DATABASE_USER="postgres"
readonly RETENTION_DAYS="${RETENTION_DAYS:-30}"
readonly COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"
readonly MAX_BACKUP_SIZE="${MAX_BACKUP_SIZE:-1G}"

# URLs y configuraciones
readonly S3_BUCKET="${S3_BUCKET:-}"
readonly S3_REGION="${S3_REGION:-}"
readonly REMOTE_BACKUP_ENABLED="${REMOTE_BACKUP_ENABLED:-false}"

# Funciones principales
main() {
    local action="${1:-create}"
    
    case "$action" in
        "create") create_backup "${2:-full}" ;;
        "restore") restore_backup "$2" ;;
        "list") list_backups "$2" ;;
        "verify") verify_backup "$2" ;;
        "cleanup") cleanup_old_backups ;;
        "schedule") schedule_backup "$2" ;;
        "status") backup_status ;;
        "config") show_backup_config ;;
        *) usage ;;
    esac
}

create_backup() {
    local backup_type="${2:-full}"
    
    log_info "💾 Creando backup: $backup_type"
    
    local backup_start_time
    backup_start_time=$(date +%s)
    local backup_id
    backup_id=$(generate_backup_id)
    local backup_dir="$BACKUP_BASE_DIR/$backup_id"
    
    mkdir -p "$backup_dir"
    
    log_info "ID del backup: $backup_id"
    log_info "Directorio: $backup_dir"
    
    # Crear metadatos del backup
    local backup_metadata
    backup_metadata=$(create_backup_metadata "$backup_type" "$backup_id")
    echo "$backup_metadata" > "$backup_dir/metadata.json"
    
    local backup_size=0
    local failed_components=0
    
    # Backup según tipo
    case "$backup_type" in
        "full")
            # Backup completo de todo
            backup_database "$backup_dir" || ((failed_components++))
            backup_code "$backup_dir" || ((failed_components++))
            backup_configs "$backup_dir" || ((failed_components++))
            backup_logs "$backup_dir" || ((failed_components++))
            backup_volumes "$backup_dir" || ((failed_components++))
            ;;
        "database")
            # Solo base de datos
            backup_database "$backup_dir" || ((failed_components++))
            ;;
        "code")
            # Solo código
            backup_code "$backup_dir" || ((failed_components++))
            ;;
        "configs")
            # Solo configuraciones
            backup_configs "$backup_dir" || ((failed_components++))
            ;;
        "incremental")
            # Backup incremental
            create_incremental_backup "$backup_dir" || ((failed_components++))
            ;;
        *)
            log_error "Tipo de backup no válido: $backup_type"
            exit 1
            ;;
    esac
    
    # Calcular tamaño total
    backup_size=$(calculate_backup_size "$backup_dir")
    
    # Comprimir backup si está habilitado
    compress_backup "$backup_dir"
    
    # Verificar integridad
    verify_backup_integrity "$backup_dir"
    
    # Sincronizar con backup remoto
    if [[ "$REMOTE_BACKUP_ENABLED" == "true" ]]; then
        sync_to_remote "$backup_dir"
    fi
    
    # Crear índice de backup
    create_backup_index "$backup_dir"
    
    local backup_end_time
    backup_end_time=$(date +%s)
    local backup_duration=$((backup_end_time - backup_start_time))
    
    # Limpiar backups antiguos si es necesario
    cleanup_old_backups
    
    if [[ $failed_components -eq 0 ]]; then
        log_success "✅ Backup creado exitosamente en ${backup_duration}s"
        log_success "Tamaño: $(format_size "$backup_size")"
        log_success "Ubicación: $backup_dir"
        
        log_metric "backup_duration" "$backup_duration"
        log_metric "backup_size_bytes" "$backup_size"
        log_metric "backup_type" "$backup_type"
        
        # Mostrar resumen
        show_backup_summary "$backup_dir"
        
        return 0
    else
        log_error "❌ Backup completado con $failed_components componentes fallidos"
        return 1
    fi
}

generate_backup_id() {
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local hostname
    hostname=$(hostname | tr '[:upper:]' '[:lower:]')
    
    echo "${timestamp}_${hostname}_${PROJECT_NAME}"
}

create_backup_metadata() {
    local backup_type="$1"
    local backup_id="$2"
    
    cat <<EOF
{
    "backup_id": "$backup_id",
    "project_name": "$PROJECT_NAME",
    "backup_type": "$backup_type",
    "created_at": "$(date -Iseconds)",
    "created_by": "$(whoami)",
    "hostname": "$(hostname)",
    "version": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "environment": "${DEPLOY_ENV:-production}",
    "database": {
        "container": "$DATABASE_CONTAINER",
        "database": "$DATABASE_NAME",
        "user": "$DATABASE_USER"
    },
    "components": [],
    "compression": {
        "enabled": true,
        "algorithm": "gzip",
        "level": $COMPRESSION_LEVEL
    }
}
EOF
}

backup_database() {
    local backup_dir="$1"
    local db_backup_dir="$backup_dir/database"
    
    log_info "Respaldando base de datos..."
    mkdir -p "$db_backup_dir"
    
    local db_backup_start_time
    db_backup_start_time=$(date +%s)
    
    # Verificar conectividad de base de datos
    if ! docker exec "$DATABASE_CONTAINER" pg_isready -U "$DATABASE_USER" > /dev/null 2>&1; then
        log_error "Base de datos no disponible"
        return 1
    fi
    
    # Crear backup completo de la base de datos
    local db_backup_file="$db_backup_dir/full_backup.sql"
    
    if docker exec "$DATABASE_CONTAINER" pg_dump -U "$DATABASE_USER" "$DATABASE_NAME" > "$db_backup_file" 2>/dev/null; then
        local db_backup_end_time
        db_backup_end_time=$(date +%s)
        local db_backup_duration=$((db_backup_end_time - db_backup_start_time))
        
        log_success "✅ Backup de base de datos completado (${db_backup_duration}s)"
        log_metric "database_backup_duration" "$db_backup_duration"
        log_metric "database_backup_size_bytes" "$(stat -f%z "$db_backup_file" 2>/dev/null || stat -c%s "$db_backup_file" 2>/dev/null)"
        
        # Actualizar metadatos
        update_metadata_component "$backup_dir" "database" "$db_backup_file"
        
        return 0
    else
        log_error "❌ Error creando backup de base de datos"
        return 1
    fi
}

backup_code() {
    local backup_dir="$1"
    local code_backup_dir="$backup_dir/code"
    
    log_info "Respaldando código fuente..."
    mkdir -p "$code_backup_dir"
    
    # Backup del backend
    if [[ -d "./backend" ]]; then
        log_info "Respaldando backend..."
        tar -czf "$code_backup_dir/backend.tar.gz" -C ./backend . 2>/dev/null || {
            log_error "Error respaldando backend"
            return 1
        }
        log_success "✅ Backend respaldado"
    fi
    
    # Backup del frontend
    if [[ -d "./frontend" ]]; then
        log_info "Respaldando frontend..."
        tar -czf "$code_backup_dir/frontend.tar.gz" -C ./frontend . 2>/dev/null || {
            log_error "Error respaldando frontend"
            return 1
        }
        log_success "✅ Frontend respaldado"
    fi
    
    # Actualizar metadatos
    if [[ -f "$code_backup_dir/backend.tar.gz" ]]; then
        update_metadata_component "$backup_dir" "backend" "$code_backup_dir/backend.tar.gz"
    fi
    
    if [[ -f "$code_backup_dir/frontend.tar.gz" ]]; then
        update_metadata_component "$backup_dir" "frontend" "$code_backup_dir/frontend.tar.gz"
    fi
    
    return 0
}

backup_configs() {
    local backup_dir="$1"
    local config_backup_dir="$backup_dir/configs"
    
    log_info "Respaldando configuraciones..."
    mkdir -p "$config_backup_dir"
    
    local configs_backed_up=0
    
    # Docker Compose
    if [[ -f "docker-compose.yml" ]]; then
        cp "docker-compose.yml" "$config_backup_dir/" || return 1
        ((configs_backed_up++))
        log_info "✅ docker-compose.yml respaldado"
    fi
    
    # Archivos .env
    if [[ -f ".env" ]]; then
        cp ".env" "$config_backup_dir/.env" || return 1
        ((configs_backed_up++))
        log_info "✅ .env respaldado"
    fi
    
    # Archivos de configuración del backend
    if [[ -f "./backend/app/core/config.py" ]]; then
        mkdir -p "$config_backup_dir/backend"
        cp -r ./backend/app/core/config.py "$config_backup_dir/backend/" || return 1
        ((configs_backed_up++))
        log_info "✅ Configuración backend respaldada"
    fi
    
    # Scripts
    if [[ -d "./scripts" ]]; then
        mkdir -p "$config_backup_dir/scripts"
        cp -r ./scripts/* "$config_backup_dir/scripts/" 2>/dev/null || true
        log_info "✅ Scripts respaldados"
    fi
    
    if [[ $configs_backed_up -gt 0 ]]; then
        update_metadata_component "$backup_dir" "configs" "$config_backup_dir"
        return 0
    else
        log_warn "No se encontraron archivos de configuración para respaldar"
        return 0
    fi
}

backup_logs() {
    local backup_dir="$1"
    local logs_backup_dir="$backup_dir/logs"
    
    log_info "Respaldando logs..."
    mkdir -p "$logs_backup_dir"
    
    local logs_backed_up=0
    
    # Logs del directorio ./logs
    if [[ -d "./logs" ]]; then
        # Solo respaldar logs de los últimos 7 días
        find ./logs -name "*.log" -mtime -7 -exec cp {} "$logs_backup_dir/" \; 2>/dev/null || true
        find ./logs -name "*.log.*.gz" -exec cp {} "$logs_backup_dir/" \; 2>/dev/null || true
        
        if [[ $(find "$logs_backup_dir" -type f | wc -l) -gt 0 ]]; then
            ((logs_backed_up++))
            log_info "✅ Logs locales respaldados"
        fi
    fi
    
    # Logs de Docker
    if command -v docker &> /dev/null; then
        docker logs "$DATABASE_CONTAINER" > "$logs_backup_dir/postgres.log" 2>&1 || true
        ((logs_backed_up++))
        log_info "✅ Logs de PostgreSQL respaldados"
    fi
    
    if [[ $logs_backed_up -gt 0 ]]; then
        update_metadata_component "$backup_dir" "logs" "$logs_backup_dir"
        return 0
    else
        log_warn "No se encontraron logs para respaldar"
        return 0
    fi
}

backup_volumes() {
    local backup_dir="$1"
    local volumes_backup_dir="$backup_dir/volumes"
    
    log_info "Respaldando volúmenes Docker..."
    mkdir -p "$volumes_backup_dir"
    
    local volumes_backed_up=0
    
    # Volumen de PostgreSQL
    if docker volume inspect ai_news_aggregator_postgres_data &> /dev/null; then
        log_info "Respaldando volumen de PostgreSQL..."
        
        # Crear contenedor temporal para acceder al volumen
        local temp_container="backup_postgres_$$"
        
        if docker run --rm \
            -v ai_news_aggregator_postgres_data:/source:ro \
            -v "$(pwd)/$volumes_backup_dir":/backup \
            alpine tar -czf /backup/postgres_data.tar.gz -C /source .; then
            ((volumes_backed_up++))
            log_success "✅ Volumen de PostgreSQL respaldado"
        else
            log_error "Error respaldando volumen de PostgreSQL"
        fi
        
        # Limpiar contenedor temporal si existe
        docker rm "$temp_container" 2>/dev/null || true
    fi
    
    # Volumen de Redis
    if docker volume inspect ai_news_aggregator_redis_data &> /dev/null; then
        log_info "Respaldando volumen de Redis..."
        
        local temp_container="backup_redis_$$"
        
        if docker run --rm \
            -v ai_news_aggregator_redis_data:/source:ro \
            -v "$(pwd)/$volumes_backup_dir":/backup \
            alpine tar -czf /backup/redis_data.tar.gz -C /source .; then
            ((volumes_backed_up++))
            log_success "✅ Volumen de Redis respaldado"
        else
            log_error "Error respaldando volumen de Redis"
        fi
        
        docker rm "$temp_container" 2>/dev/null || true
    fi
    
    if [[ $volumes_backed_up -gt 0 ]]; then
        update_metadata_component "$backup_dir" "volumes" "$volumes_backup_dir"
        return 0
    else
        log_warn "No se encontraron volúmenes Docker para respaldar"
        return 0
    fi
}

create_incremental_backup() {
    local backup_dir="$1"
    
    log_info "Creando backup incremental..."
    
    # Para un backup incremental real, necesitaríamos un sistema más sofisticado
    # que mantenga un tracking de cambios
    
    # Por ahora, creamos un backup completo pero más pequeño
    backup_database "$backup_dir" || return 1
    
    # Solo configuraciones críticas
    backup_configs "$backup_dir" || return 1
    
    log_info "✅ Backup incremental completado"
}

update_metadata_component() {
    local backup_dir="$1"
    local component="$2"
    local path="$3"
    
    if [[ -f "$backup_dir/metadata.json" ]] && command -v jq &> /dev/null; then
        local component_info
        component_info=$(jq -n --arg name "$component" --arg path "$path" \
            --arg timestamp "$(date -Iseconds)" \
            '{
                name: $name,
                path: $path,
                timestamp: $timestamp,
                size_bytes: (try ($path as $p | 
                    if $p | test(".*\\.(tar\\.gz|sql)$") then
                        (["stat", "-f%z", $p] | _make_non_char_input) | run | stdout | trim
                    else
                        "unknown"
                    end) catch "unknown")
            }')
        
        jq ".components += [$component_info]" "$backup_dir/metadata.json" > "$backup_dir/metadata.tmp" && \
        mv "$backup_dir/metadata.tmp" "$backup_dir/metadata.json"
    fi
}

compress_backup() {
    local backup_dir="$1"
    
    log_info "Comprimiendo backup..."
    
    local compress_start_time
    compress_start_time=$(date +%s)
    
    # Crear archivo comprimido principal
    local backup_name
    backup_name=$(basename "$backup_dir")
    local compressed_file="$BACKUP_BASE_DIR/${backup_name}.tar.gz"
    
    if tar -czf "$compressed_file" -C "$BACKUP_BASE_DIR" "$backup_name" 2>/dev/null; then
        # Verificar tamaño del archivo comprimido
        local compressed_size
        compressed_size=$(stat -f%z "$compressed_file" 2>/dev/null || stat -c%s "$compressed_file" 2>/dev/null)
        
        # Verificar límite de tamaño
        local max_size_bytes
        max_size_bytes=$(parse_size "$MAX_BACKUP_SIZE")
        
        if [[ $compressed_size -gt $max_size_bytes ]]; then
            log_warn "Backup comprimido excede el tamaño máximo: $(format_size "$compressed_size") > $(format_size "$max_size_bytes")"
        fi
        
        # Eliminar directorio original para ahorrar espacio
        rm -rf "$backup_dir"
        
        local compress_end_time
        compress_end_time=$(date +%s)
        local compress_duration=$((compress_end_time - compress_start_time))
        
        log_success "✅ Backup comprimido en ${compress_duration}s"
        log_success "Archivo comprimido: $compressed_file"
        log_success "Tamaño: $(format_size "$compressed_size")"
        
        # Actualizar metadatos
        if [[ -f "$compressed_file.metadata.json" ]]; then
            echo "{\"compressed_file\": \"$compressed_file\", \"compressed_size_bytes\": $compressed_size}" > "$compressed_file.metadata.json"
        fi
    else
        log_error "Error comprimiendo backup"
        return 1
    fi
}

verify_backup_integrity() {
    local backup_path="$1"
    
    log_info "Verificando integridad del backup..."
    
    # Si es archivo comprimido
    if [[ "$backup_path" =~ \.tar\.gz$ ]]; then
        if tar -tzf "$backup_path" > /dev/null 2>&1; then
            log_success "✅ Backup comprimido válido"
        else
            log_error "❌ Backup comprimido corrupto"
            return 1
        fi
    else
        # Verificar directorio
        if [[ -d "$backup_path" ]] && [[ -f "$backup_path/metadata.json" ]]; then
            log_success "✅ Directorio de backup válido"
        else
            log_error "❌ Directorio de backup incompleto"
            return 1
        fi
    fi
}

sync_to_remote() {
    local backup_path="$1"
    
    if [[ -z "$S3_BUCKET" ]]; then
        log_warn "S3_BUCKET no configurado, omitiendo sincronización remota"
        return 0
    fi
    
    log_info "Sincronizando backup con almacenamiento remoto..."
    
    local backup_name
    backup_name=$(basename "$backup_path")
    
    if command -v aws &> /dev/null; then
        if aws s3 cp "$backup_path" "s3://$S3_BUCKET/backups/$backup_name" 2>/dev/null; then
            log_success "✅ Backup sincronizado con S3"
        else
            log_error "❌ Error sincronizando con S3"
            return 1
        fi
    else
        log_warn "AWS CLI no disponible, omitiendo sincronización remota"
    fi
}

create_backup_index() {
    local backup_path="$1"
    
    log_info "Creando índice de backup..."
    
    local index_file
    index_file="$BACKUP_BASE_DIR/index.json"
    
    # Crear o actualizar índice
    if [[ -f "$index_file" ]] && command -v jq &> /dev/null; then
        local backup_info
        backup_info=$(jq -n --arg path "$backup_path" --arg timestamp "$(date -Iseconds)" \
            '{
                backup_path: $path,
                created_at: $timestamp,
                indexed: true
            }')
        
        jq ".backups += [$backup_info]" "$index_file" > "$index_file.tmp" && \
        mv "$index_file.tmp" "$index_file"
    else
        echo "{\"backups\": [{\"backup_path\": \"$backup_path\", \"created_at\": \"$(date -Iseconds)\"}]}" > "$index_file"
    fi
}

calculate_backup_size() {
    local backup_path="$1"
    
    if [[ -d "$backup_path" ]]; then
        du -sb "$backup_path" | cut -f1
    else
        stat -f%z "$backup_path" 2>/dev/null || stat -c%s "$backup_path" 2>/dev/null || echo "0"
    fi
}

parse_size() {
    local size="$1"
    local multiplier=1
    
    case "${size^^}" in
        *K) multiplier=1024 ;;
        *M) multiplier=$((1024*1024)) ;;
        *G) multiplier=$((1024*1024*1024)) ;;
    esac
    
    echo $(( $(echo "$size" | sed 's/[^0-9]//g') * multiplier ))
}

format_size() {
    local bytes="$1"
    local units=("B" "KB" "MB" "GB" "TB")
    local unit_index=0
    local size=$bytes
    
    while [[ $size -gt 1024 ]] && [[ $unit_index -lt $((${#units[@]} - 1)) ]]; do
        size=$((size / 1024))
        ((unit_index++))
    done
    
    echo "${size}${units[$unit_index]}"
}

show_backup_summary() {
    local backup_path="$1"
    
    echo ""
    log_info "📋 Resumen del backup:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [[ -f "$backup_path/metadata.json" ]]; then
        if command -v jq &> /dev/null; then
            local backup_type
            local created_at
            local hostname
            
            backup_type=$(jq -r '.backup_type' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
            created_at=$(jq -r '.created_at' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
            hostname=$(jq -r '.hostname' "$backup_path/metadata.json" 2>/dev/null || echo "unknown")
            
            echo "  ID: $(basename "$backup_path")"
            echo "  Tipo: $backup_type"
            echo "  Creado: $created_at"
            echo "  Host: $hostname"
            
            local components_count
            components_count=$(jq -r '.components | length' "$backup_path/metadata.json" 2>/dev/null || echo "0")
            echo "  Componentes: $components_count"
        else
            echo "  Archivo: $(basename "$backup_path")"
        fi
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

cleanup_old_backups() {
    log_info "Limpiando backups antiguos (>$RETENTION_DAYS días)..."
    
    local cleaned_backups=0
    
    # Limpiar archivos comprimidos
    if [[ -d "$BACKUP_BASE_DIR" ]]; then
        find "$BACKUP_BASE_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -type f | while read -r backup_file; do
            log_info "Eliminando backup antiguo: $(basename "$backup_file")"
            rm -f "$backup_file" "$backup_file.metadata.json" 2>/dev/null || true
            ((cleaned_backups++))
        done
        
        # Limpiar directorios de backup antiguos
        find "$BACKUP_BASE_DIR" -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    fi
    
    if [[ $cleaned_backups -gt 0 ]]; then
        log_success "✅ Limpieza completada: $cleaned_backups backups eliminados"
    else
        log_info "No hay backups antiguos para limpiar"
    fi
}

restore_backup() {
    local backup_path="$2"
    
    if [[ -z "$backup_path" ]]; then
        log_error "Ruta de backup requerida para restaurar"
        usage
        exit 1
    fi
    
    log_info "🔄 Restaurando backup: $backup_path"
    
    # Verificar que el backup existe
    if [[ ! -e "$backup_path" ]]; then
        log_error "Backup no encontrado: $backup_path"
        list_backups
        exit 1
    fi
    
    # Crear backup de emergencia del estado actual
    create_emergency_backup
    
    # Restaurar desde backup
    local restore_start_time
    restore_start_time=$(date +%s)
    
    if restore_from_backup_path "$backup_path"; then
        local restore_end_time
        restore_end_time=$(date +%s)
        local restore_duration=$((restore_end_time - restore_start_time))
        
        log_success "✅ Restauración completada en ${restore_duration}s"
        log_metric "restore_duration" "$restore_duration"
        
        # Verificar que los servicios estén funcionando
        log_info "Verificando servicios post-restauración..."
        if [[ -f "$SCRIPT_DIR/health-check.sh" ]]; then
            bash "$SCRIPT_DIR/health-check.sh" services
        fi
        
        return 0
    else
        log_error "❌ Error durante la restauración"
        return 1
    fi
}

restore_from_backup_path() {
    local backup_path="$1"
    local restore_dir
    
    # Si es archivo comprimido, extraerlo
    if [[ "$backup_path" =~ \.tar\.gz$ ]]; then
        restore_dir="$BACKUP_BASE_DIR/restore_temp_$$"
        mkdir -p "$restore_dir"
        
        log_info "Extrayendo backup comprimido..."
        if ! tar -xzf "$backup_path" -C "$restore_dir"; then
            log_error "Error extrayendo backup"
            return 1
        fi
        
        # El directorio extraído será el backup real
        backup_path=$(find "$restore_dir" -name "20*" -type d | head -1)
    fi
    
    # Verificar metadatos
    if [[ ! -f "$backup_path/metadata.json" ]]; then
        log_error "Metadatos de backup no encontrados"
        return 1
    fi
    
    # Restaurar componentes según metadatos
    local restore_components
    restore_components=$(jq -r '.components[].name' "$backup_path/metadata.json" 2>/dev/null || echo "")
    
    for component in $restore_components; do
        log_info "Restaurando componente: $component"
        
        case "$component" in
            "database")
                restore_database_component "$backup_path"
                ;;
            "backend")
                restore_code_component "$backup_path" "backend"
                ;;
            "frontend")
                restore_code_component "$backup_path" "frontend"
                ;;
            "configs")
                restore_configs_component "$backup_path"
                ;;
            "logs")
                log_info "Saltando logs en restauración"
                ;;
            "volumes")
                restore_volumes_component "$backup_path"
                ;;
            *)
                log_warn "Componente desconocido: $component"
                ;;
        esac
    done
    
    # Limpiar directorio temporal si existe
    if [[ -n "${restore_dir:-}" ]]; then
        rm -rf "$restore_dir"
    fi
}

restore_database_component() {
    local backup_path="$1"
    
    log_info "Restaurando base de datos..."
    
    # Detener servicios de aplicación temporalmente
    docker-compose stop backend celery_worker celery_beat 2>/dev/null || true
    
    # Encontrar archivo de backup de base de datos
    local db_backup_file
    db_backup_file=$(find "$backup_path" -name "*.sql" | head -1)
    
    if [[ -z "$db_backup_file" ]]; then
        log_error "Archivo de backup de base de datos no encontrado"
        return 1
    fi
    
    # Restaurar base de datos
    if docker exec -i "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" < "$db_backup_file"; then
        log_success "✅ Base de datos restaurada"
    else
        log_error "❌ Error restaurando base de datos"
        return 1
    fi
    
    # Reiniciar servicios
    docker-compose start backend celery_worker celery_beat 2>/dev/null || true
}

restore_code_component() {
    local backup_path="$1"
    local component="$2"
    
    log_info "Restaurando código $component..."
    
    local code_backup_file
    code_backup_file="$backup_path/code/${component}.tar.gz"
    
    if [[ -f "$code_backup_file" ]]; then
        if tar -xzf "$code_backup_file" -C "./$component" --strip-components=1; then
            log_success "✅ Código $component restaurado"
        else
            log_error "❌ Error restaurando código $component"
            return 1
        fi
    else
        log_warn "Backup de código $component no encontrado"
    fi
}

restore_configs_component() {
    local backup_path="$1"
    
    log_info "Restaurando configuraciones..."
    
    local config_backup_dir
    config_backup_dir="$backup_path/configs"
    
    if [[ -d "$config_backup_dir" ]]; then
        # Restaurar docker-compose
        if [[ -f "$config_backup_dir/docker-compose.yml" ]]; then
            cp "$config_backup_dir/docker-compose.yml" ./
            log_success "✅ docker-compose.yml restaurado"
        fi
        
        # Restaurar .env
        if [[ -f "$config_backup_dir/.env" ]]; then
            cp "$config_backup_dir/.env" ./
            log_success "✅ .env restaurado"
        fi
        
        # Restaurar scripts
        if [[ -d "$config_backup_dir/scripts" ]]; then
            cp -r "$config_backup_dir/scripts/"* ./scripts/ 2>/dev/null || true
            log_success "✅ Scripts restaurados"
        fi
    else
        log_warn "Backup de configuraciones no encontrado"
    fi
}

restore_volumes_component() {
    local backup_path="$1"
    
    log_info "Restaurando volúmenes Docker..."
    
    # Esta es una operación compleja que requiere detener contenedores
    log_warn "Restauración de volúmenes no implementada completamente"
    log_info "Se recomienda realizar esta operación manualmente"
}

create_emergency_backup() {
    log_info "Creando backup de emergencia antes de restaurar..."
    
    local emergency_timestamp
    emergency_timestamp=$(date +%Y%m%d_%H%M%S)
    local emergency_backup="$BACKUP_BASE_DIR/emergency_before_restore_$emergency_timestamp"
    
    mkdir -p "$emergency_backup"
    
    # Backup rápido de base de datos
    if docker ps | grep -q "$DATABASE_CONTAINER"; then
        docker exec "$DATABASE_CONTAINER" pg_dump -U "$DATABASE_USER" "$DATABASE_NAME" > "$emergency_backup/database_snapshot.sql" 2>/dev/null || true
        log_success "Backup de emergencia de DB creado"
    fi
    
    # Metadatos del backup de emergencia
    cat > "$emergency_backup/metadata.json" <<EOF
{
    "backup_id": "emergency_before_restore_$emergency_timestamp",
    "type": "emergency_before_restore",
    "created_at": "$(date -Iseconds)",
    "reason": "backup_before_restore_operation"
}
EOF
    
    log_success "Backup de emergencia creado: $emergency_backup"
}

list_backups() {
    local filter="${2:-all}"
    
    log_info "📋 Lista de backups disponibles"
    echo ""
    
    if [[ ! -d "$BACKUP_BASE_DIR" ]]; then
        log_info "Directorio de backups no existe: $BACKUP_BASE_DIR"
        return 0
    fi
    
    local backups_found=0
    
    # Buscar backups comprimidos
    find "$BACKUP_BASE_DIR" -name "*.tar.gz" -type f -printf '%T@ %p %s\n' | sort -nr | while read -r timestamp path size; do
        local backup_name
        local formatted_date
        local formatted_size
        
        backup_name=$(basename "$path" .tar.gz)
        formatted_date=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S')
        formatted_size=$(format_size "$size")
        
        # Aplicar filtro si se especifica
        if [[ "$filter" == "recent" ]] && [[ $(($(date +%s) - $(date -d "$formatted_date" +%s))) -gt $((7*24*3600)) ]]; then
            continue
        fi
        
        printf "  %s (%s) - %s\n" "$backup_name" "$formatted_date" "$formatted_size"
        ((backups_found++))
    done
    
    # Buscar backups en directorios
    find "$BACKUP_BASE_DIR" -name "20*" -type d | sort | while read -r backup_dir; do
        local backup_name
        local backup_size
        local backup_date
        
        backup_name=$(basename "$backup_dir")
        backup_date=$(date -d "$(stat -c '%y' "$backup_dir" 2>/dev/null | cut -d' ' -f1)" '+%Y-%m-%d %H:%M:%S')
        backup_size=$(format_size "$(du -sb "$backup_dir" | cut -f1)")
        
        if [[ "$filter" == "recent" ]] && [[ $(($(date +%s) - $(date -d "$backup_date" +%s))) -gt $((7*24*3600)) ]]; then
            continue
        fi
        
        printf "  %s (%s) - %s [directorio]\n" "$backup_name" "$backup_date" "$backup_size"
        ((backups_found++))
    done
    
    if [[ $backups_found -eq 0 ]]; then
        log_info "No se encontraron backups"
    else
        echo ""
        log_info "Total de backups: $backups_found"
        
        # Mostrar espacio total usado
        local total_size
        total_size=$(du -sb "$BACKUP_BASE_DIR" | cut -f1)
        echo "Espacio total usado: $(format_size "$total_size")"
    fi
}

verify_backup() {
    local backup_path="$2"
    
    if [[ -z "$backup_path" ]]; then
        log_error "Ruta de backup requerida para verificar"
        usage
        exit 1
    fi
    
    log_info "🔍 Verificando backup: $backup_path"
    
    local verification_passed=true
    
    # Verificar que el archivo existe
    if [[ ! -e "$backup_path" ]]; then
        log_error "Backup no encontrado: $backup_path"
        exit 1
    fi
    
    # Verificar integridad
    if [[ "$backup_path" =~ \.tar\.gz$ ]]; then
        if tar -tzf "$backup_path" > /dev/null 2>&1; then
            log_success "✅ Integridad del archivo: OK"
        else
            log_error "❌ Integridad del archivo: FAIL"
            verification_passed=false
        fi
    fi
    
    # Verificar metadatos
    local metadata_file="$backup_path"
    if [[ "$backup_path" =~ \.tar\.gz$ ]]; then
        metadata_file="$backup_path.metadata.json"
    else
        metadata_file="$backup_path/metadata.json"
    fi
    
    if [[ -f "$metadata_file" ]]; then
        log_success "✅ Metadatos encontrados"
        
        if command -v jq &> /dev/null; then
            local backup_type
            local created_at
            
            backup_type=$(jq -r '.backup_type' "$metadata_file" 2>/dev/null || echo "unknown")
            created_at=$(jq -r '.created_at' "$metadata_file" 2>/dev/null || echo "unknown")
            
            log_info "  Tipo: $backup_type"
            log_info "  Creado: $created_at"
        fi
    else
        log_error "❌ Metadatos no encontrados"
        verification_passed=false
    fi
    
    # Verificar componentes si es directorio
    if [[ -d "$backup_path" ]] && [[ -f "$backup_path/metadata.json" ]]; then
        if command -v jq &> /dev/null; then
            local components
            mapfile -t components < <(jq -r '.components[].name' "$backup_path/metadata.json" 2>/dev/null)
            
            if [[ ${#components[@]} -gt 0 ]]; then
                log_info "Componentes del backup:"
                for component in "${components[@]}"; do
                    log_success "  ✅ $component"
                done
            fi
        fi
    fi
    
    if [[ "$verification_passed" == true ]]; then
        log_success "✅ Backup verificado exitosamente"
        return 0
    else
        log_error "❌ Verificación de backup fallida"
        return 1
    fi
}

backup_status() {
    log_info "📊 Estado del sistema de backup"
    echo ""
    
    # Información general
    echo "Configuración:"
    echo "  Directorio base: $BACKUP_BASE_DIR"
    echo "  Retención: $RETENTION_DAYS días"
    echo "  Nivel compresión: $COMPRESSION_LEVEL"
    echo "  Tamaño máximo: $MAX_BACKUP_SIZE"
    echo "  Backup remoto: $REMOTE_BACKUP_ENABLED"
    echo ""
    
    # Estadísticas de backups
    if [[ -d "$BACKUP_BASE_DIR" ]]; then
        local total_backups
        local total_size_bytes
        local oldest_backup
        local newest_backup
        
        total_backups=$(find "$BACKUP_BASE_DIR" -name "*.tar.gz" -o -name "20*" -type d | wc -l)
        total_size_bytes=$(du -sb "$BACKUP_BASE_DIR" | cut -f1)
        oldest_backup=$(find "$BACKUP_BASE_DIR" -name "*.tar.gz" -o -name "20*" -type d -printf '%T@ %p\n' | sort -n | head -1 | cut -d' ' -f2- | xargs -r basename)
        newest_backup=$(find "$BACKUP_BASE_DIR" -name "*.tar.gz" -o -name "20*" -type d -printf '%T@ %p\n' | sort -nr | head -1 | cut -d' ' -f2- | xargs -r basename)
        
        echo "Estadísticas:"
        echo "  Total de backups: $total_backups"
        echo "  Espacio total usado: $(format_size "$total_size_bytes")"
        echo "  Backup más antiguo: ${oldest_backup:-"N/A"}"
        echo "  Backup más reciente: ${newest_backup:-"N/A"}"
    else
        echo "  ⚠️  Directorio de backups no existe"
    fi
    
    echo ""
    
    # Estado de servicios relevantes
    echo "Servicios:"
    if docker ps | grep -q "$DATABASE_CONTAINER"; then
        echo "  ✅ Base de datos: Disponible"
    else
        echo "  ❌ Base de datos: No disponible"
    fi
    
    if command -v aws &> /dev/null && [[ -n "$S3_BUCKET" ]]; then
        echo "  ✅ AWS CLI: Disponible"
        echo "  📦 S3 Bucket: $S3_BUCKET"
    else
        echo "  ⚠️  AWS CLI: No disponible"
    fi
    
    if command -v jq &> /dev/null; then
        echo "  ✅ jq: Disponible"
    else
        echo "  ⚠️  jq: No disponible (funciones limitadas)"
    fi
}

show_backup_config() {
    log_info "⚙️  Configuración del sistema de backup"
    echo ""
    
    cat <<EOF
Variables de entorno configurables:
  BACKUP_BASE_DIR         - Directorio base para backups (default: ./backups)
  RETENTION_DAYS          - Días de retención (default: 30)
  COMPRESSION_LEVEL       - Nivel de compresión gzip (0-9, default: 6)
  MAX_BACKUP_SIZE         - Tamaño máximo de backup (default: 1G)
  REMOTE_BACKUP_ENABLED   - Habilitar backup remoto (default: false)
  S3_BUCKET              - Bucket de S3 para backups remotos
  S3_REGION              - Región de S3

Estructura de backups:
  backups/
    ├── 20241106_041606_host_ai-news-aggregator/
    │   ├── metadata.json
    │   ├── database/
    │   ├── code/
    │   ├── configs/
    │   └── logs/
    └── 20241106_041606_host_ai-news-aggregator.tar.gz

Tipos de backup:
  full       - Backup completo de todos los componentes
  database   - Solo base de datos
  code       - Solo código fuente
  configs    - Solo configuraciones
  incremental - Backup incremental optimizado

Componentes respaldados:
  - database/       - Dump completo de PostgreSQL
  - code/           - Código fuente (backend, frontend)
  - configs/        - Archivos de configuración
  - logs/           - Logs recientes
  - volumes/        - Volúmenes Docker

EOF
}

schedule_backup() {
    local schedule_type="${2:-daily}"
    
    log_info "📅 Configurando backup programado: $schedule_type"
    
    local cron_expression
    
    case "$schedule_type" in
        "hourly")
            cron_expression="0 * * * *"
            ;;
        "daily")
            cron_expression="0 2 * * *"
            ;;
        "weekly")
            cron_expression="0 2 * * 0"
            ;;
        "monthly")
            cron_expression="0 2 1 * *"
            ;;
        *)
            log_error "Tipo de programación no válido: $schedule_type"
            usage
            exit 1
            ;;
    esac
    
    # Crear script para cron
    local cron_script="$BACKUP_BASE_DIR/backup_cron.sh"
    
    cat > "$cron_script" <<EOF
#!/bin/bash
# Script de backup automático generado por backup-restore.sh
# Tipo: $schedule_type

$(realpath "$SCRIPT_DIR/backup-restore.sh") create full >> "$BACKUP_BASE_DIR/cron.log" 2>&1
EOF
    
    chmod +x "$cron_script"
    
    # Agregar a crontab
    (crontab -l 2>/dev/null; echo "$cron_expression $(realpath "$cron_script")") | crontab -
    
    log_success "✅ Backup programado configurado"
    log_info "Expresión cron: $cron_expression"
    log_info "Script: $cron_script"
    log_info "Para ver crontab actual: crontab -l"
    log_info "Para remover programación: crontab -r"
}

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN] [parámetros]

Acciones disponibles:
  create [tipo]         - Crear backup (full|database|code|configs|incremental)
  restore <backup_path> - Restaurar desde backup
  list [filtro]         - Listar backups (all|recent)
  verify <backup_path>  - Verificar integridad de backup
  cleanup              - Limpiar backups antiguos
  schedule [tipo]       - Programar backup automático (hourly|daily|weekly|monthly)
  status               - Mostrar estado del sistema de backup
  config               - Mostrar configuración

Parámetros:
  backup_path          - Ruta al backup (archivo .tar.gz o directorio)
  tipo                 - Tipo de backup (full|database|code|configs|incremental)
  filtro               - Filtro de lista (all|recent)

Variables de entorno:
  BACKUP_BASE_DIR      - Directorio base (default: ./backups)
  RETENTION_DAYS       - Días de retención (default: 30)
  COMPRESSION_LEVEL    - Nivel compresión (0-9, default: 6)
  MAX_BACKUP_SIZE      - Tamaño máximo (default: 1G)
  REMOTE_BACKUP_ENABLED - Habilitar backup remoto (default: false)
  S3_BUCKET           - Bucket S3 para remoto
  S3_REGION           - Región S3

Ejemplos:
  $0 create                    # Backup completo
  $0 create database           # Solo base de datos
  $0 create incremental        # Backup incremental
  $0 restore backups/20241106_041606.tar.gz  # Restaurar backup
  $0 list                     # Ver todos los backups
  $0 list recent              # Ver backups recientes
  $0 verify backup.tar.gz     # Verificar backup
  $0 cleanup                  # Limpiar backups antiguos
  $0 schedule daily           # Backup diario automático
  $0 status                   # Ver estado del sistema

Estructura de backups:
  Los backups se almacenan en: $BACKUP_BASE_DIR/
  Formato: timestamp_hostname_project.tar.gz

EOF
}

# Ejecutar función principal
main "$@"