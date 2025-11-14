#!/bin/bash

# Configuración completa del sistema de monitoring para AI News Aggregator
# Este script configura y inicia todos los servicios de monitoring

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
MONITORING_DIR="./monitoring"
COMPOSE_FILE="$MONITORING_DIR/docker-compose.monitoring.yml"
HEALTH_CHECK_DIR="$MONITORING_DIR/health"
LOG_DIR="/var/log/ai-news-monitoring"
UPTIME_DIR="$MONITORING_DIR/uptime"

# Función de logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para verificar dependencias
check_dependencies() {
    log "Verificando dependencias..."
    
    # Verificar Docker
    if ! command -v docker &> /dev/null; then
        error "Docker no está instalado"
        exit 1
    fi
    
    # Verificar Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose no está instalado"
        exit 1
    fi
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        error "Python3 no está instalado"
        exit 1
    fi
    
    success "Todas las dependencias están disponibles"
}

# Función para crear directorios
setup_directories() {
    log "Creando directorios necesarios..."
    
    sudo mkdir -p "$LOG_DIR"
    sudo chown -R $USER:$USER "$LOG_DIR"
    
    sudo mkdir -p "$HEALTH_CHECK_DIR/logs"
    sudo chown -R $USER:$USER "$HEALTH_CHECK_DIR/logs"
    
    sudo mkdir -p "$MONITORING_DIR/data"
    sudo chown -R $USER:$USER "$MONITORING_DIR/data"
    
    success "Directorios creados"
}

# Función para verificar servicios existentes
check_running_services() {
    log "Verificando servicios en ejecución..."
    
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "ai-news"; then
        warning "Servicios de AI News ya están corriendo"
        
        read -p "¿Desea detener los servicios existentes? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Deteniendo servicios existentes..."
            docker-compose -f "$COMPOSE_FILE" down
        fi
    fi
}

# Función para construir imágenes personalizadas
build_custom_images() {
    log "Construyendo imágenes personalizadas..."
    
    # Construir imagen de health checker
    docker build -t ai-news-health-checker:latest "$HEALTH_CHECK_DIR"
    
    success "Imágenes construidas"
}

# Función para iniciar servicios de monitoring
start_monitoring_services() {
    log "Iniciando servicios de monitoring..."
    
    # Iniciar servicios de monitoring
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Servicios de monitoring iniciados"
}

# Función para esperar a que los servicios estén listos
wait_for_services() {
    log "Esperando a que los servicios estén listos..."
    
    local max_attempts=30
    local attempt=1
    
    # Servicios para verificar
    local services=(
        "prometheus:9090"
        "grafana:3000"
        "alertmanager:9093"
        "elasticsearch:9200"
        "kibana:5601"
        "uptime-kuma:3001"
    )
    
    for service_port in "${services[@]}"; do
        local service=${service_port%:*}
        local port=${service_port#*:}
        
        log "Esperando a $service (puerto $port)..."
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s "http://localhost:$port" > /dev/null 2>&1; then
                success "$service está listo"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                warning "$service no está disponible aún (puerto $port)"
            else
                echo -n "."
                sleep 2
            fi
            
            attempt=$((attempt + 1))
        done
        attempt=1
    done
}

# Función para configurar health checks
setup_health_checks() {
    log "Configurando health checks..."
    
    # Hacer ejecutable el script de configuración de monitors
    chmod +x "$UPTIME_DIR/setup_monitors.sh"
    
    # Ejecutar configuración de monitors después de un delay
    (
        sleep 30
        "$UPTIME_DIR/setup_monitors.sh"
    ) &
    
    success "Health checks configurados"
}

# Función para verificar configuración
verify_setup() {
    log "Verificando configuración..."
    
    local errors=0
    
    # Verificar Prometheus
    if curl -s "http://localhost:9090/api/v1/targets" | grep -q "success"; then
        success "Prometheus está funcionando"
    else
        error "Prometheus no está respondiendo correctamente"
        errors=$((errors + 1))
    fi
    
    # Verificar Grafana
    if curl -s "http://localhost:3000/api/health" | grep -q "ok"; then
        success "Grafana está funcionando"
    else
        error "Grafana no está respondiendo correctamente"
        errors=$((errors + 1))
    fi
    
    # Verificar AlertManager
    if curl -s "http://localhost:9093/-/healthy" > /dev/null; then
        success "AlertManager está funcionando"
    else
        error "AlertManager no está respondiendo correctamente"
        errors=$((errors + 1))
    fi
    
    # Verificar Elasticsearch
    if curl -s "http://localhost:9200/_cluster/health" | grep -q "green\|yellow"; then
        success "Elasticsearch está funcionando"
    else
        error "Elasticsearch no está respondiendo correctamente"
        errors=$((errors + 1))
    fi
    
    if [ $errors -eq 0 ]; then
        success "Todos los servicios están funcionando correctamente"
    else
        warning "$errors servicios tienen problemas"
    fi
    
    return $errors
}

# Función para mostrar URLs importantes
show_urls() {
    echo
    echo -e "${BLUE}=== URLs de Monitoreo ===${NC}"
    echo -e "${GREEN}Prometheus (Métricas):${NC}     http://localhost:9090"
    echo -e "${GREEN}Grafana (Dashboards):${NC}     http://localhost:3000"
    echo -e "${GREEN}AlertManager (Alertas):${NC}   http://localhost:9093"
    echo -e "${GREEN}Kibana (Logs):${NC}            http://localhost:5601"
    echo -e "${GREEN}Uptime Kuma (Status):${NC}     http://localhost:3001"
    echo -e "${GREEN}Elasticsearch:${NC}            http://localhost:9200"
    echo -e "${GREEN}cAdvisor (Containers):${NC}    http://localhost:8080"
    echo -e "${GREEN}Node Exporter:${NC}            http://localhost:9100"
    echo
    echo -e "${BLUE}=== Credenciales ===${NC}"
    echo -e "${YELLOW}Grafana:${NC} admin / admin123"
    echo
}

# Función para mostrar comandos útiles
show_commands() {
    echo -e "${BLUE}=== Comandos Útiles ===${NC}"
    echo -e "${YELLOW}Ver logs de un servicio:${NC}     docker-compose -f $COMPOSE_FILE logs [servicio]"
    echo -e "${YELLOW}Ver estado de contenedores:${NC}  docker-compose -f $COMPOSE_FILE ps"
    echo -e "${YELLOW}Reiniciar un servicio:${NC}       docker-compose -f $COMPOSE_FILE restart [servicio]"
    echo -e "${YELLOW}Parar todos los servicios:${NC}    docker-compose -f $COMPOSE_FILE down"
    echo -e "${YELLOW}Health check manual:${NC}         docker-compose -f $COMPOSE_FILE exec health-checker python health_checker.py"
    echo
}

# Función principal
main() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}    AI News Aggregator - Monitoring Setup${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo
    
    # Verificar dependencias
    check_dependencies
    
    # Crear directorios
    setup_directories
    
    # Verificar servicios existentes
    check_running_services
    
    # Construir imágenes
    build_custom_images
    
    # Iniciar servicios
    start_monitoring_services
    
    # Esperar servicios
    wait_for_services
    
    # Configurar health checks
    setup_health_checks
    
    # Verificar setup
    verify_setup
    
    # Mostrar URLs
    show_urls
    
    # Mostrar comandos
    show_commands
    
    success "Setup completado! El sistema de monitoring está funcionando."
    echo
    echo -e "${YELLOW}Nota:${NC} Los dashboards en Grafana se configurarán automáticamente."
    echo -e "${YELLOW}Nota:${NC} Uptime Kuma configurará los monitors en unos minutos."
    echo
}

# Manejo de señales
trap 'error "Script interrumpido"; exit 1' INT TERM

# Verificar argumentos
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Uso: $0 [opciones]"
    echo
    echo "Opciones:"
    echo "  --help, -h     Mostrar esta ayuda"
    echo "  --stop         Solo detener servicios de monitoring"
    echo
    exit 0
fi

if [ "$1" = "--stop" ]; then
    log "Deteniendo servicios de monitoring..."
    docker-compose -f "$COMPOSE_FILE" down
    success "Servicios de monitoring detenidos"
    exit 0
fi

# Ejecutar setup completo
main "$@"