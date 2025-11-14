#!/bin/bash
"""
Script de ejecución de tests de integración
Run integration tests script

Este script facilita la ejecución de todos los tests de integración
con diferentes configuraciones y opciones.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Configuración
PROJECT_ROOT = Path(__file__).parent.parent
INTEGRATION_TESTS_DIR = PROJECT_ROOT / "tests" / "integration"

def run_command(cmd, description, check=True):
    """Ejecutar comando con logging"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"Comando: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, cwd=PROJECT_ROOT, check=check, capture_output=True, text=True)
        if result.stdout:
            print("📤 STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("📥 STDERR:")
            print(result.stderr)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando comando: {e}")
        if e.stdout:
            print("📤 STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("📥 STDERR:")
            print(e.stderr)
        return False

def check_environment():
    """Verificar entorno de testing"""
    print("🔍 Verificando entorno de testing...")
    
    # Verificar directorio de tests
    if not INTEGRATION_TESTS_DIR.exists():
        print(f"❌ Directorio de tests no encontrado: {INTEGRATION_TESTS_DIR}")
        return False
    
    # Verificar archivos de tests
    test_files = [
        "test_api_integration.py",
        "test_database_integration.py", 
        "test_external_api_integration.py",
        "test_ai_integration.py",
        "test_cache_integration.py"
    ]
    
    for test_file in test_files:
        test_path = INTEGRATION_TESTS_DIR / test_file
        if test_path.exists():
            print(f"✅ {test_file}")
        else:
            print(f"❌ {test_file} no encontrado")
            return False
    
    return True

def setup_test_environment():
    """Configurar entorno de testing"""
    print("⚙️ Configurando entorno de testing...")
    
    env_vars = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/15",
        "PYTHONPATH": str(PROJECT_ROOT)
    }
    
    # Exportar variables de entorno
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key}={value}")
    
    return True

def install_dependencies():
    """Instalar dependencias de testing"""
    print("📦 Instalando dependencias de testing...")
    
    deps = [
        "pytest>=7.4.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.1.0",
        "pytest-xdist>=3.3.0",
        "httpx>=0.24.0",
        "redis>=4.6.0",
        "asyncpg>=0.28.0",
        "aiosqlite>=0.19.0"
    ]
    
    for dep in deps:
        cmd = f"pip install {dep}"
        if not run_command(cmd, f"Instalando {dep}", check=False):
            print(f"⚠️ Advertencia: No se pudo instalar {dep}")
    
    return True

def run_basic_tests():
    """Ejecutar tests básicos (sin dependencias externas)"""
    print("🧪 Ejecutando tests básicos...")
    
    cmd = f"""
    pytest tests/integration/ -v \
        --tb=short \
        --disable-warnings \
        -m "not slow and not requires_api_key" \
        --maxfail=3 \
        --durations=10
    """
    
    return run_command(cmd, "Tests de integración básicos")

def run_api_tests():
    """Ejecutar tests de API"""
    print("🌐 Ejecutando tests de API...")
    
    cmd = f"""
    pytest tests/integration/test_api_integration.py -v \
        --tb=short \
        --disable-warnings \
        -m "integration and api"
    """
    
    return run_command(cmd, "Tests de API")

def run_database_tests():
    """Ejecutar tests de base de datos"""
    print("🗄️ Ejecutando tests de base de datos...")
    
    cmd = f"""
    pytest tests/integration/test_database_integration.py -v \
        --tb=short \
        --disable-warnings \
        -m "integration and database"
    """
    
    return run_command(cmd, "Tests de base de datos")

def run_cache_tests():
    """Ejecutar tests de cache"""
    print("⚡ Ejecutando tests de cache...")
    
    cmd = f"""
    pytest tests/integration/test_cache_integration.py -v \
        --tb=short \
        --disable-warnings \
        -m "integration and redis"
    """
    
    return run_command(cmd, "Tests de cache")

def run_ai_tests():
    """Ejecutar tests de IA"""
    print("🤖 Ejecutando tests de IA...")
    
    cmd = f"""
    pytest tests/integration/test_ai_integration.py -v \
        --tb=short \
        --disable-warnings \
        -m "integration and ai"
    """
    
    return run_command(cmd, "Tests de IA")

def run_external_api_tests(mock_only=True):
    """Ejecutar tests de APIs externas"""
    print(f"🔌 Ejecutando tests de APIs externas ({'mockeadas' if mock_only else 'reales'})...")
    
    if mock_only:
        cmd = f"""
        pytest tests/integration/test_external_api_integration.py -v \
            --tb=short \
            --disable-warnings \
            -m "integration and external_api and not requires_api_key"
        """
    else:
        cmd = f"""
        ENABLE_API_TESTS=1 pytest tests/integration/test_external_api_integration.py -v \
            --tb=short \
            --disable-warnings \
            -m "integration and external_api"
        """
    
    return run_command(cmd, f"Tests de APIs externas ({'mockeadas' if mock_only else 'reales'})")

def run_performance_tests():
    """Ejecutar tests de performance"""
    print("⚡ Ejecutando tests de performance...")
    
    cmd = f"""
    pytest tests/integration/ -v \
        --tb=short \
        -m "integration and performance" \
        --benchmark-only \
        --benchmark-sort=mean
    """
    
    return run_command(cmd, "Tests de performance")

def run_all_tests():
    """Ejecutar todos los tests de integración"""
    print("🚀 Ejecutando todos los tests de integración...")
    
    cmd = f"""
    pytest tests/integration/ -v \
        --tb=short \
        --cov=app \
        --cov-report=html \
        --cov-report=term \
        --cov-fail-under=70 \
        --maxfail=5 \
        --durations=20
    """
    
    return run_command(cmd, "Todos los tests de integración")

def run_tests_with_coverage():
    """Ejecutar tests con cobertura"""
    print("📊 Ejecutando tests con análisis de cobertura...")
    
    cmd = f"""
    pytest tests/integration/ \
        --cov=app \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml \
        --cov-report=term-missing \
        --cov-fail-under=75 \
        --cov-branch
    """
    
    success = run_command(cmd, "Tests con cobertura")
    
    if success:
        print("\n📈 Reporte de cobertura generado:")
        print(f"  - HTML: {PROJECT_ROOT}/htmlcov/index.html")
        print(f"  - XML: {PROJECT_ROOT}/coverage.xml")
        print(f"  - Terminal: mostrado arriba")
    
    return success

def run_parallel_tests():
    """Ejecutar tests en paralelo"""
    print("⚡ Ejecutando tests en paralelo...")
    
    cmd = f"""
    pytest tests/integration/ -n auto \
        -v \
        --tb=short \
        --maxfail=3 \
        --durations=10
    """
    
    return run_command(cmd, "Tests en paralelo")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Script de tests de integración")
    parser.add_argument("--target", choices=[
        "basic", "api", "database", "cache", "ai", 
        "external-mock", "external-real", "performance",
        "all", "coverage", "parallel"
    ], default="basic", help="Tipo de tests a ejecutar")
    parser.add_argument("--install-deps", action="store_true", help="Instalar dependencias")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verbose")
    parser.add_argument("--fail-fast", action="store_true", help="Parar en el primer fallo")
    
    args = parser.parse_args()
    
    print("🧪 AI News Aggregator - Tests de Integración")
    print(f"📁 Directorio: {INTEGRATION_TESTS_DIR}")
    print(f"🎯 Target: {args.target}")
    
    # Verificar entorno
    if not check_environment():
        print("❌ Error verificando entorno")
        sys.exit(1)
    
    # Instalar dependencias si se solicita
    if args.install_deps:
        if not install_dependencies():
            print("❌ Error instalando dependencias")
            sys.exit(1)
    
    # Configurar entorno
    if not setup_test_environment():
        print("❌ Error configurando entorno")
        sys.exit(1)
    
    # Definir comandos según el target
    test_commands = {
        "basic": run_basic_tests,
        "api": run_api_tests,
        "database": run_database_tests,
        "cache": run_cache_tests,
        "ai": run_ai_tests,
        "external-mock": lambda: run_external_api_tests(mock_only=True),
        "external-real": lambda: run_external_api_tests(mock_only=False),
        "performance": run_performance_tests,
        "all": run_all_tests,
        "coverage": run_tests_with_coverage,
        "parallel": run_parallel_tests
    }
    
    # Ejecutar tests
    if args.target in test_commands:
        success = test_commands[args.target]()
        
        if success:
            print(f"\n✅ Tests de {args.target} completados exitosamente")
            sys.exit(0)
        else:
            print(f"\n❌ Tests de {args.target} fallaron")
            sys.exit(1)
    else:
        print(f"❌ Target desconocido: {args.target}")
        sys.exit(1)

if __name__ == "__main__":
    # Verificar que estamos en el directorio correcto
    if not (PROJECT_ROOT / "app").exists():
        print("❌ Error: Ejecutar desde el directorio backend del proyecto")
        print(f"Directorio actual: {os.getcwd()}")
        print(f"Directorio esperado: {PROJECT_ROOT}")
        sys.exit(1)
    
    main()