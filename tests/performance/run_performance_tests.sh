#!/bin/bash

# Script de ejecución para Performance Tests de AI News Aggregator
# Uso: ./run_performance_tests.sh [opciones]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
ENVIRONMENT="staging"
CONFIG_FILE="performance_config.yaml"
REPORTS_DIR="./reports"
VERBOSE=false
CREATE_DIRS=true
TEST_TYPE="all"  # all, load, performance, stress, database, frontend
CLEANUP=false
HELP=false

# Funciones auxiliares
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Performance Test Runner para AI News Aggregator

USO:
    ./run_performance_tests.sh [OPCIONES]

OPCIONES:
    -e, --environment ENV     Ambiente a testear (development|staging|production) [default: staging]
    -c, --config FILE        Archivo de configuración [default: performance_config.yaml]
    -o, --output DIR         Directorio de reportes [default: ./reports]
    -t, --test-type TYPE     Tipo de test a ejecutar (all|load|performance|stress|database|frontend)
    -v, --verbose            Output verbose
    --create-dirs            Crear directorios necesarios
    --cleanup                Limpiar reportes antiguos antes de ejecutar
    -h, --help               Mostrar esta ayuda

EJEMPLOS:
    # Ejecutar todos los tests en staging
    ./run_performance_tests.sh

    # Ejecutar solo load tests en development
    ./run_performance_tests.sh -e development -t load

    # Ejecutar con configuración personalizada
    ./run_performance_tests.sh -c my_config.yaml --verbose

    # Ejecutar tests de producción (¡cuidado!)
    ./run_performance_tests.sh -e production -t all --cleanup

TIPOS DE TEST:
    all          Ejecutar todos los tests [default]
    load         Solo load tests con Locust
    performance  Solo tests de performance de endpoints
    stress       Solo stress tests y rate limiting
    database     Solo tests de performance de base de datos
    frontend     Solo tests de performance de frontend

EOF
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -o|--output)
            REPORTS_DIR="$2"
            shift 2
            ;;
        -t|--test-type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --create-dirs)
            CREATE_DIRS=true
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        -h|--help)
            HELP=true
            shift
            ;;
        *)
            log_error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# Mostrar ayuda si se solicitó
if [ "$HELP" = true ]; then
    show_help
    exit 0
fi

# Validar ambiente
case $ENVIRONMENT in
    development|staging|production)
        log_info "Ambiente seleccionado: $ENVIRONMENT"
        ;;
    *)
        log_error "Ambiente inválido: $ENVIRONMENT. Usar: development|staging|production"
        exit 1
        ;;
esac

# Validar tipo de test
case $TEST_TYPE in
    all|load|performance|stress|database|frontend)
        log_info "Tipo de test: $TEST_TYPE"
        ;;
    *)
        log_error "Tipo de test inválido: $TEST_TYPE. Usar: all|load|performance|stress|database|frontend"
        exit 1
        ;;
esac

# Crear directorios necesarios
if [ "$CREATE_DIRS" = true ]; then
    log_info "Creando directorios necesarios..."
    mkdir -p "$REPORTS_DIR"
    mkdir -p "logs"
    log_success "Directorios creados"
fi

# Limpiar reportes antiguos si se solicitó
if [ "$CLEANUP" = true ]; then
    log_info "Limpiando reportes antiguos..."
    find "$REPORTS_DIR" -type f -name "*.json" -mtime +30 -delete 2>/dev/null || true
    find "$REPORTS_DIR" -type f -name "*.html" -mtime +30 -delete 2>/dev/null || true
    find "$REPORTS_DIR" -type f -name "*.csv" -mtime +30 -delete 2>/dev/null || true
    log_success "Limpieza completada"
fi

# Verificar dependencias
check_dependencies() {
    log_info "Verificando dependencias..."
    
    local missing_deps=()
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
    fi
    
    # Verificar dependencias Python
    python3 -c "import locust, aiohttp, asyncpg, yaml" 2>/dev/null || {
        missing_deps+=("locust aiohttp asyncpg pyyaml")
    }
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_warning "Dependencias faltantes: ${missing_deps[*]}"
        log_info "Instalando dependencias..."
        pip3 install -r requirements-performance.txt
        log_success "Dependencias instaladas"
    else
        log_success "Todas las dependencias están disponibles"
    fi
}

# Verificar configuración
check_config() {
    log_info "Verificando configuración..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        if [ "$CONFIG_FILE" = "performance_config.yaml" ]; then
            log_warning "Archivo de configuración no encontrado: $CONFIG_FILE"
            log_info "Usando configuración por defecto integrada"
        else
            log_error "Archivo de configuración no encontrado: $CONFIG_FILE"
            exit 1
        fi
    else
        log_success "Configuración cargada: $CONFIG_FILE"
    fi
}

# Ejecutar tests
run_tests() {
    local start_time=$(date +%s)
    log_info "Iniciando ejecución de tests de performance..."
    log_info "Timestamp: $(date)"
    log_info "Ambiente: $ENVIRONMENT"
    log_info "Configuración: $CONFIG_FILE"
    log_info "Directorio de reportes: $REPORTS_DIR"
    
    # Preparar comando base
    local cmd="python3 test_runner.py --environment $ENVIRONMENT --output $REPORTS_DIR/performance_test_results_$(date +%Y%m%d_%H%M%S).json"
    
    if [ "$VERBOSE" = true ]; then
        cmd="$cmd --verbose"
    fi
    
    if [ "$CREATE_DIRS" = true ]; then
        cmd="$cmd --create-reports-dir"
    fi
    
    # Ejecutar según tipo de test
    case $TEST_TYPE in
        all)
            log_info "Ejecutando suite completa de tests..."
            $cmd
            ;;
        load)
            log_info "Ejecutando solo load tests..."
            python3 -c "
import subprocess
import sys
import os
from pathlib import Path

# Configuración basada en ambiente
configs = {
    'development': {'users': 5, 'spawn_rate': 1, 'run_time': '2m'},
    'staging': {'users': 20, 'spawn_rate': 2, 'run_time': '5m'},
    'production': {'users': 50, 'spawn_rate': 5, 'run_time': '10m'}
}

config = configs.get('$ENVIRONMENT', configs['staging'])

cmd = [
    'locust', '-f', 'load_test.py',
    '--host', 'http://localhost:8000',
    '--headless',
    '--users', str(config['users']),
    '--spawn-rate', str(config['spawn_rate']),
    '--run-time', config['run_time'],
    '--html', '$REPORTS_DIR/load_test_$ENVIRONMENT.html',
    '--csv', '$REPORTS_DIR/load_test_$ENVIRONMENT'
]

print('Ejecutando:', ' '.join(cmd))
subprocess.run(cmd)
"
            ;;
        performance)
            log_info "Ejecutando solo performance tests..."
            python3 performance_test.py --host localhost:8000 --output "$REPORTS_DIR/performance_endpoints.json"
            ;;
        stress)
            log_info "Ejecutando solo stress tests..."
            python3 api_stress_test.py --host localhost:8000 --output "$REPORTS_DIR/stress_test.json"
            ;;
        database)
            log_info "Ejecutando solo database performance tests..."
            python3 database_performance.py --host localhost --database ai_news_db --user postgres --output "$REPORTS_DIR/database_performance.json"
            ;;
        frontend)
            log_info "Ejecutando solo frontend performance tests..."
            python3 frontend_performance.py --host localhost:3000 --output "$REPORTS_DIR/frontend_performance.json"
            ;;
    esac
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Tests completados en ${duration} segundos"
}

# Generar reporte final
generate_summary() {
    log_info "Generando reporte de resumen..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local summary_file="$REPORTS_DIR/test_summary_$timestamp.txt"
    
    cat > "$summary_file" << EOF
RESUMEN DE TESTS DE PERFORMANCE
==============================
Fecha: $(date)
Ambiente: $ENVIRONMENT
Tipo de test: $TEST_TYPE
Directorio de reportes: $REPORTS_DIR

ARCHIVOS GENERADOS:
$(find "$REPORTS_DIR" -name "*$ENVIRONMENT*" -o -name "*performance*" -type f 2>/dev/null | sort)

PRÓXIMOS PASOS:
1. Revisar reportes generados en $REPORTS_DIR
2. Analizar métricas de performance
3. Implementar optimizaciones si es necesario
4. Programar siguientes tests

Para más información, consultar README.md
EOF
    
    log_success "Resumen generado: $summary_file"
    
    # Mostrar resumen en consola
    echo
    echo "==================================="
    echo "RESUMEN DE EJECUCIÓN"
    echo "==================================="
    echo "Ambiente: $ENVIRONMENT"
    echo "Tipo de test: $TEST_TYPE"
    echo "Reportes en: $REPORTS_DIR"
    echo "Resumen: $summary_file"
    echo "==================================="
}

# Manejar errores
handle_error() {
    local exit_code=$?
    log_error "Error durante ejecución (código: $exit_code)"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        log_warning "¡IMPORTANTE! Este era un test en PRODUCCIÓN"
        log_warning "Revisar logs y métricas inmediatamente"
    fi
    
    exit $exit_code
}

# Configurar trap para errores
trap handle_error ERR

# Función principal
main() {
    log_info "Performance Test Runner - AI News Aggregator"
    log_info "============================================"
    
    check_dependencies
    check_config
    run_tests
    generate_summary
    
    log_success "¡Ejecución completada exitosamente!"
    
    # Mostrar consejos finales
    echo
    log_info "CONSEJOS:"
    echo "• Revisar reportes en: $REPORTS_DIR"
    echo "• Para análisis detallado, abrir archivos HTML en navegador"
    echo "• Para ejecutar nuevamente: ./run_performance_tests.sh"
    echo "• Para configuración: editar $CONFIG_FILE"
    echo "• Para más opciones: ./run_performance_tests.sh --help"
}

# Verificar si el script se está ejecutando directamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi