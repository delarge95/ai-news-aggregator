#!/bin/bash

# logger.sh - Sistema de logging centralizado para AI News Aggregator
# Versión: 1.0.0
# Descripción: Sistema de logging centralizado con niveles de log, rotación y formateo

set -euo pipefail

# Configuración de logging
readonly LOG_DIR="${LOG_DIR:-./logs}"
readonly LOG_MAX_SIZE="${LOG_MAX_SIZE:-100M}"
readonly LOG_ROTATION="${LOG_ROTATION:-5}"
readonly LOG_TIMESTAMP_FORMAT="${LOG_TIMESTAMP_FORMAT:-%Y-%m-%d %H:%M:%S}"
readonly LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

# Colores para output en consola
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_PURPLE='\033[0;35m'
readonly COLOR_CYAN='\033[0;36m'
readonly COLOR_WHITE='\033[1;37m'
readonly COLOR_RESET='\033[0m'

# Niveles de log con sus colores
declare -A LOG_LEVELS=(
    ["DEBUG"]="$COLOR_BLUE"
    ["INFO"]="$COLOR_GREEN"
    ["WARN"]="$COLOR_YELLOW"
    ["ERROR"]="$COLOR_RED"
    ["CRITICAL"]="$COLOR_RED"
)

# Funciones de logging
log_with_level() {
    local level="$1"
    local message="$2"
    local timestamp
    local script_name
    local timestamp_with_color
    
    timestamp=$(date +"$LOG_TIMESTAMP_FORMAT")
    script_name=$(basename "${BASH_SOURCE[2]}" .sh)
    timestamp_with_color="${COLOR_CYAN}${timestamp}${COLOR_RESET}"
    
    # Verificar si el nivel es válido según LOG_LEVEL
    if ! should_log_level "$level"; then
        return 0
    fi
    
    # Formatear mensaje
    local formatted_message
    if [[ "$3" == "json" ]]; then
        formatted_message=$(format_json_log "$level" "$message" "$script_name" "$timestamp")
    else
        formatted_message="[${timestamp}] [${level}] [${script_name}] $message"
    fi
    
    # Escribir a archivo de log
    log_to_file "$level" "$formatted_message"
    
    # Escribir a consola con colores
    log_to_console "$level" "$formatted_message"
}

should_log_level() {
    local level="$1"
    local log_priority
    
    case "$LOG_LEVEL" in
        "DEBUG") log_priority=0 ;;
        "INFO")  log_priority=1 ;;
        "WARN")  log_priority=2 ;;
        "ERROR") log_priority=3 ;;
        "CRITICAL") log_priority=4 ;;
        *)       log_priority=1 ;;
    esac
    
    local level_priority
    case "$level" in
        "DEBUG") level_priority=0 ;;
        "INFO")  level_priority=1 ;;
        "WARN")  level_priority=2 ;;
        "ERROR") level_priority=3 ;;
        "CRITICAL") level_priority=4 ;;
    esac
    
    [[ $level_priority -ge $log_priority ]]
}

format_json_log() {
    local level="$1"
    local message="$2"
    local script="$3"
    local timestamp="$4"
    
    cat <<EOF
{
    "timestamp": "$timestamp",
    "level": "$level",
    "script": "$script",
    "message": "$message",
    "host": "$(hostname)",
    "user": "$(whoami)"
}
EOF
}

log_to_file() {
    local level="$1"
    local message="$2"
    local log_file="$LOG_DIR/$(date +%Y-%m-%d).log"
    local archived_file="$log_file.$(date +%Y%m%d_%H%M%S).archive"
    
    # Rotación de logs si el archivo es demasiado grande
    if [[ -f "$log_file" ]] && [[ $(stat -f%z "$log_file" 2>/dev/null || stat -c%s "$log_file" 2>/dev/null) -gt $(parse_size "$LOG_MAX_SIZE") ]]; then
        mv "$log_file" "$archived_file"
        gzip "$archived_file"
        
        # Limpiar archivos antiguos
        cleanup_old_logs
    fi
    
    echo "$message" >> "$log_file"
}

log_to_console() {
    local level="$1"
    local message="$2"
    local color
    
    color="${LOG_LEVELS[$level]:-$COLOR_WHITE}"
    
    # Detectar si estamos en CI/CD o no hay TTY
    if [[ -n "${CI:-}" ]] || [[ ! -t 1 ]]; then
        echo "$message"
    else
        echo -e "${color}${message}${COLOR_RESET}"
    fi
}

parse_size() {
    local size="$1"
    local multiplier=1
    
    case "${size^^}" in
        *K) multiplier=1024 ;;
        *M) multiplier=$((1024*1024)) ;;
        *G) multiplier=$((1024*1024*1024)) ;;
    esac
    
    echo $(( $(echo "$size" | sed 's/[^0-9]//g') * multiplier ))
}

cleanup_old_logs() {
    local count
    count=$(find "$LOG_DIR" -name "*.log.*.archive.gz" | wc -l)
    
    if [[ $count -gt $LOG_ROTATION ]]; then
        find "$LOG_DIR" -name "*.log.*.archive.gz" -type f -printf '%T@ %p\n' | \
        sort -n | head -n $((count - LOG_ROTATION)) | \
        cut -d' ' -f2- | xargs rm -f
    fi
}

# Funciones públicas de logging
log_debug() {
    log_with_level "DEBUG" "$1" "$2"
}

log_info() {
    log_with_level "INFO" "$1" "$2"
}

log_warn() {
    log_with_level "WARN" "$1" "$2"
}

log_error() {
    log_with_level "ERROR" "$1" "$2"
}

log_critical() {
    log_with_level "CRITICAL" "$1" "$2"
}

log_success() {
    local message="$1"
    log_info "✅ $message"
}

# Funciones de utilidad para archivos de log específicos
get_deployment_log() {
    echo "$LOG_DIR/deployment-$(date +%Y%m%d).log"
}

get_deployment_archive() {
    local timestamp="$1"
    echo "$LOG_DIR/deployment-${timestamp}.archive.gz"
}

# Función para inicializar logging para un script específico
init_script_logging() {
    local script_name="${1:-$(basename "${BASH_SOURCE[1]}" .sh)}"
    local log_file="$LOG_DIR/${script_name}-$(date +%Y%m%d).log"
    
    log_info "Iniciando logging para script: $script_name"
    log_info "Archivo de log: $log_file"
    
    # Crear archivo de log específico
    touch "$log_file"
    
    # Configurar trap para logging de errores
    trap 'log_error "Script interrumpido. Último comando: $BASH_COMMAND"' ERR
    
    return 0
}

# Función para logging de métricas
log_metric() {
    local metric_name="$1"
    local metric_value="$2"
    local timestamp
    
    timestamp=$(date +%Y-%m-%dT%H:%M:%S)
    
    local log_message
    log_message="METRIC: {\"name\":\"$metric_name\",\"value\":$metric_value,\"timestamp\":\"$timestamp\"}"
    
    if [[ "${LOG_METRICS:-false}" == "true" ]]; then
        log_to_file "INFO" "$log_message"
        log_to_console "INFO" "[METRIC] $metric_name: $metric_value"
    fi
}

# Función para logging de eventos de despliegue
log_deployment_event() {
    local event_type="$1"
    local event_data="$2"
    local timestamp
    
    timestamp=$(date +%Y-%m-%dT%H:%M:%S)
    
    local log_message
    log_message="DEPLOYMENT: {\"type\":\"$event_type\",\"data\":$event_data,\"timestamp\":\"$timestamp\"}"
    
    log_to_file "INFO" "$log_message"
    log_to_console "INFO" "[DEPLOYMENT] $event_type"
}

# Exportar funciones para uso en otros scripts
export -f log_info log_warn log_error log_critical log_debug log_success
export -f init_script_logging log_metric log_deployment_event get_deployment_log

# Si el script se ejecuta directamente, mostrar ayuda
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Sistema de Logging Centralizado - AI News Aggregator"
    echo "Uso: source logger.sh && init_script_logging [nombre_script]"
    echo ""
    echo "Funciones disponibles:"
    echo "  log_info \"mensaje\"     - Log informativo"
    echo "  log_warn \"mensaje\"     - Log de advertencia"
    echo "  log_error \"mensaje\"    - Log de error"
    echo "  log_critical \"mensaje\" - Log crítico"
    echo "  log_debug \"mensaje\"    - Log de debug"
    echo "  log_success \"mensaje\"  - Log de éxito"
    echo "  log_metric \"nombre\" valor - Log de métrica"
    echo ""
    echo "Variables de entorno:"
    echo "  LOG_LEVEL=DEBUG|INFO|WARN|ERROR|CRITICAL"
    echo "  LOG_DIR=./logs"
    echo "  LOG_MAX_SIZE=100M"
    echo "  LOG_ROTATION=5"
    echo "  LOG_METRICS=true|false"
fi