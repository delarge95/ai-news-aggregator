#!/bin/bash
# Script para renovar certificados SSL automáticamente
# AI News Aggregator - Certbot Renewal

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración
CERTBOT_DIR="/etc/letsencrypt"
LOG_FILE="/var/log/certbot-renewal.log"
EMAIL_ADMIN="admin@ainews.production.ai"

# Función de logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

# Verificar que certbot esté instalado
if ! command -v certbot &> /dev/null; then
    error "Certbot no está instalado"
fi

# Función para verificar el estado de los certificados
check_cert_status() {
    log "Verificando estado de certificados..."
    
    # Listar certificados existentes
    certbot certificates 2>&1 | tee -a "$LOG_FILE"
    
    # Verificar fechas de expiración
    for cert_dir in "$CERTBOT_DIR"/live/*/; do
        if [[ -d "$cert_dir" ]]; then
            domain=$(basename "$cert_dir")
            cert_file="$cert_dir/cert.pem"
            
            if [[ -f "$cert_file" ]]; then
                expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
                expiry_timestamp=$(date -d "$expiry_date" +%s)
                current_timestamp=$(date +%s)
                days_left=$(( (expiry_timestamp - current_timestamp) / 86400 ))
                
                log "Dominio: $domain - Días restantes: $days_left"
                
                if [[ $days_left -lt 30 ]]; then
                    warning "Certificado para $domain expira en $days_left días"
                fi
            fi
        fi
    done
}

# Función para renovar certificados
renew_certs() {
    log "Iniciando proceso de renovación de certificados..."
    
    # Crear directorio webroot si no existe
    mkdir -p /var/www/certbot
    
    # Renovar todos los certificados
    certbot renew \
        --config /etc/letsencrypt/cli.ini \
        --post-hook "nginx -s reload" \
        --preferred-challenges http \
        --webroot-path /var/www/certbot \
        2>&1 | tee -a "$LOG_FILE"
    
    # Verificar si la renovación fue exitosa
    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        log "Renovación de certificados completada exitosamente"
    else
        error "Error durante la renovación de certificados"
    fi
}

# Función para obtener nuevos certificados
obtain_new_certs() {
    local domains=(
        "ainews.production.ai"
        "*.ainews.production.ai"
        "ainews.staging.ai"
        "*.ainews.staging.ai"
    )
    
    for domain in "${domains[@]}"; do
        log "Obteniendo certificado para: $domain"
        
        # Verificar si el certificado ya existe
        if [[ -f "$CERTBOT_DIR/live/$domain/cert.pem" ]]; then
            log "Certificado para $domain ya existe, saltando..."
            continue
        fi
        
        # Obtener nuevo certificado
        certbot certonly \
            --webroot \
            --webroot-path /var/www/certbot \
            --domain "$domain" \
            --email "$EMAIL_ADMIN" \
            --agree-tos \
            --non-interactive \
            --expand \
            --keep-until-expiring \
            --must-staple \
            2>&1 | tee -a "$LOG_FILE"
        
        if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
            log "Certificado obtenido exitosamente para $domain"
        else
            error "Error obteniendo certificado para $domain"
        fi
    done
}

# Función para verificar configuración SSL
verify_ssl_config() {
    log "Verificando configuración SSL..."
    
    domains=(
        "ainews.production.ai"
        "*.ainews.production.ai"
        "ainews.staging.ai"
        "*.ainews.staging.ai"
    )
    
    for domain in "${domains[@]}"; do
        log "Verificando SSL para: $domain"
        
        # Verificar certificado SSL
        timeout 10s openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | \
            openssl x509 -noout -dates 2>/dev/null || \
            warning "No se pudo verificar SSL para $domain"
    done
}

# Función principal
main() {
    log "=== Iniciando renovación automática de certificados SSL ==="
    
    # Verificar estado actual
    check_cert_status
    
    # Verificar si es necesario renovar
    if certbot renew --dry-run 2>&1 | tee -a "$LOG_FILE" | grep -q "Would be renewed"; then
        log "Certificados pendientes de renovación detectados"
        renew_certs
    else
        log "No hay certificados que necesiten renovación"
    fi
    
    # Verificar certificados nuevos
    if [[ $# -eq 1 ]] && [[ "$1" == "--new-certs" ]]; then
        log "Obteniendo nuevos certificados"
        obtain_new_certs
    fi
    
    # Verificar configuración SSL
    verify_ssl_config
    
    log "=== Proceso de renovación completado ==="
    
    # Mostrar estado final
    certbot certificates 2>&1 | tee -a "$LOG_FILE"
}

# Verificar argumentos
if [[ $# -gt 1 ]]; then
    echo "Uso: $0 [--new-certs]"
    exit 1
fi

# Ejecutar función principal
main "$@"