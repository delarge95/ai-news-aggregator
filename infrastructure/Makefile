# Makefile for AI News Aggregator Infrastructure
# Version: 1.0.0
# Description: Automation commands for infrastructure management

.PHONY: help setup terraform ansible dns ssl monitoring backup clean validate

# Default target
help:
	@echo "AI News Aggregator - Infrastructure Management"
	@echo "=============================================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@echo "SETUP AND PROVISIONING"
	@echo "  setup              - Complete automated setup"
	@echo "  setup-terraform    - Initialize and apply Terraform"
	@echo "  setup-ansible      - Run Ansible configuration"
	@echo "  setup-dns          - Configure DNS records"
	@echo "  setup-ssl          - Configure SSL certificates"
	@echo "  setup-monitoring   - Start monitoring stack"
	@echo ""
	@echo "MANAGEMENT"
	@echo "  start              - Start all services"
	@echo "  stop               - Stop all services"
	@echo "  restart            - Restart all services"
	@echo "  status             - Check service status"
	@echo ""
	@echo "MONITORING"
	@echo "  monitor            - Start monitoring stack"
	@echo "  prometheus         - Access Prometheus"
	@echo "  grafana            - Access Grafana"
	@echo "  alerts             - Access Alertmanager"
	@echo ""
	@echo "BACKUP AND RECOVERY"
	@echo "  backup             - Run full backup"
	@echo "  backup-db          - Backup database only"
	@echo "  restore            - Restore from backup"
	@echo ""
	@echo "SSL MANAGEMENT"
	@echo "  ssl-renew          - Renew SSL certificates"
	@echo "  ssl-status         - Check SSL certificate status"
	@echo "  ssl-backup         - Backup SSL certificates"
	@echo ""
	@echo "DNS MANAGEMENT"
	@echo "  dns-check          - Check DNS configuration"
	@echo "  dns-list           - List DNS records"
	@echo "  dns-propagation    - Check DNS propagation"
	@echo ""
	@echo "MAINTENANCE"
	@echo "  update             - Update system packages"
	@echo "  clean              - Clean temporary files"
	@echo "  validate           - Validate configuration"
	@echo ""
	@echo "Environment variables required:"
	@echo "  DO_TOKEN           - DigitalOcean API token"
	@echo "  DOMAIN_NAME        - Domain name"
	@echo "  ENVIRONMENT        - Environment (dev/staging/prod)"
	@echo ""
	@echo "Examples:"
	@echo "  make setup ENVIRONMENT=prod"
	@echo "  make backup DOMAIN_NAME=example.com"
	@echo "  make ssl-renew SSL_EMAIL=admin@example.com"

# Environment variables
ENVIRONMENT ?= dev
DOMAIN_NAME ?= ai-news-aggregator.com
DO_TOKEN ?= $(shell echo $$DO_TOKEN)
SSL_EMAIL ?= admin@$(DOMAIN_NAME)
BACKUP_DIR ?= /opt/backups
PROJECT_ROOT ?= $(shell dirname $(PWD))
INFRA_DIR = $(PROJECT_ROOT)/infrastructure

# Colors for output
BOLD = \033[1m
GREEN = \033[32m
YELLOW = \033[33m
RED = \033[31m
NC = \033[0m

# Check required variables
check-env:
	@echo "$(BOLD)Checking required environment variables...$(NC)"
	@if [ -z "$(DO_TOKEN)" ]; then \
		echo "$(RED)ERROR: DO_TOKEN is not set$(NC)"; \
		exit 1; \
	fi
	@if [ -z "$(DOMAIN_NAME)" ]; then \
		echo "$(RED)ERROR: DOMAIN_NAME is not set$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Environment variables OK$(NC)"

# Complete automated setup
setup: check-env
	@echo "$(BOLD)Starting complete infrastructure setup...$(NC)"
	@$(INFRA_DIR)/scripts/setup-digitalocean.sh
	@echo "$(GREEN)Setup completed!$(NC)"

# Terraform setup
setup-terraform: check-env
	@echo "$(BOLD)Setting up Terraform infrastructure...$(NC)"
	@cd $(INFRA_DIR)/terraform && \
	terraform init && \
	terraform validate && \
	terraform plan -out=tfplan && \
	terraform apply tfplan
	@echo "$(GREEN)Terraform setup completed!$(NC)"

# Ansible setup
setup-ansible: check-env
	@echo "$(BOLD)Running Ansible configuration...$(NC)"
	@cd $(INFRA_DIR)/ansible && \
	ansible-playbook -i inventory/inventory.yml playbooks/site.yml
	@echo "$(GREEN)Ansible configuration completed!$(NC)"

# DNS setup
setup-dns: check-env
	@echo "$(BOLD)Configuring DNS...$(NC)"
	@$(INFRA_DIR)/dns/manage-dns.sh setup
	@$(INFRA_DIR)/dns/manage-dns.sh check
	@echo "$(GREEN)DNS setup completed!$(NC)"

# SSL setup
setup-ssl: check-env
	@echo "$(BOLD)Configuring SSL certificates...$(NC)"
	@$(INFRA_DIR)/ssl/manage-ssl.sh install
	@$(INFRA_DIR)/ssl/manage-ssl.sh obtain
	@$(INFRA_DIR)/ssl/manage-ssl.sh setup-auto-renewal
	@echo "$(GREEN)SSL setup completed!$(NC)"

# Monitoring setup
setup-monitoring:
	@echo "$(BOLD)Starting monitoring stack...$(NC)"
	@cd $(INFRA_DIR)/monitoring && \
	docker-compose up -d
	@echo "$(GREEN)Monitoring stack started!$(NC)"

# Start all services
start:
	@echo "$(BOLD)Starting all services...$(NC)"
	@sudo systemctl start nginx docker
	@cd $(INFRA_DIR)/monitoring && docker-compose up -d
	@echo "$(GREEN)All services started!$(NC)"

# Stop all services
stop:
	@echo "$(BOLD)Stopping all services...$(NC)"
	@sudo systemctl stop nginx docker
	@cd $(INFRA_DIR)/monitoring && docker-compose down
	@echo "$(GREEN)All services stopped!$(NC)"

# Restart all services
restart: stop start
	@echo "$(GREEN)All services restarted!$(NC)"

# Check service status
status:
	@echo "$(BOLD)Checking service status...$(NC)"
	@echo "Docker containers:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "System services:"
	@sudo systemctl is-active nginx docker fail2ban

# Monitoring targets
monitor:
	@echo "$(BOLD)Starting monitoring stack...$(NC)"
	@cd $(INFRA_DIR)/monitoring && \
	docker-compose up -d
	@echo "$(GREEN)Monitoring stack started!$(NC)"
	@echo "Access URLs:"
	@echo "  Grafana: http://monitoring.$(DOMAIN_NAME)"
	@echo "  Prometheus: http://prometheus.$(DOMAIN_NAME)"
	@echo "  Alertmanager: http://alertmanager.$(DOMAIN_NAME)"

prometheus:
	@echo "Prometheus URL: http://prometheus.$(DOMAIN_NAME)"
	@echo "Local access: http://localhost:9090"

grafana:
	@echo "Grafana URL: http://monitoring.$(DOMAIN_NAME)"
	@echo "Local access: http://localhost:3000"
	@echo "Default credentials: admin/admin"

alerts:
	@echo "Alertmanager URL: http://alertmanager.$(DOMAIN_NAME)"
	@echo "Local access: http://localhost:9093"

# Backup targets
backup: check-env
	@echo "$(BOLD)Running full backup...$(NC)"
	@$(INFRA_DIR)/scripts/backup-strategy.sh
	@echo "$(GREEN)Backup completed!$(NC)"

backup-db:
	@echo "$(BOLD)Running database backup...$(NC)"
	@$(INFRA_DIR)/scripts/backup-strategy.sh --skip-terraform --skip-files --skip-ssl
	@echo "$(GREEN)Database backup completed!$(NC)"

restore:
	@echo "$(BOLD)Restoring from backup...$(NC)"
	@read -p "Enter backup file path: " backup_file; \
	$(INFRA_DIR)/scripts/restore.sh $$backup_file

# SSL targets
ssl-renew:
	@echo "$(BOLD)Renewing SSL certificates...$(NC)"
	@sudo certbot renew --quiet
	@$(INFRA_DIR)/ssl/manage-ssl.sh check
	@echo "$(GREEN)SSL certificates renewed!$(NC)"

ssl-status:
	@echo "$(BOLD)Checking SSL certificate status...$(NC)"
	@$(INFRA_DIR)/ssl/manage-ssl.sh status

ssl-backup:
	@echo "$(BOLD)Backing up SSL certificates...$(NC)"
	@$(INFRA_DIR)/ssl/manage-ssl.sh backup
	@echo "$(GREEN)SSL certificates backed up!$(NC)"

# DNS targets
dns-check:
	@echo "$(BOLD)Checking DNS configuration...$(NC)"
	@$(INFRA_DIR)/dns/manage-dns.sh check

dns-list:
	@echo "$(BOLD)Listing DNS records...$(NC)"
	@$(INFRA_DIR)/dns/manage-dns.sh list

dns-propagation:
	@echo "$(BOLD)Checking DNS propagation...$(NC)"
	@$(INFRA_DIR)/dns/manage-dns.sh propagation www

# Maintenance targets
update:
	@echo "$(BOLD)Updating system packages...$(NC)"
	@sudo apt update && sudo apt upgrade -y
	@echo "$(GREEN)System updated!$(NC)"

clean:
	@echo "$(BOLD)Cleaning temporary files...$(NC)"
	@find /tmp -name "ai-news-*" -type f -mtime +7 -delete
	@find /var/log -name "*.log" -type f -size +100M -exec truncate -s 50M {} \;
	@docker system prune -f
	@echo "$(GREEN)Cleanup completed!$(NC)"

# Validation targets
validate:
	@echo "$(BOLD)Validating infrastructure configuration...$(NC)"
	@echo "Validating Terraform:"
	@cd $(INFRA_DIR)/terraform && terraform validate
	@echo "Validating Ansible:"
	@cd $(INFRA_DIR)/ansible && ansible-playbook --syntax-check playbooks/site.yml
	@echo "Checking Docker Compose:"
	@cd $(INFRA_DIR)/monitoring && docker-compose config
	@echo "$(GREEN)Validation completed!$(NC)"

# Health checks
health-check:
	@echo "$(BOLD)Running health checks...$(NC)"
	@echo "Checking web application:"
	@curl -f http://localhost/health || echo "Web app not responding"
	@echo "Checking monitoring:"
	@curl -f http://localhost:9090/-/healthy || echo "Prometheus not responding"
	@curl -f http://localhost:3000/api/health || echo "Grafana not responding"
	@echo "Checking SSL:"
	@echo | openssl s_client -connect $(DOMAIN_NAME):443 -servername $(DOMAIN_NAME) 2>/dev/null | openssl x509 -noout -dates
	@echo "$(GREEN)Health checks completed!$(NC)"

# Deployment targets
deploy-app:
	@echo "$(BOLD)Deploying application...$(NC)"
	@cd $(PROJECT_ROOT) && \
	docker-compose down && \
	docker-compose build && \
	docker-compose up -d
	@echo "$(GREEN)Application deployed!$(NC)"

deploy-backend:
	@echo "$(BOLD)Deploying backend...$(NC)"
	@cd $(PROJECT_ROOT)/backend && \
	./deploy.sh
	@echo "$(GREEN)Backend deployed!$(NC)"

deploy-frontend:
	@echo "$(BOLD)Deploying frontend...$(NC)"
	@cd $(PROJECT_ROOT)/frontend && \
	npm run build && \
	docker build -t ai-news-frontend . && \
	docker-compose down && \
	docker-compose up -d
	@echo "$(GREEN)Frontend deployed!$(NC)"

# Log viewing
logs:
	@echo "$(BOLD)Showing recent logs...$(NC)"
	@echo "Terraform logs:"
	@ls -lt /tmp/ai-news-setup-*.log 2>/dev/null | head -1 | awk '{print $$9}' | xargs tail -n 20
	@echo "Nginx logs:"
	@sudo tail -n 20 /var/log/nginx/error.log
	@echo "Docker logs:"
	@docker logs --tail=20 ai-news-web 2>/dev/null || echo "No web container logs"

# Testing targets
test-integration:
	@echo "$(BOLD)Running integration tests...$(NC)"
	@cd $(PROJECT_ROOT) && \
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit
	@echo "$(GREEN)Integration tests completed!$(NC)"

test-performance:
	@echo "$(BOLD)Running performance tests...$(NC)"
	@which ab && ab -n 1000 -c 10 http://localhost/ || echo "Apache Bench not available"
	@which wrk && wrk -t4 -c100 -d30s http://localhost/ || echo "wrk not available"
	@echo "$(GREEN)Performance tests completed!$(NC)"

# Security targets
security-scan:
	@echo "$(BOLD)Running security scan...$(NC)"
	@which nmap && nmap -sS -O localhost || echo "nmap not available"
	@sudo fail2ban-client status
	@echo "$(GREEN)Security scan completed!$(NC)"

security-audit:
	@echo "$(BOLD)Running security audit...$(NC)"
	@echo "Checking SSL configuration:"
	@$(INFRA_DIR)/ssl/manage-ssl.sh test
	@echo "Checking firewall rules:"
	@sudo ufw status verbose
	@echo "Checking SSH configuration:"
	@sudo sshd -t
	@echo "$(GREEN)Security audit completed!$(NC)"

# Environment-specific targets
dev-setup:
	@echo "$(BOLD)Setting up development environment...$(NC)"
	@make ENVIRONMENT=dev setup
	@echo "$(GREEN)Development environment ready!$(NC)"

staging-setup:
	@echo "$(BOLD)Setting up staging environment...$(NC)"
	@make ENVIRONMENT=staging setup
	@echo "$(GREEN)Staging environment ready!$(NC)"

prod-setup:
	@echo "$(BOLD)Setting up production environment...$(NC)"
	@make ENVIRONMENT=prod setup
	@echo "$(GREEN)Production environment ready!$(NC)"

# Show current configuration
show-config:
	@echo "$(BOLD)Current Configuration:$(NC)"
	@echo "Environment: $(ENVIRONMENT)"
	@echo "Domain: $(DOMAIN_NAME)"
	@echo "Project Root: $(PROJECT_ROOT)"
	@echo "Infra Dir: $(INFRA_DIR)"
	@echo "DO_TOKEN: $(shell [ -n "$(DO_TOKEN)" ] && echo "Set" || echo "Not set")"