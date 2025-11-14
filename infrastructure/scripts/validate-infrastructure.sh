#!/bin/bash
# AI News Aggregator - Infrastructure Validation Script
# Version: 1.0.0
# Description: Validates complete infrastructure setup

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
INFRA_DIR="$PROJECT_ROOT/infrastructure"

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

log_success() {
    log "${GREEN}[✓]${NC} $1"
}

log_error() {
    log "${RED}[✗]${NC} $1"
}

log_warning() {
    log "${YELLOW}[!]${NC} $1"
}

log_info() {
    log "${BLUE}[i]${NC} $1"
}

# Validation counters
total_checks=0
passed_checks=0
failed_checks=0

# Validation function
validate() {
    local name="$1"
    local command="$2"
    
    ((total_checks++))
    
    if eval "$command" >/dev/null 2>&1; then
        log_success "$name"
        ((passed_checks++))
        return 0
    else
        log_error "$name"
        ((failed_checks++))
        return 1
    fi
}

# Check directory structure
check_structure() {
    log_info "Validando estructura de directorios..."
    
    validate "Directorio terraform existe" "[[ -d '$INFRA_DIR/terraform' ]]"
    validate "Directorio ansible existe" "[[ -d '$INFRA_DIR/ansible' ]]"
    validate "Directorio scripts existe" "[[ -d '$INFRA_DIR/scripts' ]]"
    validate "Directorio monitoring existe" "[[ -d '$INFRA_DIR/monitoring' ]]"
    validate "Directorio ssl existe" "[[ -d '$INFRA_DIR/ssl' ]]"
    validate "Directorio dns existe" "[[ -d '$INFRA_DIR/dns' ]]"
}

# Check Terraform files
check_terraform() {
    log_info "Validando archivos de Terraform..."
    
    local tf_dir="$INFRA_DIR/terraform"
    
    validate "main.tf existe" "[[ -f '$tf_dir/main.tf' ]]"
    validate "droplets.tf existe" "[[ -f '$tf_dir/droplets.tf' ]]"
    validate "dns.tf existe" "[[ -f '$tf_dir/dns.tf' ]]"
    validate "monitoring.tf existe" "[[ -f '$tf_dir/monitoring.tf' ]]"
    validate "outputs.tf existe" "[[ -f '$tf_dir/outputs.tf' ]]"
    validate "terraform.tfvars.example existe" "[[ -f '$tf_dir/terraform.tfvars.example' ]]"
    validate ".gitignore existe" "[[ -f '$tf_dir/.gitignore' ]]"
}

# Check Ansible files
check_ansible() {
    log_info "Validando archivos de Ansible..."
    
    local ansible_dir="$INFRA_DIR/ansible"
    
    validate "site.yml existe" "[[ -f '$ansible_dir/playbooks/site.yml' ]]"
    validate "inventory.yml existe" "[[ -f '$ansible_dir/inventory/inventory.yml' ]]"
    validate "ansible.cfg existe" "[[ -f '$ansible_dir/ansible.cfg' ]]"
    validate "role docker existe" "[[ -d '$ansible_dir/roles/docker' ]]"
    validate "role nginx existe" "[[ -d '$ansible_dir/roles/nginx' ]]"
    validate "role ssl existe" "[[ -d '$ansible_dir/roles/ssl' ]]"
}

# Check monitoring files
check_monitoring() {
    log_info "Validando archivos de monitoreo..."
    
    local monitoring_dir="$INFRA_DIR/monitoring"
    
    validate "prometheus.yml existe" "[[ -f '$monitoring_dir/prometheus.yml' ]]"
    validate "alert_rules.yml existe" "[[ -f '$monitoring_dir/alert_rules.yml' ]]"
    validate "recording_rules.yml existe" "[[ -f '$monitoring_dir/recording_rules.yml' ]]"
    validate "alertmanager.yml existe" "[[ -f '$monitoring_dir/alertmanager.yml' ]]"
    validate "datasources.yml existe" "[[ -f '$monitoring_dir/datasources.yml' ]]"
    validate "docker-compose.yml existe" "[[ -f '$monitoring_dir/docker-compose.yml' ]]"
}

# Check SSL files
check_ssl() {
    log_info "Validando archivos SSL..."
    
    local ssl_dir="$INFRA_DIR/ssl"
    
    validate "traefik.yml existe" "[[ -f '$ssl_dir/traefik.yml' ]]"
    validate "dynamic.yml existe" "[[ -f '$ssl_dir/dynamic.yml' ]]"
    validate "manage-ssl.sh existe" "[[ -f '$ssl_dir/manage-ssl.sh' ]]"
}

# Check DNS files
check_dns() {
    log_info "Validando archivos DNS..."
    
    local dns_dir="$INFRA_DIR/dns"
    
    validate "zone-file-template.txt existe" "[[ -f '$dns_dir/zone-file-template.txt' ]]"
    validate "manage-dns.sh existe" "[[ -f '$dns_dir/manage-dns.sh' ]]"
}

# Check scripts
check_scripts() {
    log_info "Validando scripts..."
    
    validate "setup-digitalocean.sh existe" "[[ -f '$INFRA_DIR/scripts/setup-digitalocean.sh' ]]"
    validate "backup-strategy.sh existe" "[[ -f '$INFRA_DIR/scripts/backup-strategy.sh' ]]"
}

# Check documentation
check_documentation() {
    log_info "Validando documentación..."
    
    validate "README.md existe" "[[ -f '$INFRA_DIR/README.md' ]]"
    validate "Makefile existe" "[[ -f '$INFRA_DIR/Makefile' ]]"
    validate ".gitignore existe" "[[ -f '$INFRA_DIR/.gitignore' ]]"
}

# Check file permissions
check_permissions() {
    log_info "Validando permisos de archivos..."
    
    local scripts=(
        "$INFRA_DIR/scripts/setup-digitalocean.sh"
        "$INFRA_DIR/scripts/backup-strategy.sh"
        "$INFRA_DIR/ssl/manage-ssl.sh"
        "$INFRA_DIR/dns/manage-dns.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [[ -f "$script" ]]; then
            validate "Script $script es ejecutable" "[[ -x '$script' ]]"
        fi
    done
}

# Check configuration content
check_content() {
    log_info "Validando contenido de archivos..."
    
    local terraform_dir="$INFRA_DIR/terraform"
    
    validate "main.tf contiene provider digitalocean" "grep -q 'digitalocean' '$terraform_dir/main.tf'"
    validate "main.tf contiene variables" "grep -q 'variable' '$terraform_dir/main.tf'"
    validate "droplets.tf contiene resource digitalocean_droplet" "grep -q 'digitalocean_droplet' '$terraform_dir/droplets.tf'"
    validate "droplets.tf contiene resource digitalocean_database_cluster" "grep -q 'digitalocean_database_cluster' '$terraform_dir/droplets.tf'"
    validate "droplets.tf contiene resource digitalocean_load_balancer" "grep -q 'digitalocean_load_balancer' '$terraform_dir/droplets.tf'"
    
    local ansible_dir="$INFRA_DIR/ansible"
    
    validate "site.yml contiene hosts: all" "grep -q 'hosts: all' '$ansible_dir/playbooks/site.yml'"
    validate "inventory.yml contiene grupos" "grep -q 'prod:' '$ansible_dir/inventory/inventory.yml'"
    
    local monitoring_dir="$INFRA_DIR/monitoring"
    
    validate "prometheus.yml contiene scrape_configs" "grep -q 'scrape_configs:' '$monitoring_dir/prometheus.yml'"
    validate "alert_rules.yml contiene groups" "grep -q 'groups:' '$monitoring_dir/alert_rules.yml'"
}

# Generate validation report
generate_report() {
    log_info "Generando reporte de validación..."
    
    local report_file="/tmp/infrastructure-validation-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
AI News Aggregator - Infrastructure Validation Report
====================================================
Fecha: $(date)
Directorio: $INFRA_DIR

Summary:
--------
Total de validaciones: $total_checks
Exitosas: $passed_checks
Fallidas: $failed_checks
Porcentaje de éxito: $(( passed_checks * 100 / total_checks ))%

Estructura de Directorios:
-------------------------
$(ls -la "$INFRA_DIR")

Archivos de Terraform:
---------------------
$(ls -la "$INFRA_DIR/terraform/" 2>/dev/null || echo "No encontrado")

Archivos de Ansible:
-------------------
$(ls -la "$INFRA_DIR/ansible/" 2>/dev/null || echo "No encontrado")

Scripts:
--------
$(ls -la "$INFRA_DIR/scripts/" 2>/dev/null || echo "No encontrado")

Configuración de Monitoreo:
--------------------------
$(ls -la "$INFRA_DIR/monitoring/" 2>/dev/null || echo "No encontrado")

Estado de Validación:
-------------------
$([ $failed_checks -eq 0 ] && echo "✅ INFRAESTRUCTURA VÁLIDA" || echo "❌ INFRAESTRUCTURA CON PROBLEMAS")

Recomendaciones:
---------------
EOF

    if [[ $failed_checks -eq 0 ]]; then
        cat >> "$report_file" << 'EOF'
- La infraestructura está correctamente configurada
- Puedes proceder con el deployment
- Ejecuta: ./scripts/setup-digitalocean.sh
EOF
    else
        cat >> "$report_file" << 'EOF'
- Se encontraron problemas en la configuración
- Revisa los archivos faltantes o con errores
- Consulta el README.md para instrucciones detalladas
EOF
    fi
    
    log_info "Reporte guardado en: $report_file"
    cat "$report_file"
}

# Main execution
main() {
    log_info "Iniciando validación de infraestructura AI News Aggregator"
    echo
    
    check_structure
    echo
    
    check_terraform
    echo
    
    check_ansible
    echo
    
    check_monitoring
    echo
    
    check_ssl
    echo
    
    check_dns
    echo
    
    check_scripts
    echo
    
    check_documentation
    echo
    
    check_permissions
    echo
    
    check_content
    echo
    
    # Generate summary
    log_info "=== Resumen de Validación ==="
    log_info "Total de validaciones: $total_checks"
    log_success "Exitosas: $passed_checks"
    
    if [[ $failed_checks -gt 0 ]]; then
        log_error "Fallidas: $failed_checks"
        echo
        log_error "La infraestructura tiene problemas. Revisa los errores arriba."
    else
        log_success "Fallidas: $failed_checks"
        echo
        log_success "¡Infraestructura validada correctamente!"
        log_info "Puedes proceder con: ./scripts/setup-digitalocean.sh"
    fi
    
    echo
    generate_report
}

# Execute main function
main "$@"