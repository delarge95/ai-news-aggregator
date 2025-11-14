#!/bin/bash
# Script de configuración de Firewall para AI News Aggregator
# Configuración de iptables/ufw para seguridad de red

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración de puertos
HTTP_PORT=80
HTTPS_PORT=443
SSH_PORT=22
API_PORT=8000
FRONTEND_PORT=3000
DB_PORT=5432
REDIS_PORT=6379

# Configuración de redes permitidas
ALLOWED_IPS_PRODUCTION=(
    "192.168.1.0/24"     # Red local
    "10.0.0.0/8"         # Red interna
    "172.16.0.0/12"      # Red Docker
)

ALLOWED_IPS_ADMIN=(
    "192.168.1.10"       # Admin desde IP específica
    "10.0.0.5"           # Admin desde red interna
)

# Países bloqueados (opcional)
BLOCKED_COUNTRIES=(
    "CN"  # China
    "RU"  # Rusia
    "KP"  # Corea del Norte
)

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

# Verificar privilegios de root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "Este script debe ejecutarse como root"
    fi
}

# Limpiar reglas existentes
clear_existing_rules() {
    log "Limpiando reglas existentes..."
    
    # Flush iptables
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
    iptables -t mangle -F
    iptables -t mangle -X
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    
    # Configurar ufw si está disponible
    if command -v ufw &> /dev/null; then
        ufw --force reset
    fi
}

# Configurar políticas por defecto
set_default_policies() {
    log "Configurando políticas por defecto..."
    
    # Políticas por defecto
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT
    
    # Permitir tráfico loopback
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT
    
    # Permitir conexiones establecidas y relacionadas
    iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
}

# Permitir SSH desde IPs específicas
allow_ssh_from_ips() {
    log "Configurando acceso SSH..."
    
    for ip in "${ALLOWED_IPS_ADMIN[@]}"; do
        iptables -A INPUT -p tcp -s "$ip" --dport "$SSH_PORT" -j ACCEPT
        log "SSH permitido desde: $ip"
    done
    
    # Permitir SSH desde la misma red
    iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport "$SSH_PORT" -j ACCEPT
}

# Permitir HTTP/HTTPS
allow_web_traffic() {
    log "Configurando tráfico web..."
    
    # HTTP
    iptables -A INPUT -p tcp --dport "$HTTP_PORT" -j ACCEPT
    
    # HTTPS
    iptables -A INPUT -p tcp --dport "$HTTPS_PORT" -j ACCEPT
    
    # Permitir HTTP/HTTPS desde subredes internas
    for subnet in "${ALLOWED_IPS_PRODUCTION[@]}"; do
        iptables -A INPUT -p tcp -s "$subnet" --dport "$HTTP_PORT" -j ACCEPT
        iptables -A INPUT -p tcp -s "$subnet" --dport "$HTTPS_PORT" -j ACCEPT
    done
}

# Permitir acceso a API interna
allow_internal_api() {
    log "Configurando acceso a API interna..."
    
    # API desde red interna
    iptables -A INPUT -p tcp -s "${ALLOWED_IPS_PRODUCTION[@]}" --dport "$API_PORT" -j ACCEPT
    
    # Frontend desde red interna
    iptables -A INPUT -p tcp -s "${ALLOWED_IPS_PRODUCTION[@]}" --dport "$FRONTEND_PORT" -j ACCEPT
    
    # Base de datos (solo desde red interna)
    iptables -A INPUT -p tcp -s "${ALLOWED_IPS_PRODUCTION[@]}" --dport "$DB_PORT" -j ACCEPT
    
    # Redis (solo desde red interna)
    iptables -A INPUT -p tcp -s "${ALLOWED_IPS_PRODUCTION[@]}" --dport "$REDIS_PORT" -j ACCEPT
}

# Protección contra ping flood
protect_ping() {
    log "Configurando protección contra ping flood..."
    
    # Limitar ICMP
    iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT
    iptables -A INPUT -p icmp --icmp-type echo-request -j DROP
}

# Protección contra port scanning
protect_port_scanning() {
    log "Configurando protección contra port scanning..."
    
    # Bloquear paquetes TCP con flags inusuales
    iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
    iptables -A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP
    iptables -A INPUT -p tcp --tcp-flags SYN,RST SYN,RST -j DROP
    iptables -A INPUT -p tcp --tcp-flags FIN,RST FIN,RST -j DROP
    iptables -A INPUT -p tcp --tcp-flags ACK,FIN FIN -j DROP
    
    # Log de paquetes descartados (opcional)
    # iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables denied: "
}

# Rate limiting para conexiones
add_rate_limiting() {
    log "Configurando rate limiting..."
    
    # Limitar nuevas conexiones TCP por IP
    iptables -A INPUT -p tcp -m connlimit --connlimit-above 20 -j REJECT
    
    # Rate limiting específico para SSH
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -m conntrack --ctstate NEW -m recent --set
    iptables -A INPUT -p tcp --dport "$SSH_PORT" -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 -j DROP
    
    # Rate limiting para HTTP/HTTPS
    iptables -A INPUT -p tcp --dport "$HTTP_PORT" -m conntrack --ctstate NEW -m recent --set
    iptables -A INPUT -p tcp --dport "$HTTP_PORT" -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 20 -j DROP
    
    iptables -A INPUT -p tcp --dport "$HTTPS_PORT" -m conntrack --ctstate NEW -m recent --set
    iptables -A INPUT -p tcp --dport "$HTTPS_PORT" -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 20 -j DROP
}

# Bloquear países específicos
block_countries() {
    log "Configurando bloqueo por países..."
    
    for country in "${BLOCKED_COUNTRIES[@]}"; do
        # Bloquear todo el tráfico desde países especificados
        iptables -A INPUT -m geoip --src-cc "$country" -j DROP
        log "Bloqueado tráfico desde: $country"
    done
}

# Configurar fail2ban (si está disponible)
setup_fail2ban() {
    if command -v fail2ban-client &> /dev/null; then
        log "Configurando fail2ban..."
        
        # Configurar jail para SSH
        cat > /etc/fail2ban/jail.local <<EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 1800
findtime = 600

[nginx-noscript]
enabled = true
filter = nginx-noscript
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 86400
findtime = 600
EOF
        
        systemctl restart fail2ban
        log "Fail2ban configurado"
    else
        warning "Fail2ban no está instalado"
    fi
}

# Configurar ufw como alternativa
setup_ufw() {
    if command -v ufw &> /dev/null; then
        log "Configurando ufw..."
        
        # Políticas por defecto
        ufw default deny incoming
        ufw default allow outgoing
        
        # Permitir SSH
        ufw allow "$SSH_PORT/tcp" from "${ALLOWED_IPS_ADMIN[@]}"
        
        # Permitir HTTP/HTTPS
        ufw allow "$HTTP_PORT/tcp"
        ufw allow "$HTTPS_PORT/tcp"
        
        # Activar firewall
        ufw --force enable
        log "UFW configurado y activado"
    fi
}

# Guardar reglas de iptables
save_iptables_rules() {
    log "Guardando reglas de iptables..."
    
    # Instalar iptables-persistent si no está disponible
    if ! dpkg -l | grep -q iptables-persistent; then
        apt-get update
        apt-get install -y iptables-persistent
    fi
    
    # Guardar reglas
    iptables-save > /etc/iptables/rules.v4
    
    log "Reglas guardadas en /etc/iptables/rules.v4"
}

# Mostrar estado del firewall
show_firewall_status() {
    log "Estado actual del firewall:"
    echo -e "${BLUE}=== Reglas INPUT ===${NC}"
    iptables -L INPUT --line-numbers -v
    
    echo -e "${BLUE}=== Estadísticas ===${NC}"
    iptables -L -n -v | head -20
}

# Crear script de inicio automático
create_startup_script() {
    log "Creando script de inicio automático..."
    
    cat > /etc/systemd/system/firewall.service <<EOF
[Unit]
Description=AI News Aggregator Firewall
After=network.target
Wants=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/setup-firewall.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    
    # Hacer ejecutable
    chmod +x /etc/systemd/system/firewall.service
    
    # Crear script de configuración
    cat > /usr/local/bin/setup-firewall.sh <<'EOF'
#!/bin/bash
# Script de configuración del firewall
# Cargar reglas guardadas si existen, sino aplicar reglas básicas

if [[ -f /etc/iptables/rules.v4 ]]; then
    iptables-restore < /etc/iptables/rules.v4
else
    # Aplicar reglas básicas
    echo "Aplicando reglas básicas del firewall..."
    # Aquí irían las reglas básicas
fi
EOF
    
    chmod +x /usr/local/bin/setup-firewall.sh
    
    # Habilitar servicio
    systemctl daemon-reload
    systemctl enable firewall.service
    systemctl start firewall.service
    
    log "Servicio de firewall configurado"
}

# Función principal
main() {
    log "=== Configurando Firewall para AI News Aggregator ==="
    
    # Verificar privilegios
    check_root
    
    # Seleccionar método de configuración
    echo "Seleccione método de configuración:"
    echo "1) iptables (recomendado)"
    echo "2) ufw (más simple)"
    echo "3) Solo mostrar reglas sin aplicar"
    read -p "Opción [1-3]: " choice
    
    case "$choice" in
        1)
            log "Configurando con iptables..."
            clear_existing_rules
            set_default_policies
            allow_ssh_from_ips
            allow_web_traffic
            allow_internal_api
            protect_ping
            protect_port_scanning
            add_rate_limiting
            block_countries
            save_iptables_rules
            setup_fail2ban
            create_startup_script
            ;;
        2)
            log "Configurando con ufw..."
            setup_ufw
            setup_fail2ban
            ;;
        3)
            log "Mostrando estado actual sin modificar..."
            show_firewall_status
            exit 0
            ;;
        *)
            error "Opción inválida"
            ;;
    esac
    
    # Mostrar estado final
    show_firewall_status
    
    log "=== Configuración del Firewall completada ==="
    
    info "Para ver las reglas guardadas: cat /etc/iptables/rules.v4"
    info "Para activar fail2ban: systemctl enable --now fail2ban"
    info "Para monitorear logs: tail -f /var/log/fail2ban.log"
}

# Verificar argumentos
if [[ $# -gt 0 ]]; then
    case "$1" in
        "--help"|"-h")
            echo "Configuración de Firewall para AI News Aggregator"
            echo "Uso: $0 [opciones]"
            echo "Opciones:"
            echo "  --help, -h    Mostrar ayuda"
            exit 0
            ;;
    esac
fi

# Ejecutar función principal
main "$@"