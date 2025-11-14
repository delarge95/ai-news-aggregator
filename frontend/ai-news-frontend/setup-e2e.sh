#!/bin/bash

# Script para configurar el entorno de testing E2E
# Ejecutar desde la raíz del proyecto frontend

echo "🚀 Configurando testing E2E para AI News Frontend..."

# Instalar dependencias de Playwright
echo "📦 Instalando Playwright..."
npx playwright install

# Instalar navegadores
echo "🌐 Instalando navegadores..."
npx playwright install-deps

# Crear directorios necesarios
echo "📁 Creando directorios de test results..."
mkdir -p test-results/screenshots
mkdir -p test-results/videos
mkdir -p test-results/traces

# Crear archivo de configuración de entorno de pruebas
echo "⚙️ Creando configuración de entorno..."
cat > .env.test << EOF
# Configuración para testing E2E
VITE_TEST_MODE=true
VITE_API_BASE_URL=http://localhost:5173
PLAYWRIGHT_BASE_URL=http://localhost:5173

# Configuración de timeouts
VITE_TEST_TIMEOUT=30000

# Mock data para tests
MOCK_USER_ID=test-user-123
MOCK_USER_NAME=Test User
MOCK_USER_EMAIL=test@example.com
EOF

# Actualizar scripts de package.json si es necesario
echo "✅ Configuración completada!"
echo ""
echo "🎯 Comandos disponibles:"
echo "  npm run test:e2e        - Ejecutar tests E2E"
echo "  npm run test:e2e:ui     - Ejecutar tests E2E con interfaz"
echo "  npm run test:e2e:headed - Ejecutar tests E2E con navegadores visibles"
echo "  npm run test:e2e:report - Ver reporte de tests"
echo ""
echo "🔧 Para ejecutar tests específicos:"
echo "  npx playwright test --grep \"should display homepage\""
echo "  npx playwright test test_user_flows.ts"
echo ""
echo "📊 Ver resultados:"
echo "  npx playwright show-report test-results"