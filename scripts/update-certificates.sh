#!/bin/bash

# update-certificates.sh - Gestión y renovación de certificados SSL
# Versión: 1.0.0
# Descripción: Renovación automática de certificados SSL con Let's Encrypt

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "update-certificates"

# Configuración de certificados
readonly PROJECT_NAME="ai-news-aggregator"
readonly CERT_DIR="${CERT_DIR:-./certificates}"
readonly LETSENCRYPT_DIR="${LETSENCRYPT_DIR:-./letsencrypt}"
readonly NGINX_CONFIG_DIR="${NGINX_CONFIG_DIR:-/etc/nginx/sites-available}"
readonly DOCKER_CERTS_DIR="./docker/certs"
readonly RENEWAL_THRESHOLD_DAYS="${RENEWAL_THRESHOLD_DAYS:-30}"
readonly BACKUP_CERTS="${BACKUP_CERTS:-true}"

# Configuración de Let's Encrypt
readonly STAGING_SERVER="${STAGING_SERVER:-false}"
readonly EMAIL="${EMAIL:-admin@example.com}"
readonly DOMAINS="${DOMAINS:-localhost,ai-news.local}"

# Variables de entorno
readonly DRY_RUN="${DRY_RUN:-false}"
readonly FORCE_RENEWAL="${FORCE_RENEWAL:-false}"
readonly AUTO_RELOAD_WEB_SERVER="${AUTO_RELOAD_WEB_SERVER:-true}"

# Funciones principales
main() {
    local action="${1:-renew}"
    
    case "$action" in
        "renew") renew_certificates ;;
        "install") install_certificate "$2" ;;
        "backup") backup_certificates ;;
        "restore") restore_certificates "$2" ;;
        "status") show_certificate_status ;;
        "check") check_certificate_expiry ;;
        "generate") generate_self_signed "$2" ;;
        "config") show_certificate_config ;;
        "cleanup") cleanup_old_certificates ;;
        *) usage ;;
    esac
}

renew_certificates() {
    log_info "🔒 Iniciando renovación de certificados SSL..."
    
    local renew_start_time
    renew_start_time=$(date +%s)
    
    # Crear directorio de certificados
    mkdir -p "$CERT_DIR" "$LETSENCRYPT_DIR"
    
    # Detectar método de renovación
    local renewal_method
    renewal_method=$(detect_renewal_method)
    
    log_info "Método de renovación detectado: $renewal_method"
    
    case "$renewal_method" in
        "certbot")
            renew_with_certbot
            ;;
        "acme-sh")
            renew_with_acme_sh
            ;;
        "manual")
            manual_renewal_process
            ;;
        *)
            log_error "No se pudo detectar método de renovación válido"
            exit 1
            ;;
    esac
    
    local renew_end_time
    renew_end_time=$(date +%s)
    local renew_duration=$((renew_end_time - renew_start_time))
    
    # Verificar renovación
    if verify_certificate_renewal; then
        log_success "✅ Certificados renovados exitosamente en ${renew_duration}s"
        log_metric "cert_renewal_duration" "$renew_duration"
        
        # Recargar servidor web si está habilitado
        if [[ "$AUTO_RELOAD_WEB_SERVER" == "true" ]]; then
            reload_web_server
        fi
        
        # Hacer backup si está habilitado
        if [[ "$BACKUP_CERTS" == "true" ]]; then
            backup_certificates
        fi
    else
        log_error "❌ Error verificando renovación de certificados"
        exit 1
    fi
}

detect_renewal_method() {
    # Verificar certbot
    if command -v certbot &> /dev/null; then
        echo "certbot"
        return 0
    fi
    
    # Verificar acme.sh
    if command -v acme.sh &> /dev/null; then
        echo "acme-sh"
        return 0
    fi
    
    # Verificar si estamos en Docker (método manual)
    if [[ -f "/var/run/docker.sock" ]] || docker ps &> /dev/null; then
        echo "manual"
        return 0
    fi
    
    # Verificar disponibilidad de letsencrypt (módulo Python)
    if python3 -c "import certbot" 2>/dev/null; then
        echo "certbot"
        return 0
    fi
    
    log_error "No se encontró herramienta de renovación SSL instalada"
    echo "manual"
}

renew_with_certbot() {
    log_info "Renovando certificados con certbot..."
    
    # Construir comando certbot
    local certbot_cmd="certbot renew"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        certbot_cmd="$certbot_cmd --dry-run"
    fi
    
    if [[ "$FORCE_RENEWAL" == "true" ]]; then
        certbot_cmd="$certbot_cmd --force-renewal"
    fi
    
    # Agregar servidor staging si está configurado
    if [[ "$STAGING_SERVER" == "true" ]]; then
        certbot_cmd="$certbot_cmd --server https://acme-staging-v02.api.letsencrypt.org/directory"
    fi
    
    # Configurar directorio de trabajo
    certbot_cmd="$certbot_cmd --config-dir $LETSENCRYPT_DIR --work-dir $LETSENCRYPT_DIR/work --logs-dir $LETSENCRYPT_DIR/logs"
    
    # Ejecutar renovación
    log_info "Ejecutando: $certbot_cmd"
    
    if eval "$certbot_cmd"; then
        log_success "Renovación con certbot completada"
        
        # Copiar certificados a directorio del proyecto
        copy_certificates_from_certbot
        
        return 0
    else
        log_error "Error en renovación con certbot"
        return 1
    fi
}

copy_certificates_from_certbot() {
    log_info "Copiando certificados desde certbot..."
    
    local source_dir="$LETSENCRYPT_DIR/live"
    
    if [[ ! -d "$source_dir" ]]; then
        log_warn "Directorio de certificados de certbot no encontrado"
        return 1
    fi
    
    # Encontrar todos los directorios de certificados
    local cert_domains
    mapfile -t cert_domains < <(find "$source_dir" -maxdepth 1 -type d -name "*" ! -path "$source_dir")
    
    for domain_dir in "${cert_domains[@]}"; do
        local domain_name
        domain_name=$(basename "$domain_dir")
        
        # Copiar archivos de certificado
        cp "$domain_dir/cert.pem" "$CERT_DIR/${domain_name}.crt" 2>/dev/null || true
        cp "$domain_dir/chain.pem" "$CERT_DIR/${domain_name}.chain.crt" 2>/dev/null || true
        cp "$domain_dir/fullchain.pem" "$CERT_DIR/${domain_name}.fullchain.crt" 2>/dev/null || true
        cp "$domain_dir/privkey.pem" "$CERT_DIR/${domain_name}.key" 2>/dev/null || true
        
        log_success "✅ Certificados copiados para dominio: $domain_name"
    done
    
    # Copiar configuración de renovación
    if [[ -d "$LETSENCRYPT_DIR/renewal" ]]; then
        cp -r "$LETSENCRYPT_DIR/renewal" "$CERT_DIR/" 2>/dev/null || true
        log_info "Configuración de renovación copiada"
    fi
}

renew_with_acme_sh() {
    log_info "Renovando certificados con acme.sh..."
    
    # Construir comando acme.sh
    local acme_cmd="acme.sh --renew-all"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        acme_cmd="$acme_cmd --test"
    fi
    
    # Configurar directorio de trabajo
    acme_cmd="$acme_cmd --config-home $LETSENCRYPT_DIR"
    
    # Ejecutar renovación
    log_info "Ejecutando: $acme_cmd"
    
    if eval "$acme_cmd"; then
        log_success "Renovación con acme.sh completada"
        
        # Copiar certificados a directorio del proyecto
        copy_certificates_from_acme_sh
        
        return 0
    else
        log_error "Error en renovación con acme.sh"
        return 1
    fi
}

copy_certificates_from_acme_sh() {
    log_info "Copiando certificados desde acme.sh..."
    
    local source_dir="$LETSENCRYPT_DIR/${DOMAINS%%,*}"
    
    if [[ ! -d "$source_dir" ]]; then
        log_warn "Directorio de certificados de acme.sh no encontrado"
        return 1
    fi
    
    # Copiar certificados
    cp "$source_dir/${DOMAINS%%,*}.crt" "$CERT_DIR/" 2>/dev/null || true
    cp "$source_dir/${DOMAINS%%,*}.key" "$CERT_DIR/" 2>/dev/null || true
    cp "$source_DIR/${DOMAINS%%,*}.cer" "$CERT_DIR/" 2>/dev/null || true
    
    log_success "✅ Certificados copiados desde acme.sh"
}

manual_renewal_process() {
    log_info "Proceso manual de renovación de certificados..."
    
    # Para Docker, mostrar instrucciones
    if [[ -f "/var/run/docker.sock" ]] || docker ps &> /dev/null; then
        manual_docker_renewal
    else
        log_error "Renovación manual no implementada para este entorno"
        exit 1
    fi
}

manual_docker_renewal() {
    log_info "Renovación manual para entorno Docker..."
    
    # Verificar si ya existen certificados
    if [[ -d "$CERT_DIR" ]] && [[ $(find "$CERT_DIR" -name "*.crt" | wc -l) -gt 0 ]]; then
        log_info "Certificados existentes encontrados, verificando expiración..."
        
        if ! check_certificate_expiry; then
            if [[ "$FORCE_RENEWAL" != "true" ]]; then
                log_info "Certificados aún válidos, omitiendo renovación"
                return 0
            fi
        fi
    fi
    
    log_info "Se requiere renovación manual. Opciones disponibles:"
    echo ""
    echo "1️⃣  Certificados autofirmados (desarrollo):"
    echo "   $0 generate self-signed"
    echo ""
    echo "2️⃣  Let's Encrypt con certbot (producción):"
    echo "   # Instalar certbot"
    echo "   apt-get install certbot"
    echo ""
    echo "   # Obtener certificado"
    echo "   certbot certonly --standalone -d $DOMAINS --email $EMAIL"
    echo ""
    echo "3️⃣  Copiar certificados existentes:"
    echo "   # Copiar a $CERT_DIR/"
    echo "   cp /path/to/certificates/*.crt $CERT_DIR/"
    echo "   cp /path/to/certificates/*.key $CERT_DIR/"
    echo ""
    echo "4️⃣  Usar certificados Docker (para desarrollo):"
    echo "   # Crear certificados auto-firmados en Docker"
    echo "   docker run --rm -v $CERT_DIR:/certs alpine/sh cert.sh"
    
    # Ofrecer generar certificados auto-firmados para desarrollo
    echo ""
    read -p "¿Deseas generar certificados auto-firmados para desarrollo? (y/n): " -r generate_self_signed
    
    if [[ "$generate_self_signed" =~ ^[Yy]$ ]]; then
        generate_self_signed "development"
    fi
}

verify_certificate_renewal() {
    log_info "Verificando renovación de certificados..."
    
    if [[ ! -d "$CERT_DIR" ]]; then
        log_error "Directorio de certificados no encontrado: $CERT_DIR"
        return 1
    fi
    
    local verified_certs=0
    local total_certs=0
    
    # Verificar certificados
    for cert_file in "$CERT_DIR"/*.crt; do
        if [[ -f "$cert_file" ]]; then
            ((total_certs++))
            
            local cert_name
            cert_name=$(basename "$cert_file" .crt)
            local key_file="$CERT_DIR/${cert_name}.key"
            
            # Verificar que existe el archivo clave
            if [[ ! -f "$key_file" ]]; then
                log_error "Archivo clave faltante para $cert_name"
                continue
            fi
            
            # Verificar validez del certificado
            if verify_certificate_file "$cert_file" "$key_file"; then
                log_success "✅ Certificado $cert_name: Válido"
                ((verified_certs++))
            else
                log_error "❌ Certificado $cert_name: Inválido"
            fi
        fi
    done
    
    if [[ $total_certs -eq 0 ]]; then
        log_warn "No se encontraron certificados para verificar"
        return 0
    fi
    
    if [[ $verified_certs -eq $total_certs ]]; then
        log_success "Todos los certificados verificados ($verified_certs/$total_certs)"
        return 0
    else
        log_error "Certificados con problemas ($verified_certs/$total_certs)"
        return 1
    fi
}

verify_certificate_file() {
    local cert_file="$1"
    local key_file="$2"
    
    # Verificar que el archivo de certificado es válido
    if ! openssl x509 -in "$cert_file" -noout -text > /dev/null 2>&1; then
        return 1
    fi
    
    # Verificar que la clave privada es válida
    if ! openssl rsa -in "$key_file" -noout -check > /dev/null 2>&1; then
        return 1
    fi
    
    # Verificar que certificado y clave coinciden
    local cert_modulus
    local key_modulus
    
    cert_modulus=$(openssl x509 -noout -modulus -in "$cert_file" 2>/dev/null | openssl md5)
    key_modulus=$(openssl rsa -noout -modulus -in "$key_file" 2>/dev/null | openssl md5)
    
    if [[ "$cert_modulus" == "$key_modulus" ]]; then
        return 0
    else
        return 1
    fi
}

reload_web_server() {
    log_info "Recargando servidor web..."
    
    # Recargar nginx
    if command -v nginx &> /dev/null && nginx -t > /dev/null 2>&1; then
        nginx -s reload 2>/dev/null && {
            log_success "✅ Nginx recargado"
            return 0
        }
    fi
    
    # Recargar apache
    if command -v apache2 &> /dev/null; then
        systemctl reload apache2 2>/dev/null && {
            log_success "✅ Apache recargado"
            return 0
        }
    fi
    
    # Reiniciar docker-compose si los certificados están en docker
    if [[ -d "$DOCKER_CERTS_DIR" ]] && docker ps | grep -q "ai_news_"; then
        docker-compose restart frontend backend 2>/dev/null && {
            log_success "✅ Servicios Docker reiniciados"
            return 0
        }
    fi
    
    log_warn "No se pudo recargar automáticamente el servidor web"
    log_info "Recarga manual requerida"
}

backup_certificates() {
    log_info "💾 Creando backup de certificados SSL..."
    
    if [[ ! -d "$CERT_DIR" ]]; then
        log_warn "Directorio de certificados no existe: $CERT_DIR"
        return 0
    fi
    
    local backup_timestamp
    backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$CERT_DIR/backups/cert_backup_$backup_timestamp"
    
    mkdir -p "$(dirname "$backup_dir")"
    
    # Crear backup
    cp -r "$CERT_DIR" "$backup_dir"
    
    # Comprimir backup
    local backup_file="$CERT_DIR/backups/cert_backup_$backup_timestamp.tar.gz"
    tar -czf "$backup_file" -C "$(dirname "$backup_dir")" "$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    
    local backup_size
    backup_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo "0")
    
    log_success "✅ Backup de certificados creado: $backup_file ($(format_size "$backup_size"))"
    
    # Limpiar backups antiguos (mantener últimos 5)
    cleanup_certificate_backups
    
    return 0
}

cleanup_certificate_backups() {
    local backups_dir="$CERT_DIR/backups"
    
    if [[ ! -d "$backups_dir" ]]; then
        return 0
    fi
    
    local backup_count
    backup_count=$(find "$backups_dir" -name "cert_backup_*.tar.gz" | wc -l)
    
    if [[ $backup_count -gt 5 ]]; then
        local to_remove
        to_remove=$((backup_count - 5))
        
        find "$backups_dir" -name "cert_backup_*.tar.gz" -type f -printf '%T@ %p\n' | \
        sort -n | head -n "$to_remove" | cut -d' ' -f2- | \
        while read -r backup_file; do
            rm -f "$backup_file"
            log_info "Backup antiguo eliminado: $(basename "$backup_file")"
        done
    fi
}

restore_certificates() {
    local backup_path="$1"
    
    if [[ -z "$backup_path" ]]; then
        log_error "Ruta de backup requerida"
        usage
        exit 1
    fi
    
    if [[ ! -e "$backup_path" ]]; then
        log_error "Archivo de backup no encontrado: $backup_path"
        show_available_backups
        exit 1
    fi
    
    log_info "🔄 Restaurando certificados desde backup..."
    
    # Crear backup de seguridad del estado actual
    if [[ -d "$CERT_DIR" ]] && [[ $(find "$CERT_DIR" -name "*.crt" | wc -l) -gt 0 ]]; then
        backup_certificates
    fi
    
    # Extraer backup
    local restore_dir="$CERT_DIR/restore_temp_$$"
    mkdir -p "$restore_dir"
    
    if tar -xzf "$backup_path" -C "$restore_dir" 2>/dev/null; then
        # Copiar certificados
        cp -r "$restore_dir"/* "$CERT_DIR/" 2>/dev/null || true
        
        # Verificar certificados restaurados
        if verify_certificate_renewal; then
            log_success "✅ Certificados restaurados exitosamente"
            
            # Recargar servidor web si está habilitado
            if [[ "$AUTO_RELOAD_WEB_SERVER" == "true" ]]; then
                reload_web_server
            fi
        else
            log_error "❌ Error verificando certificados restaurados"
            return 1
        fi
    else
        log_error "Error extrayendo backup: $backup_path"
        return 1
    fi
    
    # Limpiar directorio temporal
    rm -rf "$restore_dir"
}

show_certificate_status() {
    log_info "📊 Estado de certificados SSL"
    echo ""
    
    # Estado general
    if [[ -d "$CERT_DIR" ]] && [[ $(find "$CERT_DIR" -name "*.crt" | wc -l) -gt 0 ]]; then
        echo "Estado: ✅ Certificados encontrados"
    else
        echo "Estado: ❌ No se encontraron certificados"
    fi
    
    echo "Directorio: $CERT_DIR"
    echo ""
    
    # Detalles de certificados
    if [[ -d "$CERT_DIR" ]]; then
        echo "Certificados disponibles:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        local cert_count=0
        for cert_file in "$CERT_DIR"/*.crt; do
            if [[ -f "$cert_file" ]]; then
                ((cert_count++))
                show_certificate_details "$cert_file"
            fi
        done
        
        if [[ $cert_count -eq 0 ]]; then
            echo "  No hay certificados en el directorio"
        fi
        
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # Estado de renovación automática
        echo "Configuración de renovación:"
        echo "  Umbral de renovación: $RENEWAL_THRESHOLD_DAYS días"
        echo "  Servidor staging: $STAGING_SERVER"
        echo "  Email: $EMAIL"
        echo "  Dominios: $DOMAINS"
        echo "  Recarga automática: $AUTO_RELOAD_WEB_SERVER"
        echo ""
        
        # Próxima renovación programada
        if [[ -d "$LETSENCRYPT_DIR/renewal" ]]; then
            echo "Renovación programada:"
            find "$LETSENCRYPT_DIR/renewal" -name "*.conf" | while read -r renewal_config; do
                local domain
                domain=$(basename "$renewal_config" .conf)
                echo "  📅 $domain"
            done
        else
            echo "  ⚠️  No se encontró configuración de renovación automática"
        fi
    else
        echo "Directorio de certificados no existe"
    fi
}

show_certificate_details() {
    local cert_file="$1"
    
    local cert_name
    cert_name=$(basename "$cert_file" .crt)
    
    echo "🔒 $cert_name:"
    
    # Información básica del certificado
    if openssl x509 -in "$cert_file" -noout -subject 2>/dev/null; then
        echo "  Emisor: $(openssl x509 -in "$cert_file" -noout -issuer | sed 's/issuer=//')"
        echo "  Sujeto: $(openssl x509 -in "$cert_file" -noout -subject | sed 's/subject=//')"
        
        # Fechas de validez
        local not_before
        local not_after
        
        not_before=$(openssl x509 -in "$cert_file" -noout -startdate | sed 's/notBefore=//')
        not_after=$(openssl x509 -in "$cert_file" -noout -enddate | sed 's/notAfter=//')
        
        echo "  Válido desde: $not_before"
        echo "  Válido hasta: $not_after"
        
        # Días hasta expiración
        local days_until_expiry
        days_until_expiry=$(calculate_days_until_expiry "$not_after")
        
        if [[ $days_until_expiry -lt $RENEWAL_THRESHOLD_DAYS ]]; then
            echo "  ⚠️  Expira en: $days_until_expiry días (renovación recomendada)"
        else
            echo "  ✅ Expira en: $days_until_expiry días"
        fi
        
        # Tipo de certificado
        local cert_type
        cert_type=$(detect_certificate_type "$cert_file")
        echo "  Tipo: $cert_type"
        
    else
        echo "  ❌ Error leyendo certificado"
    fi
    
    # Verificar clave privada
    local key_file="$CERT_DIR/${cert_name}.key"
    if [[ -f "$key_file" ]]; then
        if verify_certificate_file "$cert_file" "$key_file"; then
            echo "  ✅ Clave privada: Válida y coincide"
        else
            echo "  ❌ Clave privada: No coincide o inválida"
        fi
    else
        echo "  ❌ Clave privada: No encontrada"
    fi
    
    echo ""
}

detect_certificate_type() {
    local cert_file="$1"
    
    # Detectar tipo por contenido
    if openssl x509 -in "$cert_file" -noout -text 2>/dev/null | grep -q "CN=localhost\|CN=ai-news"; then
        echo "Auto-firmado (desarrollo)"
    elif openssl x509 -in "$cert_file" -noout -issuer 2>/dev/null | grep -q "Let's Encrypt"; then
        echo "Let's Encrypt"
    else
        echo "Comercial/Organizacional"
    fi
}

calculate_days_until_expiry() {
    local expiry_date="$1"
    
    # Convertir fecha a timestamp
    local expiry_timestamp
    expiry_timestamp=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
    
    local current_timestamp
    current_timestamp=$(date +%s)
    
    local seconds_until_expiry
    seconds_until_expiry=$((expiry_timestamp - current_timestamp))
    
    echo $((seconds_until_expiry / 86400)) # 86400 segundos por día
}

check_certificate_expiry() {
    log_info "🔍 Verificando expiración de certificados..."
    
    if [[ ! -d "$CERT_DIR" ]]; then
        log_warn "Directorio de certificados no existe"
        return 0
    fi
    
    local expiring_soon=0
    local expired=0
    
    for cert_file in "$CERT_DIR"/*.crt; do
        if [[ -f "$cert_file" ]]; then
            local cert_name
            cert_name=$(basename "$cert_file" .crt)
            
            local not_after
            not_after=$(openssl x509 -in "$cert_file" -noout -enddate 2>/dev/null | sed 's/notAfter=//')
            
            if [[ -n "$not_after" ]]; then
                local days_until_expiry
                days_until_expiry=$(calculate_days_until_expiry "$not_after")
                
                if [[ $days_until_expiry -lt 0 ]]; then
                    log_error "❌ $cert_name: EXPIRADO ($days_until_expiry días)"
                    ((expired++))
                elif [[ $days_until_expiry -lt $RENEWAL_THRESHOLD_DAYS ]]; then
                    log_warn "⚠️  $cert_name: Expira pronto ($days_until_expiry días)"
                    ((expiring_soon++))
                else
                    log_success "✅ $cert_name: Válido ($days_until_expiry días restantes)"
                fi
            fi
        fi
    done
    
    if [[ $expired -gt 0 ]]; then
        log_error "❌ $expired certificados expirados"
        return 1
    elif [[ $expiring_soon -gt 0 ]]; then
        log_warn "⚠️  $expiring_soon certificados expiran pronto"
        return 1
    else
        log_success "✅ Todos los certificados están válidos"
        return 0
    fi
}

generate_self_signed() {
    local cert_type="${2:-development}"
    
    log_info "🔐 Generando certificados auto-firmados para $cert_type..."
    
    mkdir -p "$CERT_DIR"
    
    local domain_name
    case "$cert_type" in
        "development")
            domain_name="localhost"
            ;;
        "staging")
            domain_name="ai-news-staging.local"
            ;;
        "production")
            domain_name="ai-news.local"
            ;;
        *)
            domain_name="${2:-localhost}"
            ;;
    esac
    
    # Generar clave privada
    local key_file="$CERT_DIR/${domain_name}.key"
    local cert_file="$CERT_DIR/${domain_name}.crt"
    
    if openssl genrsa -out "$key_file" 2048 2>/dev/null; then
        log_success "✅ Clave privada generada"
    else
        log_error "❌ Error generando clave privada"
        return 1
    fi
    
    # Generar certificado
    local cert_config
    cert_config=$(cat <<EOF
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Organization
OU = Organizational Unit
CN = $domain_name

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $domain_name
DNS.2 = *.${domain_name}
DNS.3 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
)
    
    if echo "$cert_config" | openssl req -new -x509 -key "$key_file" -out "$cert_file" -days 365 -config - 2>/dev/null; then
        log_success "✅ Certificado auto-firmado generado"
    else
        log_error "❌ Error generando certificado"
        return 1
    fi
    
    # Establecer permisos correctos
    chmod 600 "$key_file"
    chmod 644 "$cert_file"
    
    # Verificar certificado generado
    if verify_certificate_file "$cert_file" "$key_file"; then
        log_success "✅ Certificado auto-firmado verificado"
        log_info "Dominio: $domain_name"
        log_info "Válido por: 365 días"
        log_info "Archivos: $cert_file, $key_file"
        
        # Mostrar información del certificado
        echo ""
        echo "Detalles del certificado:"
        openssl x509 -in "$cert_file" -noout -text | grep -E "Subject:|Issuer:|Not Before:|Not After:" | sed 's/^/  /'
        
        return 0
    else
        log_error "❌ Error verificando certificado generado"
        return 1
    fi
}

show_certificate_config() {
    log_info "⚙️  Configuración de certificados SSL"
    echo ""
    
    cat <<EOF
Variables de entorno configurables:
  CERT_DIR                    - Directorio de certificados (default: ./certificates)
  LETSENCRYPT_DIR            - Directorio de Let's Encrypt (default: ./letsencrypt)
  RENEWAL_THRESHOLD_DAYS     - Días para renovar automáticamente (default: 30)
  STAGING_SERVER             - Usar servidor staging (default: false)
  EMAIL                      - Email para Let's Encrypt (default: admin@example.com)
  DOMAINS                    - Lista de dominios (default: localhost,ai-news.local)
  DRY_RUN                    - Modo simulación (default: false)
  FORCE_RENEWAL              - Forzar renovación (default: false)
  AUTO_RELOAD_WEB_SERVER     - Recarga automática (default: true)
  BACKUP_CERTS               - Backup automático (default: true)

Herramientas de renovación:
  certbot                     - Cliente oficial de Let's Encrypt
  acme.sh                     - Cliente alternativo de Let's Encrypt
  manual                      - Renovación manual (Docker/otros)

Tipos de certificados:
  Let's Encrypt              - Gratuitos, automáticos (producción)
  Auto-firmados             - Para desarrollo y testing
  Comerciales               - Certificados pagados

Archivos generados:
  $CERT_DIR/
  ├── *.crt                  - Certificados
  ├── *.key                  - Claves privadas
  ├── *.chain.crt           - Cadenas de certificados
  ├── *.fullchain.crt       - Certificado completo
  └── backups/              - Backups automáticos

Comandos útiles:
  $0 renew                   - Renovar certificados
  $0 status                 - Ver estado actual
  $0 check                  - Verificar expiración
  $0 generate development   - Generar auto-firmados
  $0 backup                 - Crear backup
  $0 restore <archivo>      - Restaurar backup

Ejemplos de uso:
  # Renovación normal
  $0 renew
  
  # Modo simulación
  DRY_RUN=true $0 renew
  
  # Forzar renovación
  FORCE_RENEWAL=true $0 renew
  
  # Generar certificados de desarrollo
  $0 generate development
  
  # Verificar estado
  $0 status
  
  # Crear backup
  $0 backup

EOF
}

cleanup_old_certificates() {
    log_info "🧹 Limpiando certificados antiguos..."
    
    local cleaned_files=0
    
    # Limpiar certificados expirados
    if [[ -d "$CERT_DIR" ]]; then
        for cert_file in "$CERT_DIR"/*.crt; do
            if [[ -f "$cert_file" ]]; then
                local not_after
                not_after=$(openssl x509 -in "$cert_file" -noout -enddate 2>/dev/null | sed 's/notAfter=//')
                
                if [[ -n "$not_after" ]]; then
                    local days_until_expiry
                    days_until_expiry=$(calculate_days_until_expiry "$not_after")
                    
                    if [[ $days_until_expiry -lt -30 ]]; then
                        log_info "Eliminando certificado expirado: $(basename "$cert_file")"
                        rm -f "$cert_file"
                        rm -f "${cert_file%.crt}.key"
                        rm -f "${cert_file%.crt}.chain.crt"
                        ((cleaned_files++))
                    fi
                fi
            fi
        done
    fi
    
    # Limpiar logs de Let's Encrypt antiguos
    if [[ -d "$LETSENCRYPT_DIR/logs" ]]; then
        find "$LETSENCRYPT_DIR/logs" -name "*.log" -mtime +30 -type f | while read -r log_file; do
            rm -f "$log_file"
            log_info "Log antiguo eliminado: $(basename "$log_file")"
            ((cleaned_files++))
        done
    fi
    
    if [[ $cleaned_files -gt 0 ]]; then
        log_success "✅ Cleanup completado: $cleaned_files archivos eliminados"
    else
        log_info "No hay archivos antiguos para limpiar"
    fi
}

show_available_backups() {
    log_info "Backups de certificados disponibles:"
    
    local backups_dir="$CERT_DIR/backups"
    
    if [[ -d "$backups_dir" ]]; then
        find "$backups_dir" -name "cert_backup_*.tar.gz" -type f -printf '%T@ %p\n' | sort -nr | while read -r timestamp path; do
            local backup_name
            local backup_size
            local backup_date
            
            backup_name=$(basename "$path")
            backup_size=$(stat -f%z "$path" 2>/dev/null || stat -c%s "$path" 2>/dev/null || echo "0")
            backup_date=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S')
            
            printf "  %s (%s) - %s\n" "$backup_name" "$(format_size "$backup_size")" "$backup_date"
        done
    else
        echo "  No hay backups disponibles"
    fi
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

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN] [parámetros]

Acciones disponibles:
  renew                    - Renovar certificados SSL (predeterminado)
  install <cert_path>     - Instalar certificado específico
  backup                   - Crear backup de certificados
  restore <backup_path>    - Restaurar desde backup
  status                   - Mostrar estado de certificados
  check                    - Verificar expiración
  generate [tipo]          - Generar certificados auto-firmados
  config                   - Mostrar configuración
  cleanup                  - Limpiar certificados antiguos

Parámetros:
  cert_path               - Ruta al archivo de certificado
  backup_path             - Ruta al archivo de backup
  tipo                    - Tipo de certificado (development|staging|production)

Variables de entorno:
  CERT_DIR               - Directorio de certificados (default: ./certificates)
  RENEWAL_THRESHOLD_DAYS - Días para renovar (default: 30)
  STAGING_SERVER         - Usar Let's Encrypt staging (default: false)
  EMAIL                  - Email para Let's Encrypt (default: admin@example.com)
  DOMAINS                - Lista de dominios (default: localhost,ai-news.local)
  DRY_RUN                - Simulación (default: false)
  FORCE_RENEWAL          - Forzar renovación (default: false)
  AUTO_RELOAD_WEB_SERVER - Recarga automática (default: true)

Ejemplos:
  $0 renew                       # Renovar certificados
  DRY_RUN=true $0 renew         # Modo simulación
  $0 status                      # Ver estado actual
  $0 check                       # Verificar expiración
  $0 generate development       # Generar certificados de desarrollo
  $0 backup                      # Crear backup
  $0 restore cert_backup_2024.tar.gz  # Restaurar backup

Certificados:
  - Let's Encrypt: Renovación automática gratuita
  - Auto-firmados: Para desarrollo y testing
  - Comerciales: Certificados de CA comerciales

EOF
}

# Ejecutar función principal
main "$@"