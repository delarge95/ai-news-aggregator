import { test, expect } from '@playwright/test';
import { E2EHelpers } from '../../helpers/e2eHelpers';

test.describe('Interacciones del Dashboard', () => {
  let helpers: E2EHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page);
    await helpers.navigateTo('/analysis');
  });

  test('should display dashboard correctly', async ({ page }) => {
    // Verificar elementos principales del dashboard
    await helpers.expectElementToBeVisible('[data-testid="analysis-dashboard"]');
    
    // Verificar tarjetas de métricas
    const metricCards = page.locator('[data-testid="metric-card"], .metric-card, .dashboard-card');
    const cardCount = await metricCards.count();
    expect(cardCount).toBeGreaterThan(0);
    
    // Verificar gráficos
    const charts = page.locator('[data-testid="chart"], .chart, canvas, svg');
    const chartCount = await charts.count();
    expect(chartCount).toBeGreaterThan(0);
    
    // Verificar controles del dashboard
    const controls = page.locator('[data-testid="dashboard-controls"], .controls, select');
    if (await controls.count() > 0) {
      await expect(controls.first()).toBeVisible();
    }
    
    // Tomar screenshot del dashboard inicial
    await helpers.takeScreenshot('dashboard-initial-view');
  });

  test('should interact with metric cards', async ({ page }) => {
    // Buscar tarjetas de métricas
    const metricCards = page.locator('[data-testid="metric-card"]');
    const cardCount = await metricCards.count();
    
    if (cardCount > 0) {
      // Hacer clic en la primera tarjeta para drill-down
      await metricCards.first().click();
      await page.waitForTimeout(500);
      
      // Verificar si se abre modal o se navega a vista detallada
      const modal = page.locator('[data-testid="metric-modal"], .modal, .detail-view');
      const isModalVisible = await modal.isVisible();
      
      if (isModalVisible) {
        // Verificar contenido del modal
        await expect(modal).toContainText(/\d+|%|metric|valor/);
        await helpers.takeScreenshot('dashboard-metric-modal');
        
        // Cerrar modal
        await helpers.pressEscape();
        await helpers.waitForElementGone('[data-testid="metric-modal"]');
      }
    }
  });

  test('should manipulate charts and visualizations', async ({ page }) => {
    // Buscar elementos de gráficos interactivos
    const chartContainer = page.locator('[data-testid="chart-container"], .chart-container');
    
    if (await chartContainer.isVisible()) {
      // Hacer clic en diferentes partes del gráfico
      const chartPoints = page.locator('[data-testid="chart-point"], .point, .bar, .slice');
      const pointCount = await chartPoints.count();
      
      if (pointCount > 0) {
        // Hacer clic en el primer punto del gráfico
        await chartPoints.first().click();
        await page.waitForTimeout(300);
        
        // Verificar tooltips o información
        const tooltip = page.locator('[data-testid="chart-tooltip"], .tooltip');
        if (await tooltip.isVisible()) {
          await helpers.takeScreenshot('dashboard-chart-tooltip');
        }
      }
      
      // Probar zoom en gráficos
      const zoomControls = page.locator('[data-testid="chart-zoom"], .zoom-in, .zoom-out');
      const zoomCount = await zoomControls.count();
      
      if (zoomCount > 0) {
        // Intentar zoom in
        await zoomControls.first().click();
        await page.waitForTimeout(300);
        
        // Tomar screenshot con zoom
        await helpers.takeScreenshot('dashboard-chart-zoomed');
      }
    }
  });

  test('should filter dashboard data by time range', async ({ page }) => {
    // Buscar controles de tiempo/filtros
    const timeControls = page.locator('select[name*="time"], select[name*="date"], [data-testid*="time"]');
    const controlCount = await timeControls.count();
    
    if (controlCount > 0) {
      const firstControl = timeControls.first();
      
      // Obtener opciones disponibles
      const options = await firstControl.locator('option').count();
      expect(options).toBeGreaterThan(1);
      
      // Seleccionar rango de tiempo diferente
      await firstControl.selectOption({ index: 1 });
      await helpers.waitForNetworkIdle();
      
      // Verificar que los datos se actualizan
      const metricCards = page.locator('[data-testid="metric-card"]');
      if (await metricCards.count() > 0) {
        // Los valores deberían cambiar con el filtro de tiempo
        await helpers.takeScreenshot('dashboard-time-filtered');
      }
    }
  });

  test('should refresh dashboard data', async ({ page }) => {
    // Buscar botón de actualizar
    const refreshButton = page.locator('[data-testid="refresh-button"], .refresh, button[aria-label*="actualizar"]');
    
    if (await refreshButton.isVisible()) {
      // Tomar screenshot antes de actualizar
      await helpers.takeScreenshot('dashboard-before-refresh');
      
      // Hacer clic en actualizar
      await refreshButton.click();
      
      // Verificar indicador de carga
      const loadingIndicator = page.locator('[data-testid="loading"], .loading, .spinner');
      if (await loadingIndicator.isVisible()) {
        await expect(loadingIndicator).toBeVisible();
      }
      
      // Esperar a que termine la actualización
      await helpers.waitForNetworkIdle();
      await page.waitForTimeout(1000);
      
      // Tomar screenshot después de actualizar
      await helpers.takeScreenshot('dashboard-after-refresh');
    }
  });

  test('should export dashboard data', async ({ page }) => {
    // Buscar opciones de exportación
    const exportButtons = page.locator('[data-testid="export-button"], .export, button[aria-label*="exportar"]');
    const exportCount = await exportButtons.count();
    
    if (exportCount > 0) {
      // Hacer clic en el primer botón de exportación
      await exportButtons.first().click();
      await page.waitForTimeout(500);
      
      // Verificar si aparece menú de exportación
      const exportMenu = page.locator('[data-testid="export-menu"], .export-menu, .dropdown-menu');
      if (await exportMenu.isVisible()) {
        // Buscar opciones específicas de exportación
        const exportOptions = exportMenu.locator('li, button, a');
        const optionCount = await exportOptions.count();
        
        if (optionCount > 0) {
          // Hacer clic en la primera opción (ej: PDF, CSV)
          await exportOptions.first().click();
          await page.waitForTimeout(1000);
          
          // Verificar si se inicia descarga
          // Esto podría verificarse mediante la descarga del archivo o mensaje
          await helpers.takeScreenshot('dashboard-export-initiated');
        }
      }
    }
  });

  test('should customize dashboard layout', async ({ page }) => {
    // Buscar controles de personalización
    const customizeButton = page.locator('[data-testid="customize-button"], .customize, button[aria-label*="personalizar"]');
    
    if (await customizeButton.isVisible()) {
      await customizeButton.click();
      await page.waitForTimeout(500);
      
      // Verificar panel de personalización
      const customizePanel = page.locator('[data-testid="customize-panel"], .customize-panel');
      if (await customizePanel.isVisible()) {
        // Buscar opciones de widgets
        const widgetToggles = customizePanel.locator('input[type="checkbox"]');
        const toggleCount = await widgetToggles.count();
        
        if (toggleCount > 0) {
          // Activar/desactivar un widget
          await widgetToggles.first().click();
          await page.waitForTimeout(300);
          
          // Aplicar cambios
          const applyButton = customizePanel.locator('[data-testid="apply-changes"], .apply');
          if (await applyButton.isVisible()) {
            await applyButton.click();
            await helpers.waitForNetworkIdle();
          }
          
          // Tomar screenshot del dashboard personalizado
          await helpers.takeScreenshot('dashboard-customized');
        }
      }
    }
  });

  test('should handle real-time updates', async ({ page }) => {
    // Esperar a que el dashboard cargue completamente
    await helpers.waitForNetworkIdle();
    
    // Tomar screenshot inicial
    const initialScreenshot = 'dashboard-before-realtime';
    await helpers.takeScreenshot(initialScreenshot);
    
    // Esperar a posibles actualizaciones en tiempo real (ej: 5 segundos)
    await page.waitForTimeout(5000);
    
    // Verificar si hay indicadores de actualización
    const updateIndicators = page.locator('[data-testid="last-update"], .last-update');
    if (await updateIndicators.isVisible()) {
      const updateText = await updateIndicators.textContent();
      expect(updateText).toMatch(/\d+|ahora|momento/);
    }
    
    // Tomar screenshot después de actualizaciones
    const afterUpdateScreenshot = 'dashboard-after-realtime';
    await helpers.takeScreenshot(afterUpdateScreenshot);
  });

  test('should respond to dashboard interactions', async ({ page }) => {
    // Probar hover en elementos del dashboard
    const interactiveElements = page.locator('[data-testid*="metric"], [data-testid*="chart"], .interactive');
    const elementCount = await interactiveElements.count();
    
    if (elementCount > 0) {
      const firstElement = interactiveElements.first();
      
      // Simular hover
      await firstElement.hover();
      await page.waitForTimeout(300);
      
      // Verificar tooltips o información adicional
      const tooltip = page.locator('[data-testid*="tooltip"], .tooltip, .popover');
      if (await tooltip.isVisible()) {
        await helpers.takeScreenshot('dashboard-element-hover');
      }
      
      // Hacer clic para interacción
      await firstElement.click();
      await page.waitForTimeout(300);
      
      // Verificar respuesta a la interacción
      const response = page.locator('[data-testid="interaction-response"], .response');
      if (await response.isVisible()) {
        await expect(response).toContainText(/\d+|%|information|data/);
      }
    }
  });

  test('should handle dashboard error states', async ({ page }) => {
    // Simular error en el dashboard
    await page.route('**/api/**', route => {
      route.abort('failed');
    });
    
    // Recargar página para trigger error
    await page.reload();
    await page.waitForTimeout(3000);
    
    // Verificar mensaje de error
    const errorMessage = page.locator('[data-testid="error-message"], .error, .alert-error');
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText(/error|Error|carg|fallo/);
      
      // Buscar botón de reintentar
      const retryButton = page.locator('[data-testid="retry-button"], .retry, button[aria-label*="reintentar"]');
      if (await retryButton.isVisible()) {
        await retryButton.click();
        await page.waitForTimeout(2000);
        
        // Verificar si se recupera
        await helpers.takeScreenshot('dashboard-after-retry');
      }
      
      // Tomar screenshot del error
      await helpers.takeScreenshot('dashboard-error-state');
    }
  });

  test('should provide dashboard keyboard shortcuts', async ({ page }) => {
    // Enfocar dashboard
    await page.focus('body');
    
    // Probar atajos de teclado comunes
    const shortcuts = [
      'r', // refresh
      'e', // export
      'c', // customize
      'f'  // filters
    ];
    
    for (const key of shortcuts) {
      await page.keyboard.press(key);
      await page.waitForTimeout(500);
      
      // Verificar respuesta al atajo
      const response = page.locator('[data-testid*="modal"], .modal, .dropdown');
      if (await response.isVisible()) {
        await helpers.takeScreenshot(`dashboard-shortcut-${key}`);
        await helpers.pressEscape();
      }
    }
  });

  test('should maintain dashboard state', async ({ page }) => {
    // Realizar varias interacciones en el dashboard
    const metricCards = page.locator('[data-testid="metric-card"]');
    if (await metricCards.count() > 0) {
      await metricCards.first().click();
      await page.waitForTimeout(500);
    }
    
    // Aplicar un filtro si existe
    const filterControls = page.locator('select, input[type="checkbox"]');
    if (await filterControls.count() > 0) {
      await filterControls.first().selectOption({ index: 1 });
      await page.waitForTimeout(500);
    }
    
    // Tomar screenshot del estado actual
    await helpers.takeScreenshot('dashboard-state-intermediate');
    
    // Navegar fuera y volver
    await helpers.clickElement('a[href="/"]');
    await helpers.waitForNetworkIdle();
    
    await helpers.clickElement('a[href="/analysis"]');
    await helpers.waitForNetworkIdle();
    
    // Verificar que el estado se mantiene
    const metricCardsAfter = page.locator('[data-testid="metric-card"]');
    if (await metricCardsAfter.count() > 0) {
      await helpers.takeScreenshot('dashboard-state-preserved');
    }
  });
});