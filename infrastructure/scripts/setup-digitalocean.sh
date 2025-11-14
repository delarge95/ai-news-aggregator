#!/bin/bash
# AI News Aggregator - DigitalOcean Infrastructure Setup Script
# Version: 1.0.0
# Description: Automated infrastructure provisioning and configuration

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
INFRA_DIR="$PROJECT_ROOT/infrastructure"
LOG_FILE="/tmp/ai-news-setup-$(date +%Y%m%d-%H%M%S).log"

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
    log "${GREEN}[SUCCESS]${NC} $1"
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

# Function to check dependencies
check_dependencies() {
    log_header "Checking Dependencies"
    
    local deps=("terraform" "ansible" "docker" "curl" "git")
    
    for dep in "${deps[@]}"; do
        if command -v "$dep" >/dev/null 2>&1; then
            version=$(${dep} --version 2>/dev/null | head -n1 || echo "unknown")
            log_success "$dep is installed: $version"
        else
            log_error "$dep is not installed"
            return 1
        fi
    done
    
    log_info "Checking DigitalOcean CLI..."
    if command -v doctl >/dev/null 2>&1; then
        log_success "doctl is installed"
    else
        log_warning "doctl not found - will use Terraform API only"
    fi
}

# Function to validate configuration
validate_config() {
    log_header "Validating Configuration"
    
    local required_vars=("DO_TOKEN" "DOMAIN_NAME" "ENVIRONMENT")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        printf '   %s\n' "${missing_vars[@]}"
        log_info "Please set: export $var=value"
        return 1
    fi
    
    log_success "Configuration validation passed"
    
    # Display configuration
    log_info "Environment: $ENVIRONMENT"
    log_info "Domain: $DOMAIN_NAME"
    log_info "Region: ${DO_REGION:-nyc3}"
}

# Function to generate SSH keys if needed
setup_ssh_keys() {
    log_header "Setting Up SSH Keys"
    
    local key_path="${SSH_KEY_PATH:-$HOME/.ssh/ai-news-$ENVIRONMENT}"
    
    if [[ ! -f "$key_path" ]]; then
        log_info "Generating SSH key pair: $key_path"
        ssh-keygen -t ed25519 -f "$key_path" -N "" -C "ai-news-$ENVIRONMENT@$(hostname)"
        chmod 600 "$key_path"
        chmod 644 "$key_path.pub"
        
        log_success "SSH key pair generated"
        log_info "Public key: $key_path.pub"
        
        # Optionally upload to DigitalOcean (requires doctl)
        if command -v doctl >/dev/null 2>&1; then
            read -p "Upload SSH key to DigitalOcean? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                doctl compute ssh-key import "ai-news-$ENVIRONMENT-$(date +%Y%m%d)" --public-key-file "$key_path.pub"
                log_success "SSH key uploaded to DigitalOcean"
            fi
        fi
    else
        log_success "SSH key pair already exists: $key_path"
    fi
    
    export SSH_PRIVATE_KEY="$key_path"
    export SSH_PUBLIC_KEY="$key_path.pub"
}

# Function to setup Terraform
setup_terraform() {
    log_header "Setting Up Terraform"
    
    cd "$INFRA_DIR/terraform"
    
    # Create terraform.tfvars if it doesn't exist
    if [[ ! -f terraform.tfvars ]]; then
        log_info "Creating terraform.tfvars from example..."
        cp terraform.tfvars.example terraform.tfvars
        
        # Update with environment variables
        sed -i "s/DO_${ENVIRONMENT^^}_TOKEN/$DO_TOKEN/g" terraform.tfvars
        sed -i "s/example\.com/$DOMAIN_NAME/g" terraform.tfvars
        sed -i "s/\~/.ssh/\/home\/$USER\/.ssh/g" terraform.tfvars
        
        log_info "Please review terraform.tfvars and adjust as needed"
        read -p "Continue with Terraform setup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Edit terraform.tfvars and run this script again"
            return 1
        fi
    fi
    
    # Initialize Terraform
    log_info "Initializing Terraform..."
    terraform init
    
    # Validate configuration
    log_info "Validating Terraform configuration..."
    terraform validate
    
    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    read -p "Apply Terraform plan? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Apply manually with: terraform apply tfplan"
        return 0
    fi
    
    # Apply configuration
    log_info "Applying Terraform configuration..."
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > terraform-outputs.json
    log_success "Terraform deployment completed"
    
    # Parse outputs for later use
    source <(terraform output -json | jq -r 'to_entries | .[] | "export \(.key)='\''\(.value.value)'\''"')
}

# Function to setup Ansible
setup_ansible() {
    log_header "Setting Up Ansible"
    
    cd "$INFRA_DIR/ansible"
    
    # Create .vault-pass.txt if using Ansible Vault
    if [[ ! -f .vault-pass.txt ]]; then
        log_info "Creating Ansible vault password file..."
        openssl rand -base64 32 > .vault-pass.txt
        chmod 600 .vault-pass.txt
        log_warning "Store .vault-pass.txt securely for future Ansible runs"
    fi
    
    # Test Ansible connectivity
    log_info "Testing Ansible connectivity..."
    if [[ -n "${web_droplet_ips:-}" ]]; then
        for ip in $web_droplet_ips; do
            log_info "Testing connection to $ip..."
            ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$SSH_USER@$ip" "echo 'Connection successful'" || {
                log_warning "Could not connect to $ip - you may need to add the SSH key to the droplet"
            }
        done
    fi
    
    # Run Ansible playbook
    log_info "Running Ansible configuration..."
    ansible-playbook -i inventory/inventory.yml \
                     --vault-password-file=.vault-pass.txt \
                     playbooks/site.yml
    
    log_success "Ansible configuration completed"
}

# Function to setup monitoring
setup_monitoring() {
    log_header "Setting Up Monitoring"
    
    if [[ ! -f "$INFRA_DIR/monitoring/docker-compose.yml" ]]; then
        log_info "Setting up monitoring infrastructure..."
        mkdir -p "$INFRA_DIR/monitoring"
        
        # Create basic monitoring setup
        cat > "$INFRA_DIR/monitoring/docker-compose.yml" << 'EOF'
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
  
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  prometheus_data:
  grafana_data:
EOF
        
        # Create Prometheus configuration
        mkdir -p "$INFRA_DIR/monitoring/prometheus"
        cat > "$INFRA_DIR/monitoring/prometheus/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
    scrape_interval: 5s
EOF
    fi
    
    log_success "Monitoring setup completed"
}

# Function to setup SSL certificates
setup_ssl() {
    log_header "Setting Up SSL Certificates"
    
    log_info "SSL certificates will be obtained by Ansible during configuration"
    log_info "Domain: $DOMAIN_NAME"
    log_info "Email: ${SSL_EMAIL:-admin@$DOMAIN_NAME}"
    
    if [[ "${SSL_AUTO_RENEWAL:-true}" == "true" ]]; then
        log_success "SSL auto-renewal will be configured"
    fi
}

# Function to run health checks
run_health_checks() {
    log_header "Running Health Checks"
    
    # Check web servers
    if [[ -n "${load_balancer_ip:-}" ]]; then
        log_info "Testing load balancer at $load_balancer_ip..."
        if curl -f -s "http://$load_balancer_ip/health" >/dev/null; then
            log_success "Load balancer health check passed"
        else
            log_warning "Load balancer health check failed"
        fi
    fi
    
    # Check monitoring
    if [[ -n "${monitoring_droplet_ip:-}" ]]; then
        log_info "Testing monitoring at $monitoring_droplet_ip..."
        if curl -f -s "http://$monitoring_droplet_ip:9090/-/healthy" >/dev/null; then
            log_success "Prometheus health check passed"
        else
            log_warning "Prometheus health check failed"
        fi
        
        if curl -f -s "http://$monitoring_droplet_ip:3000/api/health" >/dev/null; then
            log_success "Grafana health check passed"
        else
            log_warning "Grafana health check failed"
        fi
    fi
    
    # Check SSL certificates
    if [[ -n "$DOMAIN_NAME" ]]; then
        log_info "Testing SSL certificate for $DOMAIN_NAME..."
        if echo | openssl s_client -connect "$DOMAIN_NAME:443" -servername "$DOMAIN_NAME" 2>/dev/null | grep -q "Verify return code: 0"; then
            log_success "SSL certificate verification passed"
        else
            log_warning "SSL certificate verification failed"
        fi
    fi
}

# Function to display summary
display_summary() {
    log_header "Setup Summary"
    
    log_success "AI News Aggregator infrastructure setup completed!"
    echo
    log_info "Environment: $ENVIRONMENT"
    log_info "Domain: $DOMAIN_NAME"
    
    if [[ -n "${load_balancer_ip:-}" ]]; then
        log_info "Application URL: https://$DOMAIN_NAME"
        log_info "Load Balancer IP: $load_balancer_ip"
    fi
    
    if [[ -n "${monitoring_droplet_ip:-}" ]]; then
        log_info "Monitoring: http://$monitoring_droplet_ip:3000 (Grafana)"
        log_info "Prometheus: http://$monitoring_droplet_ip:9090"
    fi
    
    if [[ -n "${database_host:-}" ]]; then
        log_info "Database: $database_host"
    fi
    
    echo
    log_info "Logs saved to: $LOG_FILE"
    log_info "Configuration files:"
    echo "  - Terraform: $INFRA_DIR/terraform/terraform.tfvars"
    echo "  - Ansible: $INFRA_DIR/ansible/inventory/inventory.yml"
    echo "  - Monitoring: $INFRA_DIR/monitoring/docker-compose.yml"
    
    echo
    log_warning "Next steps:"
    echo "  1. Deploy application code using the deployment scripts"
    echo "  2. Configure DNS records to point to the load balancer"
    echo "  3. Set up backup schedules"
    echo "  4. Configure monitoring alerts"
    echo "  5. Review security settings"
}

# Function to cleanup on exit
cleanup() {
    local exit_code=$?
    log_info "Cleaning up..."
    # Add cleanup logic here if needed
    exit $exit_code
}

# Main execution
main() {
    log_header "AI News Aggregator - DigitalOcean Infrastructure Setup"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Check if running as correct user
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root - this is not recommended"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-validation)
                SKIP_VALIDATION=true
                shift
                ;;
            --skip-terraform)
                SKIP_TERRAFORM=true
                shift
                ;;
            --skip-ansible)
                SKIP_ANSIBLE=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-validation    Skip configuration validation"
                echo "  --skip-terraform     Skip Terraform deployment"
                echo "  --skip-ansible       Skip Ansible configuration"
                echo "  --help               Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute setup steps
    if [[ "${SKIP_VALIDATION:-false}" != "true" ]]; then
        check_dependencies || exit 1
        validate_config || exit 1
    fi
    
    setup_ssh_keys || exit 1
    
    if [[ "${SKIP_TERRAFORM:-false}" != "true" ]]; then
        setup_terraform || exit 1
    fi
    
    if [[ "${SKIP_ANSIBLE:-false}" != "true" ]]; then
        setup_ansible || exit 1
    fi
    
    setup_monitoring
    setup_ssl
    run_health_checks
    display_summary
    
    log_success "Setup completed successfully!"
}

# Execute main function
main "$@"