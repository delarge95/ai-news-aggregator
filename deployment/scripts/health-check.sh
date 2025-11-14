#!/bin/bash
# Script de Health Check para AI News Aggregator
# Verificación completa del estado de todos los servicios

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
DEPLOYMENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$DEPLOYMENT_DIR/docker-compose.deployment.yml"
DOMAIN_PRODUCTION="${DOMAIN_PRODUCTION:-ainews.production.ai}"
DOMAIN_STAGING="${DOMAIN_STAGING:-ainews.staging.ai}"

# Contadores
total_checks=0
passed_checks=0
failed_checks=0
warning_checks=0

# Función de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    ((failed_checks++))
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
    ((warning_checks++))
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

step() {
    echo -e "${CYAN}[CHECK] $1${NC}"
    ((total_checks++))
}

# Verificar servicios Docker
check_docker_services() {
    header "Verificación de Servicios Docker"
    
    local services=(
        "postgres"
        "redis-cache"
        "backend"
        "frontend"
        "haproxy"
        "nginx-proxy"
    )
    
    for service in "${services[@]}"; do
        step "Servicio $service"
        
        if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            log "✓ $service está corriendo"
            ((passed_checks++))
            
            # Verificar health status si está disponible
            if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy"; then
                log "  Health status: HEALTHY"
            elif docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "unhealthy"; then
                warning "  Health status: UNHEALTHY"
            fi
        else
            error "✗ $service no está corriendo"
        fi
    done
}

# Verificar conectividad web
check_web_connectivity() {
    header "Verificación de Conectividad Web"
    
    # Verificar health endpoint
    step "Health endpoint"
    if curl -s -f "http://localhost/health" > /dev/null; then
        log "✓ Health endpoint disponible"
        ((passed_checks++))
    else
        error "✗ Health endpoint no disponible"
    fi
    
    # Verificar dominio de producción
    step "Dominio de producción: $DOMAIN_PRODUCTION"
    if curl -s -f -m 10 "https://$DOMAIN_PRODUCTION" > /dev/null; then
        log "✓ Dominio de producción accesible"
        ((passed_checks++))
    else
        error "✗ Dominio de producción no accesible"
    fi
    
    # Verificar API endpoint
    step "API endpoint"
    if curl -s -f -m 10 "https://$DOMAIN_PRODUCTION/api/v1/health" > /dev/null; then
        log "✓ API endpoint accesible"
        ((passed_checks++))
    else
        error "✗ API endpoint no accesible"
    fi
}

# Verificar certificados SSL
check_ssl_certificates() {
    header "Verificación de Certificados SSL"
    
    local domains=("$DOMAIN_PRODUCTION" "$DOMAIN_STAGING")
    
    for domain in "${domains[@]}"; do
        step "Certificado SSL para $domain"
        
        # Verificar si el certificado existe
        local cert_path="/etc/letsencrypt/live/$domain/fullchain.pem"
        if [[ ! -f "$cert_path" ]]; then
            error "✗ Certificado no encontrado: $cert_path"
            continue
        fi
        
        # Verificar validez del certificado
        if timeout 10s openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | \
           grep -q "Verify return code: 0"; then
            log "✓ Certificado válido para $domain"
            ((passed_checks++))
        else
            error "✗ Certificado inválido para $domain"
            continue
        fi
        
        # Verificar fecha de expiración
        local expiry_date
        expiry_date=$(openssl x509 -enddate -noout -in "$cert_path" | cut -d= -f2)
        local expiry_timestamp
        expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp
        current_timestamp=$(date +%s)
        local days_left=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_left -gt 30 ]]; then
            log "  ✓ Válido por $days_left días"
            ((passed_checks++))
        elif [[ $days_left -gt 7 ]]; then
            warning "  ⚠ Expira en $days_left días"
        else
            error "  ✗ Expira en $days_left días"
        fi
    done
}

# Verificar DNS
check_dns_configuration() {
    header "Verificación de Configuración DNS"
    
    local domains=("$DOMAIN_PRODUCTION" "$DOMAIN_STAGING")
    
    for domain in "${domains[@]}"; do
        step "Resolución DNS para $domain"
        
        # Verificar resolución A record
        local ip_resolved
        ip_resolved=$(dig +short "$domain" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
        
        if [[ -n "$ip_resolved" ]]; then
            log "✓ DNS resuelve a: $ip_resolved"
            ((passed_checks++))
        else
            error "✗ DNS no resuelve para $domain"
        fi
        
        # Verificar subdominios comunes
        local subdomains=("api" "cdn" "admin" "docs")
        for subdomain in "${subdomains[@]}"; do
            local full_domain="$subdomain.$domain"
            
            if dig +short "$full_domain" | grep -q .; then
                log "  ✓ $full_domain resuelve"
            else
                warning "  ⚠ $full_domain no resuelve"
            fi
        done
    done
}

# Verificar bases de datos
check_databases() {
    header "Verificación de Bases de Datos"
    
    # Verificar PostgreSQL
    step "Conectividad PostgreSQL"
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres -d ai_news_db -c "SELECT 1;" > /dev/null 2>&1; then
        log "✓ PostgreSQL accesible"
        ((passed_checks++))
    else
        error "✗ PostgreSQL no accesible"
    fi
    
    # Verificar Redis
    step "Conectividad Redis"
    if docker-compose -f "$COMPOSE_FILE" exec -T redis-cache redis-cli ping | grep -q "PONG"; then
        log "✓ Redis accesible"
        ((passed_checks++))
    else
        error "✗ Redis no accesible"
    fi
}

# Verificar logs de errores
check_error_logs() {
    header "Verificación de Logs de Errores"
    
    local services=("nginx-proxy" "backend" "frontend")
    
    for service in "${services[@]}"; do
        step "Logs de $service"
        
        local error_count
        error_count=$(docker-compose -f "$COMPOSE_FILE" logs --since="1h" "$service" 2>&1 | grep -i error | wc -l)
        
        if [[ $error_count -eq 0 ]]; then
            log "✓ No hay errores recientes en $service"
            ((passed_checks++))
        else
            warning "⚠ $error_count errores encontrados en $service (última hora)"
        fi
        
        # Mostrar algunos errores recientes si existen
        if [[ $error_count -gt 0 ]]; then
            echo "  Errores recientes:"
            docker-compose -f "$COMPOSE_FILE" logs --since="1h" "$service" 2>&1 | grep -i error | tail -3 | sed 's/^/    /'
        fi
    done
}

# Verificar recursos del sistema
check_system_resources() {
    header "Verificación de Recursos del Sistema"
    
    # Verificar uso de memoria
    step "Uso de memoria"
    local memory_usage
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    
    if (( $(echo "$memory_usage < 90" | bc -l) )); then
        log "✓ Uso de memoria: $memory_usage%"
        ((passed_checks++))
    else
        warning "⚠ Uso de memoria alto: $memory_usage%"
    fi
    
    # Verificar uso de disco
    step "Uso de disco"
    local disk_usage
    disk_usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $disk_usage -lt 80 ]]; then
        log "✓ Uso de disco: $disk_usage%"
        ((passed_checks++))
    elif [[ $disk_usage -lt 90 ]]; then
        warning "⚠ Uso de disco moderadamente alto: $disk_usage%"
    else
        error "✗ Uso de disco alto: $disk_usage%"
    fi
    
    # Verificar carga del sistema
    step "Carga del sistema"
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores
    cpu_cores=$(nproc)
    
    if (( $(echo "$load_avg < $cpu_cores" | bc -l) )); then
        log "✓ Carga del sistema: $load_avg (cores: $cpu_cores)"
        ((passed_checks++))
    else
        warning "⚠ Carga del sistema alta: $load_avg"
    fi
}

# Verificar configuración de seguridad
check_security_configuration() {
    header "Verificación de Configuración de Seguridad"
    
    # Verificar headers de seguridad
    step "Headers de seguridad"
    local security_headers=(
        "Strict-Transport-Security"
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
    )
    
    local headers_missing=0
    for header in "${security_headers[@]}"; do
        if curl -s -I "https://$DOMAIN_PRODUCTION" | grep -qi "$header"; then
            log "  ✓ $header presente"
        else
            warning "  ⚠ $header faltante"
            ((headers_missing++))
        fi
    done
    
    if [[ $headers_missing -eq 0 ]]; then
        log "✓ Todos los headers de seguridad están presentes"
        ((passed_checks++))
    else
        warning "⚠ $headers_missing headers de seguridad faltantes"
    fi
    
    # Verificar configuración SSL
    step "Configuración SSL"
    local ssl_info
    ssl_info=$(timeout 10s openssl s_client -connect "$DOMAIN_PRODUCTION:443" -servername "$DOMAIN_PRODUCTION" </dev/null 2>/dev/null)
    
    if echo "$ssl_info" | grep -q "Protocol.*TLSv1.3"; then
        log "  ✓ TLS 1.3 habilitado"
    fi
    
    if echo "$ssl_info" | grep -q "Cipher.*ECDHE"; then
        log "  ✓ Cifrado ECDHE habilitado"
        ((passed_checks++))
    else
        error "  ✗ Cifrado ECDHE no encontrado"
    fi
}

# Verificar servicios de monitoreo (si están habilitados)
check_monitoring_services() {
    header "Verificación de Servicios de Monitoreo"
    
    local monitoring_services=("prometheus" "grafana" "node_exporter")
    
    for service in "${monitoring_services[@]}"; do
        step "Servicio $service"
        
        if docker-compose -f "$COMPOSE_FILE" ps "$service" 2>/dev/null | grep -q "Up"; then
            log "✓ $service está corriendo"
            ((passed_checks++))
            
            # Verificar puerto específico
            case $service in
                "prometheus")
                    if curl -s -f "http://localhost:9090/-/healthy" > /dev/null; then
                        log "  ✓ Prometheus healthy endpoint accesible"
                    else
                        warning "  ⚠ Prometheus healthy endpoint no accesible"
                    fi
                    ;;
                "grafana")
                    if curl -s -f "http://localhost:3000/api/health" > /dev/null; then
                        log "  ✓ Grafana health endpoint accesible"
                    else
                        warning "  ⚠ Grafana health endpoint no accesible"
                    fi
                    ;;
                "node_exporter")
                    if curl -s -f "http://localhost:9100/metrics" > /dev/null; then
                        log "  ✓ Node Exporter metrics accesibles"
                    else
                        warning "  ⚠ Node Exporter metrics no accesibles"
                    fi
                    ;;
            esac
        else
            warning "⚠ $service no está corriendo (puede ser normal si no está habilitado)"
        fi
    done
}

# Verificar configuración de respaldos
check_backup_configuration() {
    header "Verificación de Configuración de Respaldos"
    
    # Verificar cron jobs de respaldo
    step "Cron jobs de respaldo"
    if crontab -l 2>/dev/null | grep -q "backup\|certbot\|renew"; then
        log "✓ Cron jobs de respaldo configurados"
        ((passed_checks++))
        
        # Mostrar jobs relacionados
        echo "  Jobs configurados:"
        crontab -l 2>/dev/null | grep -E "(backup|certbot|renew)" | sed 's/^/    /'
    else
        warning "⚠ No se encontraron cron jobs de respaldo"
    fi
    
    # Verificar directorio de respaldos
    step "Directorio de respaldos"
    if [[ -d "/backup" ]] || [[ -d "$DEPLOYMENT_DIR/database/backup" ]]; then
        log "✓ Directorio de respaldos existe"
        ((passed_checks++))
    else
        warning "⚠ Directorio de respaldos no encontrado"
    fi
}

# Mostrar resumen
show_summary() {
    header "Resumen de Health Check"
    
    echo "Total de verificaciones: $total_checks"
    echo -e "Verificaciones exitosas: ${GREEN}$passed_checks${NC}"
    echo -e "Advertencias: ${YELLOW}$warning_checks${NC}"
    echo -e "Verificaciones fallidas: ${RED}$failed_checks${NC}"
    echo
    
    if [[ $failed_checks -eq 0 ]]; then
        if [[ $warning_checks -eq 0 ]]; then
            echo -e "${GREEN}🎉 ¡Sistema saludable!${NC}"
            exit 0
        else
            echo -e "${YELLOW}⚠️  Sistema funcional con advertencias${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Se encontraron problemas críticos${NC}"
        exit 2
    fi
}

# Función principal
main() {
    header "AI News Aggregator - Health Check"
    log "Iniciando verificación completa..."
    
    # Verificar que Docker Compose está disponible
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está disponible"
        exit 2
    fi
    
    # Verificar que el archivo de composición existe
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Archivo Docker Compose no encontrado: $COMPOSE_FILE"
        exit 2
    fi
    
    # Ejecutar todas las verificaciones
    check_docker_services
    check_web_connectivity
    check_ssl_certificates
    check_dns_configuration
    check_databases
    check_error_logs
    check_system_resources
    check_security_configuration
    check_monitoring_services
    check_backup_configuration
    
    # Mostrar resumen
    show_summary
}

# Verificar argumentos
if [[ $# -gt 0 ]]; then
    case "$1" in
        "--help"|"-h")
            echo "Health Check para AI News Aggregator"
            echo "Uso: $0 [opciones]"
            echo "Opciones:"
            echo "  --help, -h    Mostrar esta ayuda"
            echo "  --docker      Solo verificar servicios Docker"
            echo "  --web         Solo verificar conectividad web"
            echo "  --ssl         Solo verificar certificados SSL"
            echo "  --dns         Solo verificar DNS"
            echo "  --security    Solo verificar configuración de seguridad"
            exit 0
            ;;
        --docker)
            check_docker_services
            exit 0
            ;;
        --web)
            check_web_connectivity
            exit 0
            ;;
        --ssl)
            check_ssl_certificates
            exit 0
            ;;
        --dns)
            check_dns_configuration
            exit 0
            ;;
        --security)
            check_security_configuration
            exit 0
            ;;
    esac
fi

# Ejecutar función principal
main