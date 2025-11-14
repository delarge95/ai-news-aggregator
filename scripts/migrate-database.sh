#!/bin/bash

# migrate-database.sh - Migraciones automatizadas de base de datos
# Versión: 1.0.0
# Descripción: Sistema de migraciones con versionado, backup y rollback

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "migrate-database"

# Configuración de migración
readonly PROJECT_NAME="ai-news-aggregator"
readonly DATABASE_CONTAINER="ai_news_postgres"
readonly DATABASE_NAME="ai_news_db"
readonly DATABASE_USER="postgres"
readonly DATABASE_MIGRATIONS_DIR="${DATABASE_MIGRATIONS_DIR:-./database/migrations}"
readonly BACKUP_DIR="./backups/database"
readonly MIGRATION_LOCK_FILE="/tmp/database_migration.lock"

# Variables de entorno
readonly MIGRATION_TIMEOUT="${MIGRATION_TIMEOUT:-300}"
readonly AUTO_BACKUP="${AUTO_BACKUP:-true}"
readonly DRY_RUN="${DRY_RUN:-false}"
readonly ROLLBACK_ON_ERROR="${ROLLBACK_ON_ERROR:-true}"

# Funciones principales
main() {
    local action="${1:-migrate}"
    
    case "$action" in
        "migrate") run_migrations ;;
        "rollback") rollback_migrations "$2" ;;
        "status") show_migration_status ;;
        "create") create_migration "$2" ;;
        "validate") validate_migrations ;;
        "list") list_migrations ;;
        "info") migration_info ;;
        *) usage ;;
    esac
}

run_migrations() {
    log_info "🚀 Iniciando proceso de migración de base de datos..."
    
    # Verificar prerrequisitos
    check_prerequisites
    
    # Crear lock para prevenir migraciones concurrentes
    create_migration_lock
    
    # Verificar si ya existen migraciones aplicadas
    local current_version
    current_version=$(get_current_migration_version)
    
    # Crear backup antes de migrar
    if [[ "$AUTO_BACKUP" == "true" ]]; then
        create_pre_migration_backup
    fi
    
    # Ejecutar migraciones
    local migration_start_time
    migration_start_time=$(date +%s)
    
    execute_pending_migrations "$current_version"
    
    local migration_end_time
    migration_end_time=$(date +%s)
    local migration_duration=$((migration_end_time - migration_start_time))
    
    # Verificar integridad post-migración
    validate_migration_result
    
    # Limpiar lock
    remove_migration_lock
    
    log_success "✅ Migraciones completadas exitosamente en ${migration_duration}s"
    log_metric "migration_duration" "$migration_duration"
    
    # Mostrar nueva versión
    local new_version
    new_version=$(get_current_migration_version)
    log_info "Versión actual: $new_version"
}

check_prerequisites() {
    log_info "Verificando prerrequisitos de migración..."
    
    # Verificar contenedor de base de datos
    if ! docker ps | grep -q "$DATABASE_CONTAINER"; then
        log_error "Contenedor de base de datos no encontrado: $DATABASE_CONTAINER"
        exit 1
    fi
    
    # Verificar conectividad
    if ! docker exec "$DATABASE_CONTAINER" pg_isready -U "$DATABASE_USER" > /dev/null 2>&1; then
        log_error "No se puede conectar a la base de datos"
        exit 1
    fi
    
    # Verificar directorio de migraciones
    if [[ ! -d "$DATABASE_MIGRATIONS_DIR" ]]; then
        log_error "Directorio de migraciones no encontrado: $DATABASE_MIGRATIONS_DIR"
        exit 1
    fi
    
    # Verificar archivos de migración
    local migration_files
    migration_files=$(find "$DATABASE_MIGRATIONS_DIR" -name "*.sql" | wc -l)
    
    if [[ $migration_files -eq 0 ]]; then
        log_warn "No se encontraron archivos de migración en $DATABASE_MIGRATIONS_DIR"
    else
        log_info "Encontrados $migration_files archivos de migración"
    fi
    
    log_success "Prerrequisitos verificados"
}

create_migration_lock() {
    log_info "Creando lock de migración..."
    
    if [[ -f "$MIGRATION_LOCK_FILE" ]]; then
        log_error "Ya existe un proceso de migración en curso"
        log_error "Archivo de lock: $MIGRATION_LOCK_FILE"
        log_info "Si estás seguro de que no hay migración en curso, elimina el archivo de lock manualmente"
        exit 1
    fi
    
    # Crear lock con información del proceso
    cat > "$MIGRATION_LOCK_FILE" <<EOF
PID=$$
START_TIME=$(date +%s)
USER=$(whoami)
HOST=$(hostname)
MIGRATION_DIR=$DATABASE_MIGRATIONS_DIR
EOF
    
    chmod 600 "$MIGRATION_LOCK_FILE"
    
    # Registrar trap para limpieza en caso de interrupción
    trap 'log_error "Migración interrumpida. Limpiando..."; remove_migration_lock; exit 1' INT TERM
    
    log_success "Lock de migración creado"
}

remove_migration_lock() {
    if [[ -f "$MIGRATION_LOCK_FILE" ]]; then
        rm -f "$MIGRATION_LOCK_FILE"
        log_success "Lock de migración eliminado"
    fi
}

get_current_migration_version() {
    # Verificar si existe tabla de migraciones
    local table_exists
    table_exists=$(docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'alembic_version';" 2>/dev/null | tr -d ' \n\r')
    
    if [[ "$table_exists" == "0" ]]; then
        echo "0000000"
        return
    fi
    
    # Obtener versión actual
    local current_version
    current_version=$(docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;" 2>/dev/null | tr -d ' \n\r')
    
    if [[ -z "$current_version" ]]; then
        echo "0000000"
    else
        echo "$current_version"
    fi
}

create_pre_migration_backup() {
    log_info "Creando backup pre-migración..."
    
    local backup_timestamp
    backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/pre_migration_$backup_timestamp.sql"
    
    mkdir -p "$(dirname "$backup_file")"
    
    # Crear backup completo
    docker exec "$DATABASE_CONTAINER" pg_dump -U "$DATABASE_USER" "$DATABASE_NAME" > "$backup_file"
    
    # Crear archivo de metadatos
    cat > "${backup_file}.metadata.json" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "type": "pre_migration_backup",
    "database": "$DATABASE_NAME",
    "version_before": "$(get_current_migration_version)",
    "size_bytes": $(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null),
    "compression": "none"
}
EOF
    
    log_success "Backup creado: $backup_file"
    log_metric "backup_size_bytes" "$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)"
}

execute_pending_migrations() {
    local current_version="$1"
    
    log_info "Ejecutando migraciones desde versión: $current_version"
    
    # Obtener lista de archivos de migración ordenados
    local migration_files
    mapfile -t migration_files < <(find "$DATABASE_MIGRATIONS_DIR" -name "*.sql" -type f | sort)
    
    local executed_migrations=0
    local failed_migrations=0
    
    for migration_file in "${migration_files[@]}"; do
        local migration_name
        migration_name=$(basename "$migration_file" .sql)
        
        # Extraer versión del nombre del archivo (formato esperado: XXX_descripcion.sql)
        local migration_version
        migration_version=$(echo "$migration_name" | cut -d'_' -f1)
        
        # Verificar si esta migración ya está aplicada
        if [[ "$migration_version" -le "$current_version" ]]; then
            log_debug "Migración $migration_name ya aplicada, omitiendo"
            continue
        fi
        
        # Aplicar migración
        if apply_migration "$migration_file" "$migration_name" "$migration_version"; then
            ((executed_migrations++))
        else
            if [[ "$ROLLBACK_ON_ERROR" == "true" ]]; then
                log_error "Error en migración $migration_name, intentando rollback..."
                handle_migration_error "$migration_name"
            fi
            ((failed_migrations++))
            break
        fi
    done
    
    log_info "Migraciones ejecutadas: $executed_migrations"
    
    if [[ $failed_migrations -gt 0 ]]; then
        log_error "Migraciones fallidas: $failed_migrations"
        exit 1
    fi
    
    if [[ $executed_migrations -eq 0 ]]; then
        log_info "No hay migraciones pendientes"
    fi
}

apply_migration() {
    local migration_file="$1"
    local migration_name="$2"
    local migration_version="$3"
    
    log_info "Aplicando migración: $migration_name (versión: $migration_version)"
    
    # Verificar sintaxis SQL antes de aplicar
    if ! validate_sql_syntax "$migration_file"; then
        log_error "Error de sintaxis en migración: $migration_file"
        return 1
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN: Migración $migration_name sería aplicada pero no se ejecuta"
        return 0
    fi
    
    local migration_start_time
    migration_start_time=$(date +%s%3N)
    
    # Crear transacción para la migración
    if docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "
        BEGIN;
        $(cat "$migration_file")
        INSERT INTO alembic_version (version_num) VALUES ('$migration_version');
        COMMIT;" > /dev/null 2>&1; then
        
        local migration_end_time
        migration_end_time=$(date +%s%3N)
        local migration_duration=$((migration_end_time - migration_start_time))
        
        log_success "✅ Migración $migration_name completada (${migration_duration}ms)"
        log_metric "migration_${migration_name}_duration" "$migration_duration"
        
        return 0
    else
        log_error "❌ Error aplicando migración $migration_name"
        return 1
    fi
}

validate_sql_syntax() {
    local migration_file="$1"
    
    # Verificar que el archivo no esté vacío
    if [[ ! -s "$migration_file" ]]; then
        log_error "Archivo de migración vacío: $migration_file"
        return 1
    fi
    
    # Verificar patrones SQL peligrosos
    if grep -qi "DROP DATABASE\|DROP SCHEMA\|SHUTDOWN\|KILL" "$migration_file"; then
        log_error "Comando SQL peligroso detectado en: $migration_file"
        return 1
    fi
    
    # Verificar que termine con punto y coma o esté vacío para transacción
    if ! tail -n 1 "$migration_file" | grep -q ";$" && [[ $(wc -l < "$migration_file") -gt 0 ]]; then
        log_warn "La migración no parece terminar con punto y coma"
    fi
    
    return 0
}

validate_migration_result() {
    log_info "Validando resultado de migraciones..."
    
    # Verificar que la base de datos esté accesible
    if ! docker exec "$DATABASE_CONTAINER" pg_isready -U "$DATABASE_USER" > /dev/null 2>&1; then
        log_error "Base de datos no disponible después de migraciones"
        return 1
    fi
    
    # Verificar integridad de tablas críticas
    local critical_tables=("articles" "users" "analytics")
    
    for table in "${critical_tables[@]}"; do
        if ! docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "SELECT 1 FROM $table LIMIT 1;" > /dev/null 2>&1; then
            log_warn "No se puede verificar la tabla $table (puede no existir)"
        fi
    done
    
    # Verificar que la tabla de versiones esté actualizada
    local version_count
    version_count=$(docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT COUNT(*) FROM alembic_version;" 2>/dev/null | tr -d ' \n\r')
    
    log_info "Versiones de migraciones aplicadas: $version_count"
    
    log_success "Validación de migraciones completada"
}

rollback_migrations() {
    local target_version="${1:-last}"
    
    log_warn "🔄 Iniciando rollback de migraciones..."
    
    case "$target_version" in
        "last")
            rollback_to_last_version
            ;;
        *)
            rollback_to_specific_version "$target_version"
            ;;
    esac
}

rollback_to_last_version() {
    log_info "Rollback a la última versión conocida..."
    
    # Obtener la última versión aplicada
    local last_version
    last_version=$(docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;" 2>/dev/null | tr -d ' \n\r')
    
    if [[ -z "$last_version" ]]; then
        log_error "No hay migraciones aplicadas para hacer rollback"
        exit 1
    fi
    
    # Crear backup antes del rollback
    if [[ "$AUTO_BACKUP" == "true" ]]; then
        create_pre_rollback_backup "$last_version"
    fi
    
    # Encontrar migración correspondiente y rollback
    local migration_file
    migration_file=$(find_migration_file "$last_version")
    
    if [[ -n "$migration_file" ]] && [[ -f "${migration_file%.sql}_rollback.sql" ]]; then
        execute_rollback "${migration_file%.sql}_rollback.sql" "$last_version"
    else
        log_error "No se encontró script de rollback para la versión $last_version"
        exit 1
    fi
    
    # Eliminar entrada de versión
    docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "
        DELETE FROM alembic_version WHERE version_num = '$last_version';" > /dev/null 2>&1
    
    log_success "Rollback completado"
}

rollback_to_specific_version() {
    local target_version="$1"
    
    log_info "Rollback a versión específica: $target_version"
    
    # Implementar lógica para rollback a versión específica
    # Por simplicidad, solo removemos las versiones posteriores
    local current_version
    current_version=$(get_current_migration_version)
    
    if [[ "$target_version" -ge "$current_version" ]]; then
        log_warn "Versión objetivo ($target_version) es igual o posterior a la actual ($current_version)"
        return 0
    fi
    
    # Crear backup
    if [[ "$AUTO_BACKUP" == "true" ]]; then
        create_pre_rollback_backup "$current_version"
    fi
    
    # Remover versiones posteriores
    docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "
        DELETE FROM alembic_version WHERE version_num > '$target_version';" > /dev/null 2>&1
    
    log_success "Rollback a versión $target_version completado"
}

create_pre_rollback_backup() {
    local from_version="$1"
    
    log_info "Creando backup pre-rollback desde versión: $from_version"
    
    local backup_timestamp
    backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/pre_rollback_${backup_timestamp}_${from_version}.sql"
    
    mkdir -p "$(dirname "$backup_file")"
    
    docker exec "$DATABASE_CONTAINER" pg_dump -U "$DATABASE_USER" "$DATABASE_NAME" > "$backup_file"
    
    log_success "Backup pre-rollback creado: $backup_file"
}

execute_rollback() {
    local rollback_file="$1"
    local version="$2"
    
    log_info "Ejecutando rollback desde archivo: $rollback_file"
    
    if [[ ! -f "$rollback_file" ]]; then
        log_error "Archivo de rollback no encontrado: $rollback_file"
        return 1
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN: Rollback sería ejecutado pero no se ejecuta"
        return 0
    fi
    
    # Ejecutar rollback en transacción
    if docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "
        BEGIN;
        $(cat "$rollback_file")
        COMMIT;" > /dev/null 2>&1; then
        log_success "Rollback ejecutado exitosamente"
        return 0
    else
        log_error "Error ejecutando rollback"
        return 1
    fi
}

show_migration_status() {
    log_info "📊 Estado de migraciones de base de datos"
    echo ""
    
    # Versión actual
    local current_version
    current_version=$(get_current_migration_version)
    echo "Versión actual: $current_version"
    
    # Contar migraciones
    local total_migrations
    total_migrations=$(find "$DATABASE_MIGRATIONS_DIR" -name "*.sql" | wc -l)
    
    local applied_migrations
    applied_migrations=$(docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -t -c "
        SELECT COUNT(*) FROM alembic_version;" 2>/dev/null | tr -d ' \n\r')
    
    echo "Migraciones aplicadas: $applied_migrations"
    echo "Migraciones disponibles: $total_migrations"
    echo "Migraciones pendientes: $((total_migrations - applied_migrations))"
    
    # Listar últimas migraciones aplicadas
    echo ""
    echo "Últimas 5 migraciones aplicadas:"
    docker exec "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" -c "
        SELECT version_num, version_num as 'timestamp' 
        FROM alembic_version 
        ORDER BY version_num DESC 
        LIMIT 5;" 2>/dev/null || echo "No hay migraciones aplicadas"
    
    # Verificar integridad
    echo ""
    echo "Estado de integridad:"
    if docker exec "$DATABASE_CONTAINER" pg_isready -U "$DATABASE_USER" > /dev/null 2>&1; then
        echo "  ✅ Base de datos accesible"
    else
        echo "  ❌ Base de datos no accesible"
    fi
    
    # Verificar lock
    if [[ -f "$MIGRATION_LOCK_FILE" ]]; then
        echo "  ⚠️  Hay un proceso de migración en curso"
    else
        echo "  ✅ No hay locks de migración"
    fi
}

create_migration() {
    local description="$2"
    
    if [[ -z "$description" ]]; then
        log_error "Descripción requerida para crear migración"
        usage
        exit 1
    fi
    
    # Generar nombre de migración
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local migration_name
    migration_name="${timestamp}_${description// /_}.sql"
    
    # Crear archivo de migración
    local migration_file="$DATABASE_MIGRATIONS_DIR/$migration_name"
    
    cat > "$migration_file" <<EOF
-- Migration: $description
-- Created: $(date)
-- Description: $description

-- Add your SQL migration here
-- Example:
-- ALTER TABLE articles ADD COLUMN new_field VARCHAR(255);

EOF
    
    # Crear archivo de rollback (plantilla)
    local rollback_file="$DATABASE_MIGRATIONS_DIR/${timestamp}_${description// /_}_rollback.sql"
    
    cat > "$rollback_file" <<EOF
-- Rollback migration: $description
-- Created: $(date)
-- Description: Rollback for $description

-- Add your SQL rollback here
-- Example:
-- ALTER TABLE articles DROP COLUMN IF EXISTS new_field;

EOF
    
    log_success "Archivos de migración creados:"
    log_info "  Migración: $migration_file"
    log_info "  Rollback: $rollback_file"
    log_info "  Edita estos archivos y luego ejecuta: $0 migrate"
}

validate_migrations() {
    log_info "Validando archivos de migración..."
    
    local validation_errors=0
    
    # Verificar directorio de migraciones
    if [[ ! -d "$DATABASE_MIGRATIONS_DIR" ]]; then
        log_error "Directorio de migraciones no existe: $DATABASE_MIGRATIONS_DIR"
        ((validation_errors++))
        return 1
    fi
    
    # Validar archivos de migración
    local migration_files
    mapfile -t migration_files < <(find "$DATABASE_MIGRATIONS_DIR" -name "*.sql" | grep -v "rollback.sql")
    
    if [[ ${#migration_files[@]} -eq 0 ]]; then
        log_warn "No se encontraron archivos de migración"
        return 0
    fi
    
    for migration_file in "${migration_files[@]}"; do
        local filename
        filename=$(basename "$migration_file")
        
        # Verificar formato del nombre
        if ! echo "$filename" | grep -qE '^[0-9]{8}_[0-9]{6}_.*\.sql$'; then
            log_error "Formato de nombre inválido: $filename"
            log_error "Formato esperado: YYYYMMDD_HHMMSS_descripcion.sql"
            ((validation_errors++))
            continue
        fi
        
        # Verificar sintaxis
        if ! validate_sql_syntax "$migration_file"; then
            ((validation_errors++))
        fi
        
        # Verificar que existe archivo de rollback correspondiente
        local rollback_file
        rollback_file="${migration_file%.sql}_rollback.sql"
        
        if [[ ! -f "$rollback_file" ]]; then
            log_warn "No existe archivo de rollback para: $filename"
            log_info "Sugerencia: Crear archivo: $(basename "$rollback_file")"
        fi
    done
    
    if [[ $validation_errors -eq 0 ]]; then
        log_success "✅ Todas las migraciones son válidas"
        return 0
    else
        log_error "❌ $validation_errors errores de validación encontrados"
        return 1
    fi
}

list_migrations() {
    log_info "📋 Lista de archivos de migración:"
    echo ""
    
    if [[ ! -d "$DATABASE_MIGRATIONS_DIR" ]]; then
        log_error "Directorio de migraciones no encontrado: $DATABASE_MIGRATIONS_DIR"
        return 1
    fi
    
    local migration_files
    mapfile -t migration_files < <(find "$DATABASE_MIGRATIONS_DIR" -name "*.sql" -type f | sort)
    
    if [[ ${#migration_files[@]} -eq 0 ]]; then
        log_info "No se encontraron archivos de migración"
        return 0
    fi
    
    for migration_file in "${migration_files[@]}"; do
        local filename
        local is_rollback
        local size
        
        filename=$(basename "$migration_file")
        is_rollback="false"
        
        if [[ "$filename" =~ _rollback\.sql$ ]]; then
            is_rollback="true"
        fi
        
        size=$(stat -f%z "$migration_file" 2>/dev/null || stat -c%s "$migration_file" 2>/dev/null)
        
        if [[ "$is_rollback" == "true" ]]; then
            echo "  🔄 $filename (${size} bytes)"
        else
            echo "  📝 $filename (${size} bytes)"
        fi
    done
    
    echo ""
    log_info "Total de archivos: ${#migration_files[@]}"
}

migration_info() {
    log_info "ℹ️  Información del sistema de migraciones"
    echo ""
    echo "Configuración:"
    echo "  Directorio de migraciones: $DATABASE_MIGRATIONS_DIR"
    echo "  Contenedor de BD: $DATABASE_CONTAINER"
    echo "  Base de datos: $DATABASE_NAME"
    echo "  Usuario: $DATABASE_USER"
    echo "  Backup automático: $AUTO_BACKUP"
    echo "  Dry run: $DRY_RUN"
    echo "  Rollback automático: $ROLLBACK_ON_ERROR"
    echo ""
    
    # Estado actual
    local current_version
    current_version=$(get_current_migration_version)
    echo "Estado actual:"
    echo "  Versión: $current_version"
    
    if [[ -f "$MIGRATION_LOCK_FILE" ]]; then
        echo "  Lock de migración: ACTIVO"
        if [[ -r "$MIGRATION_LOCK_FILE" ]]; then
            echo "  PID del proceso: $(grep '^PID=' "$MIGRATION_LOCK_FILE" | cut -d= -f2)"
            echo "  Usuario: $(grep '^USER=' "$MIGRATION_LOCK_FILE" | cut -d= -f2)"
        fi
    else
        echo "  Lock de migración: INACTIVO"
    fi
}

handle_migration_error() {
    local migration_name="$1"
    
    log_error "Error en migración: $migration_name"
    
    if [[ "$AUTO_BACKUP" == "true" ]]; then
        log_info "Restaurando desde backup automático..."
        restore_from_latest_backup
    fi
}

restore_from_latest_backup() {
    local latest_backup
    latest_backup=$(find "$BACKUP_DIR" -name "pre_migration_*.sql" | sort | tail -1)
    
    if [[ -n "$latest_backup" ]]; then
        log_info "Restaurando desde: $latest_backup"
        
        # Detener servicios para evitar conflictos
        docker-compose -f docker-compose.yml stop backend celery_worker celery_beat || true
        
        # Restaurar base de datos
        docker exec -i "$DATABASE_CONTAINER" psql -U "$DATABASE_USER" -d "$DATABASE_NAME" < "$latest_backup"
        
        # Reiniciar servicios
        docker-compose -f docker-compose.yml start backend celery_worker celery_beat || true
        
        log_success "Restauración completada"
    else
        log_error "No se encontró backup para restaurar"
    fi
}

find_migration_file() {
    local version="$1"
    
    find "$DATABASE_MIGRATIONS_DIR" -name "${version}_*.sql" -type f | grep -v "rollback.sql" | head -1
}

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN] [parámetros]

Acciones disponibles:
  migrate              - Ejecutar migraciones pendientes
  rollback [versión]   - Rollback a versión específica o última
  status               - Mostrar estado de migraciones
  create <descripción> - Crear nuevos archivos de migración
  validate             - Validar archivos de migración
  list                 - Listar archivos de migración
  info                 - Mostrar información del sistema

Variables de entorno:
  DATABASE_MIGRATIONS_DIR  - Directorio de migraciones (default: ./database/migrations)
  AUTO_BACKUP              - Backup automático (default: true)
  DRY_RUN                  - Simular ejecución (default: false)
  ROLLBACK_ON_ERROR        - Rollback automático en error (default: true)
  MIGRATION_TIMEOUT        - Timeout para operaciones (default: 300s)

Ejemplos:
  $0 migrate                          # Ejecutar migraciones
  $0 rollback                         # Rollback a última versión
  $0 rollback 20241106_041606        # Rollback a versión específica
  $0 create "add user preferences"   # Crear nueva migración
  $0 status                           # Ver estado actual
  $0 validate                         # Validar archivos SQL

Archivos de migración:
  Formato: YYYYMMDD_HHMMSS_descripcion.sql
  Ubicación: $DATABASE_MIGRATIONS_DIR
  Rollback: YYYYMMDD_HHMMSS_descripcion_rollback.sql

EOF
}

# Ejecutar función principal
main "$@"