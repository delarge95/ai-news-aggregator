#!/bin/bash
# DNS Management Script for AI News Aggregator
# Version: 1.0.0
# Description: Automated DNS record management

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOMAIN="${DOMAIN_NAME:-ai-news-aggregator.com}"
DIGITALOCEAN_TOKEN="${DO_TOKEN:-}"
DNS_CONFIG="$SCRIPT_DIR/zone-file-template.txt"

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

# Check dependencies
check_dependencies() {
    if ! command -v doctl >/dev/null 2>&1; then
        log_error "DigitalOcean CLI (doctl) is not installed"
        log_info "Install it from: https://docs.digitalocean.com/reference/doctl/how-to/install/"
        exit 1
    fi
    
    if ! command -v dig >/dev/null 2>&1; then
        log_warning "dig command not found, installing dnsutils..."
        sudo apt update && sudo apt install -y dnsutils
    fi
    
    log_info "Dependencies check completed"
}

# Authenticate with DigitalOcean
authenticate() {
    if [[ -z "$DIGITALOCEAN_TOKEN" ]]; then
        log_info "DigitalOcean token not found in environment"
        if [[ -f ~/.config/doctl/config.yaml ]]; then
            log_info "Using existing doctl configuration"
        else
            log_info "Authenticating with DigitalOcean..."
            doctl auth init
        fi
    else
        log_info "Using token from environment"
        export DIGITALOCEAN_TOKEN
    fi
}

# Create domain
create_domain() {
    log_info "Creating domain $DOMAIN in DigitalOcean..."
    
    doctl compute domain create "$DOMAIN"
    log_success "Domain $DOMAIN created successfully"
}

# Add A record
add_a_record() {
    local subdomain="$1"
    local ip_address="$2"
    
    log_info "Adding A record: $subdomain.$DOMAIN -> $ip_address"
    
    doctl compute domain records create "$DOMAIN" \
        --record-type A \
        --record-name "$subdomain" \
        --record-data "$ip_address"
    
    log_success "A record added: $subdomain.$DOMAIN"
}

# Add CNAME record
add_cname_record() {
    local subdomain="$1"
    local target="$2"
    
    log_info "Adding CNAME record: $subdomain.$DOMAIN -> $target"
    
    doctl compute domain records create "$DOMAIN" \
        --record-type CNAME \
        --record-name "$subdomain" \
        --record-data "$target"
    
    log_success "CNAME record added: $subdomain.$DOMAIN"
}

# Add TXT record
add_txt_record() {
    local name="$1"
    local value="$2"
    
    log_info "Adding TXT record: $name.$DOMAIN -> $value"
    
    doctl compute domain records create "$DOMAIN" \
        --record-type TXT \
        --record-name "$name" \
        --record-data "$value"
    
    log_success "TXT record added: $name.$DOMAIN"
}

# Add MX record
add_mx_record() {
    local priority="$1"
    local target="$2"
    
    log_info "Adding MX record: $DOMAIN -> $target (priority $priority)"
    
    doctl compute domain records create "$DOMAIN" \
        --record-type MX \
        --record-name "@" \
        --record-data "$target" \
        --record-priority "$priority"
    
    log_success "MX record added"
}

# Add NS record
add_ns_record() {
    local target="$2"
    
    log_info "Adding NS record: $DOMAIN -> $target"
    
    doctl compute domain records create "$DOMAIN" \
        --record-type NS \
        --record-name "@" \
        --record-data "$target"
    
    log_success "NS record added"
}

# Delete record
delete_record() {
    local record_id="$1"
    
    log_info "Deleting record ID: $record_id"
    
    doctl compute domain records delete "$DOMAIN" "$record_id" --force
    
    log_success "Record deleted: $record_id"
}

# List DNS records
list_records() {
    log_info "DNS records for $DOMAIN:"
    echo
    
    doctl compute domain records list "$DOMAIN" --format "ID,Type,Name,Data,Priority" --no-header | \
    while IFS= read -r line; do
        echo "  $line"
    done
}

# Check DNS propagation
check_dns_propagation() {
    local record_name="$1"
    
    log_info "Checking DNS propagation for $record_name.$DOMAIN"
    
    local servers=(
        "8.8.8.8"      # Google
        "1.1.1.1"      # Cloudflare
        "208.67.222.222" # OpenDNS
    )
    
    for server in "${servers[@]}"; do
        log_info "Checking from DNS server: $server"
        dig @"$server" "$record_name.$DOMAIN" +short
    done
}

# Verify DNS configuration
verify_dns() {
    log_info "Verifying DNS configuration for $DOMAIN..."
    
    # Check A record
    local resolved_ip
    resolved_ip=$(dig +short "$DOMAIN" | head -1)
    
    if [[ -n "$resolved_ip" ]]; then
        log_success "Domain resolves to: $resolved_ip"
    else
        log_warning "Domain does not resolve to an IP address"
    fi
    
    # Check www subdomain
    local www_ip
    www_ip=$(dig +short "www.$DOMAIN" | head -1)
    
    if [[ -n "$www_ip" ]]; then
        log_success "www subdomain resolves to: $www_ip"
    else
        log_warning "www subdomain does not resolve"
    fi
    
    # Check MX record
    local mx_record
    mx_record=$(dig +short "$DOMAIN" MX | head -1)
    
    if [[ -n "$mx_record" ]]; then
        log_success "MX record: $mx_record"
    else
        log_info "No MX record found (optional)"
    fi
    
    # Check TXT records
    local spf_record
    spf_record=$(dig +short "$DOMAIN" TXT | grep "v=spf1")
    
    if [[ -n "$spf_record" ]]; then
        log_success "SPF record found"
    else
        log_info "No SPF record found (optional)"
    fi
}

# Generate DNS configuration report
generate_report() {
    local report_file="/tmp/dns-report-$(date +%Y%m%d-%H%M%S).txt"
    
    log_info "Generating DNS configuration report: $report_file"
    
    cat > "$report_file" << EOF
AI News Aggregator - DNS Configuration Report
============================================
Domain: $DOMAIN
Generated: $(date)

DNS Records:
$(doctl compute domain records list "$DOMAIN" --format "ID,Type,Name,Data,Priority" --no-header)

DNS Propagation Check:
====================

Main Domain:
$(dig +short "$DOMAIN")

WWW Subdomain:
$(dig +short "www.$DOMAIN")

API Subdomain:
$(dig +short "api.$DOMAIN")

MX Record:
$(dig +short "$DOMAIN" MX)

TXT Records:
$(dig +short "$DOMAIN" TXT)

NS Records:
$(dig +short "$DOMAIN" NS)

DNS Servers:
$(dig +short "$DOMAIN" NS)

External DNS Check:
=================
Cloudflare: https://www.cloudflare.com/dns
Google DNS: https://dns.google
OpenDNS: https://dnschecker.org
EOF

    log_success "DNS report saved to: $report_file"
}

# Backup DNS configuration
backup_dns() {
    local backup_file="/tmp/dns-backup-$(date +%Y%m%d-%H%M%S).json"
    
    log_info "Backing up DNS configuration to: $backup_file"
    
    doctl compute domain records list "$DOMAIN" --format json > "$backup_file"
    
    log_success "DNS configuration backed up"
}

# Load DNS records from configuration file
load_from_config() {
    local config_file="${1:-$DNS_CONFIG}"
    
    log_info "Loading DNS records from configuration file: $config_file"
    
    if [[ ! -f "$config_file" ]]; then
        log_error "Configuration file not found: $config_file"
        return 1
    fi
    
    # Parse A records
    grep -E "^[a-zA-Z0-9.-]+.*IN.*A.*" "$config_file" | while read -r line; do
        local name
        local ip
        name=$(echo "$line" | awk '{print $1}' | sed 's/\.$//')
        ip=$(echo "$line" | awk '{print $4}')
        
        if [[ "$name" != "@" ]] && [[ -n "$ip" ]]; then
            log_info "Would add A record: $name.$DOMAIN -> $ip"
        fi
    done
    
    log_info "Review the above records and run specific commands to add them"
}

# Main function
main() {
    local command="${1:-check}"
    
    case "$command" in
        "setup")
            check_dependencies
            authenticate
            create_domain
            ;;
        "check")
            check_dependencies
            verify_dns
            ;;
        "list")
            check_dependencies
            authenticate
            list_records
            ;;
        "add-a")
            check_dependencies
            authenticate
            add_a_record "$2" "$3"
            ;;
        "add-cname")
            check_dependencies
            authenticate
            add_cname_record "$2" "$3"
            ;;
        "add-txt")
            check_dependencies
            authenticate
            add_txt_record "$2" "$3"
            ;;
        "add-mx")
            check_dependencies
            authenticate
            add_mx_record "$2" "$3"
            ;;
        "delete")
            check_dependencies
            authenticate
            delete_record "$2"
            ;;
        "propagation")
            check_dns_propagation "${2:-www}"
            ;;
        "verify")
            verify_dns
            ;;
        "report")
            check_dependencies
            authenticate
            generate_report
            ;;
        "backup")
            check_dependencies
            authenticate
            backup_dns
            ;;
        "load-config")
            load_from_config "$2"
            ;;
        *)
            echo "Usage: $0 {setup|check|list|add-a|add-cname|add-txt|add-mx|delete|propagation|verify|report|backup|load-config} [args]"
            echo
            echo "Commands:"
            echo "  setup              - Set up domain and basic records"
            echo "  check              - Check DNS configuration"
            echo "  list               - List all DNS records"
            echo "  add-a <name> <ip>  - Add A record"
            echo "  add-cname <name> <target> - Add CNAME record"
            echo "  add-txt <name> <value>    - Add TXT record"
            echo "  add-mx <priority> <target> - Add MX record"
            echo "  delete <record_id> - Delete DNS record"
            echo "  propagation [name] - Check DNS propagation"
            echo "  verify             - Verify DNS configuration"
            echo "  report             - Generate DNS report"
            echo "  backup             - Backup DNS configuration"
            echo "  load-config [file] - Load records from config file"
            echo
            echo "Environment variables:"
            echo "  DOMAIN_NAME        - Domain name"
            echo "  DO_TOKEN          - DigitalOcean API token"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"