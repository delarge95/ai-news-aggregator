#!/bin/bash
# Script de gestión DNS para AI News Aggregator
# Gestión automatizada de registros DNS

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
CLOUDFLARE_API_TOKEN="${CLOUDFLARE_API_TOKEN:-}"
CLOUDFLARE_EMAIL="${CLOUDFLARE_EMAIL:-}"
DOMAIN_PRODUCTION="ainews.production.ai"
DOMAIN_STAGING="ainews.staging.ai"
ZONE_ID_PRODUCTION="" # Obtener automáticamente
ZONE_ID_STAGING=""    # Obtener automáticamente

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

# Verificar dependencias
check_dependencies() {
    local missing_deps=()
    
    for cmd in curl jq aws; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        error "Dependencias faltantes: ${missing_deps[*]}"
    fi
}

# Función para hacer llamadas a Cloudflare API
cf_api_call() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="${3:-}"
    
    local headers=(
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
        -H "Content-Type: application/json"
    )
    
    if [[ -n "$CLOUDFLARE_EMAIL" ]]; then
        headers+=(-H "X-Auth-Email: $CLOUDFLARE_EMAIL")
    fi
    
    if [[ "$method" == "POST" ]] && [[ -n "$data" ]]; then
        headers+=(-d "$data")
    elif [[ "$method" == "PUT" ]] && [[ -n "$data" ]]; then
        headers+=(-d "$data")
    elif [[ "$method" == "DELETE" ]]; then
        headers+=(-X DELETE)
    fi
    
    curl -s "${headers[@]}" \
         -X "$method" \
         "https://api.cloudflare.com/client/v4$endpoint"
}

# Obtener ZONE_ID para un dominio
get_zone_id() {
    local domain="$1"
    local response
    
    log "Obteniendo ZONE_ID para $domain..."
    
    response=$(cf_api_call "/zones?name=$domain")
    
    local zone_id=$(echo "$response" | jq -r '.result[0].id // empty')
    
    if [[ -z "$zone_id" ]]; then
        error "No se pudo obtener ZONE_ID para $domain"
    fi
    
    echo "$zone_id"
}

# Listar registros DNS existentes
list_dns_records() {
    local domain="$1"
    local zone_id
    
    zone_id=$(get_zone_id "$domain")
    
    log "Listando registros DNS para $domain..."
    
    local response
    response=$(cf_api_call "/zones/$zone_id/dns_records")
    
    echo "$response" | jq -r '.result[] | "\(.type):\(.name) -> \(.content) [TTL: \(.ttl)]"'
}

# Crear registro DNS
create_dns_record() {
    local domain="$1"
    local type="$2"
    local content="$3"
    local name="${4:-$domain}"
    local ttl="${5:-300}"
    
    local zone_id
    zone_id=$(get_zone_id "$domain")
    
    log "Creando registro DNS: $type $name -> $content"
    
    local data
    data=$(cat <<EOF
{
    "type": "$type",
    "name": "$name",
    "content": "$content",
    "ttl": $ttl,
    "proxied": $([ "$type" == "A" ] && echo "true" || echo "false")
}
EOF
)
    
    local response
    response=$(cf_api_call "/zones/$zone_id/dns_records" "POST" "$data")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        log "Registro DNS creado exitosamente"
        echo "$response" | jq -r '.result | "\(.type):\(.name) -> \(.content) [TTL: \(.ttl)]"'
    else
        error "Error creando registro DNS: $(echo "$response" | jq -r '.errors[0].message')"
    fi
}

# Actualizar registro DNS
update_dns_record() {
    local domain="$1"
    local type="$2"
    local content="$3"
    local name="${4:-$domain}"
    
    local zone_id
    zone_id=$(get_zone_id "$domain")
    
    # Obtener ID del registro existente
    local record_id
    record_id=$(cf_api_call "/zones/$zone_id/dns_records?type=$type&name=$name" | jq -r '.result[0].id // empty')
    
    if [[ -z "$record_id" ]]; then
        warning "Registro no encontrado, creando nuevo..."
        create_dns_record "$domain" "$type" "$content" "$name"
        return
    fi
    
    log "Actualizando registro DNS: $type $name -> $content"
    
    local data
    data=$(cat <<EOF
{
    "type": "$type",
    "name": "$name",
    "content": "$content",
    "ttl": 300,
    "proxied": $([ "$type" == "A" ] && echo "true" || echo "false")
}
EOF
)
    
    local response
    response=$(cf_api_call "/zones/$zone_id/dns_records/$record_id" "PUT" "$data")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        log "Registro DNS actualizado exitosamente"
        echo "$response" | jq -r '.result | "\(.type):\(.name) -> \(.content) [TTL: \(.ttl)]"'
    else
        error "Error actualizando registro DNS: $(echo "$response" | jq -r '.errors[0].message')"
    fi
}

# Eliminar registro DNS
delete_dns_record() {
    local domain="$1"
    local type="$2"
    local name="${3:-$domain}"
    
    local zone_id
    zone_id=$(get_zone_id "$domain")
    
    # Obtener ID del registro
    local record_id
    record_id=$(cf_api_call "/zones/$zone_id/dns_records?type=$type&name=$name" | jq -r '.result[0].id // empty')
    
    if [[ -z "$record_id" ]]; then
        warning "Registro no encontrado: $type $name"
        return
    fi
    
    log "Eliminando registro DNS: $type $name"
    
    local response
    response=$(cf_api_call "/zones/$zone_id/dns_records/$record_id" "DELETE")
    
    if echo "$response" | jq -e '.success' > /dev/null; then
        log "Registro DNS eliminado exitosamente"
    else
        error "Error eliminando registro DNS: $(echo "$response" | jq -r '.errors[0].message')"
    fi
}

# Configurar registros DNS para producción
setup_production_dns() {
    local server_ip="${1:-}"
    
    if [[ -z "$server_ip" ]]; then
        server_ip=$(curl -s ifconfig.me || curl -s ipecho.net/plain)
    fi
    
    if [[ -z "$server_ip" ]]; then
        error "No se pudo determinar la IP del servidor"
    fi
    
    log "Configurando DNS para producción con IP: $server_ip"
    
    # Crear registro A principal
    create_dns_record "$DOMAIN_PRODUCTION" "A" "$server_ip" "$DOMAIN_PRODUCTION" 300
    
    # Crear wildcard para subdominios
    create_dns_record "$DOMAIN_PRODUCTION" "A" "$server_ip" "*.$DOMAIN_PRODUCTION" 300
    
    # Crear registro CNAME para www
    create_dns_record "$DOMAIN_PRODUCTION" "CNAME" "$DOMAIN_PRODUCTION" "www" 300
    
    # Crear registros específicos para servicios
    create_dns_record "$DOMAIN_PRODUCTION" "CNAME" "api.ainews.production.ai" "api" 300
    create_dns_record "$DOMAIN_PRODUCTION" "CNAME" "cdn.ainews.production.ai" "cdn" 300
    
    log "Configuración DNS para producción completada"
}

# Configurar registros DNS para staging
setup_staging_dns() {
    local server_ip="${1:-}"
    
    if [[ -z "$server_ip" ]]; then
        server_ip=$(curl -s ifconfig.me || curl -s ipecho.net/plain)
    fi
    
    if [[ -z "$server_ip" ]]; then
        error "No se pudo determinar la IP del servidor"
    fi
    
    log "Configurando DNS para staging con IP: $server_ip"
    
    # Crear registro A principal
    create_dns_record "$DOMAIN_STAGING" "A" "$server_ip" "$DOMAIN_STAGING" 300
    
    # Crear wildcard para subdominios
    create_dns_record "$DOMAIN_STAGING" "A" "$server_ip" "*.$DOMAIN_STAGING" 300
    
    log "Configuración DNS para staging completada"
}

# Verificar estado de DNS
verify_dns() {
    local domain="$1"
    
    log "Verificando configuración DNS para $domain..."
    
    # Verificar resolución DNS
    if dig +short "$domain" | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' > /dev/null; then
        log "Resolución DNS correcta para $domain"
    else
        warning "Problema con resolución DNS para $domain"
    fi
    
    # Verificar certificado SSL
    if timeout 10s openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | \
       grep -q "Verify return code: 0"; then
        log "Certificado SSL válido para $domain"
    else
        warning "Problema con certificado SSL para $domain"
    fi
}

# Función de ayuda
show_help() {
    cat <<EOF
Gestión DNS para AI News Aggregator

Uso: $0 [comando] [opciones]

Comandos:
    list-domain <dominio>     - Listar registros DNS de un dominio
    create <dominio> <tipo> <contenido> [nombre] [ttl] - Crear registro DNS
    update <dominio> <tipo> <contenido> [nombre]       - Actualizar registro DNS
    delete <dominio> <tipo> [nombre]                   - Eliminar registro DNS
    setup-prod [ip]                                    - Configurar DNS producción
    setup-stage [ip]                                   - Configurar DNS staging
    verify <dominio>                                   - Verificar configuración DNS
    
Ejemplos:
    $0 list-domain ainews.production.ai
    $0 create ainews.production.ai A 192.168.1.100 api 300
    $0 setup-prod 192.168.1.100
    $0 verify ainews.production.ai

Variables de entorno requeridas:
    CLOUDFLARE_API_TOKEN - Token de API de Cloudflare
    CLOUDFLARE_EMAIL     - Email de Cloudflare (opcional)

EOF
}

# Función principal
main() {
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi
    
    # Verificar dependencias
    check_dependencies
    
    # Verificar variables de entorno
    if [[ -z "$CLOUDFLARE_API_TOKEN" ]]; then
        error "Variable CLOUDFLARE_API_TOKEN no configurada"
    fi
    
    case "$1" in
        "list-domain")
            [[ $# -ne 2 ]] && { show_help; exit 1; }
            list_dns_records "$2"
            ;;
        "create")
            [[ $# -lt 4 ]] && { show_help; exit 1; }
            create_dns_record "$2" "$3" "$4" "${5:-$2}" "${6:-300}"
            ;;
        "update")
            [[ $# -lt 4 ]] && { show_help; exit 1; }
            update_dns_record "$2" "$3" "$4" "${5:-$2}"
            ;;
        "delete")
            [[ $# -lt 3 ]] && { show_help; exit 1; }
            delete_dns_record "$2" "$3" "${4:-$2}"
            ;;
        "setup-prod")
            setup_production_dns "$2"
            ;;
        "setup-stage")
            setup_staging_dns "$2"
            ;;
        "verify")
            [[ $# -ne 2 ]] && { show_help; exit 1; }
            verify_dns "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            error "Comando desconocido: $1. Usa '$0 help' para ver la ayuda."
            ;;
    esac
}

# Ejecutar función principal
main "$@"