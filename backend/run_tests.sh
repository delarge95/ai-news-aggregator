#!/bin/bash

# AI News Aggregator - AI Processor Test Runner
# Script para ejecutar tests comprehensivos del sistema de IA

set -e

echo "🤖 AI News Aggregator - Test Suite"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Change to backend directory
cd "$(dirname "$0")"

print_status "Ejecutando tests comprehensivos del sistema de IA..."
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest no está instalado. Instalando dependencias..."
    pip install pytest pytest-asyncio pytest-mock httpx
fi

# Check if AI processor module can be imported
print_status "Verificando imports del sistema de IA..."
python -c "
try:
    from app.services.ai_processor import SentimentAnalyzer, TopicClassifier, Summarizer, AIProcessor
    print('✅ Importación exitosa del sistema de IA')
except ImportError as e:
    print(f'❌ Error importando sistema de IA: {e}')
    exit(1)
"

echo ""

# Parse command line arguments
TEST_CATEGORY="all"
VERBOSE=false
COVERAGE=false
PARALLEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--category)
            TEST_CATEGORY="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -h|--help)
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones:"
            echo "  -c, --category  Categoría de tests (unit|integration|performance|stress|all)"
            echo "  -v, --verbose   Ejecutar tests en modo verbose"
            echo "  --coverage     Generar reporte de cobertura"
            echo "  -p, --parallel  Ejecutar tests en paralelo"
            echo "  -h, --help      Mostrar esta ayuda"
            echo ""
            echo "Ejemplos:"
            echo "  $0                           # Ejecutar todos los tests"
            echo "  $0 -c unit -v               # Solo tests unitarios en modo verbose"
            echo "  $0 --coverage               # Tests con reporte de cobertura"
            exit 0
            ;;
        *)
            print_error "Opción desconocida: $1"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
else
    PYTEST_CMD="$PYTEST_CMD -q"
fi

if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app.services.ai_processor --cov-report=html --cov-report=term"
fi

# Add markers based on category
case $TEST_CATEGORY in
    "unit")
        print_test "Ejecutando tests unitarios..."
        PYTEST_CMD="$PYTEST_CMD -m unit"
        ;;
    "integration")
        print_test "Ejecutando tests de integración..."
        PYTEST_CMD="$PYTEST_CMD -m integration"
        ;;
    "performance")
        print_test "Ejecutando tests de performance..."
        PYTEST_CMD="$PYTEST_CMD -m performance"
        ;;
    "stress")
        print_test "Ejecutando stress tests..."
        PYTEST_CMD="$PYTEST_CMD -m 'performance and slow'"
        ;;
    "all"|*)
        print_test "Ejecutando todos los tests..."
        PYTEST_CMD="$PYTEST_CMD"
        ;;
esac

# Add specific file
PYTEST_CMD="$PYTEST_CMD tests/services/test_ai_processor.py"

echo ""
print_status "Comando pytest: $PYTEST_CMD"
echo ""

# Execute tests
print_status "Iniciando ejecución de tests..."
echo ""

if eval $PYTEST_CMD; then
    echo ""
    print_status "🎉 Tests completados exitosamente!"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        print_status "📊 Reporte de cobertura generado en htmlcov/index.html"
    fi
    
    echo ""
    print_status "Resumen de tests ejecutados:"
    
    case $TEST_CATEGORY in
        "unit")
            echo "   ✅ Tests unitarios para SentimentAnalyzer, TopicClassifier, Summarizer"
            echo "   ✅ Tests de mocking de OpenAI API"
            echo "   ✅ Tests de manejo de errores"
            echo "   ✅ Tests de cache y performance"
            ;;
        "integration")
            echo "   ✅ Tests de integración del AIProcessor"
            echo "   ✅ Tests de pipeline completo"
            echo "   ✅ Tests de Celery tasks"
            echo "   ✅ Tests de configuración Redis"
            ;;
        "performance")
            echo "   ✅ Tests de performance bajo carga"
            echo "   ✅ Tests de concurrencia"
            echo "   ✅ Tests de memoria y cache"
            echo "   ✅ Tests de stress y límites"
            ;;
        "all")
            echo "   ✅ Tests unitarios completos"
            echo "   ✅ Tests de integración"
            echo "   ✅ Tests de performance"
            echo "   ✅ Tests de stress"
            echo "   ✅ Tests de Celery tasks"
            echo "   ✅ Tests de mocking y fixtures"
            ;;
    esac
    
else
    echo ""
    print_error "❌ Algunos tests fallaron"
    echo ""
    print_warning "Para debuggear, intenta:"
    echo "   $0 -c unit -v"
    echo "   pytest tests/services/test_ai_processor.py -v -s"
    exit 1
fi

echo ""
print_status "✨ Sistema de IA listo para producción!"
echo ""

# Display test categories info
echo "Categorías de tests disponibles:"
echo "  📦 unit          - Tests unitarios básicos"
echo "  🔗 integration   - Tests de integración"
echo "  ⚡ performance   - Tests de performance"
echo "  💪 stress        - Stress tests pesados"
echo "  🌟 all          - Todos los tests"
echo ""

print_status "Para ejecutar tests específicos:"
echo "  ./run_tests.sh -c unit"
echo "  ./run_tests.sh -c integration -v"
echo "  ./run_tests.sh -c performance --coverage"