#!/bin/bash
# AI News Aggregator - Comprehensive Test Runner Script
# Runs complete test suite with coverage reporting and quality checks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COVERAGE_DIR="$PROJECT_ROOT/htmlcov"
REPORTS_DIR="$PROJECT_ROOT/test_reports"
TEST_RESULTS_FILE="$REPORTS_DIR/test_results.xml"
COVERAGE_XML="$REPORTS_DIR/coverage.xml"

# Create reports directory
mkdir -p "$REPORTS_DIR"

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_step() {
    echo -e "${CYAN}➤ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Test categories
TEST_CATEGORIES=(
    "unit:Unit tests (fast, isolated)"
    "integration:Integration tests"
    "performance:Performance tests"
    "slow:Slow tests"
    "redis:Redis tests"
    "openai:OpenAI API tests"
    "celery:Celery tests"
    "database:Database tests"
    "api:API tests"
)

# Parse command line arguments
CLEAN=false
VERBOSE=false
COVERAGE_ONLY=false
PARALLEL=false
BENCHMARK=false
QUALITY_CHECKS=true
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean|-c)
            CLEAN=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coverage-only)
            COVERAGE_ONLY=true
            shift
            ;;
        --parallel|-p)
            PARALLEL=true
            shift
            ;;
        --benchmark)
            BENCHMARK=true
            shift
            ;;
        --no-quality)
            QUALITY_CHECKS=false
            shift
            ;;
        --test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --help|-h)
            echo "AI News Aggregator Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean, -c           Clean test artifacts before running"
            echo "  --verbose, -v         Verbose output"
            echo "  --coverage-only       Run only coverage report generation"
            echo "  --parallel, -p        Run tests in parallel"
            echo "  --benchmark          Include performance benchmarks"
            echo "  --no-quality         Skip code quality checks"
            echo "  --test SPECIFIC      Run specific test file or pattern"
            echo "  --help, -h           Show this help message"
            echo ""
            echo "Test Categories:"
            for category in "${TEST_CATEGORIES[@]}"; do
                IFS=':' read -r name desc <<< "$category"
                echo "  $name: $desc"
            done
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Clean previous test artifacts
clean_artifacts() {
    print_step "Cleaning previous test artifacts..."
    
    # Clean coverage files
    find "$PROJECT_ROOT" -name "*.pyc" -delete
    find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -name ".coverage*" -delete
    rm -rf "$COVERAGE_DIR" 2>/dev/null || true
    rm -f "$PROJECT_ROOT/coverage.xml" 2>/dev/null || true
    rm -f "$PROJECT_ROOT/coverage.json" 2>/dev/null || true
    rm -f "$TEST_RESULTS_FILE" 2>/dev/null || true
    
    print_success "Artifacts cleaned"
}

# Setup environment
setup_environment() {
    print_step "Setting up test environment..."
    
    # Set environment variables
    export TESTING=true
    export DATABASE_URL="sqlite+aiosqlite:///:memory:"
    export REDIS_URL="redis://localhost:6379/15"
    export OPENAI_API_KEY="test-key-for-testing"
    export CELERY_BROKER_URL="redis://localhost:6379/15"
    export CELERY_RESULT_BACKEND="redis://localhost:6379/15"
    export JWT_SECRET_KEY="test-jwt-secret-key-for-testing"
    export DEBUG=false
    export AI_ANALYSIS_TIMEOUT=10
    export CACHE_TTL=300
    
    print_success "Environment configured"
}

# Code quality checks
run_quality_checks() {
    if [ "$QUALITY_CHECKS" = false ]; then
        print_warning "Skipping code quality checks (--no-quality specified)"
        return
    fi
    
    print_header "Code Quality Checks"
    
    # Python code formatting
    print_step "Checking code formatting with Black..."
    if black --check --diff app/ tests/; then
        print_success "Code formatting is correct"
    else
        print_warning "Code formatting issues found. Run 'black app/ tests/' to fix"
    fi
    
    # Import sorting
    print_step "Checking import sorting with isort..."
    if isort --check-only --diff app/ tests/; then
        print_success "Import sorting is correct"
    else
        print_warning "Import sorting issues found. Run 'isort app/ tests/' to fix"
    fi
    
    # Linting with flake8
    print_step "Running linting with flake8..."
    if flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503; then
        print_success "No linting issues found"
    else
        print_warning "Linting issues found"
    fi
    
    # Type checking with mypy
    print_step "Running type checking with mypy..."
    if mypy app/ --ignore-missing-imports; then
        print_success "Type checking passed"
    else
        print_warning "Type checking issues found"
    fi
    
    # Security analysis with bandit
    print_step "Running security analysis with bandit..."
    if bandit -r app/ -f json -o "$REPORTS_DIR/security_report.json"; then
        print_success "Security analysis completed"
    else
        print_warning "Security issues found"
    fi
}

# Run unit tests
run_unit_tests() {
    print_header "Unit Tests"
    
    local pytest_args=(
        "tests/"
        "--cov=app"
        "--cov-branch"
        "--cov-report=term-missing"
        "--cov-report=html:$COVERAGE_DIR"
        "--cov-report=xml:$COVERAGE_XML"
        "--cov-report=json:$REPORTS_DIR/coverage.json"
        "--junit-xml=$TEST_RESULTS_FILE"
        "--html=$REPORTS_DIR/report.html"
        "--self-contained-html"
        "-v"
        "--tb=short"
        "--maxfail=10"
        "-m" "unit or not slow"
    )
    
    if [ "$VERBOSE" = true ]; then
        pytest_args+=("--capture=no")
    fi
    
    if [ "$PARALLEL" = true ]; then
        pytest_args+=("-n" "auto")
    fi
    
    if [ -n "$SPECIFIC_TEST" ]; then
        pytest_args+=("$SPECIFIC_TEST")
    fi
    
    print_step "Running unit tests..."
    if pytest "${pytest_args[@]}"; then
        print_success "Unit tests passed"
        return 0
    else
        print_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    print_header "Integration Tests"
    
    local pytest_args=(
        "tests/"
        "--cov=app"
        "--cov-append"
        "--cov-report=term-missing"
        "--junit-xml=$REPORTS_DIR/integration_results.xml"
        "-v"
        "--tb=short"
        "-m" "integration and not slow"
    )
    
    if [ "$PARALLEL" = true ]; then
        pytest_args+=("-n" "2")
    fi
    
    print_step "Running integration tests..."
    if pytest "${pytest_args[@]}"; then
        print_success "Integration tests passed"
        return 0
    else
        print_error "Integration tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    if [ "$BENCHMARK" = false ]; then
        print_warning "Skipping performance tests (--benchmark not specified)"
        return 0
    fi
    
    print_header "Performance Tests"
    
    local pytest_args=(
        "tests/"
        "--benchmark-only"
        "--benchmark-json=$REPORTS_DIR/benchmark_results.json"
        "-v"
        "-m" "performance"
    )
    
    print_step "Running performance benchmarks..."
    if pytest "${pytest_args[@]}"; then
        print_success "Performance tests completed"
        return 0
    else
        print_error "Performance tests failed"
        return 1
    fi
}

# Generate coverage report
generate_coverage_report() {
    print_header "Coverage Report"
    
    if [ -f "$COVERAGE_XML" ]; then
        print_step "Generating HTML coverage report..."
        
        # Ensure coverage directory exists
        mkdir -p "$COVERAGE_DIR"
        
        # Generate HTML report if not exists
        if [ ! -d "$COVERAGE_DIR/index.html" ]; then
            coverage html -d "$COVERAGE_DIR"
        fi
        
        # Generate coverage badge
        print_step "Generating coverage badge..."
        if command -v coverage-badge >/dev/null 2>&1; then
            coverage-badge -o "$PROJECT_ROOT/coverage-badge.svg"
        fi
        
        # Print coverage summary
        print_step "Coverage Summary:"
        coverage report --show-missing
        
        # Extract coverage percentage
        COVERAGE_PERCENT=$(coverage report --format=total | cut -d'%' -f1)
        
        if (( $(echo "$COVERAGE_PERCENT >= 80" | bc -l) )); then
            print_success "Coverage target achieved: ${COVERAGE_PERCENT}%"
        else
            print_warning "Coverage below target: ${COVERAGE_PERCENT}% (target: 80%)"
        fi
        
        print_success "Coverage report available at: $COVERAGE_DIR/index.html"
        return 0
    else
        print_error "Coverage data not found. Run tests first."
        return 1
    fi
}

# Generate test report summary
generate_report_summary() {
    print_header "Test Report Summary"
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    local skipped_tests=0
    
    # Parse JUnit XML if available
    if [ -f "$TEST_RESULTS_FILE" ]; then
        # Extract test counts from XML (basic parsing)
        total_tests=$(grep -o 'tests="[0-9]*"' "$TEST_RESULTS_FILE" | head -1 | cut -d'"' -f2 || echo "0")
        failures=$(grep -o 'failures="[0-9]*"' "$TEST_RESULTS_FILE" | head -1 | cut -d'"' -f2 || echo "0")
        skipped=$(grep -o 'skipped="[0-9]*"' "$TEST_RESULTS_FILE" | head -1 | cut -d'"' -f2 || echo "0")
        
        failed_tests=$failures
        passed_tests=$((total_tests - failed_tests - skipped_tests))
    fi
    
    echo -e "${CYAN}Test Execution Summary:${NC}"
    echo -e "  Total Tests: ${total_tests:-N/A}"
    echo -e "  Passed: ${GREEN}$passed_tests${NC}"
    echo -e "  Failed: ${RED}$failed_tests${NC}"
    echo -e "  Skipped: ${YELLOW}$skipped_tests${NC}"
    
    # Coverage information
    if [ -f "$COVERAGE_XML" ]; then
        COVERAGE_PERCENT=$(coverage report --format=total 2>/dev/null || echo "N/A")
        echo -e "  Coverage: ${COVERAGE_PERCENT}%"
    fi
    
    # Performance summary
    if [ -f "$REPORTS_DIR/benchmark_results.json" ]; then
        echo -e "  Benchmark Results: Available in $REPORTS_DIR/benchmark_results.json"
    fi
    
    # Reports location
    echo -e "\n${CYAN}Reports Location:${NC}"
    echo -e "  HTML Report: $REPORTS_DIR/report.html"
    echo -e "  Coverage Report: $COVERAGE_DIR/index.html"
    echo -e "  JUnit XML: $TEST_RESULTS_FILE"
    echo -e "  Coverage XML: $COVERAGE_XML"
    
    if [ -f "$REPORTS_DIR/security_report.json" ]; then
        echo -e "  Security Report: $REPORTS_DIR/security_report.json"
    fi
}

# Open reports in browser (optional)
open_reports() {
    if command -v xdg-open >/dev/null 2>&1; then
        print_step "Opening reports in browser..."
        xdg-open "$REPORTS_DIR/report.html" 2>/dev/null || true
        xdg-open "$COVERAGE_DIR/index.html" 2>/dev/null || true
    elif command -v open >/dev/null 2>&1; then
        print_step "Opening reports in browser..."
        open "$REPORTS_DIR/report.html" 2>/dev/null || true
        open "$COVERAGE_DIR/index.html" 2>/dev/null || true
    fi
}

# Main execution
main() {
    print_header "AI News Aggregator - Test Suite"
    echo -e "${PURPLE}Starting comprehensive test execution...${NC}"
    echo ""
    
    # Clean if requested
    if [ "$CLEAN" = true ]; then
        clean_artifacts
        echo ""
    fi
    
    # Setup environment
    setup_environment
    echo ""
    
    # Run quality checks first
    if [ "$QUALITY_CHECKS" = true ]; then
        run_quality_checks
        echo ""
    fi
    
    # Run tests based on options
    if [ "$COVERAGE_ONLY" = true ]; then
        generate_coverage_report
    else
        # Run unit tests
        if ! run_unit_tests; then
            print_error "Unit tests failed"
            generate_report_summary
            exit 1
        fi
        echo ""
        
        # Run integration tests
        if ! run_integration_tests; then
            print_error "Integration tests failed"
            generate_report_summary
            exit 1
        fi
        echo ""
        
        # Run performance tests
        run_performance_tests
        echo ""
        
        # Generate coverage report
        if ! generate_coverage_report; then
            print_error "Coverage report generation failed"
        fi
        echo ""
    fi
    
    # Generate final summary
    generate_report_summary
    echo ""
    
    # Optionally open reports
    if [ "$VERBOSE" = true ]; then
        open_reports
    fi
    
    print_success "Test suite completed successfully!"
}

# Error handling
trap 'print_error "Test execution interrupted"; exit 1' INT TERM

# Run main function
main "$@"