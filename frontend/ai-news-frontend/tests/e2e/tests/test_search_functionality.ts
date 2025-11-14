import { test, expect } from '@playwright/test';
import { E2EHelpers } from '../../helpers/e2eHelpers';

test.describe('Funcionalidad de Búsqueda y Filtros', () => {
  let helpers: E2EHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page);
    await helpers.navigateTo('/search');
  });

  test('should display search interface correctly', async ({ page }) => {
    // Verificar elementos de la interfaz de búsqueda
    await helpers.expectElementToBeVisible('input[type="search"], input[placeholder*="buscar"]');
    await helpers.expectElementToBeVisible('[data-testid="search-button"], button[type="submit"]');
    
    // Verificar filtros disponibles
    const filterElements = page.locator('[data-testid*="filter"], .filter, select');
    const filterCount = await filterElements.count();
    
    if (filterCount > 0) {
      await expect(filterElements.first()).toBeVisible();
    }
    
    // Verificar área de resultados
    await helpers.expectElementToBeVisible('[data-testid="search-results"], .results');
    
    // Tomar screenshot de la interfaz inicial
    await helpers.takeScreenshot('search-interface-initial');
  });

  test('should perform basic search', async ({ page }) => {
    // Ingresar término de búsqueda
    const searchTerm = 'inteligencia artificial';
    await helpers.fillInput('input[type="search"]', searchTerm);
    
    // Enviar búsqueda
    await helpers.clickElement('[data-testid="search-button"], button[type="submit"]');
    
    // Esperar resultados
    await helpers.waitForText('[data-testid="search-results"], .results', searchTerm);
    
    // Verificar que los resultados se muestran
    const results = page.locator('[data-testid="search-result-item"], .result-item, article');
    const resultCount = await results.count();
    
    // Debería haber al menos algún resultado o mensaje
    expect(resultCount).toBeGreaterThan(0);
    
    // Tomar screenshot de resultados
    await helpers.takeScreenshot('search-results-basic');
  });

  test('should handle search with autocomplete', async ({ page }) => {
    // Verificar si hay funcionalidad de autocompletado
    const searchInput = page.locator('input[type="search"], input[placeholder*="buscar"]');
    
    // Escribir parcialmente para activar autocompletado
    await helpers.typeInInput('input[type="search"]', 'intelige');
    await page.waitForTimeout(500);
    
    // Verificar si aparecen sugerencias
    const suggestions = page.locator('[data-testid*="suggestion"], .suggestion, .autocomplete-list');
    const suggestionCount = await suggestions.count();
    
    if (suggestionCount > 0) {
      // Hacer clic en la primera sugerencia
      await suggestions.first().click();
      
      // Verificar que el input se actualiza
      const inputValue = await searchInput.getAttribute('value');
      expect(inputValue).toBeTruthy();
      
      // Tomar screenshot de autocompletado
      await helpers.takeScreenshot('search-autocomplete');
    }
  });

  test('should filter search results by category', async ({ page }) => {
    // Realizar búsqueda inicial
    const searchTerm = 'tecnología';
    await helpers.fillInput('input[type="search"]', searchTerm);
    await helpers.clickElement('[data-testid="search-button"]');
    await helpers.waitForNetworkIdle();
    
    // Buscar filtros de categoría
    const categoryFilters = page.locator('select[name*="category"], input[type="checkbox"][name*="category"], [data-testid*="category"]');
    const filterCount = await categoryFilters.count();
    
    if (filterCount > 0) {
      // Seleccionar un filtro
      await categoryFilters.first().click();
      
      // Verificar que los resultados se actualizan
      await helpers.waitForNetworkIdle();
      
      // Verificar que el filtro está seleccionado
      const isChecked = await categoryFilters.first().isChecked();
      expect(isChecked).toBeTruthy();
      
      // Tomar screenshot con filtro aplicado
      await helpers.takeScreenshot('search-with-category-filter');
    }
  });

  test('should filter by date range', async ({ page }) => {
    // Buscar filtros de fecha
    const dateFilters = page.locator('input[type="date"], select[name*="date"], [data-testid*="date"]');
    const dateFilterCount = await dateFilters.count();
    
    if (dateFilterCount > 0) {
      // Aplicar filtro de fecha
      const today = new Date().toISOString().split('T')[0];
      
      // Buscar campo de fecha y llenarlo
      for (let i = 0; i < dateFilterCount; i++) {
        const filter = dateFilters.nth(i);
        const type = await filter.getAttribute('type') || await filter.tagName();
        
        if (type === 'date' || type === 'INPUT') {
          await filter.fill(today);
          break;
        }
      }
      
      // Aplicar filtro
      await helpers.clickElement('[data-testid="apply-filter"], button[type="submit"]');
      await helpers.waitForNetworkIdle();
      
      // Tomar screenshot con filtro de fecha
      await helpers.takeScreenshot('search-with-date-filter');
    }
  });

  test('should sort search results', async ({ page }) => {
    // Realizar búsqueda para generar resultados
    await helpers.fillInput('input[type="search"]', 'noticias');
    await helpers.clickElement('[data-testid="search-button"]');
    await helpers.waitForNetworkIdle();
    
    // Buscar controles de ordenamiento
    const sortControls = page.locator('select[name*="sort"], [data-testid*="sort"], .sort-control');
    const sortCount = await sortControls.count();
    
    if (sortCount > 0) {
      // Cambiar criterio de ordenamiento
      await sortControls.first().selectOption('relevance');
      await helpers.waitForNetworkIdle();
      
      // Verificar que los resultados se reordenan
      const results = page.locator('[data-testid="search-result-item"], .result-item');
      const firstResult = results.first();
      await expect(firstResult).toBeVisible();
      
      // Cambiar a otro criterio
      await sortControls.first().selectOption('date');
      await helpers.waitForNetworkIdle();
      
      // Tomar screenshot de ordenamiento
      await helpers.takeScreenshot('search-sorting-results');
    }
  });

  test('should handle empty search results', async ({ page }) => {
    // Realizar búsqueda que probablemente no dé resultados
    const uniqueTerm = 'xzyabc123nonexistent';
    await helpers.fillInput('input[type="search"]', uniqueTerm);
    await helpers.clickElement('[data-testid="search-button"]');
    
    // Esperar resultados o mensaje de "no encontrado"
    await helpers.waitForNetworkIdle();
    
    // Verificar mensaje de "no encontrado" o estado vacío
    const noResultsMessage = page.locator('[data-testid="no-results"], .no-results, .empty-state');
    const hasNoResults = await noResultsMessage.isVisible();
    
    if (hasNoResults) {
      await expect(noResultsMessage).toContainText(/no.*encontr|vacio|semresult/);
    }
    
    // Verificar que el área de resultados está vacía
    const results = page.locator('[data-testid="search-result-item"], .result-item');
    await expect(results).toHaveCount(0);
    
    // Tomar screenshot de resultados vacíos
    await helpers.takeScreenshot('search-empty-results');
  });

  test('should save and retrieve search history', async ({ page }) => {
    // Realizar varias búsquedas para generar historial
    const searches = ['IA', 'machine learning', 'noticias'];
    
    for (const searchTerm of searches) {
      await helpers.clearInput('input[type="search"]');
      await helpers.fillInput('input[type="search"]', searchTerm);
      await helpers.clickElement('[data-testid="search-button"]');
      await helpers.waitForNetworkIdle();
      await page.waitForTimeout(500);
    }
    
    // Verificar si aparece historial de búsquedas
    const historyButton = page.locator('[data-testid="search-history"], button[aria-label*="historial"]');
    if (await historyButton.isVisible()) {
      await historyButton.click();
      
      // Verificar que aparecen búsquedas anteriores
      const historyItems = page.locator('[data-testid="history-item"], .history-item');
      const historyCount = await historyItems.count();
      expect(historyCount).toBeGreaterThan(0);
      
      // Hacer clic en una búsqueda anterior
      if (historyCount > 0) {
        await historyItems.first().click();
        
        // Verificar que la búsqueda se restaura
        const inputValue = await page.locator('input[type="search"]').getAttribute('value');
        expect(inputValue).toBeTruthy();
      }
      
      // Tomar screenshot del historial
      await helpers.takeScreenshot('search-history');
    }
  });

  test('should save favorite searches', async ({ page }) => {
    // Realizar búsqueda
    const searchTerm = 'investigación científica';
    await helpers.fillInput('input[type="search"]', searchTerm);
    await helpers.clickElement('[data-testid="search-button"]');
    await helpers.waitForNetworkIdle();
    
    // Buscar botón de guardar/favoritos
    const saveButton = page.locator('[data-testid="save-search"], button[aria-label*="guardar"], .save-search');
    
    if (await saveButton.isVisible()) {
      await saveButton.click();
      
      // Verificar que se muestra confirmación de guardado
      const confirmation = page.locator('[data-testid="save-confirmation"], .success-message');
      if (await confirmation.isVisible()) {
        await expect(confirmation).toContainText(/guard|save|exito/);
      }
      
      // Tomar screenshot de búsqueda guardada
      await helpers.takeScreenshot('search-saved');
    }
  });

  test('should handle search shortcuts and hotkeys', async ({ page }) => {
    // Enfocar campo de búsqueda
    await helpers.clickElement('input[type="search"]');
    
    // Probar atajo de teclado (Ctrl+K es común para búsqueda)
    await page.keyboard.press('Control+k');
    
    // Verificar que se abre interfaz de búsqueda rápida
    const quickSearch = page.locator('[data-testid="quick-search"], .quick-search-modal');
    if (await quickSearch.isVisible()) {
      // Realizar búsqueda rápida
      await helpers.typeInInput('[data-testid="quick-search"] input', 'AI');
      await helpers.pressEnter();
      
      await helpers.waitForNetworkIdle();
      
      // Tomar screenshot de búsqueda rápida
      await helpers.takeScreenshot('search-quick-modal');
    }
  });

  test('should filter by multiple criteria', async ({ page }) => {
    // Realizar búsqueda base
    await helpers.fillInput('input[type="search"]', 'ciencia');
    await helpers.clickElement('[data-testid="search-button"]');
    await helpers.waitForNetworkIdle();
    
    // Aplicar múltiples filtros
    const allFilters = page.locator('input[type="checkbox"], select, input[type="date"]');
    const filterCount = await allFilters.count();
    
    if (filterCount >= 2) {
      // Seleccionar primer filtro
      await allFilters.first().check();
      await page.waitForTimeout(300);
      
      // Seleccionar segundo filtro
      await allFilters.nth(1).check();
      await page.waitForTimeout(300);
      
      // Aplicar filtros
      await helpers.clickElement('[data-testid="apply-filters"], .apply-filters');
      await helpers.waitForNetworkIdle();
      
      // Verificar que múltiples filtros están activos
      const activeFilters = page.locator('input[type="checkbox"]:checked, select option:checked');
      const activeCount = await activeFilters.count();
      expect(activeCount).toBeGreaterThanOrEqual(2);
      
      // Tomar screenshot con múltiples filtros
      await helpers.takeScreenshot('search-multiple-filters');
    }
  });

  test('should handle search suggestions', async ({ page }) => {
    // Escribir en el campo de búsqueda para activar sugerencias
    await helpers.typeInInput('input[type="search"]', 'intelig');
    
    // Esperar a que aparezcan sugerencias
    await page.waitForTimeout(1000);
    
    // Buscar elementos de sugerencias
    const suggestions = page.locator('[data-testid*="suggestion"], .suggestion-item, .autocomplete-item');
    const suggestionCount = await suggestions.count();
    
    if (suggestionCount > 0) {
      // Verificar que las sugerencias son relevantes
      for (let i = 0; i < Math.min(suggestionCount, 3); i++) {
        const suggestion = suggestions.nth(i);
        const suggestionText = await suggestion.textContent();
        expect(suggestionText?.toLowerCase()).toContain('intelig');
      }
      
      // Hacer clic en una sugerencia
      await suggestions.first().click();
      
      // Verificar que se completa la búsqueda
      const inputValue = await page.locator('input[type="search"]').getAttribute('value');
      expect(inputValue).toBeTruthy();
      
      // Tomar screenshot de sugerencias
      await helpers.takeScreenshot('search-suggestions');
    }
  });

  test('should show search statistics', async ({ page }) => {
    // Realizar búsqueda para generar estadísticas
    await helpers.fillInput('input[type="search"]', 'tecnología');
    await helpers.clickElement('[data-testid="search-button"]');
    await helpers.waitForNetworkIdle();
    
    // Buscar información de estadísticas de búsqueda
    const stats = page.locator('[data-testid="search-stats"], .search-stats, .results-info');
    const statsCount = await stats.count();
    
    if (statsCount > 0) {
      // Verificar que se muestran estadísticas relevantes
      const statsText = await stats.first().textContent();
      expect(statsText).toMatch(/\d+|result|tiempo/);
      
      // Tomar screenshot de estadísticas
      await helpers.takeScreenshot('search-statistics');
    }
  });
});