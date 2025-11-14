# 🎯 Comandos Rápidos - E2E Testing

## Instalación Inicial
```bash
# 1. Instalar Playwright y dependencias
npm install -D @playwright/test
npx playwright install

# 2. Ejecutar tests básicos
npm run test:e2e

# 3. Ver resultados
npm run test:e2e:report
```

## Desarrollo y Debug
```bash
# Tests con UI interactiva
npm run test:e2e:ui

# Tests con navegador visible
npm run test:e2e:headed

# Un test específico
npx playwright test test_user_flows.ts --grep "should display homepage"

# Debug con pausa
npx playwright test --debug
```

## Paralelización y Rendimiento
```bash
# Ejecutar en paralelo (por defecto)
npx playwright test --workers=4

# Solo un navegador
npx playwright test --project=chromium

# Con timeouts largos
npx playwright test --timeout=60000
```

## Screenshots y Videos
```bash
# Capturar screenshots al fallar (automático)
# Capturar videos al fallar (automático)

# Screenshots manuales
await page.screenshot({ path: 'mi-test.png', fullPage: true });
```

## CI/CD Integration
```bash
# Para GitHub Actions
npm run test:e2e -- --reporter=github

# Para otros CI
npm run test:e2e -- --reporter=json --output-file=results.json
```

## Limpiar Resultados
```bash
# Limpiar resultados anteriores
rm -rf test-results/ playwright-report/

# Instalar navegadores de nuevo
npx playwright install --force
```

## Troubleshooting
```bash
# Verificar instalación
npx playwright --version

# Instalar dependencias del sistema
sudo npx playwright install-deps

# Limpiar cache
npm run clean && npm install
```

## Useful Playwright Commands
```bash
# Generar tests
npx playwright codegen http://localhost:5173

# Abrir interfaz de tests
npx playwright test --ui

# Ver traces
npx playwright show-trace trace.zip

# Instalar para diferentes OS
npx playwright install-deps ubuntu-20.04  # Para Ubuntu
```

## Parallel Testing Examples
```bash
# Ejecutar solo tests críticos en paralelo
npx playwright test test_user_flows.ts test_navigation.ts --parallel

# Tests por prioridad
npx playwright test --grep="critical" --workers=4
npx playwright test --grep="important" --workers=2
npx playwright test --grep="optional" --workers=1
```

## Mobile Testing
```bash
# Solo mobile
npx playwright test --project="Mobile Chrome"

# Tablet
npx playwright test --project="iPad"

# Todos los viewports
npx playwright test
```

## Performance Testing
```bash
# Con métricas de performance
npx playwright test --project=chromium --trace=on

# Tests de carga
npx playwright test --max-failures=10

# Timeout personalizados
npx playwright test --timeout=120000
```