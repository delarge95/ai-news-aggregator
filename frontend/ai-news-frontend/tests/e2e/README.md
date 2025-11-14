# Testing E2E - AI News Aggregator Frontend

Este directorio contiene los tests end-to-end (E2E) para el frontend de AI News Aggregator, implementados con Playwright.

## 📁 Estructura de Archivos

```
tests/e2e/
├── tests/
│   ├── test_user_flows.ts           # Flujos principales de usuario
│   ├── test_navigation.ts           # Routing y navegación
│   ├── test_search_functionality.ts # Búsqueda y filtros
│   ├── test_dashboard_interactions.ts # Interacciones del dashboard
│   └── test_responsive_design.ts    # Responsive (mobile/tablet)
├── fixtures/
│   └── baseFixtures.ts              # Configuraciones base de tests
├── helpers/
│   └── e2eHelpers.ts                # Métodos auxiliares
├── playwright.config.ts             # Configuración de Playwright
└── README.md                        # Este archivo
```

## 🚀 Configuración Inicial

### 1. Ejecutar el script de configuración

```bash
# Desde el directorio del frontend
./setup-e2e.sh
```

### 2. Instalación manual (si el script falla)

```bash
# Instalar Playwright
npm install -D @playwright/test

# Instalar navegadores
npx playwright install

# Crear directorios de resultados
mkdir -p test-results/{screenshots,videos,traces}
```

## 🏃‍♂️ Ejecutar Tests

### Comandos Principales

```bash
# Ejecutar todos los tests E2E
npm run test:e2e

# Ejecutar tests con interfaz visual
npm run test:e2e:ui

# Ejecutar tests con navegadores visibles
npm run test:e2e:headed

# Ver reporte de tests
npm run test:e2e:report
```

### Comandos Específicos

```bash
# Ejecutar solo tests de flujos de usuario
npx playwright test test_user_flows.ts

# Ejecutar solo tests de navegación
npx playwright test test_navigation.ts

# Ejecutar solo tests de búsqueda
npx playwright test test_search_functionality.ts

# Ejecutar solo tests del dashboard
npx playwright test test_dashboard_interactions.ts

# Ejecutar solo tests responsive
npx playwright test test_responsive_design.ts

# Ejecutar tests que contengan texto específico
npx playwright test --grep "should display"

# Ejecutar tests en paralelo (por defecto)
npx playwright test --workers=4
```

## 🌍 Navegadores Soportados

Los tests se ejecutan automáticamente en:

- **Chromium** (Chrome)
- **Firefox** 
- **WebKit** (Safari)
- **Mobile Chrome** (Pixel 5)
- **Mobile Safari** (iPhone 12)

## 📱 Testing Responsive

### Viewports Configurados

```typescript
Mobile:      375 × 667 (iPhone 12)
Tablet:      768 × 1024 (iPad)
Desktop:     1280 × 720
Large:       1440 × 900
```

### Testing en Dispositivos Específicos

```bash
# Solo mobile
npx playwright test --project="Mobile Chrome"

# Solo tablet
npx playwright test --project="iPad"

# Solo desktop
npx playwright test --project="chromium"
```

## 🎬 Screenshots y Videos

### Configuración Automática

- **Screenshots**: Se capturan automáticamente al fallar un test
- **Videos**: Se graban automáticamente cuando los tests fallan
- **Traces**: Se generan para análisis detallado

### Ubicaciones

```
test-results/
├── screenshots/          # Capturas de pantalla
├── videos/              # Grabaciones de video
├── traces/              # Trazas de ejecución
└── results.json         # Reporte JSON
```

### Captura Manual

```typescript
// En tus tests
await page.screenshot({ 
  path: 'mi-screenshot.png',
  fullPage: true 
});
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env.test`:

```env
VITE_TEST_MODE=true
VITE_API_BASE_URL=http://localhost:5173
PLAYWRIGHT_BASE_URL=http://localhost:5173
MOCK_USER_ID=test-user-123
```

### Timeouts Personalizados

```typescript
// En playwright.config.ts
use: {
  baseURL: 'http://localhost:5173',
  timeout: 30000,        // Timeout general
  actionTimeout: 10000,  // Timeout de acciones
  navigationTimeout: 15000,
}
```

### Parallel Testing

```typescript
// En playwright.config.ts
export default defineConfig({
  fullyParallel: true,    // Ejecutar tests en paralelo
  workers: 4,             // Número de workers
  retries: 2,             // Reintentos en CI
});
```

## 📊 Reportes y Análisis

### Ver Reporte Web

```bash
npx playwright show-report
```

### Reporte CLI

```bash
# Durante ejecución
npx playwright test --reporter=list

# Reporte detallado
npx playwright test --reporter=line
```

### Integración con CI/CD

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npx playwright install
      - run: npm run test:e2e
```

## 🐛 Debugging

### Debug Visual

```bash
# Abrir interfaz de debug
npx playwright test --ui

# Con navegador visible
npx playwright test --headed

# Debug con trazas
npx playwright test --trace on
```

### Debug en Código

```typescript
test('mi test', async ({ page }) => {
  // Pausar ejecución
  await page.pause();
  
  // logs del navegador
  page.on('console', msg => console.log('Browser:', msg.text()));
  
  // Capturar errores de red
  page.on('response', response => {
    if (!response.ok()) {
      console.log(`Error ${response.status()}: ${response.url()}`);
    }
  });
});
```

## 📝 Escribir Nuevos Tests

### Estructura Básica

```typescript
import { test, expect } from '@playwright/test';
import { E2EHelpers } from '../../helpers/e2eHelpers';

test.describe('Mi Nueva Funcionalidad', () => {
  let helpers: E2EHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page);
    await helpers.navigateTo('/mi-pagina');
  });

  test('should do something specific', async ({ page }) => {
    // Tu lógica de test aquí
    await helpers.clickElement('[data-testid="mi-elemento"]');
    await helpers.expectElementToBeVisible('[data-testid="resultado"]');
  });
});
```

### Selectores Recomendados

```html
<!-- ✅ Buenas prácticas -->
<button data-testid="submit-button">Enviar</button>
<div data-testid="user-card">
  <span data-testid="user-name">Juan</span>
</div>

<!-- ❌ Evitar selectores frágiles -->
<button class="btn btn-primary btn-lg">Enviar</button>
<div class="user-card">
  <span class="name">Juan</span>
</div>
```

## 🚨 Buenas Prácticas

1. **Usar data-testid** para elementos que se testearán
2. **Esperar a que los elementos estén visibles** antes de interactuar
3. **Usar timeouts apropiados** para acciones lentas
4. **Limpiar estado** entre tests con beforeEach
5. **Manejar errores** de red y tiempo de espera
6. **Tomar screenshots** en puntos clave de debugging
7. **Usar helpers** para operaciones comunes
8. **No hardcodear URLs** (usar constantes o configuración)

## 🆘 Problemas Comunes

### El servidor no inicia

```bash
# Verificar que no hay otro proceso usando el puerto
lsof -i :5173

# Matar procesos existentes
kill -9 <PID>
```

### Tests fallan por timing

```typescript
// Usar waitFor en lugar de timeouts fijos
await page.waitForSelector('[data-testid="element"]', { 
  state: 'visible',
  timeout: 10000 
});
```

### Problemas de autenticación

```typescript
// Mock de datos de usuario en beforeEach
test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('user', JSON.stringify({
      id: 'test-user',
      authenticated: true
    }));
  });
});
```

## 📚 Recursos Adicionales

- [Documentación oficial de Playwright](https://playwright.dev/)
- [Playwright Test API](https://playwright.dev/docs/api/class-test)
- [Mejores prácticas de E2E testing](https://playwright.dev/docs/best-practices)
- [Configuración avanzada](https://playwright.dev/docs/test-configuration)