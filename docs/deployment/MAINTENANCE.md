# Guía de Mantenimiento Operacional

## Tabla de Contenidos
- [Tareas de Mantenimiento Rutinario](#tareas-de-mantenimiento-rutinario)
- [Actualizaciones de Sistema](#actualizaciones-de-sistema)
- [Mantenimiento de Base de Datos](#mantenimiento-de-base-de-datos)
- [Mantenimiento de Redis](#mantenimiento-de-redis)
- [Mantenimiento de Docker](#mantenimiento-de-docker)
- [Limpieza de Logs](#limpieza-de-logs)
- [Optimización de Performance](#optimización-de-performance)
- [Seguridad y Parches](#seguridad-y-parches)
- [Monitoring y Alertas](#monitoring-y-alertas)
- [Documentación y Procedimientos](#documentación-y-procedimientos)

## Tareas de Mantenimiento Rutinario

### 1. Checklist Diario

```bash
#!/bin/bash
# maintenance/daily-checklist.sh

set -euo pipefail

LOG_FILE="/var/log/maintenance-daily.log"
DATE=$(date +%Y-%m-%d)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Verificar estado de servicios
check_services() {
    log "=== Verificando estado de servicios ==="
    
    local services=("nginx" "docker" "postgresql" "redis-server")
    local failed_services=()
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet "$service"; then
            log "✅ $service: Running"
        else
            log_error "❌ $service: Not running"
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Servicios fallidos: ${failed_services[*]}"
        return 1
    fi
    
    return 0
}

# Verificar uso de recursos
check_resource_usage() {
    log "=== Verificando uso de recursos ==="
    
    # CPU usage
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
    log "CPU Usage: ${cpu_usage}%"
    
    # Memory usage
    local memory_usage=$(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')
    log "Memory Usage: $memory_usage"
    
    # Disk usage
    local disk_usage=$(df -h / | awk 'NR==2{print $5}')
    log "Disk Usage: $disk_usage"
    
    # Network connections
    local connections=$(ss -tuln | wc -l)
    log "Network Connections: $connections"
    
    # Alert if resources are high
    local cpu_numeric=$(echo "$cpu_usage" | cut -d'.' -f1)
    if [[ $cpu_numeric -gt 80 ]]; then
        log_error "High CPU usage: $cpu_usage"
    fi
    
    local disk_numeric=$(echo "$disk_usage" | sed 's/%//')
    if [[ $disk_numeric -gt 85 ]]; then
        log_error "High disk usage: $disk_usage"
    fi
}

# Verificar aplicaciones
check_applications() {
    log "=== Verificando aplicaciones ==="
    
    # Health check API
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log "✅ API: Health check OK"
    else
        log_error "❌ API: Health check failed"
    fi
    
    # Check database connectivity
    if pg_isready -h localhost > /dev/null 2>&1; then
        log "✅ Database: Connection OK"
    else
        log_error "❌ Database: Connection failed"
    fi
    
    # Check Redis connectivity
    if redis-cli ping | grep -q PONG; then
        log "✅ Redis: Connection OK"
    else
        log_error "❌ Redis: Connection failed"
    fi
    
    # Check Docker containers
    if docker-compose ps | grep -q "Up"; then
        log "✅ Docker containers: Running"
    else
        log_error "❌ Docker containers: Some containers down"
    fi
}

# Verificar logs de errores
check_error_logs() {
    log "=== Verificando logs de errores ==="
    
    # Nginx error logs (last 24 hours)
    local nginx_errors=$(journalctl -u nginx --since "1 day ago" --priority=err | wc -l)
    log "Nginx errors (24h): $nginx_errors"
    
    # Application logs
    if [[ -f "/var/www/ai-news-aggregator/logs/app.log" ]]; then
        local app_errors=$(grep -i "error" /var/www/ai-news-aggregator/logs/app.log | tail -100 | wc -l)
        log "Application errors (recent): $app_errors"
    fi
    
    # System logs
    local system_errors=$(journalctl --since "1 day ago" --priority=err | wc -l)
    log "System errors (24h): $system_errors"
}

# Verificar backup status
check_backup_status() {
    log "=== Verificando status de backups ==="
    
    # Check if backup script exists and is executable
    if [[ -x "/backup/database-backup.sh" ]]; then
        log "✅ Backup script: Available"
    else
        log_error "❌ Backup script: Missing or not executable"
    fi
    
    # Check for recent backups
    local recent_backups=$(find /backup/local -name "*.gpg" -mtime -1 | wc -l)
    log "Recent backups (24h): $recent_backups"
    
    if [[ $recent_backups -eq 0 ]]; then
        log_error "No recent backups found"
    fi
}

# Verificar SSL certificates
check_ssl_certificates() {
    log "=== Verificando certificados SSL ==="
    
    if [[ -f "/etc/letsencrypt/live/$(hostname)/cert.pem" ]]; then
        local expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$(hostname)/cert.pem" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        log "SSL Certificate expires in: $days_until_expiry days"
        
        if [[ $days_until_expiry -lt 30 ]]; then
            log_error "SSL Certificate expires soon: $days_until_expiry days"
        else
            log "✅ SSL Certificate: OK"
        fi
    else
        log_error "❌ SSL Certificate: Not found"
    fi
}

# Limpiar archivos temporales
cleanup_temp_files() {
    log "=== Limpiando archivos temporales ==="
    
    # Clean system temp files
    local temp_cleaned=$(find /tmp -type f -atime +7 -delete 2>/dev/null | wc -l)
    log "Cleaned temp files: $temp_cleaned"
    
    # Clean package cache
    apt-get autoremove -y > /dev/null 2>&1 || true
    apt-get autoclean > /dev/null 2>&1 || true
    log "Package cache cleaned"
    
    # Clean log files older than 7 days
    local logs_cleaned=$(find /var/log -name "*.log" -mtime +7 -delete 2>/dev/null | wc -l)
    log "Cleaned old log files: $logs_cleaned"
}

# Generar reporte diario
generate_daily_report() {
    local report_file="/var/log/maintenance/daily-report-${DATE}.json"
    
    log "=== Generando reporte diario ==="
    
    # Crear directorio si no existe
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
{
    "date": "$DATE",
    "hostname": "$(hostname)",
    "checks": {
        "services": "completed",
        "resources": "completed", 
        "applications": "completed",
        "error_logs": "completed",
        "backup_status": "completed",
        "ssl_certificates": "completed"
    },
    "summary": "Daily maintenance check completed successfully"
}
EOF
    
    log "Reporte diario generado: $report_file"
}

# Función principal
main() {
    log "=== INICIANDO CHECKLIST DIARIO ==="
    log "Fecha: $DATE"
    log "Host: $(hostname)"
    
    # Ejecutar checks
    check_services || log_error "Service check failed"
    check_resource_usage
    check_applications || log_error "Application check failed"
    check_error_logs
    check_backup_status || log_error "Backup check failed"
    check_ssl_certificates || log_error "SSL check failed"
    
    # Limpiar
    cleanup_temp_files
    
    # Generar reporte
    generate_daily_report
    
    log "=== CHECKLIST DIARIO COMPLETADO ==="
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Checklist Semanal

```bash
#!/bin/bash
# maintenance/weekly-checklist.sh

set -euo pipefail

LOG_FILE="/var/log/maintenance-weekly.log"
WEEK_DATE=$(date +%Y-%m-%d)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Actualizar información del sistema
update_system_info() {
    log "=== Actualizando información del sistema ==="
    
    # Update package lists
    apt-get update > /dev/null 2>&1
    log "Package lists updated"
    
    # Check for security updates
    apt list --upgradable 2>/dev/null | grep -i security | wc -l > /tmp/security_updates_count
    local security_updates=$(cat /tmp/security_updates_count)
    
    if [[ $security_updates -gt 0 ]]; then
        log "Security updates available: $security_updates"
    else
        log "No security updates available"
    fi
    
    # Check system updates
    apt list --upgradable 2>/dev/null | grep -v security | wc -l > /tmp_general_updates_count
    local general_updates=$(cat /tmp_general_updates_count)
    
    log "General updates available: $general_updates"
}

# Verificar integridad de archivos
check_file_integrity() {
    log "=== Verificando integridad de archivos ==="
    
    # Check important config files
    local config_files=(
        "/etc/nginx/sites-available/ai-news-aggregator"
        "/etc/nginx/nginx.conf"
        "/var/www/ai-news-aggregator/docker-compose.yml"
        "/etc/ssl/certs/ai-news-aggregator.crt"
    )
    
    local missing_files=()
    
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            log "✅ Found: $file"
        else
            log_error "❌ Missing: $file"
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing config files: ${missing_files[*]}"
    fi
    
    # Check file permissions
    log "Checking file permissions..."
    
    # Important files should not be world-writable
    find /var/www/ai-news-aggregator -type f -perm /o+w | head -10 | while read file; do
        log_warning "World-writable file found: $file"
    done
}

# Optimizar base de datos
optimize_database() {
    log "=== Optimizando base de datos ==="
    
    # Update table statistics
    if command -v psql > /dev/null; then
        PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" << 'EOF'
-- Update statistics
ANALYZE;

-- Check for bloat
SELECT 
    schemaname,
    tablename,
    n_tup_ins + n_tup_upd + n_tup_del as total_changes,
    n_dead_tup,
    round(n_dead_tup::float / greatest(n_live_tup + n_dead_tup, 1) * 100, 2) as dead_tuples_percent
FROM pg_stat_user_tables 
WHERE n_dead_tup > 1000
ORDER BY dead_tuples_percent DESC
LIMIT 10;
EOF
        log "Database optimization completed"
    else
        log_error "PostgreSQL client not available"
    fi
}

# Limpiar logs y archivos grandes
cleanup_logs_and_files() {
    log "=== Limpiando logs y archivos grandes ==="
    
    # Find and log large files (>100MB)
    log "Large files (>100MB):"
    find /var /tmp -type f -size +100M -exec ls -lh {} \; 2>/dev/null | awk '{print $5, $9}' | head -10 | while read size file; do
        log "  $size $file"
    done
    
    # Clean log files older than 14 days
    local logs_cleaned=$(find /var/log -name "*.log" -mtime +14 -delete 2>/dev/null | wc -l)
    log "Cleaned old log files (14+ days): $logs_cleaned"
    
    # Clean application logs older than 7 days
    if [[ -d "/var/www/ai-news-aggregator/logs" ]]; then
        local app_logs_cleaned=$(find /var/www/ai-news-aggregator/logs -name "*.log" -mtime +7 -delete 2>/dev/null | wc -l)
        log "Cleaned old application logs (7+ days): $app_logs_cleaned"
    fi
    
    # Clean Docker logs
    if command -v docker > /dev/null; then
        docker system prune -f > /dev/null 2>&1 || true
        log "Docker system cleaned"
    fi
    
    # Clean old backups (keep last 4 weeks locally)
    if [[ -d "/backup/local" ]]; then
        local backups_cleaned=$(find /backup/local -name "*.gpg" -mtime +28 -delete 2>/dev/null | wc -l)
        log "Cleaned old backups (28+ days): $backups_cleaned"
    fi
}

# Verificar performance
check_performance() {
    log "=== Verificando performance ==="
    
    # Load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}')
    log "Load average:$load_avg"
    
    # Memory usage trend
    local memory_info=$(free -m)
    log "Memory usage:"
    echo "$memory_info" | head -2 | while read line; do
        log "  $line"
    done
    
    # Disk I/O stats
    if command -v iostat > /dev/null; then
        log "Disk I/O (last 5 seconds):"
        iostat -x 5 1 | tail -n +4 | head -5 | while read line; do
            log "  $line"
        done
    fi
    
    # Top processes by CPU
    log "Top 5 processes by CPU:"
    ps aux --sort=-%cpu | head -6 | tail -5 | while read line; do
        log "  $line"
    done
}

# Verificar conectividad externa
check_external_connectivity() {
    log "=== Verificando conectividad externa ==="
    
    # Test internet connectivity
    if ping -c 3 8.8.8.8 > /dev/null 2>&1; then
        log "✅ Internet: Connected"
    else
        log_error "❌ Internet: No connectivity"
    fi
    
    # Test DNS resolution
    if nslookup google.com > /dev/null 2>&1; then
        log "✅ DNS: Working"
    else
        log_error "❌ DNS: Resolution failed"
    fi
    
    # Test API endpoints
    local apis=("api.github.com" "httpbin.org" "jsonplaceholder.typicode.com")
    
    for api in "${apis[@]}"; do
        if curl -f -s --max-time 10 "https://$api" > /dev/null; then
            log "✅ API: $api - Reachable"
        else
            log_error "❌ API: $api - Not reachable"
        fi
    done
}

# Generar reporte semanal
generate_weekly_report() {
    local report_file="/var/log/maintenance/weekly-report-${WEEK_DATE}.json"
    
    log "=== Generando reporte semanal ==="
    
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
{
    "week_date": "$WEEK_DATE",
    "hostname": "$(hostname)",
    "tasks_completed": [
        "update_system_info",
        "check_file_integrity", 
        "optimize_database",
        "cleanup_logs_and_files",
        "check_performance",
        "check_external_connectivity"
    ],
    "system_info": {
        "uptime": "$(uptime -p)",
        "last_boot": "$(who -b | awk '{print $3, $4}')",
        "disk_usage": "$(df -h / | awk 'NR==2{print $5}')",
        "memory_usage": "$(free -h | awk 'NR==2{print $3"/"$2}')",
        "load_average": "$(uptime | awk -F'load average:' '{print $2}')"
    },
    "summary": "Weekly maintenance check completed successfully"
}
EOF
    
    log "Reporte semanal generado: $report_file"
}

# Función principal
main() {
    log "=== INICIANDO CHECKLIST SEMANAL ==="
    log "Fecha: $WEEK_DATE"
    log "Host: $(hostname)"
    
    # Ejecutar tareas semanales
    update_system_info
    check_file_integrity || log_error "File integrity check failed"
    optimize_database || log_error "Database optimization failed"
    cleanup_logs_and_files
    check_performance
    check_external_connectivity || log_error "External connectivity check failed"
    
    # Generar reporte
    generate_weekly_report
    
    log "=== CHECKLIST SEMANAL COMPLETADO ==="
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 3. Checklist Mensual

```bash
#!/bin/bash
# maintenance/monthly-checklist.sh

set -euo pipefail

LOG_FILE="/var/log/maintenance-monthly.log"
MONTH_DATE=$(date +%Y-%m)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Actualizar sistema completo
update_system() {
    log "=== Actualizando sistema completo ==="
    
    # Check if updates are available
    apt list --upgradable 2>/dev/null | grep -v security > /tmp/available_updates
    local update_count=$(wc -l < /tmp/available_updates)
    
    if [[ $update_count -gt 0 ]]; then
        log "Updates available: $update_count"
        
        # Apply updates
        apt-get update
        apt-get upgrade -y
        
        # Check for kernel updates
        if dpkg -l | grep -q "linux-image.*upgrade"; then
            log "Kernel updates require reboot"
            echo "$(date): Kernel updates applied, reboot required" >> /var/log/reboot-required
        fi
        
        log "System updates completed"
    else
        log "No system updates available"
    fi
}

# Verificar SSL/TLS configuration
check_ssl_configuration() {
    log "=== Verificando configuración SSL/TLS ==="
    
    # Test SSL configuration
    if command -v sslscan > /dev/null; then
        sslscan yourdomain.com > /tmp/ssl-scan-result.txt 2>&1
        
        log "SSL Scan results saved to /tmp/ssl-scan-result.txt"
        
        # Check for weak ciphers
        local weak_ciphers=$(grep -c "Weak\|Deprecated" /tmp/ssl-scan-result.txt || echo "0")
        
        if [[ $weak_ciphers -gt 0 ]]; then
            log_error "Weak ciphers detected: $weak_ciphers"
        else
            log "SSL configuration: No weak ciphers detected"
        fi
    else
        log "sslscan not available, skipping detailed SSL check"
    fi
    
    # Check SSL certificate chain
    echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -text > /tmp/ssl-cert-details.txt
    
    if grep -q "CN=yourdomain.com" /tmp/ssl-cert-details.txt; then
        log "✅ SSL Certificate: Valid"
    else
        log_error "❌ SSL Certificate: Issues detected"
    fi
}

# Realizar backup completo del sistema
full_system_backup() {
    log "=== Realizando backup completo del sistema ==="
    
    local backup_name="system-backup-${MONTH_DATE}"
    
    # Create full system backup
    tar -czf "/backup/local/${backup_name}.tar.gz" \
        --exclude=/proc \
        --exclude=/sys \
        --exclude=/dev \
        --exclude=/tmp \
        --exclude=/var/lib/docker \
        /etc /var/www /home/deploy /opt 2>/dev/null || log_error "Some files could not be backed up"
    
    # Encrypt backup
    if [[ -f "/backup/keys/system.key" ]]; then
        gpg --cipher-algo AES256 \
            --symmetric --output "/backup/local/${backup_name}.tar.gz.gpg" \
            --passphrase-file "/backup/keys/system.key" \
            < "/backup/local/${backup_name}.tar.gz"
        
        rm "/backup/local/${backup_name}.tar.gz"
        log "Full system backup completed: ${backup_name}.tar.gz.gpg"
    else
        log_error "Encryption key not found, backup not encrypted"
    fi
}

# Verificar configuración de seguridad
security_audit() {
    log "=== Auditoría de seguridad ==="
    
    # Check for failed login attempts
    local failed_logins=$(grep "Failed password" /var/log/auth.log | wc -l)
    log "Failed login attempts: $failed_logins"
    
    if [[ $failed_logins -gt 100 ]]; then
        log_error "High number of failed login attempts: $failed_logins"
    fi
    
    # Check for sudo usage
    local sudo_usage=$(grep "sudo:" /var/log/auth.log | wc -l)
    log "Sudo usage: $sudo_usage"
    
    # Check file permissions on sensitive files
    log "Checking sensitive file permissions:"
    
    local sensitive_files=(
        "/etc/passwd"
        "/etc/shadow"
        "/etc/sudoers"
        "/root/.ssh"
    )
    
    for file in "${sensitive_files[@]}"; do
        if [[ -f "$file" ]]; then
            local perms=$(stat -c "%a" "$file")
            log "  $file: $perms"
            
            # Check for world-writable
            if [[ "$perms" =~ [2367]$ ]]; then
                log_error "World-writable file: $file ($perms)"
            fi
        fi
    done
    
    # Check for SUID binaries
    local suid_binaries=$(find /usr /bin /sbin -perm /4000 -type f 2>/dev/null | wc -l)
    log "SUID binaries: $suid_binaries"
    
    # Check for running services
    log "Active services:"
    systemctl list-units --type=service --state=running | grep -v "dbus\|systemd" | while read line; do
        log "  $line"
    done
}

# Performance benchmarking
performance_benchmark() {
    log "=== Benchmarking de performance ==="
    
    # CPU benchmark (simple)
    log "Running CPU benchmark..."
    timeout 30s yes > /dev/null &
    local cpu_pid=$!
    sleep 30
    kill $cpu_pid 2>/dev/null || true
    
    # Memory test
    log "Testing memory performance..."
    dd if=/dev/zero of=/tmp/memory_test bs=1M count=1000 2>/dev/null
    local write_speed=$(dd if=/tmp/memory_test of=/dev/null bs=1M count=1000 2>&1 | grep -o '[0-9.]* MB/s' | head -1)
    log "Memory write speed: $write_speed"
    rm -f /tmp/memory_test
    
    # Disk I/O test
    log "Testing disk I/O..."
    local disk_test_file="/tmp/disk_test_$(date +%s)"
    dd if=/dev/zero of="$disk_test_file" bs=1M count=100 2>/dev/null
    local disk_write_speed=$(dd if="$disk_test_file" of=/dev/null bs=1M count=100 2>&1 | grep -o '[0-9.]* MB/s' | head -1)
    log "Disk write speed: $disk_write_speed"
    rm -f "$disk_test_file"
    
    # Database performance test
    if command -v psql > /dev/null; then
        log "Testing database performance..."
        
        PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" << 'EOF'
-- Simple query performance test
\timing on
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM user_preferences;
\timing off
EOF
    fi
}

# Generar reporte mensual
generate_monthly_report() {
    local report_file="/var/log/maintenance/monthly-report-${MONTH_DATE}.json"
    
    log "=== Generando reporte mensual ==="
    
    mkdir -p "$(dirname "$report_file")"
    
    # Collect system information
    local uptime_info=$(uptime)
    local disk_usage=$(df -h / | awk 'NR==2{print $5}')
    local memory_usage=$(free -h | awk 'NR==2{print $3"/"$2}')
    local last_update=$(stat -c %Y /var/cache/apt/pkgcache.bin 2>/dev/null || echo "0")
    local last_update_date=$(date -d "@$last_update" 2>/dev/null || echo "Unknown")
    
    cat > "$report_file" << EOF
{
    "month": "$MONTH_DATE",
    "hostname": "$(hostname)",
    "tasks_completed": [
        "update_system",
        "check_ssl_configuration",
        "full_system_backup",
        "security_audit",
        "performance_benchmark"
    ],
    "system_metrics": {
        "uptime": "$uptime_info",
        "disk_usage": "$disk_usage",
        "memory_usage": "$memory_usage",
        "last_system_update": "$last_update_date"
    },
    "security": {
        "failed_logins": "$(grep "Failed password" /var/log/auth.log | wc -l)",
        "suid_binaries": "$(find /usr /bin /sbin -perm /4000 -type f 2>/dev/null | wc -l)"
    },
    "recommendations": [
        "Review failed login attempts",
        "Consider implementing additional monitoring",
        "Schedule next maintenance window"
    ],
    "summary": "Monthly maintenance check completed successfully"
}
EOF
    
    log "Reporte mensual generado: $report_file"
}

# Función principal
main() {
    log "=== INICIANDO CHECKLIST MENSUAL ==="
    log "Mes: $MONTH_DATE"
    log "Host: $(hostname)"
    
    # Verificar si es necesario reiniciar
    if [[ -f "/var/log/reboot-required" ]]; then
        local last_reboot_required=$(tail -1 /var/log/reboot-required | cut -d: -f1)
        log "⚠️  Reboot required (last noted: $last_reboot_required)"
    fi
    
    # Ejecutar tareas mensuales
    update_system || log_error "System update failed"
    check_ssl_configuration || log_error "SSL check failed"
    full_system_backup || log_error "System backup failed"
    security_audit || log_error "Security audit failed"
    performance_benchmark || log_error "Performance benchmark failed"
    
    # Generar reporte
    generate_monthly_report
    
    log "=== CHECKLIST MENSUAL COMPLETADO ==="
    
    # Recomendaciones finales
    log "=== RECOMENDACIONES ==="
    log "1. Revisar logs de seguridad regularmente"
    log "2. Programar próxima actualización de seguridad"
    log "3. Verificar backups remotos"
    log "4. Considerar actualización de dependencias"
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Actualizaciones de Sistema

### 1. Script de Actualización

```bash
#!/bin/bash
# maintenance/system-update.sh

set -euo pipefail

LOG_FILE="/var/log/system-update.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Verificar prerrequisitos
check_prerequisites() {
    log "=== Verificando prerrequisitos ==="
    
    # Verificar que se ejecuta como root
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script debe ejecutarse como root"
        exit 1
    fi
    
    # Verificar conectividad
    if ! ping -c 3 8.8.8.8 > /dev/null 2>&1; then
        log_error "Sin conectividad a internet"
        exit 1
    fi
    
    # Verificar espacio en disco
    local disk_usage=$(df / | awk 'NR==2{print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 85 ]]; then
        log_error "Espacio en disco insuficiente: ${disk_usage}%"
        exit 1
    fi
    
    # Verificar que no hay procesos importantes ejecutándose
    local critical_processes=("nginx" "postgresql" "redis-server")
    local running_processes=()
    
    for process in "${critical_processes[@]}"; do
        if pgrep "$process" > /dev/null; then
            running_processes+=("$process")
        fi
    done
    
    if [[ ${#running_processes[@]} -gt 0 ]]; then
        log "Procesos críticos en ejecución: ${running_processes[*]}"
        log "Se recomienda programar mantenimiento fuera de horario de alto tráfico"
    fi
    
    log "Prerrequisitos verificados"
}

# Crear snapshot del sistema
create_system_snapshot() {
    log "=== Creando snapshot del sistema ==="
    
    local snapshot_date=$(date +%Y%m%d_%H%M%S)
    local snapshot_dir="/var/backups/system-snapshot-${snapshot_date}"
    
    mkdir -p "$snapshot_dir"
    
    # Backup de configuraciones críticas
    log "Respaldando configuraciones..."
    cp -r /etc/nginx "$snapshot_dir/" 2>/dev/null || true
    cp -r /var/www/ai-news-aggregator "$snapshot_dir/" 2>/dev/null || true
    cp -r /home/deploy "$snapshot_dir/" 2>/dev/null || true
    
    # Backup de base de datos
    if command -v pg_dump > /dev/null; then
        log "Respaldando base de datos..."
        pg_dumpall -h localhost > "$snapshot_dir/database-backup.sql" 2>/dev/null || log_error "Error en backup de base de datos"
    fi
    
    # Comprimir snapshot
    log "Comprimiendo snapshot..."
    tar -czf "${snapshot_dir}.tar.gz" -C "$(dirname "$snapshot_dir)" "$(basename "$snapshot_dir")"
    rm -rf "$snapshot_dir"
    
    log "Snapshot creado: ${snapshot_dir}.tar.gz"
    
    # Limpiar snapshots antiguos (mantener últimos 3)
    find /var/backups -name "system-snapshot-*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -n | head -n -3 | cut -d' ' -f2- | xargs rm -f 2>/dev/null || true
}

# Actualizar repositorios
update_repositories() {
    log "=== Actualizando repositorios ==="
    
    apt-get update
    
    log "Repositorios actualizados"
}

# Verificar actualizaciones disponibles
check_available_updates() {
    log "=== Verificando actualizaciones disponibles ==="
    
    # Actualizaciones de seguridad
    local security_updates=$(apt list --upgradable 2>/dev/null | grep -i security | wc -l)
    
    # Actualizaciones generales
    local general_updates=$(apt list --upgradable 2>/dev/null | grep -v security | wc -l)
    
    log "Actualizaciones de seguridad disponibles: $security_updates"
    log "Actualizaciones generales disponibles: $general_updates"
    
    # Kernel updates
    if apt list --upgradable 2>/dev/null | grep -q "linux-image"; then
        log "⚠️  Actualizaciones de kernel detectadas - se requerirá reinicio"
        echo "$(date): Kernel updates available" >> /var/log/reboot-required
    fi
    
    return 0
}

# Aplicar actualizaciones de seguridad
apply_security_updates() {
    log "=== Aplicando actualizaciones de seguridad ==="
    
    local security_updates=$(apt list --upgradable 2>/dev/null | grep -i security | awk -F/ '{print $1}' | tr '\n' ' ')
    
    if [[ -n "$security_updates" ]]; then
        log "Aplicando actualizaciones de seguridad: $security_updates"
        
        apt-get install -y --only-upgrade $security_updates
        
        log "Actualizaciones de seguridad aplicadas"
    else
        log "No hay actualizaciones de seguridad disponibles"
    fi
}

# Aplicar actualizaciones generales
apply_general_updates() {
    log "=== Aplicando actualizaciones generales ==="
    
    local general_updates=$(apt list --upgradable 2>/dev/null | grep -v security | awk -F/ '{print $1}' | tr '\n' ' ')
    
    if [[ -n "$general_updates" ]]; then
        log "Aplicando actualizaciones generales..."
        
        apt-get install -y --only-upgrade $general_updates
        
        log "Actualizaciones generales aplicadas"
    else
        log "No hay actualizaciones generales disponibles"
    fi
}

# Actualizar certificados SSL
update_ssl_certificates() {
    log "=== Actualizando certificados SSL ==="
    
    # Verificar y renovar certificados Let's Encrypt
    if command -v certbot > /dev/null; then
        log "Verificando certificados SSL..."
        
        certbot renew --dry-run > /tmp/certbot-dry-run.log 2>&1
        
        if grep -q "Congratulations" /tmp/certbot-dry-run.log; then
            log "Certificados SSL válidos"
        else
            log_error "Problemas con certificados SSL - revisar /tmp/certbot-dry-run.log"
        fi
    else
        log "certbot no disponible"
    fi
}

# Reiniciar servicios si es necesario
restart_services_if_needed() {
    log "=== Verificando necesidad de reiniciar servicios ==="
    
    local services_to_restart=()
    
    # Nginx necesita reinicio si hay cambios en SSL
    if systemctl is-active --quiet nginx; then
        services_to_restart+=("nginx")
    fi
    
    # Reiniciar servicios si hay actualizaciones relevantes
    for service in "${services_to_restart[@]}"; do
        log "Reiniciando servicio: $service"
        systemctl restart "$service"
        
        # Verificar que el servicio esté funcionando
        sleep 5
        if systemctl is-active --quiet "$service"; then
            log "✅ $service: Reiniciado exitosamente"
        else
            log_error "❌ $service: Error al reiniciar"
        fi
    done
}

# Verificar funcionalidad después de actualizaciones
post_update_verification() {
    log "=== Verificando funcionalidad después de actualizaciones ==="
    
    local verification_errors=0
    
    # Verificar Nginx
    if systemctl is-active --quiet nginx; then
        if nginx -t > /dev/null 2>&1; then
            log "✅ Nginx: Configuración válida"
        else
            log_error "❌ Nginx: Error en configuración"
            ((verification_errors++))
        fi
    else
        log_error "❌ Nginx: No está ejecutándose"
        ((verification_errors++))
    fi
    
    # Verificar conectividad web
    if curl -f -s http://localhost/ > /dev/null; then
        log "✅ Web: Conectividad OK"
    else
        log_error "❌ Web: Error de conectividad"
        ((verification_errors++))
    fi
    
    # Verificar API
    if curl -f -s http://localhost:8000/health > /dev/null; then
        log "✅ API: Health check OK"
    else
        log_error "❌ API: Health check failed"
        ((verification_errors++))
    fi
    
    # Verificar base de datos
    if pg_isready -h localhost > /dev/null 2>&1; then
        log "✅ Database: Conectividad OK"
    else
        log_error "❌ Database: Error de conectividad"
        ((verification_errors++))
    fi
    
    return $verification_errors
}

# Limpiar paquetes
cleanup_packages() {
    log "=== Limpiando paquetes ==="
    
    # Limpiar cache de apt
    apt-get autoremove -y
    apt-get autoclean
    apt-get clean
    
    log "Limpieza de paquetes completada"
}

# Generar reporte de actualización
generate_update_report() {
    local report_file="/var/log/maintenance/update-report-$(date +%Y%m%d_%H%M%S).json"
    
    log "=== Generando reporte de actualización ==="
    
    local kernel_update=false
    if [[ -f "/var/log/reboot-required" ]]; then
        local last_kernel_update=$(tail -1 /var/log/reboot-required | grep "Kernel" || echo "")
        if [[ -n "$last_kernel_update" ]]; then
            kernel_update=true
        fi
    fi
    
    cat > "$report_file" << EOF
{
    "update_date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "kernel_update_required": $kernel_update,
    "reboot_required": $(grep -q "Kernel updates" /var/log/reboot-required 2>/dev/null && echo "true" || echo "false"),
    "packages_updated": "$(apt list --installed 2>/dev/null | wc -l)",
    "services_restarted": ["nginx"],
    "verification_passed": $(post_update_verification > /dev/null 2>&1 && echo "true" || echo "false"),
    "log_file": "$LOG_FILE"
}
EOF
    
    log "Reporte de actualización generado: $report_file"
}

# Función principal
main() {
    log "=== INICIANDO ACTUALIZACIÓN DE SISTEMA ==="
    log "Fecha: $(date)"
    log "Host: $(hostname)"
    
    # Verificar prerrequisitos
    check_prerequisites
    
    # Crear snapshot
    create_system_snapshot
    
    # Actualizar repositorios
    update_repositories
    
    # Verificar actualizaciones
    check_available_updates
    
    # Aplicar actualizaciones de seguridad
    apply_security_updates
    
    # Aplicar actualizaciones generales
    apply_general_updates
    
    # Actualizar certificados SSL
    update_ssl_certificates
    
    # Reiniciar servicios
    restart_services_if_needed
    
    # Verificar funcionalidad
    if post_update_verification; then
        log "✅ Actualización completada exitosamente"
    else
        log_error "❌ Errores detectados después de la actualización"
    fi
    
    # Limpiar
    cleanup_packages
    
    # Generar reporte
    generate_update_report
    
    log "=== ACTUALIZACIÓN DE SISTEMA COMPLETADA ==="
    
    # Verificar si se requiere reinicio
    if grep -q "Kernel updates" /var/log/reboot-required 2>/dev/null; then
        log "⚠️  REINICIO REQUERIDO: Se detectaron actualizaciones de kernel"
        log "Ejecutar: reboot"
    fi
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 2. Cron para Actualizaciones

```bash
# Crontab para actualizaciones automáticas de seguridad
# 0 2 * * 0 /path/to/maintenance/system-update.sh security-only

# Actualizaciones de seguridad diarias a las 2 AM
0 2 * * * /usr/bin/unattended-upgrade

# Verificación semanal de sistema completo
0 3 * * 0 /path/to/maintenance/system-update.sh full

# Limpieza de logs mensual
0 1 1 * * find /var/log -name "*.log" -mtime +30 -delete
```

## Mantenimiento de Base de Datos

### 1. Script de Mantenimiento PostgreSQL

```sql
-- maintenance/postgresql-maintenance.sql
-- Script de mantenimiento para PostgreSQL

-- 1. VACUUM y ANALYZE para todas las tablas
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN 
        SELECT schemaname||'.'||tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'VACUUM ANALYZE ' || t;
        RAISE NOTICE 'Vacuumed and analyzed %', t;
    END LOOP;
END $$;

-- 2. Reindexar índices si es necesario
DO $$
DECLARE
    idx TEXT;
    idx_name TEXT;
BEGIN
    FOR idx IN 
        SELECT indexname, schemaname||'.'||tablename
        FROM pg_indexes 
        WHERE schemaname = 'public'
        AND indexname NOT LIKE '%_pkey'
    LOOP
        idx_name := split_part(idx, '|', 1);
        RAISE NOTICE 'Considering reindex for %', idx_name;
        
        -- Verificar si el índice necesita ser recreado
        IF EXISTS (
            SELECT 1 
            FROM pg_stat_user_indexes 
            WHERE indexrelname = idx_name 
            AND idx_scan < 100
        ) THEN
            EXECUTE 'REINDEX INDEX ' || idx_name;
            RAISE NOTICE 'Reindexed %', idx_name;
        END IF;
    END LOOP;
END $$;

-- 3. Actualizar estadísticas para mejores planes de consulta
ANALYZE;

-- 4. Verificar integridad de la base de datos
SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;

-- 5. Estadísticas de uso por tabla
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    round(n_dead_tup::float / greatest(n_live_tup + n_dead_tup, 1) * 100, 2) as dead_tuples_percent
FROM pg_stat_user_tables 
ORDER BY n_dead_tup DESC;

-- 6. Identificar tablas con índices no utilizados
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- 7. Consultas más lentas (requiere pg_stat_statements)
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    rows
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- 8. Conexiones por estado
SELECT 
    state,
    count(*) as connection_count
FROM pg_stat_activity 
GROUP BY state;

-- 9. Bloqueos activos
SELECT 
    a.datname,
    l.relation::regclass,
    l.transactionid,
    l.mode,
    l.GRANTED,
    a.usename,
    a.query,
    a.query_start,
    age(now(), a.query_start) AS query_duration
FROM pg_stat_activity a
JOIN pg_locks l ON l.pid = a.pid
WHERE a.state = 'active';

-- 10. Configuración actual de performance
SELECT 
    name,
    setting,
    unit,
    context
FROM pg_settings 
WHERE name IN (
    'shared_buffers',
    'effective_cache_size',
    'work_mem',
    'maintenance_work_mem',
    'max_connections',
    'checkpoint_completion_target',
    'wal_buffers',
    'default_statistics_target'
)
ORDER BY name;
```

### 2. Script de Monitoreo de Base de Datos

```bash
#!/bin/bash
# maintenance/db-monitoring.sh

set -euo pipefail

source /backup/config/backup-config.env

LOG_FILE="/var/log/db-maintenance.log"
DATE=$(date +%Y-%m-%d)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# Ejecutar mantenimiento de PostgreSQL
run_postgresql_maintenance() {
    log "=== Ejecutando mantenimiento de PostgreSQL ==="
    
    # Ejecutar el script SQL
    if PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -f /path/to/maintenance/postgresql-maintenance.sql > /tmp/db-maintenance-output.log 2>&1; then
        log "Mantenimiento de PostgreSQL completado"
    else
        log_error "Error en mantenimiento de PostgreSQL"
        cat /tmp/db-maintenance-output.log >> "$LOG_FILE"
        return 1
    fi
}

# Verificar espacio en disco de base de datos
check_database_size() {
    log "=== Verificando espacio de base de datos ==="
    
    local db_size=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -t -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME:-ai_news_aggregator}'));" | tr -d ' ')
    
    log "Tamaño de base de datos: $db_size"
    
    # Verificar crecimiento de la base de datos
    local db_size_bytes=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -t -c "SELECT pg_database_size('${DB_NAME:-ai_news_aggregator}');")
    
    local last_size=0
    if [[ -f "/tmp/last_db_size.txt" ]]; then
        last_size=$(cat /tmp/last_db_size.txt)
    fi
    
    echo "$db_size_bytes" > /tmp/last_db_size.txt
    
    if [[ $last_size -gt 0 ]]; then
        local growth=$((db_size_bytes - last_size))
        local growth_mb=$((growth / 1024 / 1024))
        log "Crecimiento de BD desde última verificación: ${growth_mb}MB"
        
        if [[ $growth_mb -gt 1000 ]]; then
            log_error "Crecimiento acelerado detectado: ${growth_mb}MB"
        fi
    fi
}

# Limpiar estadísticas antiguas
cleanup_old_statistics() {
    log "=== Limpiando estadísticas antiguas ==="
    
    # Si pg_stat_statements está instalado
    if PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -c "SELECT * FROM pg_stat_statements LIMIT 1" > /dev/null 2>&1; then
        PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" << 'EOF'
-- Limpiar estadísticas de consultas antiguas
SELECT pg_stat_statements_reset();

-- Log de limpieza
INSERT INTO maintenance_log (timestamp, operation, status) 
VALUES (NOW(), 'cleanup_old_statistics', 'completed');
EOF
        log "Estadísticas de consultas limpiadas"
    else
        log "pg_stat_statements no disponible, saltando limpieza de estadísticas"
    fi
}

# Verificar índices optimizados
check_optimized_indexes() {
    log "=== Verificando índices optimizados ==="
    
    # Buscar índices no utilizados
    local unused_indexes=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -t -c "
        SELECT COUNT(*) 
        FROM pg_stat_user_indexes 
        WHERE idx_scan = 0 
        AND indexname NOT LIKE '%_pkey';
    " | tr -d ' ')
    
    log "Índices no utilizados: $unused_indexes"
    
    if [[ $unused_indexes -gt 10 ]]; then
        log_error "Muchos índices no utilizados detectados: $unused_indexes"
        
        # Obtener lista de índices no utilizados
        PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -c "
            SELECT schemaname, tablename, indexname
            FROM pg_stat_user_indexes 
            WHERE idx_scan = 0 
            AND indexname NOT LIKE '%_pkey'
            LIMIT 20;
        " >> "$LOG_FILE"
    fi
    
    # Verificar índices duplicados o redundantes
    local duplicate_indexes=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -t -c "
        SELECT COUNT(*) 
        FROM (
            SELECT indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND indexname NOT LIKE '%_pkey'
            GROUP BY indexdef 
            HAVING COUNT(*) > 1
        ) as duplicates;
    " | tr -d ' ')
    
    if [[ $duplicate_indexes -gt 0 ]]; then
        log_error "Índices duplicados detectados: $duplicate_indexes"
    fi
}

# Optimizar consultas lentas
optimize_slow_queries() {
    log "=== Optimizando consultas lentas ==="
    
    # Crear índices para consultas frecuentes si es necesario
    local slow_queries=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -t -c "
        SELECT COUNT(*) 
        FROM pg_stat_statements 
        WHERE mean_time > 100 
        AND calls > 100;
    " | tr -d ' ')
    
    if [[ $slow_queries -gt 5 ]]; then
        log "Consultas lentas detectadas: $slow_queries"
        
        # Obtener consultas más lentas
        PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -c "
            SELECT query, calls, mean_time, total_time 
            FROM pg_stat_statements 
            WHERE mean_time > 100 
            AND calls > 100 
            ORDER BY mean_time DESC 
            LIMIT 5;
        " >> "$LOG_FILE"
        
        log "Revisar consultas lentas para optimización"
    fi
}

# Backup específico antes de mantenimiento
create_maintenance_backup() {
    log "=== Creando backup antes de mantenimiento ==="
    
    local backup_file="/backup/local/pre-maintenance-$(date +%Y%m%d_%H%M%S).sql"
    
    PGPASSWORD="${DB_PASSWORD:-}" pg_dump \
        -h "${DB_HOST:-localhost}" \
        -U "${DB_USER:-postgres}" \
        -d "${DB_NAME:-ai_news_aggregator}" \
        --format=custom \
        --verbose \
        --file="$backup_file"
    
    # Encriptar backup
    if [[ -f "$backup_file" ]]; then
        gpg --cipher-algo AES256 \
            --symmetric --output "${backup_file}.gpg" \
            --passphrase-file "$ENCRYPTION_KEY_PATH" \
            < "$backup_file"
        
        rm "$backup_file"
        log "Backup pre-mantenimiento creado: ${backup_file}.gpg"
    fi
}

# Verificar conectividad y performance
check_db_performance() {
    log "=== Verificando performance de base de datos ==="
    
    # Test de conectividad
    if pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" > /dev/null 2>&1; then
        log "✅ Conectividad: OK"
    else
        log_error "❌ Conectividad: FAILED"
        return 1
    fi
    
    # Test de queries simples
    local query_start=$(date +%s.%N)
    PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -c "SELECT COUNT(*) FROM articles;" > /dev/null 2>&1
    local query_end=$(date +%s.%N)
    local query_duration=$(echo "$query_end - $query_start" | bc)
    
    log "Tiempo de query simple: ${query_duration}s"
    
    if (( $(echo "$query_duration > 5.0" | bc -l) )); then
        log_error "Query lenta detectada: ${query_duration}s"
    fi
    
    # Verificar conexiones activas
    local active_connections=$(PGPASSWORD="${DB_PASSWORD:-}" psql -h "${DB_HOST:-localhost}" -U "${DB_USER:-postgres}" -d "${DB_NAME:-ai_news_aggregator}" -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active';" | tr -d ' ')
    
    log "Conexiones activas: $active_connections"
    
    if [[ $active_connections -gt 50 ]]; then
        log_error "Muchas conexiones activas: $active_connections"
    fi
}

# Generar reporte de mantenimiento
generate_maintenance_report() {
    local report_file="/var/log/maintenance/db-report-$(date +%Y%m%d).json"
    
    log "=== Generando reporte de mantenimiento ==="
    
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
{
    "date": "$DATE",
    "hostname": "$(hostname)",
    "database": {
        "host": "${DB_HOST:-localhost}",
        "name": "${DB_NAME:-ai_news_aggregator}",
        "user": "${DB_USER:-postgres}"
    },
    "maintenance_completed": [
        "vacuum_analyze",
        "reindex_if_needed",
        "cleanup_statistics",
        "check_indexes",
        "optimize_slow_queries"
    ],
    "performance_metrics": {
        "connection_test": "passed",
        "query_performance": "monitored"
    },
    "recommendations": [
        "Review unused indexes",
        "Monitor query performance",
        "Consider connection pooling"
    ]
}
EOF
    
    log "Reporte de mantenimiento generado: $report_file"
}

# Función principal
main() {
    log "=== INICIANDO MANTENIMIENTO DE BASE DE DATOS ==="
    log "Fecha: $DATE"
    
    # Crear backup antes del mantenimiento
    create_maintenance_backup
    
    # Ejecutar mantenimiento
    run_postgresql_maintenance || log_error "Error en mantenimiento de PostgreSQL"
    
    # Verificar performance
    check_db_performance || log_error "Error en verificación de performance"
    
    # Verificar optimizaciones
    check_optimized_indexes
    optimize_slow_queries
    
    # Verificar espacio
    check_database_size
    
    # Limpiar
    cleanup_old_statistics
    
    # Generar reporte
    generate_maintenance_report
    
    log "=== MANTENIMIENTO DE BASE DE DATOS COMPLETADO ==="
}

# Verificar si se ejecuta directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

## Documentación y Procedimientos

### 1. Runbooks Operacionales

```markdown
# Runbooks de Mantenimiento

## Runbook 1: Actualización de Sistema Completa

### Objetivo
Actualizar sistema operativo y aplicaciones de manera segura con rollback disponible.

### Prerrequisitos
- Backup completo del sistema
- Ventana de mantenimiento programada
- Acceso root
- Conexión a internet estable

### Procedimiento

#### Fase 1: Preparación (15 minutos)
1. **Crear snapshot del sistema**
   ```bash
   ./maintenance/create-system-snapshot.sh
   ```

2. **Verificar prerrequisitos**
   ```bash
   ./maintenance/system-update.sh --check
   ```

3. **Notificar a stakeholders**
   - Enviar notificación de inicio de mantenimiento
   - Actualizar status page si aplica

#### Fase 2: Actualización (30-60 minutos)
4. **Ejecutar actualización**
   ```bash
   sudo ./maintenance/system-update.sh
   ```

5. **Verificar servicios**
   ```bash
   ./maintenance/verify-services.sh
   ```

#### Fase 3: Verificación (15 minutos)
6. **Ejecutar health checks**
   ```bash
   make health-check
   ```

7. **Verificar funcionalidad crítica**
   - Test de login
   - Test de API endpoints
   - Test de base de datos
   - Test de cache

#### Rollback (Si es necesario)
```bash
./maintenance/rollback-snapshot.sh latest
```

### Post-Mantenimiento
- Actualizar documentación
- Notificar finalización
- Programar próximo mantenimiento

## Runbook 2: Mantenimiento de Base de Datos

### Objetivo
Realizar mantenimiento preventivo de la base de datos PostgreSQL.

### Frecuencia
Semanal, preferiblemente durante horas de bajo tráfico.

### Procedimiento

1. **Backup pre-mantenimiento**
   ```bash
   ./backup/database-backup.sh critical
   ```

2. **Ejecutar mantenimiento**
   ```bash
   ./maintenance/db-monitoring.sh
   ```

3. **Verificar integridad**
   ```bash
   psql -c "SELECT pg_database_size('ai_news_aggregator');"
   ```

4. **Monitorear performance**
   - Verificar consultas lentas
   - Verificar uso de índices
   - Verificar conexiones

## Runbook 3: Limpieza de Logs

### Objetivo
Liberar espacio en disco limpiando logs antiguos.

### Frecuencia
Semanal

### Procedimiento

1. **Identificar logs grandes**
   ```bash
   du -sh /var/log/* | sort -hr
   ```

2. **Limpiar logs antiguos**
   ```bash
   ./maintenance/cleanup-logs.sh
   ```

3. **Verificar rotación de logs**
   ```bash
   logrotate -d /etc/logrotate.conf
   ```

## Runbook 4: Monitoreo de Performance

### Objetivo
Monitorear y optimizar performance del sistema.

### Frecuencia
Semanal

### Procedimiento

1. **Ejecutar benchmarks**
   ```bash
   ./performance/run-benchmarks.sh
   ```

2. **Revisar métricas**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

3. **Analizar logs de performance**
   ```bash
   ./monitoring/analyze-performance-logs.sh
   ```

4. **Generar recomendaciones**
   - Identificar cuellos de botella
   - Sugerir optimizaciones
   - Planificar escalado
```

### 2. Plantillas de Notificación

```bash
#!/bin/bash
# maintenance/notifications.sh

# Configuración de notificaciones
ADMIN_EMAIL="admin@yourdomain.com"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
STATUS_PAGE_API="https://api.statuspage.io/v1/pages/YOUR_PAGE_ID"

# Notificar inicio de mantenimiento
notify_maintenance_start() {
    local message="$1"
    local maintenance_type="$2"
    
    # Email
    echo "$message" | mail -s "[MANTENIMIENTO] Inicio - $maintenance_type" "$ADMIN_EMAIL"
    
    # Slack
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🔧 Mantenimiento iniciado: $maintenance_type\"}" \
        "$SLACK_WEBHOOK" 2>/dev/null || true
    
    # Status page
    curl -X POST "$STATUS_PAGE_API/incidents" \
        -H "Authorization: OAuth YOUR_API_TOKEN" \
        -H "Content-type: application/json" \
        -d '{
            "incident": {
                "name": "Scheduled Maintenance",
                "status": "investigating",
                "body": "'"$message"'",
                "component_id": "your-component-id"
            }
        }' 2>/dev/null || true
}

# Notificar finalización de mantenimiento
notify_maintenance_complete() {
    local message="$1"
    local maintenance_type="$2"
    
    # Email
    echo "$message" | mail -s "[MANTENIMIENTO] Finalizado - $maintenance_type" "$ADMIN_EMAIL"
    
    # Slack
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Mantenimiento completado: $maintenance_type\"}" \
        "$SLACK_WEBHOOK" 2>/dev/null || true
    
    # Status page
    curl -X POST "$STATUS_PAGE_API/incidents" \
        -H "Authorization: OAuth YOUR_API_TOKEN" \
        -H "Content-type: application/json" \
        -d '{
            "incident": {
                "name": "Scheduled Maintenance",
                "status": "resolved",
                "body": "'"$message"'"
            }
        }' 2>/dev/null || true
}

# Notificar error
notify_error() {
    local error_message="$1"
    
    # Email urgente
    echo "$error_message" | mail -s "[URGENTE] Error en mantenimiento" "$ADMIN_EMAIL"
    
    # Slack con emoji de alerta
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 ERROR en mantenimiento: $error_message\"}" \
        "$SLACK_WEBHOOK" 2>/dev/null || true
}
```

---

**Nota**: Esta guía de mantenimiento debe ser actualizada regularmente y adaptada según las necesidades específicas del entorno de producción.