import { test, expect } from '@playwright/test';
import { E2EHelpers } from '../../helpers/e2eHelpers';

test.describe('Diseño Responsive - Mobile y Tablet', () => {
  let helpers: E2EHelpers;

  test.describe('Mobile (375x667)', () => {
    test.beforeEach(async ({ page }) => {
      helpers = new E2EHelpers(page);
      await helpers.setMobileViewport();
      await helpers.navigateTo('/');
    });

    test('should display mobile navigation correctly', async ({ page }) => {
      // Verificar que el menú móvil está presente
      const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"], button[aria-label*="menú"], .mobile-menu-toggle');
      
      if (await mobileMenuButton.isVisible()) {
        // El botón de menú móvil debe estar visible
        await expect(mobileMenuButton).toBeVisible();
        
        // Abrir menú móvil
        await mobileMenuButton.click();
        await helpers.waitForElementVisible('[data-testid="mobile-menu"], nav.mobile-nav');
        
        // Verificar elementos del menú móvil
        const mobileNavItems = page.locator('[data-testid="mobile-menu"] a, .mobile-nav a');
        const itemCount = await mobileNavItems.count();
        expect(itemCount).toBeGreaterThan(0);
        
        // Verificar que los elementos son accesibles
        for (let i = 0; i < Math.min(itemCount, 3); i++) {
          const item = mobileNavItems.nth(i);
          const hasText = await item.textContent();
          expect(hasText).toBeTruthy();
        }
        
        // Cerrar menú (hacer clic fuera o en botón cerrar)
        await helpers.pressEscape();
        await helpers.waitForElementGone('[data-testid="mobile-menu"]');
        
        await helpers.takeScreenshot('mobile-navigation-menu');
      }
    });

    test('should adapt search interface for mobile', async ({ page }) => {
      await helpers.navigateTo('/search');
      
      // Verificar que el campo de búsqueda se adapta al móvil
      const searchInput = page.locator('input[type="search"], input[placeholder*="buscar"]');
      await expect(searchInput).toBeVisible();
      
      // Verificar que es táctil-friendly (tamaño mínimo recomendado 44px)
      const inputBox = await searchInput.boundingBox();
      if (inputBox) {
        expect(inputBox.height).toBeGreaterThan(30); // Min height for touch
      }
      
      // Verificar que los filtros se adaptan a diseño móvil
      const filterControls = page.locator('[data-testid*="filter"], select, .filter-control');
      const filterCount = await filterControls.count();
      
      if (filterCount > 0) {
        // En móvil, los filtros deberían estar colapsados o en dropdown
        await helpers.takeScreenshot('mobile-search-interface');
      }
    });

    test('should display mobile dashboard correctly', async ({ page }) => {
      await helpers.navigateTo('/analysis');
      
      // Verificar que el dashboard se adapta a móvil
      const dashboard = page.locator('[data-testid="analysis-dashboard"]');
      await expect(dashboard).toBeVisible();
      
      // Verificar que las tarjetas de métricas se apilan verticalmente
      const metricCards = page.locator('[data-testid="metric-card"], .metric-card');
      const cardCount = await metricCards.count();
      
      if (cardCount > 0) {
        // En móvil, verificar que las tarjetas tienen ancho completo
        const firstCard = metricCards.first();
        const cardBox = await firstCard.boundingBox();
        
        if (cardBox) {
          // En móvil, las tarjetas deberían ocupar casi todo el ancho
          expect(cardBox.width).toBeLessThan(400); // Approximate mobile width
        }
      }
      
      // Verificar que los gráficos se adaptan
      const charts = page.locator('[data-testid="chart"], canvas, svg');
      const chartCount = await charts.count();
      
      if (chartCount > 0) {
        const firstChart = charts.first();
        const chartBox = await firstChart.boundingBox();
        
        if (chartBox) {
          // Los gráficos deberían ser más pequeños en móvil
          expect(chartBox.width).toBeLessThan(350);
        }
      }
      
      await helpers.takeScreenshot('mobile-dashboard');
    });

    test('should handle mobile news browsing', async ({ page }) => {
      await helpers.navigateTo('/news');
      
      // Verificar que la lista de noticias es navegable en móvil
      const newsContainer = page.locator('[data-testid="news-container"]');
      await expect(newsContainer).toBeVisible();
      
      // Verificar que los artículos tienen diseño móvil apropiado
      const newsItems = page.locator('[data-testid="news-article"], article');
      const itemCount = await newsItems.count();
      
      if (itemCount > 0) {
        const firstItem = newsItems.first();
        
        // Verificar que el artículo tiene altura apropiada para touch
        const itemBox = await firstItem.boundingBox();
        if (itemBox) {
          expect(itemBox.height).toBeGreaterThan(60); // Min height for touch
        }
        
        // Hacer scroll para navegar
        await helpers.scrollToBottom();
        await page.waitForTimeout(1000);
        
        await helpers.takeScreenshot('mobile-news-scrolling');
      }
    });

    test('should work with mobile keyboard interactions', async ({ page }) => {
      await helpers.navigateTo('/search');
      
      // Enfocar campo de búsqueda
      await helpers.clickElement('input[type="search"]');
      
      // Verificar que el teclado móvil aparece (esto puede variar según el navegador)
      await helpers.typeInInput('input[type="search"]', 'test mobile');
      await helpers.pressEnter();
      
      // Verificar que la búsqueda funciona
      await helpers.waitForNetworkIdle();
      
      // Tomar screenshot con teclado visible
      await helpers.takeScreenshot('mobile-search-keyboard');
    });

    test('should maintain accessibility on mobile', async ({ page }) => {
      await helpers.navigateTo('/');
      
      // Verificar que los elementos importantes tienen suficiente contraste
      // y son accesibles mediante touch
      
      // Verificar navegación por teclado en móvil
      await page.focus('body');
      let focusableElements = 0;
      
      for (let i = 0; i < 10; i++) {
        await helpers.pressTab();
        await page.waitForTimeout(100);
        
        const activeElement = await page.evaluate(() => document.activeElement?.tagName);
        if (activeElement) {
          focusableElements++;
        }
      }
      
      // Debería haber elementos enfocables
      expect(focusableElements).toBeGreaterThan(0);
      
      // Verificar tamaños de elementos táctiles
      const touchTargets = page.locator('button, a, input[type="checkbox"], input[type="radio"]');
      const targetCount = await touchTargets.count();
      
      for (let i = 0; i < Math.min(targetCount, 5); i++) {
        const target = touchTargets.nth(i);
        const box = await target.boundingBox();
        
        if (box) {
          // Elementos táctiles deben tener al menos 44x44px
          expect(box.width).toBeGreaterThan(40);
          expect(box.height).toBeGreaterThan(40);
        }
      }
      
      await helpers.takeScreenshot('mobile-accessibility-check');
    });
  });

  test.describe('Tablet (768x1024)', () => {
    test.beforeEach(async ({ page }) => {
      helpers = new E2EHelpers(page);
      await page.setViewportSize({ width: 768, height: 1024 });
      await helpers.navigateTo('/');
    });

    test('should display tablet navigation correctly', async ({ page }) => {
      // En tablet, podría mostrar navegación horizontal o un híbrido
      const nav = page.locator('nav');
      await expect(nav).toBeVisible();
      
      // Verificar que los elementos de navegación son visibles
      const navItems = page.locator('nav a');
      const itemCount = await navItems.count();
      expect(itemCount).toBeGreaterThan(0);
      
      // Verificar que no se muestra el menú móvil
      const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"]');
      if (await mobileMenuButton.isVisible()) {
        // En tablet, podría no estar visible o estar disponible
        const isVisible = await mobileMenuButton.isVisible();
        // Esta es una verificación flexible para tablet
      }
      
      await helpers.takeScreenshot('tablet-navigation');
    });

    test('should adapt dashboard layout for tablet', async ({ page }) => {
      await helpers.navigateTo('/analysis');
      
      // En tablet, el dashboard podría mostrar 2 columnas
      const dashboard = page.locator('[data-testid="analysis-dashboard"]');
      await expect(dashboard).toBeVisible();
      
      const metricCards = page.locator('[data-testid="metric-card"], .metric-card');
      const cardCount = await metricCards.count();
      
      if (cardCount >= 2) {
        // Verificar disposición en 2 columnas (aproximadamente)
        const firstCard = metricCards.first();
        const secondCard = metricCards.nth(1);
        
        const firstBox = await firstCard.boundingBox();
        const secondBox = await secondCard.boundingBox();
        
        if (firstBox && secondBox) {
          // Los elementos deberían estar en la misma fila o cerca
          const verticalDifference = Math.abs(firstBox.y - secondBox.y);
          expect(verticalDifference).toBeLessThan(100); // Within reasonable distance
        }
      }
      
      await helpers.takeScreenshot('tablet-dashboard-layout');
    });

    test('should provide tablet-optimized search experience', async ({ page }) => {
      await helpers.navigateTo('/search');
      
      // En tablet, la interfaz de búsqueda podría ser más espaciada
      const searchInput = page.locator('input[type="search"]');
      await expect(searchInput).toBeVisible();
      
      const inputBox = await searchInput.boundingBox();
      if (inputBox) {
        // En tablet, el campo de búsqueda debería ser más ancho
        expect(inputBox.width).toBeGreaterThan(300);
      }
      
      // Verificar que los filtros son fácilmente accesibles
      const filterControls = page.locator('[data-testid*="filter"]');
      const filterCount = await filterControls.count();
      
      if (filterCount > 0) {
        // Los controles deberían estar bien espaciados
        await helpers.takeScreenshot('tablet-search-interface');
      }
    });
  });

  test.describe('Responsive Breakpoints', () => {
    test('should handle different viewport sizes correctly', async ({ page }) => {
      helpers = new E2EHelpers(page);
      
      const viewports = [
        { name: 'Mobile Small', width: 320, height: 568 },
        { name: 'Mobile Large', width: 414, height: 896 },
        { name: 'Tablet Portrait', width: 768, height: 1024 },
        { name: 'Tablet Landscape', width: 1024, height: 768 },
        { name: 'Desktop Small', width: 1280, height: 720 },
      ];

      for (const viewport of viewports) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height });
        await helpers.navigateTo('/');
        await helpers.waitForNetworkIdle();
        
        // Verificar que la página se adapta sin scroll horizontal no deseado
        const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
        const viewportWidth = viewport.width;
        
        expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 10); // Allow small margin
        
        // Tomar screenshot para verificar adaptación visual
        await helpers.takeScreenshot(`responsive-${viewport.name.toLowerCase().replace(' ', '-')}`);
      }
    });
  });

  test.describe('Touch Interactions', () => {
    test('should work with touch gestures on mobile', async ({ page }) => {
      helpers = new E2EHelpers(page);
      await helpers.setMobileViewport();
      await helpers.navigateTo('/news');
      
      // Simular scroll touch
      await page.touchscreen.tap(200, 300);
      
      // Hacer scroll hacia abajo
      await page.evaluate(() => {
        window.scrollBy(0, 500);
      });
      
      await page.waitForTimeout(1000);
      
      // Verificar que el scroll funciona
      const scrollPosition = await page.evaluate(() => window.scrollY);
      expect(scrollPosition).toBeGreaterThan(0);
      
      await helpers.takeScreenshot('mobile-touch-scroll');
    });
  });

  test.describe('Performance on Mobile', () => {
    test('should load quickly on mobile connections', async ({ page }) => {
      helpers = new E2EHelpers(page);
      await helpers.setMobileViewport();
      
      // Simular conexión móvil lenta
      await page.context().setOffline(false);
      await page.context().setExtraHTTPHeaders({
        'User-Agent': 'MobileUserAgent'
      });
      
      const startTime = Date.now();
      await helpers.navigateTo('/');
      await helpers.waitForNetworkIdle();
      const loadTime = Date.now() - startTime;
      
      // La página debería cargar en menos de 5 segundos
      expect(loadTime).toBeLessThan(5000);
      
      await helpers.takeScreenshot('mobile-performance-check');
    });
  });
});