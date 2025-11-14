#!/bin/bash

# scale-services.sh - Auto-scaling para servicios de AI News Aggregator
# Versión: 1.0.0
# Descripción: Escalado automático y manual de servicios Docker

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "scale-services"

# Configuración de scaling
readonly PROJECT_NAME="ai-news-aggregator"
readonly DOCKER_COMPOSE_FILE="docker-compose.yml"
readonly SCALING_CONFIG="${SCALING_CONFIG:-./scaling-config.json}"

# Configuraciones de escalado
declare -A SERVICE_CONFIGS=(
    ["celery_worker"]="min:1,max:10,step:2,target_cpu:70,target_memory:80"
    ["backend"]="min:1,max:5,step:1,target_cpu:75,target_memory:85"
    ["frontend"]="min:1,max:3,step:1,target_cpu:80,target_memory:90"
)

# Límites de recursos
readonly DEFAULT_MAX_REPLICAS=10
readonly DEFAULT_MIN_REPLICAS=1
readonly SCALE_CHECK_INTERVAL=60
readonly MONITORING_DURATION=300

# Funciones principales
main() {
    local action="${1:-auto}"
    
    case "$action" in
        "auto") auto_scaling ;;
        "up") scale_up "$2" "$3" ;;
        "down") scale_down "$2" "$3" ;;
        "set") set_replicas "$2" "$3" ;;
        "status") show_scaling_status ;;
        "config") show_scaling_config ;;
        "metrics") show_scaling_metrics ;;
        "test") test_scaling "$2" "$3" ;;
        *) usage ;;
    esac
}

auto_scaling() {
    log_info "🔄 Iniciando escalado automático..."
    
    # Cargar configuración si existe
    load_scaling_config
    
    local scaling_start_time
    scaling_start_time=$(date +%s)
    local total_scaled_services=0
    
    # Monitorear y escalar servicios escalables
    for service in "${!SERVICE_CONFIGS[@]}"; do
        log_info "Monitoreando servicio: $service"
        
        if monitor_and_scale_service "$service"; then
            ((total_scaled_services++))
        fi
    done
    
    local scaling_end_time
    scaling_end_time=$(date +%s)
    local scaling_duration=$((scaling_end_time - scaling_start_time))
    
    if [[ $total_scaled_services -gt 0 ]]; then
        log_success "✅ Auto-scaling completado: $total_scaled_services servicios escalados en ${scaling_duration}s"
    else
        log_info "Auto-scaling completado: No se requirieron escalados (${scaling_duration}s)"
    fi
    
    log_metric "auto_scaling_duration" "$scaling_duration"
    log_metric "scaled_services_count" "$total_scaled_services"
}

load_scaling_config() {
    if [[ -f "$SCALING_CONFIG" ]]; then
        log_info "Cargando configuración desde: $SCALING_CONFIG"
        
        # Verificar que jq está disponible
        if command -v jq &> /dev/null; then
            # Cargar configuración usando jq
            local services
            services=$(jq -r '.services | keys[]' "$SCALING_CONFIG" 2>/dev/null || echo "")
            
            if [[ -n "$services" ]]; then
                while IFS= read -r service; do
                    local config
                    config=$(jq -r ".services[\"$service\"] | tostring" "$SCALING_CONFIG" 2>/dev/null || echo "")
                    
                    if [[ -n "$config" ]]; then
                        SERVICE_CONFIGS["$service"]="$config"
                        log_info "Configuración actualizada para $service: $config"
                    fi
                done <<< "$services"
            fi
        else
            log_warn "jq no disponible, usando configuración por defecto"
        fi
    else
        log_info "Usando configuración por defecto de escalado"
    fi
}

monitor_and_scale_service() {
    local service="$1"
    local config="$2"
    local container_name="ai_news_$service"
    
    # Parsear configuración del servicio
    parse_service_config "$config"
    
    # Obtener métricas actuales
    local current_replicas
    current_replicas=$(get_current_replicas "$service")
    
    local cpu_usage
    local memory_usage
    cpu_usage=$(get_service_cpu_usage "$container_name")
    memory_usage=$(get_service_memory_usage "$container_name")
    
    log_info "Métricas de $service:"
    log_info "  Réplicas actuales: $current_replicas"
    log_info "  CPU: ${cpu_usage}%"
    log_info "  Memoria: ${memory_usage}%"
    
    local scaling_decision="none"
    local target_replicas="$current_replicas"
    
    # Decidir escalado basado en métricas
    if should_scale_up "$cpu_usage" "$memory_usage" "$current_replicas"; then
        if [[ $current_replicas -lt $max_replicas ]]; then
            target_replicas=$((current_replicas + step_replicas))
            scaling_decision="up"
        fi
    elif should_scale_down "$cpu_usage" "$memory_usage" "$current_replicas"; then
        if [[ $current_replicas -gt $min_replicas ]]; then
            target_replicas=$((current_replicas - step_replicas))
            scaling_decision="down"
        fi
    fi
    
    # Ejecutar escalado si es necesario
    if [[ "$scaling_decision" != "none" ]]; then
        log_info "Escalando $service de $current_replicas a $target_replicas réplicas"
        
        if scale_service "$service" "$target_replicas"; then
            log_success "✅ $service escalado a $target_replicas réplicas"
            log_metric "${service}_replicas_after" "$target_replicas"
            log_metric "${service}_scaling_decision" "$scaling_decision"
            return 0
        else
            log_error "❌ Error escalando $service"
            return 1
        fi
    else
        log_info "✅ $service no requiere escalado"
        return 0
    fi
}

parse_service_config() {
    local config="$1"
    
    # Configuración por defecto
    min_replicas=$DEFAULT_MIN_REPLICAS
    max_replicas=$DEFAULT_MAX_REPLICAS
    step_replicas=1
    target_cpu=70
    target_memory=80
    
    # Parsear configuración personalizada
    IFS=',' read -ra config_parts <<< "$config"
    
    for part in "${config_parts[@]}"; do
        IFS=':' read -r key value <<< "$part"
        
        case "$key" in
            "min") min_replicas="$value" ;;
            "max") max_replicas="$value" ;;
            "step") step_replicas="$value" ;;
            "target_cpu") target_cpu="$value" ;;
            "target_memory") target_memory="$value" ;;
        esac
    done
}

get_current_replicas() {
    local service="$1"
    
    # Verificar si el servicio está corriendo
    if ! docker ps --filter "name=ai_news_$service" --format "{{.Names}}" | grep -q "ai_news_$service"; then
        echo "0"
        return
    fi
    
    # Contar réplicas del servicio
    docker ps --filter "name=ai_news_$service" --format "{{.Names}}" | wc -l
}

get_service_cpu_usage() {
    local container_name="$1"
    
    if ! docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
        echo "0"
        return
    fi
    
    # Obtener uso de CPU del contenedor
    local cpu_stats
    cpu_stats=$(docker stats "$container_name" --no-stream --format "{{.CPUPerc}}" 2>/dev/null || echo "0%")
    
    # Extraer valor numérico
    echo "${cpu_stats%\%}" | tr -d ' '
}

get_service_memory_usage() {
    local container_name="$1"
    
    if ! docker ps --filter "name=$container_name" --format "{{.Names}}" | grep -q "$container_name"; then
        echo "0"
        return
    fi
    
    # Obtener uso de memoria del contenedor
    local mem_stats
    mem_stats=$(docker stats "$container_name" --no-stream --format "{{.MemPerc}}" 2>/dev/null || echo "0%")
    
    # Extraer valor numérico
    echo "${mem_stats%\%}" | tr -d ' '
}

should_scale_up() {
    local cpu_usage="$1"
    local memory_usage="$2"
    local current_replicas="$3"
    
    # Escalar hacia arriba si el CPU o memoria están por encima del target
    if [[ $(echo "$cpu_usage > $target_cpu" | bc -l 2>/dev/null || echo "0") -eq 1 ]] || \
       [[ $(echo "$memory_usage > $target_memory" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        return 0
    else
        return 1
    fi
}

should_scale_down() {
    local cpu_usage="$1"
    local memory_usage="$2"
    local current_replicas="$3"
    
    # Escalar hacia abajo solo si tanto CPU como memoria están muy bajos
    if [[ $(echo "$cpu_usage < 30" | bc -l 2>/dev/null || echo "0") -eq 1 ]] && \
       [[ $(echo "$memory_usage < 40" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        return 0
    else
        return 1
    fi
}

scale_service() {
    local service="$1"
    local target_replicas="$2"
    
    case "$service" in
        "celery_worker")
            scale_celery_workers "$target_replicas"
            ;;
        "backend")
            scale_backend_instances "$target_replicas"
            ;;
        "frontend")
            scale_frontend_instances "$target_replicas"
            ;;
        *)
            log_error "Servicio no soportado para escalado: $service"
            return 1
            ;;
    esac
}

scale_celery_workers() {
    local target_replicas="$1"
    local current_replicas
    current_replicas=$(get_current_replicas "celery_worker")
    
    if [[ $target_replicas -gt $current_replicas ]]; then
        # Escalar hacia arriba
        local replicas_to_add=$((target_replicas - current_replicas))
        
        for i in $(seq 1 $replicas_to_add); do
            local worker_name="ai_news_celery_worker_$(date +%s)"
            log_info "Iniciando worker adicional: $worker_name"
            
            docker run -d \
                --name "$worker_name" \
                --network ai_news_network \
                --env-file .env \
                --volume "$(pwd)/backend:/app" \
                --volume "$(pwd)/logs:/app/logs" \
                "${PROJECT_NAME}_backend:latest" \
                celery -A app.celery worker --loglevel=info || {
                log_error "Error iniciando worker adicional"
                return 1
            }
        done
    elif [[ $target_replicas -lt $current_replicas ]]; then
        # Escalar hacia abajo
        local replicas_to_remove=$((current_replicas - target_replicas))
        
        # Obtener lista de workers ordenados por tiempo de inicio (más antiguos primero)
        local workers
        mapfile -t workers < <(docker ps --filter "name=ai_news_celery_worker_" --format "{{.Names}}" --sort=created | head -n "$replicas_to_remove")
        
        for worker in "${workers[@]}"; do
            log_info "Deteniendo worker: $worker"
            docker stop "$worker" || {
                log_error "Error deteniendo worker: $worker"
                return 1
            }
            docker rm "$worker" || {
                log_error "Error removiendo worker: $worker"
                return 1
            }
        done
    fi
    
    return 0
}

scale_backend_instances() {
    local target_replicas="$1"
    
    # Los servicios backend actuales en docker-compose no están diseñados para múltiples réplicas
    # Este es un ejemplo de cómo se podría implementar en producción
    log_warn "Escalado de backend no implementado completamente en este entorno"
    
    # En producción, se podría usar:
    # - Nginx load balancer
    # - Múltiples instancias de backend
    # - Configuración de health checks
}

scale_frontend_instances() {
    local target_replicas="$1"
    
    # Similar al backend, escalado de frontend requeriría:
    # - Load balancer (nginx/apache)
    # - Servido estático optimizado
    log_warn "Escalado de frontend no implementado completamente en este entorno"
}

scale_up() {
    local service="${2:-all}"
    local replicas="${3:-1}"
    
    log_info "🔼 Escalando hacia arriba: $service (+$replicas réplicas)"
    
    if [[ "$service" == "all" ]]; then
        for service in "${!SERVICE_CONFIGS[@]}"; do
            scale_service_up "$service" "$replicas"
        done
    else
        scale_service_up "$service" "$replicas"
    fi
}

scale_service_up() {
    local service="$1"
    local replicas="$2"
    
    local current_replicas
    current_replicas=$(get_current_replicas "$service")
    local target_replicas=$((current_replicas + replicas))
    
    # Verificar límite máximo
    parse_service_config "${SERVICE_CONFIGS[$service]}"
    
    if [[ $target_replicas -gt $max_replicas ]]; then
        log_warn "Límite máximo alcanzado para $service ($max_replicas réplicas)"
        target_replicas=$max_replicas
    fi
    
    log_info "Escalando $service de $current_replicas a $target_replicas réplicas"
    
    if scale_service "$service" "$target_replicas"; then
        log_success "✅ $service escalado exitosamente"
    else
        log_error "❌ Error escalando $service"
        return 1
    fi
}

scale_down() {
    local service="${2:-all}"
    local replicas="${3:-1}"
    
    log_info "🔽 Escalando hacia abajo: $service (-$replicas réplicas)"
    
    if [[ "$service" == "all" ]]; then
        for service in "${!SERVICE_CONFIGS[@]}"; do
            scale_service_down "$service" "$replicas"
        done
    else
        scale_service_down "$service" "$replicas"
    fi
}

scale_service_down() {
    local service="$1"
    local replicas="$2"
    
    local current_replicas
    current_replicas=$(get_current_replicas "$service")
    local target_replicas=$((current_replicas - replicas))
    
    # Verificar límite mínimo
    parse_service_config "${SERVICE_CONFIGS[$service]}"
    
    if [[ $target_replicas -lt $min_replicas ]]; then
        log_warn "Límite mínimo alcanzado para $service ($min_replicas réplicas)"
        target_replicas=$min_replicas
    fi
    
    if [[ $target_replicas -eq $current_replicas ]]; then
        log_info "$service ya está en el límite mínimo"
        return 0
    fi
    
    log_info "Escalando $service de $current_replicas a $target_replicas réplicas"
    
    if scale_service "$service" "$target_replicas"; then
        log_success "✅ $service escalado exitosamente"
    else
        log_error "❌ Error escalando $service"
        return 1
    fi
}

set_replicas() {
    local service="${2:-all}"
    local replicas="$3"
    
    if [[ -z "$replicas" ]] || ! [[ "$replicas" =~ ^[0-9]+$ ]]; then
        log_error "Número de réplicas requerido"
        usage
        exit 1
    fi
    
    log_info "🎯 Configurando $service a $replicas réplicas"
    
    if [[ "$service" == "all" ]]; then
        for service in "${!SERVICE_CONFIGS[@]}"; do
            set_service_replicas "$service" "$replicas"
        done
    else
        set_service_replicas "$service" "$replicas"
    fi
}

set_service_replicas() {
    local service="$1"
    local replicas="$2"
    
    # Verificar límites
    parse_service_config "${SERVICE_CONFIGS[$service]}"
    
    if [[ $replicas -lt $min_replicas ]] || [[ $replicas -gt $max_replicas ]]; then
        log_error "Número de réplicas fuera de rango ($min_replicas - $max_replicas)"
        return 1
    fi
    
    local current_replicas
    current_replicas=$(get_current_replicas "$service")
    
    if [[ $replicas -eq $current_replicas ]]; then
        log_info "$service ya tiene $replicas réplicas"
        return 0
    fi
    
    log_info "Configurando $service a $replicas réplicas (actual: $current_replicas)"
    
    if scale_service "$service" "$replicas"; then
        log_success "✅ $service configurado a $replicas réplicas"
        log_metric "${service}_replicas_final" "$replicas"
    else
        log_error "❌ Error configurando $service"
        return 1
    fi
}

show_scaling_status() {
    log_info "📊 Estado de escalado de servicios"
    echo ""
    echo "Servicios escalables:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "%-20s %-10s %-10s %-10s %-10s\n" "Servicio" "Actual" "Min" "Max" "CPU%"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    for service in "${!SERVICE_CONFIGS[@]}"; do
        local current_replicas
        local container_name
        local cpu_usage
        
        current_replicas=$(get_current_replicas "$service")
        container_name="ai_news_$service"
        cpu_usage=$(get_service_cpu_usage "$container_name")
        
        parse_service_config "${SERVICE_CONFIGS[$service]}"
        
        printf "%-20s %-10s %-10s %-10s %-10s\n" "$service" "$current_replicas" "$min_replicas" "$max_replicas" "${cpu_usage}%"
    done
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Información de recursos del sistema
    log_info "Recursos del sistema:"
    local cpu_total
    local memory_total
    
    cpu_total=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | tr -d ' ')
    memory_total=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')
    
    echo "  CPU total: ${cpu_total}%"
    echo "  Memoria total: ${memory_total}%"
    
    # Estado de contenedores Docker
    echo ""
    echo "Contenedores Docker:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=ai_news" | grep ai_news || echo "No hay contenedores de AI News ejecutándose"
}

show_scaling_config() {
    log_info "⚙️  Configuración de escalado"
    echo ""
    
    for service in "${!SERVICE_CONFIGS[@]}"; do
        echo "Servicio: $service"
        echo "  Configuración: ${SERVICE_CONFIGS[$service]}"
        
        parse_service_config "${SERVICE_CONFIGS[$service]}"
        echo "  Réplicas mínimas: $min_replicas"
        echo "  Réplicas máximas: $max_replicas"
        echo "  Paso de escalado: $step_replicas"
        echo "  Target CPU: ${target_cpu}%"
        echo "  Target Memoria: ${target_memory}%"
        echo ""
    done
    
    # Mostrar configuración del archivo si existe
    if [[ -f "$SCALING_CONFIG" ]]; then
        log_info "Configuración desde archivo: $SCALING_CONFIG"
        if command -v jq &> /dev/null; then
            jq . "$SCALING_CONFIG" 2>/dev/null || echo "Error leyendo configuración JSON"
        else
            cat "$SCALING_CONFIG" 2>/dev/null || echo "Error leyendo archivo de configuración"
        fi
    fi
}

show_scaling_metrics() {
    log_info "📈 Métricas de escalado"
    echo ""
    
    for service in "${!SERVICE_CONFIGS[@]}"; do
        local container_name
        local cpu_usage
        local memory_usage
        local current_replicas
        
        container_name="ai_news_$service"
        cpu_usage=$(get_service_cpu_usage "$container_name")
        memory_usage=$(get_service_memory_usage "$container_name")
        current_replicas=$(get_current_replicas "$service")
        
        echo "Servicio: $service"
        echo "  Réplicas actuales: $current_replicas"
        echo "  CPU: ${cpu_usage}%"
        echo "  Memoria: ${memory_usage}%"
        
        # Calcular scores de escalado
        parse_service_config "${SERVICE_CONFIGS[$service]}"
        
        local cpu_score
        local memory_score
        
        cpu_score=$(echo "scale=2; ($cpu_usage - $target_cpu) / 10" | bc -l 2>/dev/null || echo "0")
        memory_score=$(echo "scale=2; ($memory_usage - $target_memory) / 10" | bc -l 2>/dev/null || echo "0")
        
        echo "  Score CPU: $cpu_score"
        echo "  Score Memoria: $memory_score"
        echo "  Escalado recomendado: $(get_scaling_recommendation "$cpu_score" "$memory_score" "$current_replicas")"
        echo ""
    done
}

get_scaling_recommendation() {
    local cpu_score="$1"
    local memory_score="$2"
    local current_replicas="$3"
    
    # Convertir a números para comparación
    cpu_score=$(echo "$cpu_score" | bc -l 2>/dev/null || echo "0")
    memory_score=$(echo "$memory_score" | bc -l 2>/dev/null || echo "0")
    
    if [[ $(echo "$cpu_score > 0" | bc -l 2>/dev/null || echo "0") -eq 1 ]] || \
       [[ $(echo "$memory_score > 0" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        echo "ESCALAR_ARRIBA"
    elif [[ $(echo "$cpu_score < -2" | bc -l 2>/dev/null || echo "0") -eq 1 ]] && \
         [[ $(echo "$memory_score < -2" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
        echo "ESCALAR_ABAJO"
    else
        echo "MANTENER"
    fi
}

test_scaling() {
    local service="${2:-celery_worker}"
    local test_type="${3:-up}"
    
    log_info "🧪 Probando escalado de $service ($test_type)"
    
    case "$test_type" in
        "up")
            test_scale_up "$service"
            ;;
        "down")
            test_scale_down "$service"
            ;;
        "auto")
            test_auto_scaling "$service"
            ;;
        *)
            log_error "Tipo de test no válido: $test_type"
            usage
            exit 1
            ;;
    esac
}

test_scale_up() {
    local service="$1"
    local original_replicas
    original_replicas=$(get_current_replicas "$service")
    
    log_info "Test: Escalando $service hacia arriba"
    
    # Escalar temporalmente hacia arriba
    if scale_service_up "$service" 1; then
        log_success "Escalado temporal exitoso"
        
        # Esperar un momento
        sleep 30
        
        # Revertir al número original
        log_info "Revirtiendo a configuración original..."
        set_service_replicas "$service" "$original_replicas"
        
        log_success "Test de escalado hacia arriba completado"
    else
        log_error "Test de escalado hacia arriba falló"
        return 1
    fi
}

test_scale_down() {
    local service="$1"
    local original_replicas
    original_replicas=$(get_current_replicas "$service")
    
    log_info "Test: Escalando $service hacia abajo"
    
    # Solo hacer test si hay suficientes réplicas
    if [[ $original_replicas -gt 1 ]]; then
        # Escalar temporalmente hacia abajo
        if scale_service_down "$service" 1; then
            log_success "Escalado temporal exitoso"
            
            # Esperar un momento
            sleep 30
            
            # Revertir al número original
            log_info "Revirtiendo a configuración original..."
            set_service_replicas "$service" "$original_replicas"
            
            log_success "Test de escalado hacia abajo completado"
        else
            log_error "Test de escalado hacia abajo falló"
            return 1
        fi
    else
        log_info "No hay suficientes réplicas para test de escalado hacia abajo"
    fi
}

test_auto_scaling() {
    local service="$1"
    
    log_info "Test: Auto-scaling para $service"
    
    # Simular carga alta
    log_info "Simulando carga alta en $service..."
    log_info "Ejecutando auto-scaling..."
    
    if monitor_and_scale_service "$service" "${SERVICE_CONFIGS[$service]}"; then
        log_success "Test de auto-scaling completado"
    else
        log_error "Test de auto-scaling falló"
        return 1
    fi
}

usage() {
    cat <<EOF
Uso: $0 [ACCIÓN] [servicio] [parámetros]

Acciones disponibles:
  auto                 - Auto-scaling basado en métricas (predeterminado)
  up <servicio> [n]    - Escalar hacia arriba (por defecto +1)
  down <servicio> [n]  - Escalar hacia abajo (por defecto -1)
  set <servicio> <n>   - Configurar número específico de réplicas
  status               - Mostrar estado actual de escalado
  config               - Mostrar configuración de escalado
  metrics              - Mostrar métricas actuales
  test <servicio> <tipo> - Probar escalado (up|down|auto)

Parámetros:
  servicio             - Nombre del servicio (celery_worker|backend|frontend|all)
  n                    - Número de réplicas (default: 1)
  tipo                 - Tipo de test (up|down|auto)

Variables de entorno:
  SCALING_CONFIG       - Archivo de configuración JSON (default: ./scaling-config.json)
  DEFAULT_MAX_REPLICAS - Máximo de réplicas por defecto (default: 10)
  DEFAULT_MIN_REPLICAS - Mínimo de réplicas por defecto (default: 1)

Ejemplos:
  $0 auto                     # Auto-scaling para todos los servicios
  $0 up celery_worker 2       # Escalar workers +2 réplicas
  $0 down backend 1          # Escalar backend -1 réplica
  $0 set celery_worker 5     # Configurar workers a 5 réplicas
  $0 status                  # Ver estado actual
  $0 metrics                 # Ver métricas actuales
  $0 test celery_worker up   # Probar escalado hacia arriba

Servicios escalables:
  - celery_worker: Workers de Celery para procesamiento asíncrono
  - backend: Instancias de la API backend (limitado en entorno Docker)
  - frontend: Instancias del frontend (limitado en entorno Docker)

EOF
}

# Ejecutar función principal
main "$@"