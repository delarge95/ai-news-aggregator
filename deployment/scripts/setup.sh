#!/bin/bash
# Script Maestro de Setup para AI News Aggregator
# Configuración completa de dominio, SSL, CDN y seguridad

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$DEPLOYMENT_DIR")"

# Variables de configuración
DOMAIN_PRODUCTION="${DOMAIN_PRODUCTION:-ainews.production.ai}"
DOMAIN_STAGING="${DOMAIN_STAGING:-ainews.staging.ai}"
SSL_EMAIL="${SSL_EMAIL:-admin@${DOMAIN_PRODUCTION}}"
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"
CLOUDFLARE_EMAIL="${CLOUDFLARE_EMAIL:-}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
GRAFANA_PASSWORD="${GRAFANA_PASSWORD:-admin}"

# Función de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

step() {
    echo -e "${CYAN}[STEP] $1${NC}"
}

header() {
    echo -e "\n${MAGENTA}=== $1 ===${NC}\n"
}

# Función para mostrar ayuda
show_help() {
    cat <<EOF
Script Maestro de Setup - AI News Aggregator
Configuración completa de dominio, SSL, CDN y seguridad

Uso: $0 [opciones]

Opciones:
    --help, -h              Mostrar esta ayuda
    --step N                Ejecutar solo el paso N (1-5)
    --dns-only              Solo configurar DNS
    --ssl-only              Solo configurar SSL
    --security-only         Solo configurar seguridad
    --deploy-only           Solo hacer deploy
    --check                 Verificar configuración
    --interactive           Modo interactivo
    --skip-dns              Saltar configuración DNS
    --skip-ssl              Saltar configuración SSL
    --skip-security         Saltar configuración de seguridad

Pasos:
    1. Configuración DNS
    2. Configuración SSL/Certificados
    3. Configuración de Seguridad
    4. Deployment con Docker Compose
    5. Verificación Final

Ejemplos:
    $0                      # Setup completo
    $0 --interactive        # Modo interactivo
    $0 --step 1             # Solo configurar DNS
    $0 --deploy-only        # Solo deployment
    $0 --check              # Verificar configuración

EOF
}

# Verificar dependencias
check_dependencies() {
    header "Verificando Dependencias"
    
    local missing_deps=()
    local required_commands=(
        "docker"
        "docker-compose"
        "curl"
        "dig"
        "openssl"
        "jq"
        "certbot"
    )
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        warning "Dependencias faltantes: ${missing_deps[*]}"
        
        # Verificar si se pueden instalar
        if command -v apt-get &> /dev/null; then
            read -p "¿Instalar dependencias faltantes? (y/n): " install_deps
            if [[ "$install_deps" =~ ^[Yy]$ ]]; then
                log "Instalando dependencias..."
                sudo apt-get update
                sudo apt-get install -y curl jq openssl certbot dig-tools docker.io docker-compose
            else
                error "No se pueden continuar sin las dependencias requeridas"
            fi
        else
            error "Instale manualmente las dependencias: ${missing_deps[*]}"
        fi
    else
        log "Todas las dependencias están disponibles"
    fi
}

# Configurar variables de entorno
setup_environment() {
    header "Configurando Variables de Entorno"
    
    local env_file="$PROJECT_ROOT/.env"
    
    if [[ -f "$env_file" ]]; then
        info "Archivo .env ya existe, creando backup..."
        cp "$env_file" "$env_file.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    cat > "$env_file" <<EOF
# Configuración de AI News Aggregator
# Generado automáticamente por setup.sh

# Dominios
DOMAIN_PRODUCTION=$DOMAIN_PRODUCTION
DOMAIN_STAGING=$DOMAIN_STAGING

# Base de datos
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}
POSTGRES_USER=postgres
POSTGRES_DB=ai_news_db

# SSL
SSL_EMAIL=$SSL_EMAIL
LETSENCRYPT_EMAIL=$SSL_EMAIL

# Monitoreo
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}

# Cloudflare
CLOUDFLARE_API_TOKEN=$CLOUDFLARE_API_TOKEN
CLOUDFLARE_EMAIL=$CLOUDFLARE_EMAIL

# Seguridad
JWT_SECRET=$(openssl rand -base64 32)
SESSION_SECRET=$(openssl rand -base64 32)

# Configuración general
ENVIRONMENT=production
LOG_LEVEL=INFO
TIMEZONE=UTC
EOF
    
    log "Archivo .env creado en: $env_file"
    
    # Cargar variables
    source "$env_file"
}

# Configuración DNS
setup_dns() {
    header "Configuración DNS"
    
    if [[ "${SKIP_DNS:-false}" == "true" ]]; then
        info "Saltando configuración DNS"
        return 0
    fi
    
    # Verificar variables de Cloudflare
    if [[ -z "$CLOUDFLARE_API_TOKEN" ]]; then
        error "CLOUDFLARE_API_TOKEN no configurado. Configure la variable de entorno."
    fi
    
    # Obtener IP del servidor
    local server_ip
    server_ip=$(curl -s ifconfig.me || curl -s ipecho.net/plain)
    
    if [[ -z "$server_ip" ]]; then
        error "No se pudo determinar la IP del servidor"
    fi
    
    info "IP del servidor: $server_ip"
    
    # Configurar DNS para producción
    step "Configurando DNS para producción"
    chmod +x "$DEPLOYMENT_DIR/dns/dns-manager.sh"
    "$DEPLOYMENT_DIR/dns/dns-manager.sh" setup-prod "$server_ip"
    
    # Configurar DNS para staging
    step "Configurando DNS para staging"
    "$DEPLOYMENT_DIR/dns/dns-manager.sh" setup-stage "$server_ip"
    
    # Verificar configuración DNS
    step "Verificando configuración DNS"
    sleep 10  # Esperar propagación
    
    if "$DEPLOYMENT_DIR/dns/dns-manager.sh" verify "$DOMAIN_PRODUCTION"; then
        log "DNS configurado correctamente"
    else
        warning "Problemas con la configuración DNS, pero continuando..."
    fi
}

# Configuración SSL
setup_ssl() {
    header "Configuración SSL"
    
    if [[ "${SKIP_SSL:-false}" == "true" ]]; then
        info "Saltando configuración SSL"
        return 0
    fi
    
    # Verificar que los dominios resuelvan
    step "Verificando resolución DNS"
    if ! dig +short "$DOMAIN_PRODUCTION" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null; then
        error "El dominio $DOMAIN_PRODUCTION no resuelve. Configure DNS primero."
    fi
    
    if ! dig +short "$DOMAIN_STAGING" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null; then
        error "El dominio $DOMAIN_STAGING no resuelve. Configure DNS primero."
    fi
    
    # Configurar certificados SSL
    step "Obteniendo certificados SSL"
    chmod +x "$DEPLOYMENT_DIR/certbot/renew-certs.sh"
    
    # Ejecutar obtensión de certificados
    "$DEPLOYMENT_DIR/certbot/renew-certs.sh" --new-certs
    
    # Configurar renovación automática
    step "Configurando renovación automática"
    (crontab -l 2>/dev/null; echo "0 12 * * * $DEPLOYMENT_DIR/certbot/renew-certs.sh >> /var/log/certbot-renewal.log 2>&1") | crontab -
    
    log "Certificados SSL configurados"
}

# Configuración de seguridad
setup_security() {
    header "Configuración de Seguridad"
    
    if [[ "${SKIP_SECURITY:-false}" == "true" ]]; then
        info "Saltando configuración de seguridad"
        return 0
    fi
    
    # Configurar firewall (solo si se ejecuta como root)
    step "Configurando firewall"
    if [[ $EUID -eq 0 ]]; then
        chmod +x "$DEPLOYMENT_DIR/firewall/firewall.sh"
        "$DEPLOYMENT_DIR/firewall/firewall.sh" 2
        log "Firewall configurado"
    else
        warning "Ejecute como root para configurar firewall: sudo $DEPLOYMENT_DIR/firewall/firewall.sh"
    fi
    
    # Configurar fail2ban si está disponible
    if command -v fail2ban-client &> /dev/null; then
        step "Configurando fail2ban"
        "$DEPLOYMENT_DIR/firewall/firewall.sh" setup_fail2ban
        log "Fail2ban configurado"
    fi
}

# Deployment con Docker Compose
deploy_application() {
    header "Deployment de la Aplicación"
    
    step "Construyendo imágenes Docker"
    cd "$PROJECT_ROOT"
    
    # Construir backend
    log "Construyendo imagen del backend..."
    docker build -t ai-news-backend ./backend
    
    # Construir frontend
    log "Construyendo imagen del frontend..."
    docker build -t ai-news-frontend ./frontend
    
    # Verificar construcción
    if ! docker images | grep -q ai-news-backend; then
        error "Error construyendo imagen del backend"
    fi
    
    if ! docker images | grep -q ai-news-frontend; then
        error "Error construyendo imagen del frontend"
    fi
    
    step "Iniciando servicios con Docker Compose"
    
    # Crear redes Docker
    step "Creando redes Docker"
    docker network create ai_news_external 2>/dev/null || true
    docker network create ai_news_internal 2>/dev/null || true
    
    # Iniciar servicios
    step "Iniciando servicios base"
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" up -d postgres redis-cache
    
    # Esperar que las bases de datos estén listas
    step "Esperando que las bases de datos estén listas"
    sleep 30
    
    # Verificar health checks
    if ! docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" ps | grep -q "healthy"; then
        warning "Algunos servicios no están saludables"
    fi
    
    step "Iniciando servicios de aplicación"
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" up -d backend celery_worker celery_beat frontend
    
    step "Iniciando proxy y load balancer"
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" up -d haproxy
    
    step "Iniciando proxy reverso"
    docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" up -d nginx-proxy
    
    # Verificar que todos los servicios están corriendo
    step "Verificando estado de los servicios"
    sleep 15
    
    if docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" ps | grep -q "Exited"; then
        error "Algunos servicios han fallado. Verifique los logs."
    else
        log "Todos los servicios están corriendo"
    fi
}

# Verificación final
verify_installation() {
    header "Verificación Final"
    
    step "Verificando servicios Docker"
    local failed_services=()
    
    for service in postgres redis-cache backend frontend haproxy nginx-proxy; do
        if ! docker-compose -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" ps "$service" | grep -q "Up"; then
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        error "Servicios fallidos: ${failed_services[*]}"
    else
        log "Todos los servicios están corriendo"
    fi
    
    step "Verificando conectividad web"
    sleep 10
    
    if curl -s -f "http://localhost/health" > /dev/null; then
        log "Health check exitoso"
    else
        warning "Health check falló, pero continuando..."
    fi
    
    step "Verificando certificados SSL"
    if timeout 10s openssl s_client -connect "$DOMAIN_PRODUCTION:443" -servername "$DOMAIN_PRODUCTION" </dev/null 2>/dev/null | \
       grep -q "Verify return code: 0"; then
        log "Certificado SSL válido"
    else
        warning "Problema con certificado SSL"
    fi
    
    step "Mostrando información de acceso"
    cat <<EOF

🎉 ¡Setup completado exitosamente!

Información de acceso:
- URL Principal: https://$DOMAIN_PRODUCTION
- URL Staging: https://$DOMAIN_STAGING
- API: https://api.$DOMAIN_PRODUCTION/api/v1
- Admin: https://admin.$DOMAIN_PRODUCTION (si está configurado)

Servicios de monitoreo (si están habilitados):
- Grafana: http://localhost:3000 (admin/$GRAFANA_PASSWORD)
- Prometheus: http://localhost:9090
- Node Exporter: http://localhost:9100
- HAProxy Stats: http://localhost:8404

Logs importantes:
- Nginx: docker-compose -f $DEPLOYMENT_DIR/docker-compose.deployment.yml logs -f nginx-proxy
- Backend: docker-compose -f $DEPLOYMENT_DIR/docker-compose.deployment.yml logs -f backend
- Certbot: tail -f /var/log/certbot-renewal.log

Comandos útiles:
- Ver estado: docker-compose -f $DEPLOYMENT_DIR/docker-compose.deployment.yml ps
- Ver logs: $DEPLOYMENT_DIR/scripts/health-check.sh
- Renovar SSL: $DEPLOYMENT_DIR/certbot/renew-certs.sh
- Verificar DNS: $DEPLOYMENT_DIR/dns/dns-manager.sh verify $DOMAIN_PRODUCTION

EOF
}

# Función de verificación (sin instalación)
check_configuration() {
    header "Verificación de Configuración"
    
    step "Verificando dependencias"
    check_dependencies
    
    step "Verificando variables de entorno"
    local missing_vars=()
    
    for var in DOMAIN_PRODUCTION DOMAIN_STAGING SSL_EMAIL; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        warning "Variables faltantes: ${missing_vars[*]}"
    else
        log "Variables de entorno configuradas"
    fi
    
    step "Verificando conectividad DNS"
    if dig +short "$DOMAIN_PRODUCTION" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null; then
        log "DNS para $DOMAIN_PRODUCTION resuelve correctamente"
    else
        error "DNS para $DOMAIN_PRODUCTION no resuelve"
    fi
    
    step "Verificando certificados SSL"
    if [[ -f "/etc/letsencrypt/live/$DOMAIN_PRODUCTION/fullchain.pem" ]]; then
        log "Certificado SSL existe"
        
        # Verificar fecha de expiración
        local expiry_date
        expiry_date=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN_PRODUCTION/fullchain.pem" | cut -d= -f2)
        local expiry_timestamp
        expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp
        current_timestamp=$(date +%s)
        local days_left=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        if [[ $days_left -gt 30 ]]; then
            log "Certificado válido por $days_left días"
        else
            warning "Certificado expira en $days_left días"
        fi
    else
        error "Certificado SSL no encontrado"
    fi
    
    step "Verificando servicios Docker"
    if command -v docker-compose &> /dev/null; then
        if [[ -f "$DEPLOYMENT_DIR/docker-compose.deployment.yml" ]]; then
            log "Docker Compose file existe"
        else
            error "Docker Compose file no encontrado"
        fi
    else
        error "Docker Compose no está disponible"
    fi
}

# Modo interactivo
interactive_mode() {
    header "Modo Interactivo"
    
    echo "Configuración interactiva para AI News Aggregator"
    echo
    
    read -p "Dominio de producción [$DOMAIN_PRODUCTION]: " input_domain_prod
    [[ -n "$input_domain_prod" ]] && DOMAIN_PRODUCTION="$input_domain_prod"
    
    read -p "Dominio de staging [$DOMAIN_STAGING]: " input_domain_stage
    [[ -n "$input_domain_stage" ]] && DOMAIN_STAGING="$input_domain_stage"
    
    read -p "Email para SSL [$SSL_EMAIL]: " input_ssl_email
    [[ -n "$input_ssl_email" ]] && SSL_EMAIL="$input_ssl_email"
    
    read -p "Token de Cloudflare API: " input_cloudflare_token
    [[ -n "$input_cloudflare_token" ]] && CLOUDFLARE_API_TOKEN="$input_cloudflare_token"
    
    read -p "Email de Cloudflare [$CLOUDFLARE_EMAIL]: " input_cloudflare_email
    [[ -n "$input_cloudflare_email" ]] && CLOUDFLARE_EMAIL="$input_cloudflare_email"
    
    echo
    echo "Configuración:"
    echo "  Dominio Producción: $DOMAIN_PRODUCTION"
    echo "  Dominio Staging: $DOMAIN_STAGING"
    echo "  Email SSL: $SSL_EMAIL"
    echo "  Token Cloudflare: ${CLOUDFLARE_API_TOKEN:0:10}..."
    echo "  Email Cloudflare: $CLOUDFLARE_EMAIL"
    echo
    
    read -p "¿Continuar con esta configuración? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        error "Configuración cancelada"
    fi
}

# Función principal
main() {
    local step_number="${1:-}"
    local skip_dns="${SKIP_DNS:-false}"
    local skip_ssl="${SKIP_SSL:-false}"
    local skip_security="${SKIP_SECURITY:-false}"
    local interactive="${INTERACTIVE:-false}"
    
    # Parsear argumentos
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --interactive)
                interactive=true
                shift
                ;;
            --skip-dns)
                skip_dns=true
                shift
                ;;
            --skip-ssl)
                skip_ssl=true
                shift
                ;;
            --skip-security)
                skip_security=true
                shift
                ;;
            --check)
                check_configuration
                exit 0
                ;;
            --dns-only)
                setup_environment
                setup_dns
                exit 0
                ;;
            --ssl-only)
                setup_environment
                setup_ssl
                exit 0
                ;;
            --security-only)
                setup_environment
                setup_security
                exit 0
                ;;
            --deploy-only)
                setup_environment
                deploy_application
                exit 0
                ;;
            --step)
                step_number="$2"
                shift 2
                ;;
            *)
                error "Opción desconocida: $1. Use --help para ver las opciones disponibles."
                ;;
        esac
    done
    
    # Modo interactivo
    if [[ "$interactive" == "true" ]]; then
        interactive_mode
    fi
    
    # Validar paso si se especifica
    if [[ -n "$step_number" ]]; then
        if [[ ! "$step_number" =~ ^[1-5]$ ]]; then
            error "Paso inválido: $step_number. Use 1-5."
        fi
    fi
    
    header "AI News Aggregator - Setup de Deployment"
    log "Iniciando configuración..."
    
    # Verificar dependencias
    check_dependencies
    
    # Configurar entorno
    setup_environment
    
    # Ejecutar pasos según se especifique
    if [[ -n "$step_number" ]]; then
        case $step_number in
            1) setup_dns ;;
            2) setup_ssl ;;
            3) setup_security ;;
            4) deploy_application ;;
            5) verify_installation ;;
        esac
    else
        # Ejecución completa
        setup_dns
        setup_ssl
        setup_security
        deploy_application
        verify_installation
    fi
    
    log "¡Setup completado!"
}

# Ejecutar función principal
main "$@"