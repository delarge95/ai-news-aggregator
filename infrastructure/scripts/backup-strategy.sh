#!/bin/bash
# AI News Aggregator - Automated Backup Strategy Script
# Version: 1.0.0
# Description: Comprehensive backup solution for databases, files, and configurations

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_FILE="/tmp/ai-news-backup-$(date +%Y%m%d-%H%M%S).log"
BACKUP_DIR="${BACKUP_DIR:-/opt/backups}"
CONFIG_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[BACKUP]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}========================================${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}$1${NC}" | tee -a "$LOG_FILE"
    echo -e "${PURPLE}========================================${NC}\n" | tee -a "$LOG_FILE"
}

# Default configuration
: "${BACKUP_RETENTION_DAYS:=30}"
: "${BACKUP_S3_BUCKET:=ai-news-aggregator-backups}"
: "${BACKUP_ENCRYPTION_KEY:="}"
: "${COMPRESSION_LEVEL:=6}"
: "${PARALLEL_JOBS:=2}"

# Load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log_info "Loading configuration from $CONFIG_FILE"
        # shellcheck disable=SC1091
        source "$CONFIG_FILE"
    fi
    
    # Override with environment variables
    : "${DO_TOKEN:?"DigitalOcean token is required"}"
    : "${DATABASE_HOST:?"Database host is required"}"
    : "${DATABASE_NAME:?"Database name is required"}"
    : "${DATABASE_USER:?"Database user is required"}"
    : "${DATABASE_PASSWORD:?"Database password is required"}"
    
    export DO_TOKEN DATABASE_HOST DATABASE_NAME DATABASE_USER DATABASE_PASSWORD
}

# Create backup directory structure
setup_backup_dirs() {
    log_header "Setting Up Backup Directories"
    
    local timestamp
    timestamp=$(date +%Y%m%d-%H%M%S)
    
    BACKUP_ROOT="$BACKUP_DIR/ai-news-aggregator-$timestamp"
    BACKUP_CONFIG="$BACKUP_ROOT/config"
    BACKUP_DATABASE="$BACKUP_ROOT/database"
    BACKUP_FILES="$BACKUP_ROOT/files"
    BACKUP_DOCKER="$BACKUP_ROOT/docker"
    BACKUP_CERTIFICATES="$BACKUP_ROOT/certificates"
    
    # Create directories
    mkdir -p "$BACKUP_ROOT" \
            "$BACKUP_CONFIG" \
            "$BACKUP_DATABASE" \
            "$BACKUP_FILES" \
            "$BACKUP_DOCKER" \
            "$BACKUP_CERTIFICATES"
    
    log_success "Backup directories created: $BACKUP_ROOT"
}

# Backup Terraform state
backup_terraform() {
    log_header "Backing Up Terraform Configuration"
    
    cd "$PROJECT_ROOT/infrastructure/terraform"
    
    # Backup Terraform state
    if terraform state list >/dev/null 2>&1; then
        log_info "Backing up Terraform state..."
        terraform state pull > "$BACKUP_CONFIG/terraform-state.json"
        log_success "Terraform state backed up"
    else
        log_warning "No Terraform state found, skipping..."
    fi
    
    # Backup configuration files
    log_info "Backing up Terraform configuration..."
    cp -r . "$BACKUP_CONFIG/terraform/"
    
    # Backup important files
    local files_to_backup=(
        "terraform.tfvars"
        "main.tf"
        "variables.tf"
        "outputs.tf"
        "droplets.tf"
        "dns.tf"
        "monitoring.tf"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [[ -f "$file" ]]; then
            cp "$file" "$BACKUP_CONFIG/"
            log_info "Backed up: $file"
        fi
    done
    
    log_success "Terraform configuration backed up"
}

# Backup database
backup_database() {
    log_header "Backing Up Database"
    
    local db_backup_file="$BACKUP_DATABASE/ai_news_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log_info "Starting database backup..."
    log_info "Database: $DATABASE_NAME@$DATABASE_HOST"
    
    # Create database dump with comprehensive options
    PGPASSWORD="$DATABASE_PASSWORD" pg_dump \
        -h "$DATABASE_HOST" \
        -p "${DATABASE_PORT:-5432}" \
        -U "$DATABASE_USER" \
        -d "$DATABASE_NAME" \
        --verbose \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --format=custom \
        --compress=9 \
        --file="$db_backup_file"
    
    log_success "Database backup completed: $db_backup_file"
    
    # Create schema-only backup
    local schema_backup_file="$BACKUP_DATABASE/ai_news_schema_$(date +%Y%m%d_%H%M%S).sql"
    PGPASSWORD="$DATABASE_PASSWORD" pg_dump \
        -h "$DATABASE_HOST" \
        -p "${DATABASE_PORT:-5432}" \
        -U "$DATABASE_USER" \
        -d "$DATABASE_NAME" \
        --schema-only \
        --no-owner \
        --no-privileges \
        --file="$schema_backup_file"
    
    log_success "Schema backup completed: $schema_backup_file"
    
    # Verify backup
    if [[ -f "$db_backup_file" ]] && [[ -s "$db_backup_file" ]]; then
        local backup_size
        backup_size=$(du -h "$db_backup_file" | cut -f1)
        log_info "Database backup size: $backup_size"
    else
        log_error "Database backup failed or is empty"
        return 1
    fi
}

# Backup application files
backup_application_files() {
    log_header "Backing Up Application Files"
    
    # Backup source code
    log_info "Backing up application source code..."
    local app_backup_file="$BACKUP_FILES/application_$(date +%Y%m%d_%H%M%S).tar.gz"
    
    tar -czf "$app_backup_file" \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='dist' \
        --exclude='build' \
        -C "$PROJECT_ROOT" \
        backend/ frontend/ database/ docs/
    
    log_success "Application files backed up: $app_backup_file"
    
    # Backup Docker configurations
    log_info "Backing up Docker configurations..."
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        cp "$PROJECT_ROOT/docker-compose.yml" "$BACKUP_DOCKER/"
        log_info "Docker Compose configuration backed up"
    fi
    
    # Backup Dockerfile(s)
    find "$PROJECT_ROOT" -name "Dockerfile*" -type f | while read -r dockerfile; do
        local backup_path="$BACKUP_DOCKER/$(basename "$dockerfile")"
        cp "$dockerfile" "$backup_path"
        log_info "Backed up Docker file: $dockerfile"
    done
    
    # Backup environment files (excluding sensitive data)
    log_info "Backing up configuration templates..."
    find "$PROJECT_ROOT" -name "*.env.template" -o -name "*.conf.template" -type f | while read -r conf_file; do
        local backup_path="$BACKUP_CONFIG/$(basename "$conf_file")"
        cp "$conf_file" "$backup_path"
        log_info "Backed up config template: $conf_file"
    done
}

# Backup SSL certificates
backup_ssl_certificates() {
    log_header "Backing Up SSL Certificates"
    
    local cert_backup_dir="$BACKUP_CERTIFICATES/letsencrypt"
    mkdir -p "$cert_backup_dir"
    
    # Backup Let's Encrypt certificates
    if [[ -d "/etc/letsencrypt/live" ]]; then
        log_info "Backing up Let's Encrypt certificates..."
        
        # Find all certificate domains
        while IFS= read -r -d '' cert_dir; do
            local domain
            domain=$(basename "$(dirname "$cert_dir")")
            local backup_domain_dir="$cert_backup_dir/$domain"
            mkdir -p "$backup_domain_dir"
            
            # Copy certificate files
            cp -r "$cert_dir"/* "$backup_domain_dir/" 2>/dev/null || true
            log_info "Backed up certificate for domain: $domain"
        done < <(find /etc/letsencrypt/live -mindepth 1 -maxdepth 1 -type d -print0)
        
        log_success "Let's Encrypt certificates backed up"
    else
        log_warning "No Let's Encrypt certificates found"
    fi
    
    # Backup Nginx SSL configuration
    if [[ -d "/etc/nginx/ssl" ]]; then
        log_info "Backing up Nginx SSL configuration..."
        cp -r "/etc/nginx/ssl" "$BACKUP_CERTIFICATES/nginx/" 2>/dev/null || true
    fi
}

# Backup monitoring configuration
backup_monitoring() {
    log_header "Backing Up Monitoring Configuration"
    
    local monitoring_backup_dir="$BACKUP_ROOT/monitoring"
    mkdir -p "$monitoring_backup_dir"
    
    # Backup Grafana configuration
    if [[ -d "/etc/grafana" ]]; then
        log_info "Backing up Grafana configuration..."
        cp -r "/etc/grafana" "$monitoring_backup_dir/"
    fi
    
    # Backup Prometheus configuration
    if [[ -f "/etc/prometheus/prometheus.yml" ]]; then
        log_info "Backing up Prometheus configuration..."
        cp "/etc/prometheus/prometheus.yml" "$monitoring_backup_dir/"
    fi
    
    # Backup Docker monitoring configurations
    local docker_monitor_config="$PROJECT_ROOT/infrastructure/monitoring"
    if [[ -d "$docker_monitor_config" ]]; then
        log_info "Backing up Docker monitoring configurations..."
        cp -r "$docker_monitor_config" "$monitoring_backup_dir/docker/"
    fi
}

# Backup Ansible configuration
backup_ansible() {
    log_header "Backing Up Ansible Configuration"
    
    local ansible_backup_dir="$BACKUP_ROOT/ansible"
    mkdir -p "$ansible_backup_dir"
    
    local ansible_dir="$PROJECT_ROOT/infrastructure/ansible"
    if [[ -d "$ansible_dir" ]]; then
        log_info "Backing up Ansible configuration..."
        cp -r "$ansible_dir" "$ansible_backup_dir/"
        
        # Remove sensitive files
        find "$ansible_backup_dir" -name "*.key" -o -name ".vault-pass*" -o -name "secrets.yml" -delete
        log_info "Sensitive files removed from backup"
    fi
}

# Compress and encrypt backup
compress_and_encrypt() {
    log_header "Compressing and Encrypting Backup"
    
    cd "$BACKUP_DIR"
    
    local backup_tar="ai-news-backup-$(date +%Y%m%d_%H%M%S).tar.gz"
    local final_backup="ai-news-backup-$(date +%Y%m%d_%H%M%S).tar.gz.enc"
    
    log_info "Creating compressed archive: $backup_tar"
    
    # Create tar archive with compression
    tar -czf "$backup_tar" \
        --exclude='*.log' \
        --exclude='*.tmp' \
        --exclude='.git' \
        -C "$(dirname "$BACKUP_ROOT")" \
        "$(basename "$BACKUP_ROOT")"
    
    # Encrypt if encryption key is provided
    if [[ -n "$BACKUP_ENCRYPTION_KEY" ]]; then
        log_info "Encrypting backup with GPG..."
        echo "$BACKUP_ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 --symmetric --cipher-algo AES256 "$backup_tar"
        rm "$backup_tar"
        final_backup="$backup_tar.enc"
        log_success "Backup encrypted: $final_backup"
    else
        log_warning "No encryption key provided, backup will not be encrypted"
    fi
    
    local backup_size
    backup_size=$(du -h "$final_backup" | cut -f1)
    log_info "Final backup size: $backup_size"
    
    # Clean up temporary directory
    rm -rf "$BACKUP_ROOT"
    
    echo "$final_backup"
}

# Upload to cloud storage
upload_to_cloud() {
    local backup_file="$1"
    
    if [[ "${BACKUP_UPLOAD_TO_S3:-false}" == "true" ]]; then
        log_header "Uploading to Cloud Storage"
        
        # Upload to DigitalOcean Spaces (S3-compatible)
        if command -v aws >/dev/null 2>&1 && [[ -n "${DO_SPACES_ENDPOINT:-}" ]]; then
            log_info "Uploading to DigitalOcean Spaces..."
            
            aws s3 cp "$backup_file" \
                "s3://$BACKUP_S3_BUCKET/$(date +%Y/%m/%d)/$(basename "$backup_file")" \
                --endpoint-url="$DO_SPACES_ENDPOINT" \
                --storage-class STANDARD_IA
            log_success "Backup uploaded to DigitalOcean Spaces"
        elif command -v s3cmd >/dev/null 2>&1; then
            log_info "Uploading with s3cmd..."
            
            s3cmd put "$backup_file" "s3://$BACKUP_S3_BUCKET/$(date +%Y/%m/%d)/"
            log_success "Backup uploaded to S3"
        else
            log_warning "No S3 client found, skipping cloud upload"
        fi
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_header "Cleaning Up Old Backups"
    
    local retention_days="${BACKUP_RETENTION_DAYS:-30}"
    log_info "Removing backups older than $retention_days days..."
    
    local cleaned_count
    cleaned_count=$(find "$BACKUP_DIR" -name "ai-news-backup-*.tar.gz*" -type f -mtime +$retention_days -print | wc -l)
    
    if [[ $cleaned_count -gt 0 ]]; then
        find "$BACKUP_DIR" -name "ai-news-backup-*.tar.gz*" -type f -mtime +$retention_days -delete
        log_success "Cleaned up $cleaned_count old backup files"
    else
        log_info "No old backups found to clean up"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log_header "Verifying Backup Integrity"
    
    if [[ "$backup_file" == *.enc ]]; then
        log_info "Decrypting backup for verification..."
        if [[ -n "$BACKUP_ENCRYPTION_KEY" ]]; then
            local temp_file
            temp_file=$(mktemp)
            echo "$BACKUP_ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 --decrypt --output "$temp_file" "$backup_file"
            
            # Test tar extraction
            tar -tzf "$temp_file" >/dev/null
            local tar_status=$?
            rm "$temp_file"
            
            if [[ $tar_status -eq 0 ]]; then
                log_success "Backup integrity verified (encrypted)"
            else
                log_error "Backup integrity check failed (encrypted)"
                return 1
            fi
        else
            log_warning "Cannot verify encrypted backup without decryption key"
        fi
    else
        # Test tar extraction
        tar -tzf "$backup_file" >/dev/null
        local tar_status=$?
        
        if [[ $tar_status -eq 0 ]]; then
            log_success "Backup integrity verified"
        else
            log_error "Backup integrity check failed"
            return 1
        fi
    fi
}

# Generate backup report
generate_report() {
    local backup_file="$1"
    local backup_duration=$((SECONDS - start_time))
    
    log_header "Backup Report"
    
    log_info "Backup completed at: $(date)"
    log_info "Backup file: $backup_file"
    log_info "Backup duration: ${backup_duration}s"
    
    local backup_size
    backup_size=$(du -h "$backup_file" | cut -f1)
    log_info "Backup size: $backup_size"
    
    log_info "Components backed up:"
    echo "  - Terraform configuration"
    echo "  - Database (full and schema)"
    echo "  - Application files"
    echo "  - SSL certificates"
    echo "  - Monitoring configuration"
    echo "  - Ansible configuration"
    
    # Save report
    local report_file="$BACKUP_DIR/backup-report-$(date +%Y%m%d_%H%M%S).txt"
    cat > "$report_file" << EOF
AI News Aggregator Backup Report
================================
Date: $(date)
Backup File: $backup_file
Size: $backup_size
Duration: ${backup_duration}s
Environment: ${ENVIRONMENT:-production}
Components: Terraform, Database, Files, SSL, Monitoring, Ansible
Status: SUCCESS
EOF
    
    log_info "Report saved to: $report_file"
}

# Main execution
main() {
    local start_time=$SECONDS
    
    log_header "AI News Aggregator - Automated Backup Process"
    
    # Parse command line arguments
    local skip_components=()
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-terraform)
                skip_components+=("terraform")
                shift
                ;;
            --skip-database)
                skip_components+=("database")
                shift
                ;;
            --skip-files)
                skip_components+=("files")
                shift
                ;;
            --skip-ssl)
                skip_components+=("ssl")
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-terraform    Skip Terraform configuration backup"
                echo "  --skip-database     Skip database backup"
                echo "  --skip-files        Skip application files backup"
                echo "  --skip-ssl          Skip SSL certificates backup"
                echo "  --help              Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Load configuration
    load_config || exit 1
    
    # Setup backup directories
    setup_backup_dirs
    
    # Execute backup components
    if [[ ! " ${skip_components[*]} " =~ " terraform " ]]; then
        backup_terraform
    fi
    
    if [[ ! " ${skip_components[*]} " =~ " database " ]]; then
        backup_database
    fi
    
    if [[ ! " ${skip_components[*]} " =~ " files " ]]; then
        backup_application_files
    fi
    
    backup_ssl_certificates
    backup_monitoring
    backup_ansible
    
    # Compress and encrypt
    local backup_file
    backup_file=$(compress_and_encrypt)
    
    # Verify backup
    verify_backup "$backup_file"
    
    # Upload to cloud
    upload_to_cloud "$backup_file"
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Generate report
    generate_report "$backup_file"
    
    log_success "Backup process completed successfully!"
    log_info "Backup file: $backup_file"
    log_info "Logs saved to: $LOG_FILE"
}

# Execute main function
main "$@"