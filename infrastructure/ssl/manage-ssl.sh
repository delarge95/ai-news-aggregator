#!/bin/bash
# SSL Certificate Management Script for AI News Aggregator
# Version: 1.0.0
# Description: Automated SSL certificate management with Let's Encrypt

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOMAIN="${DOMAIN_NAME:-ai-news-aggregator.com}"
EMAIL="${SSL_EMAIL:-admin@$DOMAIN_NAME}"
LETSENCRYPT_DIR="/etc/letsencrypt/live"
BACKUP_DIR="/opt/ssl-backups"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Check if certbot is installed
check_certbot() {
    if ! command -v certbot &> /dev/null; then
        log_error "Certbot is not installed. Please install it first:"
        echo "sudo apt install certbot python3-certbot-nginx"
        exit 1
    fi
    log_info "Certbot is installed: $(certbot --version)"
}

# Install certbot if not present
install_certbot() {
    if ! command -v certbot &> /dev/null; then
        log_info "Installing Certbot..."
        sudo apt update
        sudo apt install -y certbot python3-certbot-nginx
        log_success "Certbot installed successfully"
    fi
}

# Check domain DNS configuration
check_dns() {
    log_info "Checking DNS configuration for $DOMAIN..."
    
    local resolved_ip
    resolved_ip=$(dig +short "$DOMAIN" | head -1)
    
    if [[ -z "$resolved_ip" ]]; then
        log_error "Domain $DOMAIN does not resolve to an IP address"
        return 1
    fi
    
    log_info "Domain $DOMAIN resolves to: $resolved_ip"
    
    # Check if domain resolves to our server
    local server_ip
    server_ip=$(curl -s ifconfig.me)
    
    if [[ "$resolved_ip" == "$server_ip" ]]; then
        log_success "Domain correctly points to this server"
    else
        log_warning "Domain points to $resolved_ip, but this server IP is $server_ip"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Please update your DNS configuration and run again"
            exit 1
        fi
    fi
}

# Obtain SSL certificates
obtain_certificates() {
    log_info "Obtaining SSL certificates for $DOMAIN..."
    
    local domains=(
        "$DOMAIN"
        "www.$DOMAIN"
        "api.$DOMAIN"
        "admin.$DOMAIN"
        "monitoring.$DOMAIN"
        "prometheus.$DOMAIN"
        "grafana.$DOMAIN"
        "alertmanager.$DOMAIN"
    )
    
    # Create domain list for certbot
    local domain_args=()
    for domain in "${domains[@]}"; do
        domain_args+=("-d" "$domain")
    done
    
    # Request certificates
    sudo certbot certonly \
        --nginx \
        --non-interactive \
        --agree-tos \
        --email "$EMAIL" \
        "${domain_args[@]}"
    
    log_success "SSL certificates obtained successfully"
}

# Setup auto-renewal
setup_auto_renewal() {
    log_info "Setting up automatic certificate renewal..."
    
    # Create renewal hook script
    local hook_script="/etc/letsencrypt/renewal-hooks/post/renew-and-reload.sh"
    sudo tee "$hook_script" > /dev/null << 'EOF'
#!/bin/bash
# Post-renewal hook for AI News Aggregator
# This script runs after certificate renewal

set -e

DOMAIN="ai-news-aggregator.com"
LOG_FILE="/var/log/ssl-renewal.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

log "Starting SSL certificate renewal post-hook"

# Reload nginx if running
if systemctl is-active --quiet nginx; then
    log "Reloading nginx..."
    sudo systemctl reload nginx
fi

# Reload traefik if running
if systemctl is-active --quiet traefik; then
    log "Reloading traefik..."
    sudo systemctl reload traefik
fi

# Update monitoring systems
if [[ -f "/opt/ai-news-aggregator/scripts/ssl-health-check.sh" ]]; then
    log "Running SSL health check..."
    sudo -u deploy /opt/ai-news-aggregator/scripts/ssl-health-check.sh >> "$LOG_FILE" 2>&1
fi

log "SSL certificate renewal post-hook completed"
EOF

    sudo chmod +x "$hook_script"
    
    # Test renewal process
    log_info "Testing renewal process..."
    sudo certbot renew --dry-run
    
    # Add cron job for manual renewal check (in addition to systemd timer)
    (sudo crontab -l 2>/dev/null || echo "") | grep -v "certbot renew" | sudo crontab -
    echo "0 2 * * * /usr/bin/certbot renew --quiet --post-hook '/etc/letsencrypt/renewal-hooks/post/renew-and-reload.sh'" | sudo crontab -
    
    log_success "Auto-renewal configured"
}

# Backup certificates
backup_certificates() {
    log_info "Backing up SSL certificates..."
    
    mkdir -p "$BACKUP_DIR"
    
    local backup_file="$BACKUP_DIR/ssl-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    sudo tar -czf "$backup_file" \
        -C /etc \
        letsencrypt/
    
    sudo chown "$(whoami):$(whoami)" "$backup_file"
    
    # Encrypt backup if encryption key is provided
    if [[ -n "${SSL_ENCRYPTION_KEY:-}" ]]; then
        log_info "Encrypting backup..."
        echo "$SSL_ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 --symmetric --cipher-algo AES256 "$backup_file"
        rm "$backup_file"
        backup_file="$backup_file.enc"
    fi
    
    log_success "Certificate backup created: $backup_file"
    
    # Cleanup old backups (keep last 10)
    find "$BACKUP_DIR" -name "ssl-backup-*.tar.gz*" -type f -mtime +30 -delete
    find "$BACKUP_DIR" -name "ssl-backup-*.tar.gz*" -type f | tail -n +11 | xargs rm -f
}

# Check certificate status
check_certificate_status() {
    log_info "Checking certificate status for $DOMAIN..."
    
    if [[ -f "$LETSENCRYPT_DIR/$DOMAIN/cert.pem" ]]; then
        local cert_info
        cert_info=$(sudo openssl x509 -in "$LETSENCRYPT_DIR/$DOMAIN/cert.pem" -noout -dates -subject -issuer)
        
        echo "Certificate Information:"
        echo "$cert_info" | while read -r line; do
            echo "  $line"
        done
        
        # Check expiration
        local expiry_date
        expiry_date=$(sudo openssl x509 -in "$LETSENCRYPT_DIR/$DOMAIN/cert.pem" -noout -enddate | cut -d= -f2)
        local expiry_epoch
        expiry_epoch=$(date -d "$expiry_date" +%s)
        local current_epoch
        current_epoch=$(date +%s)
        local days_until_expiry
        days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        if [[ $days_until_expiry -lt 7 ]]; then
            log_error "Certificate expires in $days_until_expiry days!"
        elif [[ $days_until_expiry -lt 30 ]]; then
            log_warning "Certificate expires in $days_until_expiry days"
        else
            log_success "Certificate is valid for $days_until_expiry days"
        fi
    else
        log_error "No certificate found for $DOMAIN"
        return 1
    fi
}

# Test SSL configuration
test_ssl_config() {
    log_info "Testing SSL configuration..."
    
    # Test with OpenSSL
    local ssl_test
    ssl_test=$(echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null)
    
    if echo "$ssl_test" | grep -q "Verify return code: 0"; then
        log_success "SSL configuration test passed"
    else
        log_error "SSL configuration test failed"
        echo "$ssl_test"
        return 1
    fi
    
    # Test SSL Labs (requires API key)
    if [[ -n "${SSL_LABS_API_KEY:-}" ]]; then
        log_info "Running SSL Labs test..."
        curl -s "https://api.ssllabs.com/api/v3/analyze?host=$DOMAIN&startNew=on" | \
        jq '.status' 2>/dev/null || log_warning "SSL Labs test requires API key"
    fi
}

# Revoke certificate
revoke_certificate() {
    local domain="$1"
    
    if [[ -z "$domain" ]]; then
        domain="$DOMAIN"
    fi
    
    log_info "Revoking certificate for $domain..."
    
    read -p "Are you sure you want to revoke the certificate for $domain? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo certbot revoke --cert-name "$domain" --delete-keys
        log_success "Certificate revoked successfully"
    else
        log_info "Certificate revocation cancelled"
    fi
}

# Main function
main() {
    local command="${1:-check}"
    
    case "$command" in
        "install")
            install_certbot
            ;;
        "check")
            check_certbot
            check_dns
            check_certificate_status
            test_ssl_config
            ;;
        "obtain")
            check_certbot
            check_dns
            obtain_certificates
            setup_auto_renewal
            ;;
        "renew")
            log_info "Attempting to renew certificates..."
            sudo certbot renew --quiet --post-hook "systemctl reload nginx traefik"
            ;;
        "renewal-test")
            log_info "Testing renewal process..."
            sudo certbot renew --dry-run
            ;;
        "backup")
            backup_certificates
            ;;
        "status")
            check_certificate_status
            ;;
        "test")
            test_ssl_config
            ;;
        "revoke")
            revoke_certificate "$2"
            ;;
        "setup-auto-renewal")
            setup_auto_renewal
            ;;
        *)
            echo "Usage: $0 {install|check|obtain|renew|renewal-test|backup|status|test|revoke|setup-auto-renewal}"
            echo
            echo "Commands:"
            echo "  install            - Install certbot"
            echo "  check              - Check certificate status and test configuration"
            echo "  obtain             - Obtain new SSL certificates"
            echo "  renew              - Renew existing certificates"
            echo "  renewal-test       - Test renewal process"
            echo "  backup             - Backup SSL certificates"
            echo "  status             - Show certificate status"
            echo "  test               - Test SSL configuration"
            echo "  revoke [domain]    - Revoke certificate"
            echo "  setup-auto-renewal - Configure automatic renewal"
            echo
            echo "Environment variables:"
            echo "  DOMAIN_NAME        - Domain name (default: ai-news-aggregator.com)"
            echo "  SSL_EMAIL          - Email for certificate registration"
            echo "  SSL_ENCRYPTION_KEY - Key for encrypting backups"
            echo "  SSL_LABS_API_KEY   - SSL Labs API key for testing"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"