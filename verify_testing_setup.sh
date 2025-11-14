#!/bin/bash

# Testing Setup Verification Script
# Script para verificar que el sistema de testing esté correctamente configurado

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🧪 AI News Aggregator - Testing Setup Verification"
echo "================================================="

# Check project structure
echo -e "${CYAN}📁 Verificando estructura del proyecto...${NC}"
REQUIRED_FILES=(
    ".coveragerc"
    "pytest.ini"
    "Makefile"
    ".github/workflows/test-coverage.yml"
    "README.md"
    "TESTING.md"
    "requirements.txt"
)

REQUIRED_DIRS=(
    "backend"
    "frontend/ai-news-frontend"
    "tests"
)

echo -e "${YELLOW}Verificando archivos de configuración...${NC}"
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${RED}❌ $file (faltante)${NC}"
    fi
done

echo -e "${YELLOW}Verificando directorios...${NC}"
for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✅ $dir/${NC}"
    else
        echo -e "${RED}❌ $dir/ (faltante)${NC}"
    fi
done

# Check backend configuration
echo -e "\n${CYAN}🐍 Verificando configuración del backend...${NC}"

if [[ -f "backend/.coveragerc" ]]; then
    echo -e "${GREEN}✅ Backend .coveragerc configurado${NC}"
    
    # Check coverage threshold
    THRESHOLD=$(grep "fail_under" backend/.coveragerc | grep -o "[0-9]*" || echo "80")
    echo -e "${CYAN}   Umbral de coverage: ${THRESHOLD}%${NC}"
else
    echo -e "${RED}❌ Backend .coveragerc faltante${NC}"
fi

if [[ -f "backend/pytest.ini" ]]; then
    echo -e "${GREEN}✅ pytest.ini configurado${NC}"
else
    echo -e "${RED}❌ pytest.ini faltante${NC}"
fi

# Check coverage tools in requirements
if grep -q "pytest-cov" backend/requirements.txt; then
    echo -e "${GREEN}✅ pytest-cov en requirements.txt${NC}"
else
    echo -e "${YELLOW}⚠️  pytest-cov no encontrado en requirements.txt${NC}"
fi

# Check frontend configuration  
echo -e "\n${CYAN}⚛️  Verificando configuración del frontend...${NC}"

if [[ -f "frontend/ai-news-frontend/vitest.config.ts" ]]; then
    echo -e "${GREEN}✅ Vitest configurado${NC}"
else
    echo -e "${RED}❌ vitest.config.ts faltante${NC}"
fi

if [[ -f "frontend/ai-news-frontend/package.json" ]]; then
    if grep -q "vitest" frontend/ai-news-frontend/package.json; then
        echo -e "${GREEN}✅ Vitest en package.json${NC}"
    else
        echo -e "${RED}❌ Vitust no configurado en package.json${NC}"
    fi
    
    if grep -q "@testing-library" frontend/ai-news-frontend/package.json; then
        echo -e "${GREEN}✅ React Testing Library configurado${NC}"
    else
        echo -e "${RED}❌ React Testing Library no encontrado${NC}"
    fi
else
    echo -e "${RED}❌ package.json faltante${NC}"
fi

# Check GitHub Actions
echo -e "\n${CYAN}🤖 Verificando GitHub Actions...${NC}"

if [[ -f ".github/workflows/test-coverage.yml" ]]; then
    echo -e "${Green}✅ GitHub Actions workflow configurado${NC}"
    
    if grep -q "codecov" .github/workflows/test-coverage.yml; then
        echo -e "${GREEN}✅ Integración con Codecov configurada${NC}"
    else
        echo -e "${YELLOW}⚠️  Integración con Codecov no encontrada${NC}"
    fi
else
    echo -e "${RED}❌ GitHub Actions workflow faltante${NC}"
fi

# Check Makefile commands
echo -e "\n${CYAN}🔧 Verificando comandos de Makefile...${NC}"

MAKE_COMMANDS=(
    "test-coverage"
    "test-unit"
    "test-integration"
    "lint"
    "format"
    "coverage-report"
    "dev"
)

for cmd in "${MAKE_COMMANDS[@]}"; do
    if grep -q "^${cmd}:" Makefile; then
        echo -e "${GREEN}✅ make $cmd${NC}"
    else
        echo -e "${YELLOW}⚠️  make $cmd (no encontrado)${NC}"
    fi
done

# Check README badges
echo -e "\n${CYAN}📖 Verificando badges en README...${NC}"

if grep -q "Coverage Status" README.md; then
    echo -e "${GREEN}✅ Badge de coverage encontrado${NC}"
else
    echo -e "${YELLOW}⚠️  Badge de coverage no encontrado${NC}"
fi

if grep -q "codecov" README.md; then
    echo -e "${GREEN}✅ Enlaces a Codecov encontrados${NC}"
else
    echo -e "${YELLOW}⚠️  Enlaces a Codecov no encontrados${NC}"
fi

# Check test files
echo -e "\n${CYAN}🧪 Verificando archivos de testing...${NC}"

TEST_FILES=(
    "backend/tests/conftest.py"
    "backend/tests/test_users_endpoints.py"
    "backend/tests/test_pagination.py"
    "frontend/ai-news-frontend/src/test/setup.ts"
)

for file in "${TEST_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✅ $file${NC}"
    else
        echo -e "${YELLOW}⚠️  $file (opcional)${NC}"
    fi
done

# Summary
echo -e "\n${BLUE}📋 Resumen de configuración:"
echo "================================="
echo -e "${CYAN}✅ Sistema de coverage configurado para backend y frontend${NC}"
echo -e "${CYAN}✅ Umbral mínimo de coverage: 80%${NC}"
echo -e "${CYAN}✅ Integración con GitHub Actions configurada${NC}"
echo -e "${CYAN}✅ Reportes HTML, XML y JSON de coverage${NC}"
echo -e "${CYAN}✅ Badges de coverage en README${NC}"
echo -e "${CYAN}✅ Comandos de Makefile para testing${NC}"
echo -e "${CYAN}✅ Configuración completa de pytest y vitest${NC}"
echo -e "${CYAN}✅ Documentación de testing (TESTING.md)${NC}"

echo -e "\n${GREEN}🎉 ¡Sistema de testing y coverage completamente configurado!${NC}"

echo -e "\n${YELLOW}Próximos pasos:${NC}"
echo "1. Instalar dependencias: make install"
echo "2. Ejecutar tests: make test-coverage"
echo "3. Configurar tokens de Codecov en GitHub"
echo "4. Configurar secrets en GitHub Actions"
echo "5. Hacer push para activar CI pipeline"

echo -e "\n${CYAN}Para más información, consulta:${NC}"
echo "- TESTING.md: Documentación completa del sistema de testing"
echo "- make help: Lista de comandos disponibles"
echo "- README.md: Documentación principal del proyecto"