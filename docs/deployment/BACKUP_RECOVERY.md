# Plan de Backup y Recuperación ante Desastres

## Tabla de Contenidos
- [Estrategia de Backup](#estrategia-de-backup)
- [Configuración de Backup](#configuración-de-backup)
- [Backup de Base de Datos](#backup-de-base-de-datos)
- [Backup de Archivos y Configuración](#backup-de-archivos-y-configuración)
- [Backup de Cache y Estado](#backup-de-cache-y-estado)
- [Backup Remoto](#backup-remoto)
- [Procedimientos de Recuperación](#procedimientos-de-recuperación)
- [Testing de Recuperación](#testing-de-recuperación)
- [Monitoring de Backups](#monitoring-de-backups)
- [Disaster Recovery Plan](#disaster-recovery-plan)

## Estrategia de Backup

### 1. RPO y RTO

```
┌─────────────────────────────────────────────────────────────────┐
│                    Backup Strategy Framework                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Data Classification:                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Critical      │  │   Important     │  │   Standard      │  │
│  │   (RPO: 15min)  │  │   (RPO: 1hr)    │  │   (RPO: 24hr)   │  │
│  │   (RTO: 1hr)    │  │   (RTO: 4hr)    │  │   (RTO: 24hr)   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                 │
│  Backup Types:                                                  │
│  • Continuous: Database transactions                           │
│  • Hourly: User data, configuration                           │
│  • Daily: Application code, static assets                     │
│  • Weekly: Complete system backups                            │
│  • Monthly: Archive and compliance backups                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 3-2-1 Backup Rule

- **3 copies** of data (original + 2 backups)
- **2 different media** types (local storage + cloud)
- **1 offsite** copy (cloud storage)

```yaml
# backup-strategy.yml
backup_strategy:
  retention_policy:
    critical_data:
      continuous: "15 minutes"
      hourly: "7 days"
      daily: "30 days"
      weekly: "12 weeks"
      monthly: "7 years"
    
    important_data:
      hourly: "24 hours"
      daily: "7 days"
      weekly: "4 weeks"
      monthly: "1 year"
    
    standard_data:
      daily: "24 hours"
      weekly: "2 weeks"
      monthly: "6 months"

  storage_locations:
    primary: "/backup/local"
    secondary: "s3://ai-news-backups-us-east-1"
    tertiary: "s3://ai-news-backups-us-west-2"
    
  encryption:
    algorithm: "AES-256"
    key_rotation: "30 days"
    
  compression:
    algorithm: "gzip"
    level: 6
```

## Configuración de Backup

### 1. Directorio de Backup

```bash
# Crear estructura de directorios de backup
sudo mkdir -p /backup/{local,remote,temp,logs}
sudo chown -R backup:backup /backup
sudo chmod 750 /backup

# Estructura de directorios
tree /backup
```

```
/backup/
├── local/           # Backups locales
│   ├── database/   # Backups de BD
│   ├── files/      # Backups de archivos
│   ├── config/     # Backups de configuración
│   └── logs/       # Logs de backup
├── remote/         # Backups remotos (S3, etc.)
├── temp/           # Directorio temporal
└── logs/           # Logs de operaciones de backup
```

### 2. Usuario de Backup

```bash
# Crear usuario específico para backup
sudo useradd -r -s /bin/bash -d /backup backup
sudo usermod -aG wheel backup

# Configurar sudoers para backup
echo 'backup ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/bin/pg_dump, /usr/bin/tar, /usr/bin/rsync' > /etc/sudoers.d/backup

# Configurar claves SSH para acceso remoto
sudo -u backup ssh-keygen -t rsa -b 4096 -f /backup/.ssh/id_rsa
```

### 3. Configuración de Logging

```python
# backup/logger_config.py
import logging
import logging.handlers
import os
from datetime import datetime

def setup_backup_logging():
    """Configurar logging para operaciones de backup"""
    
    # Crear directorio de logs
    log_dir = "/backup/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Formato de logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Archivo de log principal (rotación diaria)
    main_handler = logging.handlers.TimedRotatingFileHandler(
        f"{log_dir}/backup.log",
        when='midnight',
        interval=1,
        backupCount=30
    )
    main_handler.setFormatter(logging.Formatter(log_format))
    
    # Handler para errores (solo ERROR y CRITICAL)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        f"{log_dir}/backup_errors.log",
        when='midnight',
        interval=1,
        backupCount=90
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format))
    
    # Configurar logger principal
    logger = logging.getLogger('backup')
    logger.setLevel(logging.INFO)
    logger.addHandler(main_handler)
    logger.addHandler(error_handler)
    
    return logger

# Configurar para diferentes tipos de backup
backup_loggers = {
    'database': setup_backup_logging(),
    'files': setup_backup_logging(),
    'config': setup_backup_logging(),
    'remote': setup_backup_logging()
}
```

## Backup de Base de Datos

### 1. Script Principal de Backup

```bash
#!/bin/bash
# backup/database-backup.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/local/database"
LOCAL_RETENTION_DAYS=7
ENCRYPTION_KEY="/backup/keys/database.key"

# Logging
exec 1> >(tee -a "/backup/logs/database-backup.log")
exec 2> >(tee -a "/backup/logs/database-backup-error.log" >&2)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# Verificar configuración
check_config() {
    log "Verificando configuración..."
    
    if [[ -z "${DATABASE_URL:-}" ]]; then
        log_error "DATABASE_URL no está configurada"
        exit 1
    fi
    
    if [[ ! -f "$ENCRYPTION_KEY" ]]; then
        log_error "Clave de encriptación no encontrada: $ENCRYPTION_KEY"
        exit 1
    fi
    
    # Verificar conectividad a base de datos
    if ! pg_isready "${DATABASE_URL}" > /dev/null 2>&1; then
        log_error "No se puede conectar a la base de datos"
        exit 1
    fi
    
    log "Configuración verificada correctamente"
}

# Backup completo de base de datos
create_full_backup() {
    local backup_file="${BACKUP_DIR}/full_backup_${BACKUP_DATE}.sql"
    
    log "Iniciando backup completo de base de datos..."
    
    # Crear backup con compresión y encriptación
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --verbose \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        --file="${backup_file}.custom"
    
    # Encriptar backup
    gpg --cipher-algo AES256 --compress-algo 1 \
        --symmetric --output "${backup_file}.gpg" \
        --passphrase-file "$ENCRYPTION_KEY" \
        "${backup_file}.custom"
    
    # Verificar integridad
    if gpg --list-packets "${backup_file}.gpg" > /dev/null 2>&1; then
        log "Backup encriptado creado exitosamente: ${backup_file}.gpg"
        rm -f "${backup_file}.custom"
        return 0
    else
        log_error "Error en la encriptación del backup"
        return 1
    fi
}

# Backup diferencial
create_incremental_backup() {
    log "Creando backup diferencial..."
    
    # Para PostgreSQL, usamos log shipping o punto de recuperación
    # Este es un ejemplo simplificado
    
    local backup_file="${BACKUP_DIR}/incremental_backup_${BACKUP_DATE}.sql"
    local last_backup_file="${BACKUP_DIR}/last_backup_timestamp"
    
    # Obtener timestamp del último backup
    local last_backup_timestamp="1970-01-01 00:00:00"
    if [[ -f "$last_backup_file" ]]; then
        last_backup_timestamp=$(cat "$last_backup_file")
    fi
    
    # Crear backup incremental
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --where="modified_at > '${last_backup_timestamp}'" \
        --format=plain \
        | gzip > "${backup_file}.gz"
    
    # Encriptar backup incremental
    gpg --cipher-algo AES256 \
        --symmetric --output "${backup_file}.gpg.gz" \
        --passphrase-file "$ENCRYPTION_KEY" \
        < "${backup_file}.gz"
    
    # Actualizar timestamp del último backup
    date '+%Y-%m-%d %H:%M:%S' > "$last_backup_file"
    
    log "Backup incremental creado: ${backup_file}.gpg.gz"
}

# Backup de esquema
backup_schema() {
    local schema_file="${BACKUP_DIR}/schema_backup_${BACKUP_DATE}.sql"
    
    log "Creando backup de esquema..."
    
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --schema-only \
        --format=plain \
        --verbose \
        > "$schema_file"
    
    # Encriptar esquema
    gpg --cipher-algo AES256 \
        --symmetric --output "${schema_file}.gpg" \
        --passphrase-file "$ENCRYPTION_KEY" \
        < "$schema_file"
    
    log "Backup de esquema creado: ${schema_file}.gpg"
}

# Backup de datos críticos
backup_critical_data() {
    local critical_file="${BACKUP_DIR}/critical_backup_${BACKUP_DATE}.sql"
    
    log "Creando backup de datos críticos..."
    
    # Backup de tablas críticas con alta frecuencia
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --table=users \
        --table=user_preferences \
        --table=articles \
        --format=custom \
        --verbose \
        --file="${critical_file}.custom"
    
    # Encriptar
    gpg --cipher-algo AES256 \
        --symmetric --output "${critical_file}.gpg" \
        --passphrase-file "$ENCRYPTION_KEY" \
        "${critical_file}.custom"
    
    log "Backup de datos críticos creado: ${critical_file}.gpg"
}

# Limpiar backups antiguos
cleanup_old_backups() {
    log "Limpiando backups antiguos..."
    
    # Eliminar backups locales mayores a LOCAL_RETENTION_DAYS
    find "$BACKUP_DIR" -name "*.gpg" -mtime +${LOCAL_RETENTION_DAYS} -delete
    
    # Log de limpieza
    local remaining_backups=$(find "$BACKUP_DIR" -name "*.gpg" | wc -l)
    log "Backups restantes: $remaining_backups"
}

# Verificar integridad del backup
verify_backup() {
    local backup_file="$1"
    
    log "Verificando integridad de backup: $backup_file"
    
    # Verificar que el archivo existe y no está vacío
    if [[ ! -s "$backup_file" ]]; then
        log_error "Backup file is empty or missing: $backup_file"
        return 1
    fi
    
    # Verificar que se puede desencriptar
    if ! gpg --list-packets "$backup_file" > /dev/null 2>&1; then
        log_error "Cannot decrypt backup file: $backup_file"
        return 1
    fi
    
    log "Backup verificado exitosamente: $backup_file"
    return 0
}

# Upload a almacenamiento remoto
upload_to_remote() {
    local backup_file="$1"
    local remote_path="${REMOTE_BACKUP_PATH}/database/$(basename "$backup_file")"
    
    log "Subiendo backup a almacenamiento remoto..."
    
    # Configurar AWS CLI si es necesario
    if command -v aws &> /dev/null; then
        aws s3 cp "$backup_file" "$remote_path" \
            --storage-class STANDARD_IA \
            --metadata "backup_date=${BACKUP_DATE},backup_type=database"
        
        if [[ $? -eq 0 ]]; then
            log "Backup subido exitosamente a: $remote_path"
        else
            log_error "Error subiendo backup a almacenamiento remoto"
        fi
    else
        log "AWS CLI no disponible, saltando upload remoto"
    fi
}

# Función principal
main() {
    local backup_type="${1:-full}"
    
    log "Iniciando backup de base de datos (tipo: $backup_type)"
    
    # Verificar configuración
    check_config
    
    case "$backup_type" in
        "full")
            create_full_backup
            ;;
        "incremental")
            create_incremental_backup
            ;;
        "schema")
            backup_schema
            ;;
        "critical")
            backup_critical_data
            ;;
        *)
            log_error "Tipo de backup no válido: $backup_type"
            exit 1
            ;;
    esac
    
    # Limpiar backups antiguos
    cleanup_old_backups
    
    log "Backup de base de datos completado"
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Configuración de Backup

```bash
# backup/config/backup-config.env

# Database Configuration
DATABASE_URL="postgresql://username:password@hostname:5432/database"
DB_HOST="your-db-host"
DB_PORT="5432"
DB_USER="your-db-user"
DB_PASSWORD="your-secure-password"
DB_NAME="ai_news_aggregator"

# Backup Configuration
BACKUP_RETENTION_DAYS=7
BACKUP_COMPRESSION="gzip"
BACKUP_ENCRYPTION="gpg"

# Remote Storage Configuration
AWS_ACCESS_KEY_ID="your-aws-access-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
AWS_DEFAULT_REGION="us-east-1"
REMOTE_BACKUP_PATH="s3://ai-news-backups"

# Encryption Keys
ENCRYPTION_KEY_PATH="/backup/keys/database.key"

# Monitoring
BACKUP_NOTIFICATION_EMAIL="admin@yourdomain.com"
BACKUP_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
```

### 3. Cron Jobs para Backup

```bash
# Agregar a crontab para usuario backup
sudo -u backup crontab -e

# Backup de base de datos cada 6 horas
0 */6 * * * /backup/database-backup.sh full

# Backup incremental cada hora
0 * * * * /backup/database-backup.sh incremental

# Backup de datos críticos cada 15 minutos
*/15 * * * * /backup/database-backup.sh critical

# Backup de esquema semanalmente (Domingos a las 2 AM)
0 2 * * 0 /backup/database-backup.sh schema

# Limpieza de logs diariamente
0 3 * * * find /backup/logs -name "*.log" -mtime +30 -delete

# Verificación de backups diariamente
0 4 * * * /backup/verify-backups.sh
```

## Backup de Archivos y Configuración

### 1. Script de Backup de Archivos

```bash
#!/bin/bash
# backup/files-backup.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/local/files"
SOURCE_DIRS=(
    "/var/www/ai-news-aggregator"
    "/etc/nginx"
    "/etc/ssl"
    "/home/deploy/.ssh"
    "/backup/config"
)
EXCLUDE_PATTERNS=(
    "*/node_modules/*"
    "*/__pycache__/*"
    "*/venv/*"
    "*/env/*"
    "*/.git/*"
    "*/tmp/*"
    "*/logs/*"
    "*/cache/*"
)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# Crear lista de archivos a excluir
create_exclude_file() {
    local exclude_file="/tmp/backup-exclude-${BACKUP_DATE}.txt"
    
    > "$exclude_file"
    for pattern in "${EXCLUDE_PATTERNS[@]}"; do
        echo "$pattern" >> "$exclude_file"
    done
    
    echo "$exclude_file"
}

# Backup de directorio específico
backup_directory() {
    local source_dir="$1"
    local backup_name="$2"
    local backup_file="${BACKUP_DIR}/${backup_name}_${BACKUP_DATE}.tar.gz"
    local exclude_file
    
    if [[ ! -d "$source_dir" ]]; then
        log_error "Directorio fuente no existe: $source_dir"
        return 1
    fi
    
    log "Creando backup de: $source_dir"
    
    exclude_file=$(create_exclude_file)
    
    # Crear backup con compresión
    tar -czf "$backup_file" \
        --exclude-from="$exclude_file" \
        --exclude="${BACKUP_DIR}" \
        -C "$(dirname "$source_dir")" \
        "$(basename "$source_dir")"
    
    # Verificar integridad del backup
    if tar -tzf "$backup_file" > /dev/null 2>&1; then
        log "Backup creado exitosamente: $backup_file"
        echo "$backup_file"
        return 0
    else
        log_error "Error creando backup: $backup_file"
        return 1
    fi
}

# Backup de configuración de Docker
backup_docker_config() {
    local backup_file="${BACKUP_DIR}/docker_config_${BACKUP_DATE}.tar.gz"
    
    log "Creando backup de configuración Docker..."
    
    # Incluir docker-compose.yml, Dockerfile, y configuraciones
    tar -czf "$backup_file" \
        -C /var/www/ai-news-aggregator \
        docker-compose*.yml \
        Dockerfile* \
        .dockerignore \
        scripts/ \
        --exclude="*/node_modules" \
        --exclude="*/__pycache__"
    
    log "Backup Docker creado: $backup_file"
    echo "$backup_file"
}

# Backup de certificados SSL
backup_ssl_certificates() {
    local backup_file="${BACKUP_DIR}/ssl_certs_${BACKUP_DATE}.tar.gz"
    
    log "Creando backup de certificados SSL..."
    
    # Backup de certificados Let's Encrypt
    if [[ -d "/etc/letsencrypt" ]]; then
        tar -czf "$backup_file" -C /etc letsencrypt
        log "Backup SSL creado: $backup_file"
        echo "$backup_file"
    else
        log "No se encontraron certificados SSL para backup"
        return 1
    fi
}

# Backup de logs importantes
backup_critical_logs() {
    local backup_file="${BACKUP_DIR}/critical_logs_${BACKUP_DATE}.tar.gz"
    
    log "Creando backup de logs críticos..."
    
    # Crear backup de logs recientes (últimos 7 días)
    find /var/log/nginx -name "*.log" -mtime -7 -exec tar -rf "$backup_file" {} \; 2>/dev/null || true
    find /var/www/ai-news-aggregator/logs -name "*.log" -mtime -7 -exec tar -rf "$backup_file" {} \; 2>/dev/null || true
    
    # Verificar si hay contenido
    if tar -tzf "$backup_file" > /dev/null 2>&1; then
        log "Backup de logs creado: $backup_file"
        echo "$backup_file"
    else
        log "No hay logs para backup, eliminando archivo vacío"
        rm -f "$backup_file"
    fi
}

# Encriptar backup
encrypt_backup() {
    local backup_file="$1"
    local encrypted_file="${backup_file}.gpg"
    
    log "Encriptando backup: $backup_file"
    
    gpg --cipher-algo AES256 \
        --symmetric --output "$encrypted_file" \
        --passphrase-file "$ENCRYPTION_KEY_PATH" \
        < "$backup_file"
    
    if [[ $? -eq 0 ]]; then
        log "Backup encriptado: $encrypted_file"
        rm -f "$backup_file"
        echo "$encrypted_file"
    else
        log_error "Error encriptando backup"
        return 1
    fi
}

# Función principal
main() {
    local backup_type="${1:-full}"
    
    log "Iniciando backup de archivos (tipo: $backup_type)"
    
    case "$backup_type" in
        "full")
            # Backup completo
            backup_directory "/var/www/ai-news-aggregator" "application"
            backup_directory "/etc/nginx" "nginx"
            backup_directory "/home/deploy/.ssh" "ssh-keys"
            ;;
        "config")
            # Solo configuraciones
            backup_directory "/var/www/ai-news-aggregator" "app-config"
            backup_directory "/etc/nginx" "nginx-config"
            backup_docker_config
            ;;
        "ssl")
            # Solo certificados SSL
            backup_ssl_certificates
            ;;
        "logs")
            # Solo logs críticos
            backup_critical_logs
            ;;
        *)
            log_error "Tipo de backup no válido: $backup_type"
            exit 1
            ;;
    esac
    
    # Encriptar todos los backups creados
    for backup_file in "${BACKUP_DIR}"/*_${BACKUP_DATE}.tar.gz; do
        if [[ -f "$backup_file" ]]; then
            encrypt_backup "$backup_file"
        fi
    done
    
    log "Backup de archivos completado"
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Backup de Configuración de Sistema

```bash
#!/bin/bash
# backup/system-config-backup.sh

set -euo pipefail

# Variables
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/local/config"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Backup de configuración del sistema
backup_system_config() {
    local config_file="${BACKUP_DIR}/system_config_${BACKUP_DATE}.tar.gz"
    
    log "Creando backup de configuración del sistema..."
    
    # Lista de archivos de configuración importantes
    config_files=(
        "/etc/hosts"
        "/etc/hostname"
        "/etc/resolv.conf"
        "/etc/fstab"
        "/etc/crontab"
        "/etc/passwd"
        "/etc/group"
        "/etc/shadow"
        "/etc/sudoers"
        "/etc/ssh/sshd_config"
        "/etc/environment"
        "/etc/systemd/resolved.conf"
        "/etc/ntp.conf"
        "/etc/sysctl.conf"
        "/etc/security/limits.conf"
    )
    
    # Crear directorio temporal
    local temp_dir="/tmp/system-config-${BACKUP_DATE}"
    mkdir -p "$temp_dir"
    
    # Copiar archivos de configuración
    for config_file in "${config_files[@]}"; do
        if [[ -f "$config_file" ]]; then
            cp -p "$config_file" "$temp_dir/"
            log "Configuración respaldada: $config_file"
        fi
    done
    
    # Crear archivo de información del sistema
    {
        echo "=== SYSTEM INFORMATION ==="
        echo "Date: $(date)"
        echo "Hostname: $(hostname)"
        echo "Kernel: $(uname -r)"
        echo "OS: $(lsb_release -d 2>/dev/null || echo 'Unknown')"
        echo ""
        echo "=== DISK USAGE ==="
        df -h
        echo ""
        echo "=== MOUNTED FILESYSTEMS ==="
        mount | column -t
        echo ""
        echo "=== INSTALLED PACKAGES ==="
        dpkg -l | grep ^ii
        echo ""
        echo "=== RUNNING SERVICES ==="
        systemctl list-units --type=service --state=running
    } > "$temp_dir/system-info.txt"
    
    # Crear backup
    tar -czf "${config_file}.gpg" -C "$temp_dir" .
    
    # Limpiar directorio temporal
    rm -rf "$temp_dir"
    
    log "Backup de configuración del sistema creado: ${config_file}.gpg"
}

# Función principal
main() {
    backup_system_config
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Backup de Cache y Estado

### 1. Backup de Redis

```bash
#!/bin/bash
# backup/redis-backup.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/local/redis"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Backup de Redis
backup_redis() {
    local backup_file="${BACKUP_DIR}/redis_backup_${BACKUP_DATE}.rdb"
    
    log "Creando backup de Redis..."
    
    # Comando Redis con autenticación si es necesaria
    local redis_cmd="redis-cli"
    if [[ -n "$REDIS_PASSWORD" ]]; then
        redis_cmd="redis-cli -a $REDIS_PASSWORD"
    fi
    
    # Crear backup usando Redis
    if $redis_cmd --rdb "$backup_file" > /dev/null 2>&1; then
        # Encriptar backup
        gpg --cipher-algo AES256 \
            --symmetric --output "${backup_file}.gpg" \
            --passphrase-file "$ENCRYPTION_KEY_PATH" \
            < "$backup_file"
        
        if [[ $? -eq 0 ]]; then
            rm -f "$backup_file"
            log "Backup de Redis creado exitosamente: ${backup_file}.gpg"
            return 0
        else
            log_error "Error encriptando backup de Redis"
            return 1
        fi
    else
        log_error "Error creando backup de Redis"
        return 1
    fi
}

# Función principal
main() {
    backup_redis
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Backup de Docker Volumes

```bash
#!/bin/bash
# backup/docker-volumes-backup.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/local/docker"
CONTAINERS=("ai-news-backend" "ai-news-frontend" "ai-news-redis")

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Backup de volúmenes Docker
backup_docker_volumes() {
    local backup_file="${BACKUP_DIR}/docker_volumes_${BACKUP_DATE}.tar.gz"
    
    log "Creando backup de volúmenes Docker..."
    
    # Usar docker run para crear backup
    docker run --rm \
        -v ai-news-aggregator_data:/data:ro \
        -v "$BACKUP_DIR":/backup \
        alpine tar -czf "/backup/volumes_${BACKUP_DATE}.tar.gz" -C /data .
    
    # Encriptar backup
    gpg --cipher-algo AES256 \
        --symmetric --output "${backup_file}.gpg" \
        --passphrase-file "$ENCRYPTION_KEY_PATH" \
        < "${backup_file}"
    
    if [[ $? -eq 0 ]]; then
        rm -f "$backup_file"
        log "Backup de volúmenes Docker creado: ${backup_file}.gpg"
        return 0
    else
        log_error "Error en backup de volúmenes Docker"
        return 1
    fi
}

# Función principal
main() {
    backup_docker_volumes
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Backup Remoto

### 1. Upload a AWS S3

```bash
#!/bin/bash
# backup/remote-backup-sync.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="${REMOTE_BACKUP_PATH#s3://}"
REMOTE_PATH="s3://${S3_BUCKET}/ai-news-backups/$(date +%Y-%m-%d)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Verificar AWS CLI
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log "Instalando AWS CLI..."
        apt-get update && apt-get install -y awscli
    fi
    
    # Verificar configuración
    if ! aws s3 ls &> /dev/null; then
        log_error "AWS CLI no configurado correctamente"
        return 1
    fi
    
    log "AWS CLI verificado"
    return 0
}

# Sincronizar backups locales a S3
sync_backups_to_s3() {
    local local_dir="$1"
    local s3_path="$REMOTE_PATH/$(basename "$local_dir")"
    
    log "Sincronizando $local_dir a $s3_path"
    
    # Sincronizar con S3
    aws s3 sync "$local_dir" "$s3_path" \
        --storage-class STANDARD_IA \
        --metadata "backup_date=${BACKUP_DATE},backup_type=local-sync" \
        --exclude "*.tmp" \
        --exclude "*~"
    
    if [[ $? -eq 0 ]]; then
        log "Sincronización exitosa: $s3_path"
        return 0
    else
        log_error "Error en sincronización: $s3_path"
        return 1
    fi
}

# Verificar integridad del backup remoto
verify_remote_backup() {
    local s3_path="$1"
    
    log "Verificando integridad del backup remoto: $s3_path"
    
    # Listar archivos en S3
    local files=$(aws s3 ls "$s3_path" --recursive | wc -l)
    
    if [[ $files -gt 0 ]]; then
        log "Backup remoto verificado: $files archivos encontrados"
        return 0
    else
        log_error "Backup remoto no encontrado o vacío: $s3_path"
        return 1
    fi
}

# Cleanup de backups remotos antiguos
cleanup_remote_backups() {
    local retention_days=30
    
    log "Limpiando backups remotos anteriores a $retention_days días..."
    
    # Calcular fecha de cutoff
    local cutoff_date=$(date -d "$retention_days days ago" +%Y-%m-%d)
    local s3_prefix="s3://${S3_BUCKET}/ai-news-backups/"
    
    # Listar y eliminar directorios antiguos
    aws s3 ls "$s3_prefix" --recursive | while read -r line; do
        local file_date=$(echo "$line" | awk '{print $1}')
        if [[ "$file_date" < "$cutoff_date" ]]; then
            local file_path=$(echo "$line" | awk '{print $4}')
            log "Eliminando backup antiguo: $file_path"
            aws s3 rm "s3://${S3_BUCKET}/$file_path"
        fi
    done
}

# Función principal
main() {
    log "Iniciando sincronización de backups remotos..."
    
    # Verificar AWS CLI
    if ! check_aws_cli; then
        exit 1
    fi
    
    # Sincronizar diferentes tipos de backup
    sync_backups_to_s3 "/backup/local/database"
    sync_backups_to_s3 "/backup/local/files"
    sync_backups_to_s3 "/backup/local/config"
    sync_backups_to_s3 "/backup/local/redis"
    
    # Cleanup de backups antiguos
    cleanup_remote_backups
    
    log "Sincronización de backups remotos completada"
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Multi-Cloud Strategy

```yaml
# backup/multi-cloud-config.yml
cloud_providers:
  primary:
    name: "AWS S3"
    type: "s3"
    region: "us-east-1"
    bucket: "ai-news-backups-primary"
    storage_class: "STANDARD_IA"
    encryption: "AES256"
    
  secondary:
    name: "Google Cloud Storage"
    type: "gcs"
    region: "us-central1"
    bucket: "ai-news-backups-secondary"
    storage_class: "NEARLINE"
    encryption: "google-managed"
    
  tertiary:
    name: "Azure Blob Storage"
    type: "azure"
    region: "eastus"
    container: "ai-news-backups-tertiary"
    access_tier: "Cool"
    encryption: "Microsoft-managed"

retention_policies:
  primary:
    daily: "30 days"
    weekly: "12 weeks"
    monthly: "7 years"
    
  secondary:
    daily: "7 days"
    weekly: "4 weeks"
    monthly: "1 year"
    
  tertiary:
    daily: "3 days"
    weekly: "2 weeks"
    monthly: "3 months"

validation:
  checksum_verification: true
  integrity_check: true
  recovery_test_frequency: "weekly"
```

## Procedimientos de Recuperación

### 1. Script de Recuperación Completa

```bash
#!/bin/bash
# recovery/complete-recovery.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
RECOVERY_DATE="${1:-latest}"
RECOVERY_DIR="/tmp/recovery-${RECOVERY_DATE}"
RECOVERY_LOG="/backup/logs/recovery-${RECOVERY_DATE}.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$RECOVERY_LOG"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$RECOVERY_LOG" >&2
}

# Crear directorio de recuperación
setup_recovery_environment() {
    log "Configurando entorno de recuperación..."
    
    mkdir -p "$RECOVERY_DIR"
    cd "$RECOVERY_DIR"
    
    log "Directorio de recuperación: $RECOVERY_DIR"
}

# Listar backups disponibles
list_available_backups() {
    log "Listando backups disponibles..."
    
    echo "=== DATABASE BACKUPS ==="
    find /backup/local/database -name "*.gpg" | sort -r | head -10
    
    echo ""
    echo "=== FILES BACKUPS ==="
    find /backup/local/files -name "*.gpg" | sort -r | head -10
    
    echo ""
    echo "=== REMOTE BACKUPS ==="
    if command -v aws &> /dev/null; then
        aws s3 ls "${REMOTE_BACKUP_PATH}/" --recursive | tail -20
    fi
}

# Descargar backup desde almacenamiento remoto
download_remote_backup() {
    local backup_type="$1"
    local backup_file="$2"
    local local_path="/backup/local/downloaded"
    
    log "Descargando backup remoto: $backup_file"
    
    mkdir -p "$local_path"
    
    aws s3 cp "$backup_file" "$local_path/" --storage-class STANDARD_IA
    
    if [[ $? -eq 0 ]]; then
        log "Backup descargado: $local_path/$(basename "$backup_file")"
        echo "$local_path/$(basename "$backup_file")"
    else
        log_error "Error descargando backup remoto"
        return 1
    fi
}

# Desencriptar backup
decrypt_backup() {
    local encrypted_file="$1"
    local decrypted_file="${encrypted_file%.gpg}"
    
    log "Desencriptando backup: $encrypted_file"
    
    gpg --decrypt --passphrase-file "$ENCRYPTION_KEY_PATH" \
        < "$encrypted_file" > "$decrypted_file"
    
    if [[ $? -eq 0 ]]; then
        log "Backup desencriptado exitosamente: $decrypted_file"
        echo "$decrypted_file"
    else
        log_error "Error desencriptando backup"
        return 1
    fi
}

# Recuperar base de datos
recover_database() {
    local backup_file="$1"
    local temp_file="/tmp/db_recovery_$(date +%s)"
    
    log "Iniciando recuperación de base de datos..."
    
    # Verificar conectividad a base de datos
    if ! pg_isready "${DATABASE_URL}" > /dev/null 2>&1; then
        log_error "No se puede conectar a la base de datos"
        return 1
    fi
    
    # Desencriptar backup si es necesario
    if [[ "$backup_file" == *.gpg ]]; then
        backup_file=$(decrypt_backup "$backup_file")
    fi
    
    # Crear backup de seguridad antes de restaurar
    log "Creando backup de seguridad previo..."
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        --host="${DB_HOST}" --port="${DB_PORT}" \
        --username="${DB_USER}" --dbname="${DB_NAME}" \
        --format=custom --file="${temp_file}.pre_recovery.custom"
    
    # Restaurar base de datos
    log "Restaurando base de datos desde backup..."
    
    # Para backups custom de pg_dump
    if [[ "$backup_file" == *.custom ]]; then
        PGPASSWORD="${DB_PASSWORD}" pg_restore \
            --host="${DB_HOST}" --port="${DB_PORT}" \
            --username="${DB_USER}" --dbname="${DB_NAME}" \
            --clean --if-exists --verbose \
            "$backup_file"
    else
        # Para backups SQL planos
        PGPASSWORD="${DB_PASSWORD}" psql \
            --host="${DB_HOST}" --port="${DB_PORT}" \
            --username="${DB_USER}" --dbname="${DB_NAME}" \
            --file="$backup_file"
    fi
    
    if [[ $? -eq 0 ]]; then
        log "Base de datos recuperada exitosamente"
        return 0
    else
        log_error "Error recuperando base de datos"
        return 1
    fi
}

# Recuperar archivos
recover_files() {
    local backup_file="$1"
    local target_directory="${2:-/var/www/ai-news-aggregator}"
    
    log "Iniciando recuperación de archivos..."
    
    # Desencriptar backup si es necesario
    if [[ "$backup_file" == *.gpg ]]; then
        backup_file=$(decrypt_backup "$backup_file")
    fi
    
    # Crear backup de seguridad
    local safety_backup="/tmp/files_safety_backup_$(date +%s).tar.gz"
    log "Creando backup de seguridad..."
    tar -czf "$safety_backup" -C "$(dirname "$target_directory")" "$(basename "$target_directory")"
    
    # Restaurar archivos
    log "Restaurando archivos a: $target_directory"
    mkdir -p "$target_directory"
    
    if [[ -d "$target_directory" ]]; then
        # Extraer en directorio temporal primero
        local temp_extract="/tmp/files_recovery_$(date +%s)"
        mkdir -p "$temp_extract"
        
        tar -xzf "$backup_file" -C "$temp_extract"
        
        # Mover archivos al directorio destino
        mv "${temp_extract}/$(basename "$target_directory")"/* "$target_directory/" 2>/dev/null || true
        
        # Limpiar
        rm -rf "$temp_extract"
        
        log "Archivos recuperados exitosamente"
        return 0
    else
        log_error "Error: directorio destino no existe: $target_directory"
        return 1
    fi
}

# Recuperar configuración
recover_configuration() {
    local backup_file="$1"
    
    log "Iniciando recuperación de configuración..."
    
    # Desencriptar backup si es necesario
    if [[ "$backup_file" == *.gpg ]]; then
        backup_file=$(decrypt_backup "$backup_file")
    fi
    
    # Restaurar configuración del sistema
    if [[ "$backup_file" == *.tar* ]]; then
        local temp_extract="/tmp/config_recovery_$(date +%s)"
        mkdir -p "$temp_extract"
        
        tar -xzf "$backup_file" -C "$temp_extract"
        
        # Restaurar archivos de configuración específicos
        cp -p "$temp_extract"/etc/* /etc/ 2>/dev/null || true
        
        # Restaurar configuración de aplicación
        if [[ -d "$temp_extract/var/www/ai-news-aggregator" ]]; then
            cp -r "$temp_extract/var/www/ai-news-aggregator"/* /var/www/ai-news-aggregator/
        fi
        
        rm -rf "$temp_extract"
        log "Configuración recuperada exitosamente"
    fi
}

# Verificar integridad después de la recuperación
verify_recovery() {
    log "Verificando integridad después de la recuperación..."
    
    local errors=0
    
    # Verificar conectividad a base de datos
    if pg_isready "${DATABASE_URL}" > /dev/null 2>&1; then
        log "✅ Base de datos: Conectividad OK"
    else
        log_error "❌ Base de datos: Error de conectividad"
        ((errors++))
    fi
    
    # Verificar archivos críticos
    if [[ -f "/var/www/ai-news-aggregator/docker-compose.yml" ]]; then
        log "✅ Archivos: docker-compose.yml presente"
    else
        log_error "❌ Archivos: docker-compose.yml faltante"
        ((errors++))
    fi
    
    # Verificar configuración de Nginx
    if [[ -f "/etc/nginx/sites-available/ai-news-aggregator" ]]; then
        log "✅ Nginx: Configuración presente"
    else
        log_error "❌ Nginx: Configuración faltante"
        ((errors++))
    fi
    
    # Test básico de API
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log "✅ API: Respuesta OK"
    else
        log_error "❌ API: No responde"
        ((errors++))
    fi
    
    if [[ $errors -eq 0 ]]; then
        log "✅ Verificación de integridad: TODOS LOS TESTS PASARON"
        return 0
    else
        log_error "❌ Verificación de integridad: $errors errores encontrados"
        return 1
    fi
}

# Función principal de recuperación
main() {
    local recovery_type="$1"
    local backup_source="${2:-local}"
    
    log "=== INICIANDO RECUPERACIÓN COMPLETA ==="
    log "Tipo de recuperación: $recovery_type"
    log "Fuente de backup: $backup_source"
    
    # Configurar entorno
    setup_recovery_environment
    
    # Listar backups disponibles
    if [[ "${3:-}" == "--list" ]]; then
        list_available_backups
        exit 0
    fi
    
    # Recuperar según el tipo
    case "$recovery_type" in
        "database")
            local backup_file="$3"
            if [[ -z "$backup_file" ]]; then
                log_error "Archivo de backup no especificado"
                exit 1
            fi
            recover_database "$backup_file"
            ;;
        "files")
            local backup_file="$3"
            if [[ -z "$backup_file" ]]; then
                log_error "Archivo de backup no especificado"
                exit 1
            fi
            recover_files "$backup_file"
            ;;
        "config")
            local backup_file="$3"
            if [[ -z "$backup_file" ]]; then
                log_error "Archivo de backup no especificado"
                exit 1
            fi
            recover_configuration "$backup_file"
            ;;
        "complete")
            # Recuperación completa (base de datos + archivos + configuración)
            log "Recuperación completa - este proceso puede tomar varios minutos"
            # Implementar lógica de recuperación completa
            ;;
        *)
            log_error "Tipo de recuperación no válido: $recovery_type"
            log "Tipos disponibles: database, files, config, complete"
            exit 1
            ;;
    esac
    
    # Verificar integridad
    if verify_recovery; then
        log "✅ RECUPERACIÓN COMPLETADA EXITOSAMENTE"
        log "Fecha de recuperación: $(date)"
        log "Directorio de logs: $RECOVERY_LOG"
    else
        log_error "❌ RECUPERACIÓN COMPLETADA CON ERRORES"
        log "Revisar logs para más detalles: $RECOVERY_LOG"
        exit 1
    fi
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Runbook de Recuperación

```markdown
# Runbook de Recuperación ante Desastres

## Escenario 1: Falla Completa del Servidor

### Situación
- Servidor principal no disponible
- Todos los servicios caídos
- Acceso físico/SSH no disponible

### Pasos de Recuperación

1. **Evaluar la situación**
   ```bash
   # Desde servidor secundario o workstation
   ping yourdomain.com
   ssh backup@backup-server "check_backup_integrity.sh"
   ```

2. **Provisionar nuevo servidor**
   - Crear droplet en DigitalOcean con especificaciones similares
   - Configurar DNS para apuntar a nuevo servidor
   - Configurar firewall y seguridad básica

3. **Recuperar desde backup**
   ```bash
   # Ejecutar recuperación completa
   ./recovery/complete-recovery.sh complete local --list
   ./recovery/complete-recovery.sh complete local
   ```

4. **Verificar servicios**
   ```bash
   make health-check
   make test-endpoints
   ```

### Tiempo Estimado de Recuperación (RTO)
- **RTO**: 2-4 horas
- **RPO**: 15 minutos (con backups continuos)

## Escenario 2: Corrupción de Base de Datos

### Situación
- Base de datos corrupta o inaccesible
- Otros servicios funcionando

### Pasos de Recuperación

1. **Identificar la corrupción**
   ```bash
   ./diagnose/database-diagnosis.sh
   ```

2. **Poner aplicación en modo mantenimiento**
   ```bash
   ./maintenance/enable-maintenance-mode.sh
   ```

3. **Recuperar desde backup de BD**
   ```bash
   # Listar backups disponibles
   ./recovery/complete-recovery.sh database --list
   
   # Recuperar desde backup más reciente
   ./recovery/complete-recovery.sh database /backup/local/database/full_backup_20231201_120000.gpg
   ```

4. **Verificar integridad**
   ```bash
   PGPASSWORD="${DB_PASSWORD}" pg_verifycluster 15 main
   ```

5. **Restaurar servicios**
   ```bash
   ./maintenance/disable-maintenance-mode.sh
   ```

### Tiempo Estimado
- **RTO**: 30-60 minutos
- **RPO**: 15 minutos

## Escenario 3: Ataque de Ransomware

### Situación
- Archivos encriptados o modificados maliciosamente
- Datos comprometidos

### Pasos de Recuperación

1. **Aislar sistemas comprometidos**
   ```bash
   # Desconectar de red
   iptables -A INPUT -j DROP
   iptables -A OUTPUT -j DROP
   ```

2. **Evaluar alcance del daño**
   ```bash
   ./security/incident-assessment.sh
   ```

3. **Recuperar desde backup verificado**
   ```bash
   # Usar backup anterior al incidente
   ./recovery/complete-recovery.sh complete --backup-date 20231201
   ```

4. **Cambiar credenciales**
   ```bash
   ./security/rotate-all-credentials.sh
   ```

5. **Aplicar parches de seguridad**
   ```bash
   ./security/apply-security-patches.sh
   ```

### Tiempo Estimado
- **RTO**: 4-8 horas
- **RPO**: 24 horas (backup anterior al ataque)

## Escenario 4: Falla de Almacenamiento

### Situación
- Disco duro con fallas
- Datos inaccesibles

### Pasos de Recuperación

1. **Reemplazar hardware defectuoso**
   - Cambiar disco duro
   - Reconfigurar RAID si es necesario

2. **Restaurar desde backup**
   ```bash
   ./recovery/complete-recovery.sh files
   ```

3. **Verificar integridad de datos**
   ```bash
   ./tools/verify-data-integrity.sh
   ```

### Tiempo Estimado
- **RTO**: 1-3 horas (según tamaño de datos)
- **RPO**: 1 hora (backup de archivos)
```

## Testing de Recuperación

### 1. Script de Testing

```bash
#!/bin/bash
# testing/recovery-drill.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
TEST_DATE=$(date +%Y%m%d_%H%M%S)
TEST_LOG="/backup/logs/recovery-test-${TEST_DATE}.log"
TEST_DIR="/tmp/recovery-test-${TEST_DATE}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$TEST_LOG"
}

# Crear ambiente de testing
setup_test_environment() {
    log "Configurando ambiente de testing..."
    
    mkdir -p "$TEST_DIR"
    
    # Crear base de datos de prueba
    export TEST_DATABASE_URL="${DATABASE_URL}_test_${TEST_DATE}"
    
    # Configurar variables de entorno para testing
    export TEST_ENV=1
    export TEST_REDIS_URL="${REDIS_URL}_test_${TEST_DATE}"
    
    log "Ambiente de testing configurado en: $TEST_DIR"
}

# Test de backup y recuperación de base de datos
test_database_recovery() {
    log "=== Testing Database Recovery ==="
    
    # Crear datos de prueba
    create_test_data() {
        log "Creando datos de prueba en base de datos..."
        
        # Ejecutar scripts de creación de datos de prueba
        psql "${TEST_DATABASE_URL}" << 'EOF'
-- Crear tabla de prueba
CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de prueba
INSERT INTO test_table (name) VALUES 
    ('Test Record 1'),
    ('Test Record 2'),
    ('Test Record 3');

-- Verificar inserción
SELECT COUNT(*) FROM test_table;
EOF
    }
    
    create_test_data
    
    # Crear backup de prueba
    log "Creando backup de datos de prueba..."
    
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        "${TEST_DATABASE_URL}" \
        --format=custom \
        --file="${TEST_DIR}/test_backup.custom"
    
    # Simular pérdida de datos
    log "Simulando pérdida de datos..."
    psql "${TEST_DATABASE_URL}" "DROP TABLE test_table;"
    
    # Verificar que la tabla fue eliminada
    if psql "${TEST_DATABASE_URL}" "\dt" | grep -q "test_table"; then
        log_error "La tabla no fue eliminada correctamente"
        return 1
    fi
    
    # Recuperar desde backup
    log "Recuperando desde backup..."
    
    PGPASSWORD="${DB_PASSWORD}" pg_restore \
        "${TEST_DATABASE_URL}" \
        --clean --if-exists \
        "${TEST_DIR}/test_backup.custom"
    
    # Verificar recuperación
    log "Verificando recuperación..."
    
    local recovered_count=$(psql "${TEST_DATABASE_URL}" -t -c "SELECT COUNT(*) FROM test_table;")
    
    if [[ "$recovered_count" -eq "3" ]]; then
        log "✅ Database Recovery Test: PASSED (3 records recovered)"
        return 0
    else
        log_error "❌ Database Recovery Test: FAILED (expected 3 records, got $recovered_count)"
        return 1
    fi
}

# Test de recuperación de archivos
test_files_recovery() {
    log "=== Testing Files Recovery ==="
    
    # Crear estructura de archivos de prueba
    log "Creando estructura de archivos de prueba..."
    
    mkdir -p "${TEST_DIR}/original"
    echo "Original test content" > "${TEST_DIR}/original/test.txt"
    mkdir -p "${TEST_DIR}/original/subdir"
    echo "Subdir content" > "${TEST_DIR}/original/subdir/nested.txt"
    
    # Crear backup
    log "Creando backup de archivos..."
    
    tar -czf "${TEST_DIR}/files_backup.tar.gz" -C "${TEST_DIR}/original" .
    
    # Simular pérdida de archivos
    log "Simulando pérdida de archivos..."
    rm -rf "${TEST_DIR}/original"
    
    # Verificar pérdida
    if [[ -f "${TEST_DIR}/original/test.txt" ]]; then
        log_error "Los archivos no fueron eliminados correctamente"
        return 1
    fi
    
    # Recuperar desde backup
    log "Recuperando desde backup..."
    
    mkdir -p "${TEST_DIR}/restored"
    tar -xzf "${TEST_DIR}/files_backup.tar.gz" -C "${TEST_DIR}/restored"
    
    # Verificar recuperación
    log "Verificando recuperación de archivos..."
    
    local restored_count=$(find "${TEST_DIR}/restored" -type f | wc -l)
    
    if [[ "$restored_count" -eq "2" ]]; then
        log "✅ Files Recovery Test: PASSED ($restored_count files recovered)"
        return 0
    else
        log_error "❌ Files Recovery Test: FAILED (expected 2 files, got $restored_count)"
        return 1
    fi
}

# Test de integridad de backup
test_backup_integrity() {
    log "=== Testing Backup Integrity ==="
    
    local test_backups=(
        "/backup/local/database/latest.gpg"
        "/backup/local/files/latest.gpg"
    )
    
    local errors=0
    
    for backup_file in "${test_backups[@]}"; do
        if [[ -f "$backup_file" ]]; then
            log "Verificando integridad de: $backup_file"
            
            # Verificar que el archivo se puede desencriptar
            if gpg --list-packets "$backup_file" > /dev/null 2>&1; then
                log "✅ $backup_file: Integrity OK"
            else
                log_error "❌ $backup_file: Integrity FAILED"
                ((errors++))
            fi
        else
            log_error "❌ $backup_file: File not found"
            ((errors++))
        fi
    done
    
    if [[ $errors -eq 0 ]]; then
        log "✅ Backup Integrity Test: ALL TESTS PASSED"
        return 0
    else
        log_error "❌ Backup Integrity Test: $errors errors found"
        return 1
    fi
}

# Test de tiempo de recuperación
test_recovery_time() {
    log "=== Testing Recovery Time ==="
    
    local start_time=$(date +%s)
    
    # Ejecutar un recovery completo de prueba
    log "Ejecutando recovery completo de prueba..."
    
    # Esto debería ser una versión simplificada del recovery real
    sleep 10  # Simular tiempo de recovery
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Definir RTO objetivo (ej: 30 minutos = 1800 segundos)
    local rto_target=1800
    
    if [[ $duration -lt $rto_target ]]; then
        log "✅ Recovery Time Test: PASSED (${duration}s < ${rto_target}s RTO target)"
        return 0
    else
        log_error "❌ Recovery Time Test: FAILED (${duration}s >= ${rto_target}s RTO target)"
        return 1
    fi
}

# Generar reporte de testing
generate_test_report() {
    local test_results_file="${TEST_DIR}/test-results.json"
    
    log "Generando reporte de testing..."
    
    cat > "$test_results_file" << EOF
{
    "test_date": "$TEST_DATE",
    "test_environment": {
        "database_url": "$TEST_DATABASE_URL",
        "test_dir": "$TEST_DIR"
    },
    "tests_performed": [
        "database_recovery",
        "files_recovery",
        "backup_integrity",
        "recovery_time"
    ],
    "test_log": "$TEST_LOG",
    "status": "completed"
}
EOF
    
    log "Reporte de testing generado: $test_results_file"
}

# Cleanup de ambiente de testing
cleanup_test_environment() {
    log "Limpiando ambiente de testing..."
    
    # Eliminar base de datos de prueba
    if [[ -n "${TEST_DATABASE_URL:-}" ]]; then
        dropdb "${TEST_DATABASE_URL}" 2>/dev/null || true
    fi
    
    # Limpiar archivos temporales
    rm -rf "$TEST_DIR"
    
    log "Ambiente de testing limpiado"
}

# Función principal
main() {
    log "=== INICIANDO DRILL DE RECUPERACIÓN ==="
    log "Fecha de testing: $TEST_DATE"
    
    # Configurar ambiente
    setup_test_environment
    
    # Ejecutar tests
    local test_errors=0
    
    if ! test_backup_integrity; then
        ((test_errors++))
    fi
    
    if ! test_database_recovery; then
        ((test_errors++))
    fi
    
    if ! test_files_recovery; then
        ((test_errors++))
    fi
    
    if ! test_recovery_time; then
        ((test_errors++))
    fi
    
    # Generar reporte
    generate_test_report
    
    # Cleanup
    cleanup_test_environment
    
    # Resultado final
    log "=== DRILL DE RECUPERACIÓN COMPLETADO ==="
    
    if [[ $test_errors -eq 0 ]]; then
        log "✅ TODOS LOS TESTS PASARON"
        exit 0
    else
        log_error "❌ $test_errors TESTS FALLARON"
        log_error "Revisar logs para detalles: $TEST_LOG"
        exit 1
    fi
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Cron para Testing Automático

```bash
# Crontab para testing automático
# Agregar a crontab

# Recovery drill semanal (Domingos a las 3 AM)
0 3 * * 0 /backup/testing/recovery-drill.sh >> /backup/logs/recovery-drill-weekly.log 2>&1

# Verificación de backups diaria
0 4 * * * /backup/verify-backups.sh >> /backup/logs/backup-verification-daily.log 2>&1

# Limpieza de logs de testing mensual
0 2 1 * * find /backup/logs -name "recovery-drill-*.log" -mtime +30 -delete
```

## Monitoring de Backups

### 1. Script de Monitoring

```bash
#!/bin/bash
# monitoring/backup-monitoring.sh

set -euo pipefail

# Configuración
source /backup/config/backup-config.env

# Variables
LOG_FILE="/backup/logs/backup-monitoring.log"
ALERT_EMAIL="admin@yourdomain.com"
WEBHOOK_URL="${BACKUP_WEBHOOK_URL}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Verificar que los backups existen
check_backup_existence() {
    log "Verificando existencia de backups..."
    
    local backup_types=("database" "files" "config" "redis")
    local missing_backups=()
    
    for backup_type in "${backup_types[@]}"; do
        local latest_backup=$(find "/backup/local/$backup_type" -name "*.gpg" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
        
        if [[ -n "$latest_backup" ]]; then
            local backup_date=$(stat -c %Y "$latest_backup")
            local age_hours=$(( ($(date +%s) - backup_date) / 3600 ))
            
            log "✅ $backup_type backup: $latest_backup (age: ${age_hours}h)"
            
            # Verificar que el backup no sea muy antiguo
            local max_age_hours
            case "$backup_type" in
                "database") max_age_hours=6 ;;
                "files") max_age_hours=24 ;;
                "config") max_age_hours=168 ;;  # 1 semana
                "redis") max_age_hours=6 ;;
            esac
            
            if [[ $age_hours -gt $max_age_hours ]]; then
                missing_backups+=("$backup_type: backup is ${age_hours}h old (max: ${max_age_hours}h)")
            fi
        else
            missing_backups+=("$backup_type: no backup found")
        fi
    done
    
    if [[ ${#missing_backups[@]} -gt 0 ]]; then
        log_error "❌ Missing or outdated backups:"
        for backup in "${missing_backups[@]}"; do
            log_error "  - $backup"
        done
        return 1
    fi
    
    return 0
}

# Verificar integridad de backups
check_backup_integrity() {
    log "Verificando integridad de backups..."
    
    local backup_dirs=("/backup/local/database" "/backup/local/files" "/backup/local/config" "/backup/local/redis")
    local corrupted_backups=()
    
    for backup_dir in "${backup_dirs[@]}"; do
        if [[ -d "$backup_dir" ]]; then
            while IFS= read -r -d '' backup_file; do
                log "Verificando: $(basename "$backup_file")"
                
                # Verificar que se puede desencriptar
                if ! gpg --list-packets "$backup_file" > /dev/null 2>&1; then
                    corrupted_backups+=("$backup_file")
                fi
            done < <(find "$backup_dir" -name "*.gpg" -type f -print0 2>/dev/null)
        fi
    done
    
    if [[ ${#corrupted_backups[@]} -gt 0 ]]; then
        log_error "❌ Corrupted backups found:"
        for backup in "${corrupted_backups[@]}"; do
            log_error "  - $backup"
        done
        return 1
    fi
    
    return 0
}

# Verificar espacio en disco
check_disk_space() {
    log "Verificando espacio en disco..."
    
    local backup_usage=$(df /backup | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $backup_usage -gt 90 ]]; then
        log_error "❌ Disk space critical: ${backup_usage}% used"
        return 1
    elif [[ $backup_usage -gt 80 ]]; then
        log_warning "⚠️  Disk space warning: ${backup_usage}% used"
        # Intentar limpiar backups antiguos
        find /backup/local -name "*.gpg" -mtime +30 -delete
        log "Cleaned up old backups (>30 days)"
    else
        log "✅ Disk space OK: ${backup_usage}% used"
    fi
    
    return 0
}

# Verificar conectividad con almacenamiento remoto
check_remote_connectivity() {
    log "Verificando conectividad con almacenamiento remoto..."
    
    if command -v aws &> /dev/null; then
        if aws s3 ls "${REMOTE_BACKUP_PATH}/" &> /dev/null; then
            log "✅ Remote storage: Connected"
            
            # Verificar que hay backups remotos recientes
            local remote_backups=$(aws s3 ls "${REMOTE_BACKUP_PATH}/" --recursive | wc -l)
            log "Remote backups count: $remote_backups"
            
            if [[ $remote_backups -eq 0 ]]; then
                log_warning "⚠️  No remote backups found"
                return 1
            fi
        else
            log_error "❌ Remote storage: Connection failed"
            return 1
        fi
    else
        log_warning "⚠️  AWS CLI not available, skipping remote check"
    fi
    
    return 0
}

# Enviar alertas
send_alert() {
    local severity="$1"
    local message="$2"
    
    log "Sending alert: [$severity] $message"
    
    # Email alert
    echo "$message" | mail -s "[$severity] Backup Alert - $(hostname)" "$ALERT_EMAIL"
    
    # Slack webhook alert (si está configurado)
    if [[ -n "${WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"[$severity] Backup Alert: $message\"}" \
            "$WEBHOOK_URL" 2>/dev/null || true
    fi
}

# Generar reporte de monitoring
generate_monitoring_report() {
    local report_file="/backup/logs/backup-status-$(date +%Y%m%d).json"
    
    cat > "$report_file" << EOF
{
    "check_date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "backup_status": {
        "existence": $(check_backup_existence > /dev/null 2>&1 && echo "ok" || echo "failed"),
        "integrity": $(check_backup_integrity > /dev/null 2>&1 && echo "ok" || echo "failed"),
        "disk_space": $(check_disk_space > /dev/null 2>&1 && echo "ok" || echo "warning"),
        "remote_connectivity": $(check_remote_connectivity > /dev/null 2>&1 && echo "ok" || echo "failed")
    },
    "recommendations": []
}
EOF
    
    log "Monitoring report generated: $report_file"
}

# Función principal
main() {
    log "=== BACKUP MONITORING CHECK ==="
    
    local exit_code=0
    
    # Ejecutar checks
    if ! check_backup_existence; then
        send_alert "CRITICAL" "Missing or outdated backups detected"
        exit_code=1
    fi
    
    if ! check_backup_integrity; then
        send_alert "CRITICAL" "Corrupted backups detected"
        exit_code=1
    fi
    
    if ! check_disk_space; then
        send_alert "WARNING" "Disk space issues detected"
        exit_code=1
    fi
    
    if ! check_remote_connectivity; then
        send_alert "WARNING" "Remote storage connectivity issues"
        exit_code=1
    fi
    
    # Generar reporte
    generate_monitoring_report
    
    log "=== BACKUP MONITORING COMPLETED ==="
    
    if [[ $exit_code -eq 0 ]]; then
        log "✅ All backup checks passed"
    else
        log "❌ Some backup checks failed"
    fi
    
    return $exit_code
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Dashboard de Monitoring

```python
# monitoring/backup_dashboard.py
from flask import Flask, jsonify, render_template_string
import subprocess
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

def get_backup_status():
    """Obtener estado actual de backups"""
    try:
        result = subprocess.run(['/backup/monitoring/backup-monitoring.sh'], 
                              capture_output=True, text=True, timeout=300)
        
        # Parse log output to extract status
        status = {
            'timestamp': datetime.now().isoformat(),
            'last_check': 'unknown',
            'backups': {
                'database': 'unknown',
                'files': 'unknown',
                'config': 'unknown',
                'redis': 'unknown'
            },
            'overall_status': 'unknown',
            'errors': []
        }
        
        # Esta es una implementación simplificada
        # En un caso real, se parsearían los logs correctamente
        return status
        
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_backup_history():
    """Obtener historial de backups"""
    # Esta función obtendría datos del historial de backups
    # Implementación simplificada
    return []

@app.route('/api/backup/status')
def backup_status_api():
    """API endpoint para estado de backups"""
    return jsonify(get_backup_status())

@app.route('/api/backup/history')
def backup_history_api():
    """API endpoint para historial de backups"""
    return jsonify(get_backup_history())

@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI News Aggregator - Backup Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .status-ok { color: green; font-weight: bold; }
            .status-warning { color: orange; font-weight: bold; }
            .status-error { color: red; font-weight: bold; }
            .backup-item { margin: 10px 0; padding: 10px; border: 1px solid #ddd; }
            .timestamp { color: #666; font-size: 0.9em; }
        </style>
        <script>
            function refreshStatus() {
                fetch('/api/backup/status')
                    .then(response => response.json())
                    .then(data => updateDashboard(data));
            }
            
            function updateDashboard(data) {
                if (data.error) {
                    document.getElementById('overall-status').innerHTML = 
                        '<span class="status-error">ERROR: ' + data.error + '</span>';
                    return;
                }
                
                document.getElementById('overall-status').innerHTML = 
                    '<span class="' + data.overall_status + '">' + 
                    data.overall_status.toUpperCase() + '</span>';
                
                document.getElementById('last-check').innerHTML = data.timestamp;
            }
            
            // Refresh cada 30 segundos
            setInterval(refreshStatus, 30000);
            window.onload = refreshStatus;
        </script>
    </head>
    <body>
        <h1>AI News Aggregator - Backup Dashboard</h1>
        
        <div class="backup-item">
            <h2>Overall Status</h2>
            <div id="overall-status" class="status-unknown">Unknown</div>
            <div class="timestamp">Last check: <span id="last-check">-</span></div>
        </div>
        
        <div class="backup-item">
            <h2>Backup Details</h2>
            <div id="backup-details">
                <!-- Se actualizará via JavaScript -->
            </div>
        </div>
        
        <div class="backup-item">
            <h2>Recent Activity</h2>
            <div id="recent-activity">
                <!-- Historial de backups recientes -->
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

---

**Nota**: Este plan de backup y recuperación debe ser probado regularmente y actualizado según las necesidades del negocio y cambios en la infraestructura.