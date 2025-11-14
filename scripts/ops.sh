#!/bin/bash

# ops.sh - Script de operaciones principal para AI News Aggregator
# Versión: 1.0.0
# Descripción: Punto de entrada centralizado para todas las operaciones de deployment y mantenimiento

set -euo pipefail

# Configuración
readonly PROJECT_NAME="ai-news-aggregator"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPTS_DIR="$SCRIPT_DIR"

# Colores para output
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_PURPLE='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_WHITE='\033[1;37m'
readonly COLOR_RESET='\033[0m'

# Funciones de utilidad
print_header() {
    echo -e "${COLOR_CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    AI News Aggregator - Operations Manager                   ║"
    echo "║                              Versión 1.0.0                                   ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${COLOR_RESET}"
}

print_banner() {
    echo -e "${COLOR_PURPLE}"
    cat << 'EOF'
    ____             __            __       __      __ __                 
   / __ \____  __  __/ /____  _____/ /_____ _/ /_____ _/ /_  __  __________
  / /_/ / __ \/ / / / __/ _ \/ ___/ __/ __ `/ __/ __ `/ __ \/ / / / ___/ __ \
 / _, _/ /_/ / /_/ / /_/  __/ /__/ /_/ /_/ / /_/ /_/ / / / / /_/ / /  / /_/ /
/_/ |_|\____/\____/\__/\___/\___/\__/\__,_/\__/\__,_/_/ /_/\____/_/   \____/ 
                                                                                
EOF
    echo -e "${COLOR_RESET}"
}

show_help() {
    print_banner
    echo ""
    cat << 'EOF'
Uso: ./ops.sh [COMANDO] [OPCIONES]

COMANDOS PRINCIPALES:
  🚀 deploy              - Deployment completo de la aplicación
  🔄 rollback           - Rollback al backup más reciente
  🔍 health             - Verificaciones de salud del sistema
  🔧 migrate            - Migraciones de base de datos
  📈 scale              - Escalado de servicios
  💾 backup             - Crear backup completo
  🔒 maintenance        - Activar/desactivar modo mantenimiento
  🔐 certificates       - Gestión de certificados SSL

COMANDOS DE UTILIDAD:
  📊 status             - Estado general del sistema
  🔧 config             - Configuración actual
  📋 list               - Listar recursos disponibles
  🧹 cleanup            - Limpiar recursos temporales
  📚 help               - Mostrar esta ayuda
  ❓ docs               - Documentación detallada

COMANDOS ESPECÍFICOS:

🌐 DEPLOYMENT:
  ./ops.sh deploy                    # Deployment completo
  ./ops.sh deploy --dry-run         # Simulación sin ejecutar
  ./ops.sh deploy --backend-only    # Solo backend
  ./ops.sh deploy --frontend-only   # Solo frontend

🔄 ROLLBACK:
  ./ops.sh rollback                 # Rollback al último backup
  ./ops.sh rollback 20241106_041606 # Rollback a timestamp específico
  ./ops.sh rollback --list          # Listar backups disponibles

🔍 HEALTH CHECKS:
  ./ops.sh health                   # Verificación completa
  ./ops.sh health services          # Solo servicios Docker
  ./ops.sh health endpoints         # Solo endpoints HTTP
  ./ops.sh health database          # Solo base de datos
  ./ops.sh health --json            # Salida en formato JSON

🔧 MIGRACIONES:
  ./ops.sh migrate                  # Ejecutar migraciones pendientes
  ./ops.sh migrate --create "desc"  # Crear nueva migración
  ./ops.sh migrate --status         # Estado actual de migraciones
  ./ops.sh migrate --rollback       # Rollback de última migración

📈 ESCALADO:
  ./ops.sh scale auto               # Auto-scaling basado en métricas
  ./ops.sh scale up celery_worker 2 # Escalar workers +2
  ./ops.sh scale down backend 1     # Escalar backend -1
  ./ops.sh scale set frontend 3     # Configurar frontend a 3 réplicas

💾 BACKUP:
  ./ops.sh backup                   # Backup completo
  ./ops.sh backup database          # Solo base de datos
  ./ops.sh backup code              # Solo código
  ./ops.sh backup --list            # Listar backups existentes
  ./ops.sh backup --restore <archivo> # Restaurar backup específico

🔒 MODO MANTENIMIENTO:
  ./ops.sh maintenance on           # Activar mantenimiento
  ./ops.sh maintenance off          # Desactivar mantenimiento
  ./ops.sh maintenance status       # Estado actual
  ./ops.sh maintenance schedule "02:00" "1h" # Programar mantenimiento

🔐 CERTIFICADOS SSL:
  ./ops.sh certificates renew       # Renovar certificados
  ./ops.sh certificates status      # Estado de certificados
  ./ops.sh certificates generate    # Generar auto-firmados
  ./ops.sh certificates backup      # Backup de certificados

COMANDOS RÁPIDOS:
  ./ops.sh start                    # Iniciar aplicación completa
  ./ops.sh stop                     # Detener aplicación
  ./ops.sh restart                  # Reiniciar aplicación
  ./ops.sh logs                     - Ver logs de servicios
  ./ops.sh monitor                  - Monitoreo en tiempo real

VARIABLES DE ENTORNO:
  DEPLOY_ENV             - Entorno (development|staging|production)
  BACKUP_ENABLED         - Habilitar backups (true|false)
  AUTO_ROLLBACK          - Rollback automático en error (true|false)
  WEB_SERVER             - Servidor web (nginx|apache|docker|auto)
  CERT_RENEWAL_THRESHOLD - Días para renovar SSL (default: 30)

EJEMPLOS PRÁCTICOS:

# Deployment completo en producción
export DEPLOY_ENV=production
export WEB_SERVER=nginx
./ops.sh deploy

# Verificación de salud post-deployment
./ops.sh health --json

# Backup antes de migración importante
./ops.sh backup database
./ops.sh migrate

# Escalado automático basado en carga
./ops.sh scale auto

# Mantenimiento programado para las 2:00 AM
./ops.sh maintenance schedule "02:00" "2h"

# Rollback rápido en caso de problema
./ops.sh rollback --list
./ops.sh rollback 20241106_041606

ARCHIVOS DE CONFIGURACIÓN:
  .env                          - Variables de entorno
  docker-compose.yml            - Configuración de servicios
  scaling-config.json           - Configuración de escalado
  certificates/                 - Certificados SSL
  backups/                      - Backups automáticos
  maintenance/                  - Página de mantenimiento

SCRIPTS INDIVIDUALES:
  deploy.sh              - Deployment automatizado
  rollback.sh            - Rollback rápido
  health-check.sh        - Verificaciones de salud
  migrate-database.sh    - Migraciones DB
  scale-services.sh      - Auto-scaling
  backup-restore.sh      - Gestión de backups
  maintenance.sh         - Modo mantenimiento
  update-certificates.sh - Renovación SSL
  logger.sh              - Sistema de logging

DOCUMENTACIÓN:
  Para documentación detallada, consulta:
  - README.md en la raíz del proyecto
  - docs/ para documentación técnica
  - ./ops.sh docs para ejemplos específicos

Soporte:
  📧 Email: devops@company.com
  📱 Slack: #ai-news-devops
  🐛 Issues: GitHub Issues

EOF
    echo ""
}

run_deploy() {
    local args=("$@")
    echo -e "${COLOR_GREEN}🚀 Iniciando deployment...${COLOR_RESET}"
    
    # Procesar argumentos
    local deploy_type="full"
    local dry_run=false
    
    for arg in "${args[@]}"; do
        case "$arg" in
            --dry-run)
                dry_run=true
                ;;
            --backend-only)
                deploy_type="backend"
                ;;
            --frontend-only)
                deploy_type="frontend"
                ;;
        esac
    done
    
    if [[ "$dry_run" == "true" ]]; then
        echo -e "${COLOR_YELLOW}Modo simulación activado${COLOR_RESET}"
        export DRY_RUN=true
    fi
    
    case "$deploy_type" in
        "backend")
            echo -e "${COLOR_BLUE}Deploying backend...${COLOR_RESET}"
            ;;
        "frontend")
            echo -e "${COLOR_BLUE}Deploying frontend...${COLOR_RESET}"
            ;;
        *)
            echo -e "${COLOR_BLUE}Deploying complete application...${COLOR_RESET}"
            ;;
    esac
    
    bash "$SCRIPTS_DIR/deploy.sh" deploy
}

run_rollback() {
    local args=("$@")
    echo -e "${COLOR_RED}🔄 Iniciando rollback...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/rollback.sh" latest
    else
        local target="${args[0]}"
        case "$target" in
            --list)
                bash "$SCRIPTS_DIR/rollback.sh" list
                ;;
            *)
                bash "$SCRIPTS_DIR/rollback.sh" "$target"
                ;;
        esac
    fi
}

run_health() {
    local args=("$@")
    echo -e "${COLOR_CYAN}🔍 Verificando salud del sistema...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/health-check.sh" all
    else
        case "${args[0]}" in
            --json)
                bash "$SCRIPTS_DIR/health-check.sh" all json
                ;;
            --html)
                bash "$SCRIPTS_DIR/health-check.sh" all html
                ;;
            services|endpoints|database|cache|performance|resources)
                bash "$SCRIPTS_DIR/health-check.sh" "${args[0]}"
                ;;
            *)
                echo -e "${COLOR_RED}Opción de health no válida: ${args[0]}${COLOR_RESET}"
                exit 1
                ;;
        esac
    fi
}

run_migrate() {
    local args=("$@")
    echo -e "${COLOR_PURPLE}🔧 Ejecutando migraciones...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/migrate-database.sh" migrate
    else
        case "${args[0]}" in
            --create)
                if [[ -n "${args[1]:-}" ]]; then
                    bash "$SCRIPTS_DIR/migrate-database.sh" create "${args[1]}"
                else
                    echo -e "${COLOR_RED}Descripción requerida para crear migración${COLOR_RESET}"
                    exit 1
                fi
                ;;
            --status)
                bash "$SCRIPTS_DIR/migrate-database.sh" status
                ;;
            --rollback)
                bash "$SCRIPTS_DIR/migrate-database.sh" rollback
                ;;
            *)
                bash "$SCRIPTS_DIR/migrate-database.sh" "${args[0]}"
                ;;
        esac
    fi
}

run_scale() {
    local args=("$@")
    echo -e "${COLOR_YELLOW}📈 Gestionando escalado...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/scale-services.sh" auto
    else
        case "${args[0]}" in
            "auto")
                bash "$SCRIPTS_DIR/scale-services.sh" auto
                ;;
            "up")
                local service="${args[1]:-celery_worker}"
                local replicas="${args[2]:-1}"
                bash "$SCRIPTS_DIR/scale-services.sh" up "$service" "$replicas"
                ;;
            "down")
                local service="${args[1]:-celery_worker}"
                local replicas="${args[2]:-1}"
                bash "$SCRIPTS_DIR/scale-services.sh" down "$service" "$replicas"
                ;;
            "set")
                local service="${args[1]:-all}"
                local replicas="${args[2]:-1}"
                bash "$SCRIPTS_DIR/scale-services.sh" set "$service" "$replicas"
                ;;
            *)
                bash "$SCRIPTS_DIR/scale-services.sh" "${args[0]}"
                ;;
        esac
    fi
}

run_backup() {
    local args=("$@")
    echo -e "${COLOR_BLUE}💾 Gestionando backups...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/backup-restore.sh" create
    else
        case "${args[0]}" in
            "database"|"code"|"configs"|"full")
                bash "$SCRIPTS_DIR/backup-restore.sh" create "${args[0]}"
                ;;
            --list)
                bash "$SCRIPTS_DIR/backup-restore.sh" list
                ;;
            --restore)
                if [[ -n "${args[1]:-}" ]]; then
                    bash "$SCRIPTS_DIR/backup-restore.sh" restore "${args[1]}"
                else
                    echo -e "${COLOR_RED}Archivo de backup requerido${COLOR_RESET}"
                    exit 1
                fi
                ;;
            *)
                bash "$SCRIPTS_DIR/backup-restore.sh" "${args[0]}"
                ;;
        esac
    fi
}

run_maintenance() {
    local args=("$@")
    echo -e "${COLOR_RED}🔒 Gestionando modo mantenimiento...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/maintenance.sh" status
    else
        case "${args[0]}" in
            "on")
                local title="${args[1]:-Sistema en Mantenimiento}"
                local message="${args[2]:-Estamos realizando trabajos de mantenimiento}"
                local eta="${args[3]:-30 minutos}"
                bash "$SCRIPTS_DIR/maintenance.sh" on "$title" "$message" "$eta"
                ;;
            "off")
                bash "$SCRIPTS_DIR/maintenance.sh" off
                ;;
            "status")
                bash "$SCRIPTS_DIR/maintenance.sh" status
                ;;
            "schedule")
                local time="${args[1]:-}"
                local duration="${args[2]:-30m}"
                if [[ -n "$time" ]]; then
                    bash "$SCRIPTS_DIR/maintenance.sh" schedule "$time" "$duration" "${args[3]:-Mantenimiento programado}"
                else
                    echo -e "${COLOR_RED}Hora requerida para programar mantenimiento${COLOR_RESET}"
                    exit 1
                fi
                ;;
            *)
                bash "$SCRIPTS_DIR/maintenance.sh" "${args[0]}"
                ;;
        esac
    fi
}

run_certificates() {
    local args=("$@")
    echo -e "${COLOR_GREEN}🔐 Gestionando certificados SSL...${COLOR_RESET}"
    
    if [[ ${#args[@]} -eq 0 ]]; then
        bash "$SCRIPTS_DIR/update-certificates.sh" status
    else
        case "${args[0]}" in
            "renew")
                bash "$SCRIPTS_DIR/update-certificates.sh" renew
                ;;
            "status")
                bash "$SCRIPTS_DIR/update-certificates.sh" status
                ;;
            "generate")
                local cert_type="${args[1]:-development}"
                bash "$SCRIPTS_DIR/update-certificates.sh" generate "$cert_type"
                ;;
            "backup")
                bash "$SCRIPTS_DIR/update-certificates.sh" backup
                ;;
            *)
                bash "$SCRIPTS_DIR/update-certificates.sh" "${args[0]}"
                ;;
        esac
    fi
}

show_status() {
    echo -e "${COLOR_CYAN}📊 Estado del sistema AI News Aggregator${COLOR_RESET}"
    echo ""
    
    # Estado de servicios
    echo -e "${COLOR_YELLOW}Servicios Docker:${COLOR_RESET}"
    if command -v docker &> /dev/null; then
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=ai_news" 2>/dev/null || echo "  No hay contenedores ejecutándose"
    else
        echo "  Docker no disponible"
    fi
    
    echo ""
    
    # Estado de salud general
    echo -e "${COLOR_YELLOW}Salud del sistema:${COLOR_RESET}"
    if [[ -f "$SCRIPTS_DIR/health-check.sh" ]]; then
        timeout 30 bash "$SCRIPTS_DIR/health-check.sh" all 2>/dev/null | head -10 || echo "  Verificación de salud no disponible"
    fi
    
    echo ""
    
    # Estado de certificados
    echo -e "${COLOR_YELLOW}Certificados SSL:${COLOR_RESET}"
    if [[ -f "$SCRIPTS_DIR/update-certificates.sh" ]]; then
        bash "$SCRIPTS_DIR/update-certificates.sh" status 2>/dev/null | head -5 || echo "  Estado de certificados no disponible"
    fi
    
    echo ""
    
    # Estado de backups
    echo -e "${COLOR_YELLOW}Backups:${COLOR_RESET}"
    if [[ -d "./backups" ]]; then
        local backup_count
        backup_count=$(find ./backups -name "*.tar.gz" -o -name "20*" -type d | wc -l)
        echo "  Total de backups: $backup_count"
    else
        echo "  Directorio de backups no existe"
    fi
}

show_config() {
    echo -e "${COLOR_CYAN}⚙️  Configuración actual${COLOR_RESET}"
    echo ""
    
    echo -e "${COLOR_YELLOW}Variables de entorno:${COLOR_RESET}"
    echo "  DEPLOY_ENV: ${DEPLOY_ENV:-production}"
    echo "  WEB_SERVER: ${WEB_SERVER:-auto}"
    echo "  BACKUP_ENABLED: ${BACKUP_ENABLED:-true}"
    echo "  AUTO_ROLLBACK: ${AUTO_ROLLBACK:-true}"
    echo "  LOG_LEVEL: ${LOG_LEVEL:-INFO}"
    
    echo ""
    echo -e "${COLOR_YELLOW}Directorios:${COLOR_RESET}"
    echo "  Scripts: $SCRIPTS_DIR"
    echo "  Certificados: ${CERT_DIR:-./certificates}"
    echo "  Backups: ${BACKUP_BASE_DIR:-./backups}"
    echo "  Logs: ${LOG_DIR:-./logs}"
    
    echo ""
    echo -e "${COLOR_YELLOW}Herramientas disponibles:${COLOR_RESET}"
    
    # Verificar herramientas
    local tools=("docker" "docker-compose" "certbot" "openssl")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo -e "  ✅ $tool"
        else
            echo -e "  ❌ $tool"
        fi
    done
}

show_list() {
    echo -e "${COLOR_CYAN}📋 Recursos disponibles${COLOR_RESET}"
    echo ""
    
    echo -e "${COLOR_YELLOW}Scripts disponibles:${COLOR_RESET}"
    ls -la "$SCRIPTS_DIR"/*.sh | awk '{print "  " $9}' | while read -r script; do
        local script_name
        script_name=$(basename "$script")
        echo -e "  🔧 $script_name"
    done
    
    echo ""
    echo -e "${COLOR_YELLOW}Backups disponibles:${COLOR_RESET}"
    if [[ -d "./backups" ]]; then
        find ./backups -name "*.tar.gz" -type f 2>/dev/null | head -5 | while read -r backup; do
            local backup_name
            backup_name=$(basename "$backup")
            echo -e "  💾 $backup_name"
        done
        
        local total_backups
        total_backups=$(find ./backups -name "*.tar.gz" -type f | wc -l)
        if [[ $total_backups -gt 5 ]]; then
            echo -e "  ... y $((total_backups - 5)) más"
        fi
    else
        echo "  No hay backups disponibles"
    fi
    
    echo ""
    echo -e "${COLOR_YELLOW}Configuraciones:${COLOR_RESET}"
    local configs=("docker-compose.yml" ".env" "scaling-config.json")
    for config in "${configs[@]}"; do
        if [[ -f "$config" ]]; then
            echo -e "  📄 $config"
        else
            echo -e "  ⚠️  $config (no encontrado)"
        fi
    done
}

run_cleanup() {
    echo -e "${COLOR_YELLOW}🧹 Limpiando recursos temporales...${COLOR_RESET}"
    
    # Limpiar archivos temporales
    local cleaned_files=0
    
    # Limpiar logs antiguos
    if [[ -d "./logs" ]]; then
        find ./logs -name "*.log.*.gz" -mtime +30 -type f 2>/dev/null | while read -r log_file; do
            rm -f "$log_file"
            ((cleaned_files++))
        done
    fi
    
    # Limpiar contenedores Docker detenidos
    if command -v docker &> /dev/null; then
        local stopped_containers
        stopped_containers=$(docker ps -a --filter "status=exited" --format "{{.Names}}" | wc -l)
        
        if [[ $stopped_containers -gt 0 ]]; then
            echo -e "${COLOR_BLUE}Limpiando $stopped_containers contenedores detenidos...${COLOR_RESET}"
            docker container prune -f > /dev/null 2>&1
        fi
    fi
    
    # Limpiar imágenes huérfanas
    if command -v docker &> /dev/null; then
        docker image prune -f > /dev/null 2>&1
    fi
    
    echo -e "${COLOR_GREEN}✅ Cleanup completado${COLOR_RESET}"
    if [[ $cleaned_files -gt 0 ]]; then
        echo -e "${COLOR_GREEN}   $cleaned_files archivos eliminados${COLOR_RESET}"
    fi
}

run_start() {
    echo -e "${COLOR_GREEN}🚀 Iniciando AI News Aggregator...${COLOR_RESET}"
    
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose up -d
        echo -e "${COLOR_GREEN}✅ Servicios iniciados${COLOR_RESET}"
        
        # Esperar a que los servicios estén listos
        echo -e "${COLOR_BLUE}Esperando que los servicios estén listos...${COLOR_RESET}"
        sleep 10
        
        # Verificar estado
        if [[ -f "$SCRIPTS_DIR/health-check.sh" ]]; then
            bash "$SCRIPTS_DIR/health-check.sh" services
        fi
    else
        echo -e "${COLOR_RED}❌ docker-compose.yml no encontrado${COLOR_RESET}"
        exit 1
    fi
}

run_stop() {
    echo -e "${COLOR_RED}⏹️  Deteniendo AI News Aggregator...${COLOR_RESET}"
    
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose down
        echo -e "${COLOR_GREEN}✅ Servicios detenidos${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ docker-compose.yml no encontrado${COLOR_RESET}"
        exit 1
    fi
}

run_restart() {
    echo -e "${COLOR_YELLOW}🔄 Reiniciando AI News Aggregator...${COLOR_RESET}"
    run_stop
    sleep 3
    run_start
}

show_logs() {
    local service="${1:-all}"
    
    echo -e "${COLOR_CYAN}📋 Logs del sistema${COLOR_RESET}"
    echo ""
    
    case "$service" in
        "backend"|"frontend"|"postgres"|"redis"|"celery")
            echo -e "${COLOR_YELLOW}Logs de $service:${COLOR_RESET}"
            if [[ -f "docker-compose.yml" ]]; then
                docker-compose logs --tail=100 -f "$service"
            fi
            ;;
        "all")
            if [[ -f "docker-compose.yml" ]]; then
                docker-compose logs --tail=50 -f
            fi
            ;;
        *)
            echo -e "${COLOR_RED}Servicio no válido: $service${COLOR_RESET}"
            echo "Servicios disponibles: backend, frontend, postgres, redis, celery, all"
            ;;
    esac
}

run_monitor() {
    echo -e "${COLOR_CYAN}📈 Monitoreo en tiempo real (Ctrl+C para salir)${COLOR_RESET}"
    echo ""
    
    while true; do
        clear
        echo -e "${COLOR_CYAN}=== MONITOREO AI NEWS AGGREGATOR ===${COLOR_RESET}"
        echo "Fecha: $(date)"
        echo ""
        
        # Estado de contenedores
        echo -e "${COLOR_YELLOW}Estado de contenedores:${COLOR_RESET}"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.CPUPerc}}" --filter "name=ai_news" 2>/dev/null || echo "Docker no disponible"
        
        echo ""
        
        # Uso de recursos
        if command -v docker &> /dev/null; then
            echo -e "${COLOR_YELLOW}Uso de recursos:${COLOR_RESET}"
            docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" --filter "name=ai_news" 2>/dev/null || echo "No hay estadísticas disponibles"
        fi
        
        echo ""
        
        # Health check rápido
        echo -e "${COLOR_YELLOW}Health check rápido:${COLOR_RESET}"
        if [[ -f "$SCRIPTS_DIR/health-check.sh" ]]; then
            timeout 10 bash "$SCRIPTS_DIR/health-check.sh" endpoints 2>/dev/null | head -3 || echo "Health check no disponible"
        else
            echo "Health check no disponible"
        fi
        
        sleep 10
    done
}

show_docs() {
    echo -e "${COLOR_CYAN}📚 Documentación detallada${COLOR_RESET}"
    echo ""
    
    cat << 'EOF'
TUTORIAL DE USO COMPLETO:

🎯 WORKFLOW DE DEPLOYMENT COMPLETO:

1. Preparación:
   ./ops.sh status              # Verificar estado actual
   ./ops.sh config              # Verificar configuración
   ./ops.sh backup              # Crear backup antes del deployment

2. Deployment:
   ./ops.sh deploy              # Deployment completo
   ./ops.sh health              # Verificar salud post-deployment
   ./ops.sh migrate             # Ejecutar migraciones si es necesario

3. Monitoreo:
   ./ops.sh scale status        # Ver estado de escalado
   ./ops.sh certificates status # Verificar certificados SSL
   ./ops.sh monitor             # Monitoreo en tiempo real

🔧 WORKFLOW DE MANTENIMIENTO:

1. Programar mantenimiento:
   ./ops.sh maintenance schedule "02:00" "1h" "Mantenimiento mensual"

2. Activar mantenimiento:
   ./ops.sh maintenance on "Actualización del sistema" "Estamos actualizando el sistema" "30 minutos"

3. Realizar trabajos:
   ./ops.sh backup database
   ./ops.sh migrate
   ./ops.sh deploy

4. Desactivar mantenimiento:
   ./ops.sh maintenance off

5. Verificar:
   ./ops.sh health
   ./ops.sh status

🚀 WORKFLOW DE ROLLBACK:

1. Identificar problema:
   ./ops.sh health

2. Listar backups disponibles:
   ./ops.sh rollback --list

3. Ejecutar rollback:
   ./ops.sh rollback 20241106_041606

4. Verificar restauración:
   ./ops.sh health
   ./ops.sh status

📈 WORKFLOW DE ESCALADO:

1. Ver estado actual:
   ./ops.sh scale status

2. Escalado manual:
   ./ops.sh scale up celery_worker 2

3. Escalado automático:
   ./ops.sh scale auto

4. Monitoreo:
   ./ops.sh scale metrics

💾 WORKFLOW DE BACKUP/RESTORE:

1. Backup automático:
   ./ops.sh backup                    # Completo
   ./ops.sh backup database           # Solo BD
   ./ops.sh backup code               # Solo código

2. Listar backups:
   ./ops.sh backup --list

3. Restaurar:
   ./ops.sh backup --restore backup_file.tar.gz

4. Verificar:
   ./ops.sh health

🔐 WORKFLOW DE CERTIFICADOS SSL:

1. Verificar estado:
   ./ops.sh certificates status

2. Renovar certificados:
   ./ops.sh certificates renew

3. Generar auto-firmados (dev):
   ./ops.sh certificates generate development

4. Backup de certificados:
   ./ops.sh certificates backup

CONFIGURACIÓN AVANZADA:

Variables de entorno por entorno:
  
  DEVELOPMENT:
    export DEPLOY_ENV=development
    export WEB_SERVER=docker
    export LOG_LEVEL=DEBUG
    export BACKUP_ENABLED=false

  STAGING:
    export DEPLOY_ENV=staging
    export WEB_SERVER=nginx
    export LOG_LEVEL=INFO
    export BACKUP_ENABLED=true

  PRODUCTION:
    export DEPLOY_ENV=production
    export WEB_SERVER=nginx
    export LOG_LEVEL=WARN
    export BACKUP_ENABLED=true
    export AUTO_ROLLBACK=true

PERSONALIZACIÓN:

Archivos de configuración:
  - .env                    # Variables de entorno
  - docker-compose.yml      # Configuración de servicios
  - scaling-config.json     # Configuración de escalado
  - maintenance/            # Página de mantenimiento
  - certificates/           # Certificados SSL

Extensibilidad:
  Todos los scripts pueden ser ejecutados independientemente:
    bash scripts/deploy.sh deploy
    bash scripts/health-check.sh all
    bash scripts/backup-restore.sh create

INTEGRACIÓN CI/CD:

Pipeline ejemplo para GitHub Actions:
  - name: Deploy to production
    run: |
      ./ops.sh deploy
      ./ops.sh health
      ./ops.sh backup

TROUBLESHOOTING:

Problemas comunes:
  1. Contenedor no inicia:
     ./ops.sh logs <servicio>
     docker-compose restart <servicio>

  2. Problemas de base de datos:
     ./ops.sh health database
     ./ops.sh migrate --rollback

  3. Certificados SSL expirados:
     ./ops.sh certificates renew --force

  4. Alto uso de recursos:
     ./ops.sh scale down <servicio> 1
     ./ops.sh health performance

  5. Servicios no responden:
     ./ops.sh health endpoints
     ./ops.sh restart

DOCUMENTACIÓN ADICIONAL:

Recursos:
  - README.md: Documentación principal
  - docs/: Documentación técnica
  - scripts/: Scripts individuales con --help

Soporte:
  📧 Email: devops@company.com
  📱 Slack: #ai-news-devops
  🐛 Issues: GitHub Issues
  📖 Wiki: Documentación interna

EOF
}

# Función principal
main() {
    local command="${1:-help}"
    shift || true
    
    # Mostrar header para comandos que no sean help
    case "$command" in
        "help"|"docs")
            # No mostrar header para help/docs
            ;;
        *)
            print_header
            ;;
    esac
    
    case "$command" in
        "deploy"|"deployment")
            run_deploy "$@"
            ;;
        "rollback")
            run_rollback "$@"
            ;;
        "health"|"check")
            run_health "$@"
            ;;
        "migrate"|"migration")
            run_migrate "$@"
            ;;
        "scale"|"scaling")
            run_scale "$@"
            ;;
        "backup"|"restore")
            run_backup "$@"
            ;;
        "maintenance"|"maintain")
            run_maintenance "$@"
            ;;
        "certificates"|"certs"|"ssl")
            run_certificates "$@"
            ;;
        "status")
            show_status
            ;;
        "config")
            show_config
            ;;
        "list"|"ls")
            show_list
            ;;
        "cleanup"|"clean")
            run_cleanup
            ;;
        "start")
            run_start
            ;;
        "stop")
            run_stop
            ;;
        "restart"|"reload")
            run_restart
            ;;
        "logs"|"log")
            show_logs "$@"
            ;;
        "monitor"|"watch")
            run_monitor
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        "docs"|"documentation")
            show_docs
            ;;
        *)
            echo -e "${COLOR_RED}❌ Comando no válido: $command${COLOR_RESET}"
            echo ""
            echo "Usa './ops.sh help' para ver comandos disponibles"
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"