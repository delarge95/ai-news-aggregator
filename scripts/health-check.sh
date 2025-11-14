#!/bin/bash

# health-check.sh - Verificaciones post-deployment para AI News Aggregator
# Versión: 1.0.0
# Descripción: Health checks comprehensivos con métricas y alertas

set -euo pipefail

# Importar sistema de logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/logger.sh"
init_script_logging "health-check"

# Configuración de health checks
readonly BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
readonly FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
readonly DATABASE_HOST="${DATABASE_HOST:-localhost}"
readonly DATABASE_PORT="${DATABASE_PORT:-5432}"
readonly REDIS_HOST="${REDIS_HOST:-localhost}"
readonly REDIS_PORT="${REDIS_PORT:-6379}"

# Timeouts y thresholds
readonly CHECK_TIMEOUT="${CHECK_TIMEOUT:-30}"
readonly MAX_RESPONSE_TIME="${MAX_RESPONSE_TIME:-5000}" # milliseconds
readonly MAX_CPU_USAGE="${MAX_CPU_USAGE:-80}" # percentage
readonly MAX_MEMORY_USAGE="${MAX_MEMORY_USAGE:-85}" # percentage
readonly MIN_DISK_SPACE="${MIN_DISK_SPACE:-10}" # percentage

# Funciones principales
main() {
    local action="${1:-all}"
    local format="${2:-console}"
    
    case "$action" in
        "all") run_all_checks ;;
        "services") check_services ;;
        "endpoints") check_endpoints ;;
        "database") check_database ;;
        "cache") check_cache ;;
        "performance") check_performance ;;
        "resources") check_resources ;;
        "external") check_external_apis ;;
        "format") format="${3:-console}" ;;
        *) usage ;;
    esac
    
    if [[ "$action" == "format" ]]; then
        format_test_results "$format"
    fi
}

run_all_checks() {
    log_info "🔍 Ejecutando verificaciones de salud completas..."
    
    local start_time
    start_time=$(date +%s)
    local total_checks=0
    local passed_checks=0
    
    # Ejecutar todas las verificaciones
    check_services && ((passed_checks++))
    ((total_checks++))
    
    check_endpoints && ((passed_checks++))
    ((total_checks++))
    
    check_database && ((passed_checks++))
    ((total_checks++))
    
    check_cache && ((passed_checks++))
    ((total_checks++))
    
    check_performance && ((passed_checks++))
    ((total_checks++))
    
    check_resources && ((passed_checks++))
    ((total_checks++))
    
    check_external_apis && ((passed_checks++))
    ((total_checks++))
    
    local end_time
    end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    # Reporte final
    echo ""
    log_info "📊 Resumen de verificaciones de salud:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Total de verificaciones: $total_checks"
    echo "  Verificaciones exitosas: $passed_checks"
    echo "  Verificaciones fallidas: $((total_checks - passed_checks))"
    echo "  Tiempo total: ${total_duration}s"
    echo "  Estado: $(if [[ $passed_checks -eq $total_checks ]]; then echo "✅ HEALTHY"; else echo "❌ UNHEALTHY"; fi)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    log_metric "health_check_total" "$total_checks"
    log_metric "health_check_passed" "$passed_checks"
    log_metric "health_check_failed" "$((total_checks - passed_checks))"
    log_metric "health_check_duration" "$total_duration"
    
    if [[ $passed_checks -eq $total_checks ]]; then
        log_success "✅ Todas las verificaciones pasaron"
        return 0
    else
        log_error "❌ Algunas verificaciones fallaron"
        return 1
    fi
}

check_services() {
    log_info "🔧 Verificando estado de servicios Docker..."
    
    local services_status
    services_status=$(docker-compose -f docker-compose.yml ps --services --filter "status=running")
    
    # Definir servicios esperados
    local expected_services=(
        "postgres"
        "redis"
        "backend"
        "celery_worker"
        "celery_beat"
        "frontend"
    )
    
    local failed_services=0
    
    for service in "${expected_services[@]}"; do
        if echo "$services_status" | grep -q "^$service$"; then
            local container_name
            container_name="ai_news_$service"
            
            # Verificar estado del contenedor
            local container_status
            container_status=$(docker inspect "$container_name" --format='{{.State.Status}}' 2>/dev/null || echo "not_found")
            
            if [[ "$container_status" == "running" ]]; then
                log_success "✅ $service: OK (running)"
            else
                log_error "❌ $service: FAIL (status: $container_status)"
                ((failed_services++))
            fi
        else
            log_error "❌ $service: FAIL (not running)"
            ((failed_services++))
        fi
    done
    
    # Verificar dependencias de red
    local network_status
    network_status=$(docker network ls --filter name=ai_news_network --format "{{.Name}}")
    
    if [[ -n "$network_status" ]]; then
        log_success "✅ Red Docker: OK"
    else
        log_error "❌ Red Docker: FAIL (network not found)"
        ((failed_services++))
    fi
    
    if [[ $failed_services -eq 0 ]]; then
        log_success "✅ Todos los servicios están funcionando correctamente"
        return 0
    else
        log_error "❌ $failed_services servicios con problemas"
        return 1
    fi
}

check_endpoints() {
    log_info "🌐 Verificando endpoints HTTP..."
    
    local endpoints=(
        "GET|http://localhost:8000/health|Backend Health"
        "GET|http://localhost:8000/api/v1/articles|Articles API"
        "GET|http://localhost:8000/api/v1/search|Search API"
        "GET|http://localhost:8000/api/v1/analytics|Analytics API"
        "GET|http://localhost:3000|Frontend"
    )
    
    local failed_endpoints=0
    
    for endpoint in "${endpoints[@]}"; do
        IFS='|' read -r method url description <<< "$endpoint"
        
        local response_time
        local status_code
        
        # Medir tiempo de respuesta y código de estado
        response_time=$(measure_response_time "$method" "$url")
        status_code=$(get_http_status "$method" "$url")
        
        if [[ $? -eq 0 ]] && [[ "$status_code" -ge 200 ]] && [[ "$status_code" -lt 400 ]]; then
            if [[ "$response_time" -le "$MAX_RESPONSE_TIME" ]]; then
                log_success "✅ $description: OK (${status_code}, ${response_time}ms)"
            else
                log_warn "⚠️  $description: SLOW (${status_code}, ${response_time}ms)"
                log_metric "${description}_response_time" "$response_time"
            fi
        else
            log_error "❌ $description: FAIL (${status_code}, ${response_time}ms)"
            ((failed_endpoints++))
        fi
    done
    
    if [[ $failed_endpoints -eq 0 ]]; then
        log_success "✅ Todos los endpoints responden correctamente"
        return 0
    else
        log_error "❌ $failed_endpoints endpoints con problemas"
        return 1
    fi
}

measure_response_time() {
    local method="$1"
    local url="$2"
    
    local start_time
    start_time=$(date +%s%3N)
    
    case "$method" in
        "GET")
            curl -s -w "%{http_code}" -o /dev/null --max-time "$CHECK_TIMEOUT" "$url"
            ;;
        "POST")
            curl -s -w "%{http_code}" -o /dev/null -X POST --max-time "$CHECK_TIMEOUT" "$url"
            ;;
    esac
    
    local end_time
    end_time=$(date +%s%3N)
    
    local response_time
    response_time=$((end_time - start_time))
    
    echo "$response_time"
}

get_http_status() {
    local method="$1"
    local url="$2"
    
    case "$method" in
        "GET")
            curl -s -o /dev/null --max-time "$CHECK_TIMEOUT" -w "%{http_code}" "$url"
            ;;
        "POST")
            curl -s -o /dev/null -X POST --max-time "$CHECK_TIMEOUT" -w "%{http_code}" "$url"
            ;;
    esac
}

check_database() {
    log_info "🗄️  Verificando base de datos..."
    
    local db_checks=0
    local db_failed=0
    
    # Verificar conectividad
    if docker exec ai_news_postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "✅ Database connectivity: OK"
        ((db_checks++))
    else
        log_error "❌ Database connectivity: FAIL"
        ((db_failed++))
    fi
    
    # Verificar base de datos específica
    if docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT 1;" > /dev/null 2>&1; then
        log_success "✅ Database access: OK"
        ((db_checks++))
    else
        log_error "❌ Database access: FAIL"
        ((db_failed++))
    fi
    
    # Verificar tablas principales
    local tables=("articles" "users" "analytics" "trending")
    for table in "${tables[@]}"; do
        if docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT COUNT(*) FROM $table;" > /dev/null 2>&1; then
            local count
            count=$(docker exec ai_news_postgres psql -U postgres -d ai_news_db -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null | tr -d ' \n\r')
            log_success "✅ Table $table: OK ($count records)"
            ((db_checks++))
        else
            log_error "❌ Table $table: FAIL"
            ((db_failed++))
        fi
    done
    
    # Verificar integridad de migraciones
    if docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT * FROM alembic_version;" > /dev/null 2>&1; then
        local version
        version=$(docker exec ai_news_postgres psql -U postgres -d ai_news_db -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null | tr -d ' \n\r')
        log_success "✅ Database migrations: OK (version: $version)"
        ((db_checks++))
    else
        log_warn "⚠️  Database migrations: No version table found"
    fi
    
    if [[ $db_failed -eq 0 ]]; then
        log_success "✅ Base de datos funcionando correctamente ($db_checks/$((db_checks + db_failed)) verificaciones)"
        return 0
    else
        log_error "❌ Base de datos con problemas ($db_failed fallos)"
        return 1
    fi
}

check_cache() {
    log_info "🧠 Verificando caché Redis..."
    
    local cache_checks=0
    local cache_failed=0
    
    # Verificar conectividad
    if docker exec ai_news_redis redis-cli ping | grep -q PONG; then
        log_success "✅ Redis connectivity: OK"
        ((cache_checks++))
    else
        log_error "❌ Redis connectivity: FAIL"
        ((cache_failed++))
    fi
    
    # Verificar operación de escritura/lectura
    if docker exec ai_news_redis redis-cli SET health_check_test "ok" EX 300 > /dev/null 2>&1; then
        local test_value
        test_value=$(docker exec ai_news_redis redis-cli GET health_check_test 2>/dev/null | tr -d '\r\n')
        
        if [[ "$test_value" == "ok" ]]; then
            log_success "✅ Redis operations: OK"
            ((cache_checks++))
        else
            log_error "❌ Redis operations: FAIL (value mismatch)"
            ((cache_failed++))
        fi
    else
        log_error "❌ Redis operations: FAIL (write test)"
        ((cache_failed++))
    fi
    
    # Verificar memoria
    local memory_info
    memory_info=$(docker exec ai_news_redis redis-cli INFO memory 2>/dev/null | grep "used_memory_human")
    
    if [[ -n "$memory_info" ]]; then
        log_success "✅ Redis memory: OK ($memory_info)"
        ((cache_checks++))
    else
        log_error "❌ Redis memory: FAIL (no info)"
        ((cache_failed++))
    fi
    
    # Limpiar clave de prueba
    docker exec ai_news_redis redis-cli DEL health_check_test > /dev/null 2>&1 || true
    
    if [[ $cache_failed -eq 0 ]]; then
        log_success "✅ Caché Redis funcionando correctamente ($cache_checks/$((cache_checks + cache_failed)) verificaciones)"
        return 0
    else
        log_error "❌ Caché Redis con problemas ($cache_failed fallos)"
        return 1
    fi
}

check_performance() {
    log_info "⚡ Verificando rendimiento..."
    
    local performance_checks=0
    local performance_failed=0
    
    # Verificar tiempo de respuesta del endpoint principal
    local response_time
    response_time=$(measure_response_time "GET" "http://localhost:8000/health")
    
    if [[ "$response_time" -le "$MAX_RESPONSE_TIME" ]]; then
        log_success "✅ Response time: OK (${response_time}ms < ${MAX_RESPONSE_TIME}ms)"
        ((performance_checks++))
    else
        log_error "❌ Response time: FAIL (${response_time}ms > ${MAX_RESPONSE_TIME}ms)"
        ((performance_failed++))
    fi
    
    # Verificar throughput
    local requests_per_second
    requests_per_second=$(calculate_requests_per_second)
    
    if [[ "$requests_per_second" -ge 10 ]]; then
        log_success "✅ Throughput: OK (${requests_per_second} req/s)"
        ((performance_checks++))
    else
        log_error "❌ Throughput: FAIL (${requests_per_second} req/s < 10 req/s)"
        ((performance_failed++))
    fi
    
    # Verificar latencia de base de datos
    local db_latency
    db_latency=$(measure_database_latency)
    
    if [[ "$db_latency" -le 100 ]]; then
        log_success "✅ Database latency: OK (${db_latency}ms)"
        ((performance_checks++))
    else
        log_error "❌ Database latency: FAIL (${db_latency}ms > 100ms)"
        ((performance_failed++))
    fi
    
    if [[ $performance_failed -eq 0 ]]; then
        log_success "✅ Rendimiento dentro de parámetros normales ($performance_checks/$((performance_checks + performance_failed)) verificaciones)"
        return 0
    else
        log_error "❌ Problemas de rendimiento detectados ($performance_failed fallos)"
        return 1
    fi
}

calculate_requests_per_second() {
    local start_time
    start_time=$(date +%s)
    local successful_requests=0
    
    # Realizar 10 requests concurrentes
    for i in {1..10}; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" | grep -q "200"; then
            ((successful_requests++))
        fi
    done
    
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $duration -gt 0 ]]; then
        echo $((successful_requests / duration))
    else
        echo 0
    fi
}

measure_database_latency() {
    local start_time
    start_time=$(date +%s%3N)
    
    docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT 1;" > /dev/null 2>&1
    
    local end_time
    end_time=$(date +%s%3N)
    
    echo $((end_time - start_time))
}

check_resources() {
    log_info "💻 Verificando recursos del sistema..."
    
    local resource_checks=0
    local resource_failed=0
    
    # Verificar uso de CPU
    local cpu_usage
    cpu_usage=$(calculate_cpu_usage)
    
    if [[ "$cpu_usage" -le "$MAX_CPU_USAGE" ]]; then
        log_success "✅ CPU usage: OK (${cpu_usage}% < ${MAX_CPU_USAGE}%)"
        ((resource_checks++))
    else
        log_error "❌ CPU usage: FAIL (${cpu_usage}% > ${MAX_CPU_USAGE}%)"
        ((resource_failed++))
    fi
    
    # Verificar uso de memoria
    local memory_usage
    memory_usage=$(calculate_memory_usage)
    
    if [[ "$memory_usage" -le "$MAX_MEMORY_USAGE" ]]; then
        log_success "✅ Memory usage: OK (${memory_usage}% < ${MAX_MEMORY_USAGE}%)"
        ((resource_checks++))
    else
        log_error "❌ Memory usage: FAIL (${memory_usage}% > ${MAX_MEMORY_USAGE}%)"
        ((resource_failed++))
    fi
    
    # Verificar espacio en disco
    local disk_usage
    disk_usage=$(calculate_disk_usage)
    
    if [[ "$disk_usage" -le $((100 - MIN_DISK_SPACE)) ]]; then
        log_success "✅ Disk space: OK (${disk_usage}% used, ${MIN_DISK_SPACE}% free)"
        ((resource_checks++))
    else
        log_error "❌ Disk space: FAIL (${disk_usage}% used, < ${MIN_DISK_SPACE}% free)"
        ((resource_failed++))
    fi
    
    if [[ $resource_failed -eq 0 ]]; then
        log_success "✅ Recursos del sistema dentro de parámetros ($resource_checks/$((resource_checks + resource_failed)) verificaciones)"
        return 0
    else
        log_error "❌ Recursos del sistema con problemas ($resource_failed fallos)"
        return 1
    fi
}

calculate_cpu_usage() {
    if command -v top &> /dev/null; then
        top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | tr -d ' '
    else
        echo "0"
    fi
}

calculate_memory_usage() {
    if command -v free &> /dev/null; then
        free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}'
    else
        echo "0"
    fi
}

calculate_disk_usage() {
    df -h . | awk 'NR==2 {print $5}' | sed 's/%//'
}

check_external_apis() {
    log_info "🌍 Verificando APIs externas..."
    
    # Nota: Este es un ejemplo - ajustar según las APIs externas que use la aplicación
    local external_apis=(
        "NEWSAPI|https://newsapi.org/health|NewsAPI"
        "NYTIMES|https://api.nytimes.com/svc/books/v3/lists/overview.json?api-key=test|New York Times API"
    )
    
    local api_failed=0
    
    for api_spec in "${external_apis[@]}"; do
        IFS='|' read -r api_name api_url api_description <<< "$api_spec"
        
        # Solo verificar que el endpoint responda (no necesariamente autenticado)
        local status_code
        status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$api_url")
        
        if [[ "$status_code" =~ ^[0-9]$ ]] && [[ "$status_code" != "000" ]]; then
            log_success "✅ $api_description: OK (HTTP $status_code)"
        else
            log_warn "⚠️  $api_description: WARN (HTTP $status_code)"
        fi
    done
    
    if [[ $api_failed -eq 0 ]]; then
        log_success "✅ APIs externas verificadas"
        return 0
    else
        log_error "❌ $api_failed APIs externas con problemas"
        return 1
    fi
}

format_test_results() {
    local format="$1"
    local results_file="health-check-results-$(date +%Y%m%d-%H%M%S).json"
    
    case "$format" in
        "json")
            format_json_output "$results_file"
            ;;
        "html")
            format_html_output "$results_file"
            ;;
        "console"|*)
            format_console_output
            ;;
    esac
}

format_json_output() {
    local output_file="$1"
    
    cat > "$output_file" <<EOF
{
    "timestamp": "$(date -Iseconds)",
    "environment": "${DEPLOY_ENV:-production}",
    "hostname": "$(hostname)",
    "overall_status": "$(run_all_checks > /dev/null 2>&1 && echo "healthy" || echo "unhealthy")",
    "checks_performed": [
        "services",
        "endpoints", 
        "database",
        "cache",
        "performance",
        "resources",
        "external_apis"
    ]
}
EOF
    
    log_info "Resultados guardados en: $output_file"
}

format_html_output() {
    local output_file="${1:-health-report.html}"
    
    cat > "$output_file" <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>Health Check Report - AI News Aggregator</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        .success { border-left-color: #28a745; }
        .error { border-left-color: #dc3545; }
        .warning { border-left-color: #ffc107; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Health Check Report</h1>
        <p><strong>Timestamp:</strong> $(date)</p>
        <p><strong>Environment:</strong> ${DEPLOY_ENV:-production}</p>
        <p><strong>Hostname:</strong> $(hostname)</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <p>Health check completed. Review individual sections below for detailed results.</p>
    </div>
</body>
</html>
EOF
    
    log_info "Reporte HTML generado: $output_file"
}

format_console_output() {
    log_info "Formato de salida: console (predeterminado)"
}

usage() {
    cat <<EOF
Uso: $0 [VERIFICACIÓN] [FORMATO]

Verificaciones disponibles:
  all                 - Ejecutar todas las verificaciones (predeterminado)
  services            - Verificar servicios Docker
  endpoints           - Verificar endpoints HTTP
  database            - Verificar base de datos
  cache               - Verificar caché Redis
  performance         - Verificar rendimiento
  resources           - Verificar recursos del sistema
  external            - Verificar APIs externas
  format              - Formatear resultados

Formatos de salida:
  console             - Salida en consola (predeterminado)
  json                - Salida en formato JSON
  html                - Salida en formato HTML

Variables de entorno:
  BACKEND_URL         - URL del backend (default: http://localhost:8000)
  FRONTEND_URL        - URL del frontend (default: http://localhost:3000)
  CHECK_TIMEOUT       - Timeout para verificaciones (default: 30)
  MAX_RESPONSE_TIME   - Tiempo máximo de respuesta (default: 5000ms)
  MAX_CPU_USAGE       - CPU máximo permitido (default: 80%)
  MAX_MEMORY_USAGE    - Memoria máxima permitida (default: 85%)
  MIN_DISK_SPACE      - Espacio mínimo en disco (default: 10%)

Ejemplos:
  $0 all                      # Verificación completa
  $0 services                 # Solo servicios
  $0 performance json         # Rendimiento en JSON
  $0 resources html           # Recursos en HTML

EOF
}

# Ejecutar función principal
main "$@"