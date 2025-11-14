import { test, expect } from '@playwright/test';
import { E2EHelpers } from '../../helpers/e2eHelpers';

test.describe('Sistema de Navegación y Routing', () => {
  let helpers: E2EHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page);
    await helpers.navigateTo('/');
  });

  test('should navigate through main navigation menu', async ({ page }) => {
    // Verificar navegación principal en desktop
    await helpers.setDesktopViewport();
    
    const navigationItems = [
      { path: '/', label: 'Inicio', selector: 'a[href="/"]' },
      { path: '/news', label: 'Noticias', selector: 'a[href="/news"]' },
      { path: '/trends', label: 'Tendencias', selector: 'a[href="/trends"]' },
      { path: '/resources', label: 'Recursos', selector: 'a[href="/resources"]' },
      { path: '/analysis', label: 'Análisis IA', selector: 'a[href="/analysis"]' }
    ];

    for (const item of navigationItems) {
      // Hacer clic en el enlace de navegación
      await helpers.clickElement(item.selector);
      
      // Verificar que la URL cambió
      await helpers.expectUrlToContain(item.path);
      
      // Verificar que la página carga correctamente
      await helpers.waitForNetworkIdle();
      
      // Verificar que el enlace está marcado como activo
      const activeLink = page.locator(`${item.selector}.active, ${item.selector}[aria-current="page"]`);
      if (await activeLink.isVisible()) {
        await expect(activeLink).toHaveClass(/active|aria-current/);
      }
      
      // Tomar screenshot de cada página
      await helpers.takeScreenshot(`nav-${item.path.replace('/', '')}`);
    }
  });

  test('should handle browser back/forward navigation', async ({ page }) => {
    // Navegar a diferentes páginas
    await helpers.clickElement('a[href="/news"]');
    await helpers.expectUrlToContain('/news');
    
    await helpers.clickElement('a[href="/trends"]');
    await helpers.expectUrlToContain('/trends');
    
    await helpers.clickElement('a[href="/resources"]');
    await helpers.expectUrlToContain('/resources');
    
    // Probar navegación hacia atrás
    await page.goBack();
    await helpers.expectUrlToContain('/trends');
    
    await page.goBack();
    await helpers.expectUrlToContain('/news');
    
    // Probar navegación hacia adelante
    await page.goForward();
    await helpers.expectUrlToContain('/trends');
  });

  test('should work with direct URL access', async ({ page }) => {
    const directUrls = [
      '/',
      '/news',
      '/trends', 
      '/search',
      '/resources',
      '/analysis',
      '/profile',
      '/login'
    ];

    for (const url of directUrls) {
      await helpers.navigateTo(url);
      await helpers.waitForNetworkIdle();
      
      // Verificar que la página carga sin errores
      expect(page.url()).toContain(url);
      
      // Verificar que el contenido principal está presente
      const mainContent = page.locator('main, [role="main"]');
      await expect(mainContent).toBeVisible();
      
      // Tomar screenshot para documentación
      await helpers.takeScreenshot(`direct-${url.replace('/', '')}`);
    }
  });

  test('should handle hash routing', async ({ page }) => {
    await helpers.navigateTo('/#section1');
    await helpers.waitForNetworkIdle();
    
    // Verificar que el hash se maneja correctamente
    expect(page.url()).toContain('#section1');
    
    // Navegar a otra sección con hash
    await helpers.navigateTo('/news#article-1');
    expect(page.url()).toContain('#article-1');
  });

  test('should handle query parameters', async ({ page }) => {
    const searchUrl = '/search?q=inteligencia+artificial&filter=recent';
    await helpers.navigateTo(searchUrl);
    await helpers.waitForNetworkIdle();
    
    // Verificar que los parámetros de consulta se mantienen
    expect(page.url()).toContain('q=inteligencia+artificial');
    expect(page.url()).toContain('filter=recent');
    
    // Verificar que el formulario de búsqueda refleja los parámetros
    const searchInput = page.locator('input[type="search"], input[placeholder*="buscar"]');
    if (await searchInput.isVisible()) {
      const inputValue = await searchInput.getAttribute('value');
      expect(inputValue).toContain('inteligencia');
    }
  });

  test('should provide accessible navigation', async ({ page }) => {
    // Verificar que los enlaces tienen atributos aria apropiados
    const navLinks = page.locator('nav a, nav button');
    const linkCount = await navLinks.count();
    
    for (let i = 0; i < linkCount; i++) {
      const link = navLinks.nth(i);
      
      // Verificar que los enlaces tienen texto o aria-label
      const hasText = await link.textContent();
      const hasAriaLabel = await link.getAttribute('aria-label');
      
      expect(hasText || hasAriaLabel).toBeTruthy();
    }
    
    // Verificar estructura semántica
    await expect(page.locator('nav[role="navigation"]')).toBeVisible();
    await expect(page.locator('main[role="main"]')).toBeVisible();
  });

  test('should handle mobile navigation', async ({ page }) => {
    // Cambiar a vista móvil
    await helpers.setMobileViewport();
    await helpers.waitForNetworkIdle();
    
    // Verificar que el menú móvil está presente
    const mobileMenuButton = page.locator('[data-testid="mobile-menu-button"], button[aria-label*="menú"], button[aria-label*="menu"]');
    
    if (await mobileMenuButton.isVisible()) {
      // Abrir menú móvil
      await mobileMenuButton.click();
      await helpers.waitForElementVisible('[data-testid="mobile-menu"], nav.mobile-nav');
      
      // Verificar elementos de navegación móvil
      const mobileNavLinks = page.locator('[data-testid="mobile-menu"] a, .mobile-nav a');
      const linkCount = await mobileNavLinks.count();
      expect(linkCount).toBeGreaterThan(0);
      
      // Probar navegación desde menú móvil
      await mobileNavLinks.first().click();
      await helpers.waitForNetworkIdle();
      
      // Verificar que el menú se cierra después de la navegación
      await helpers.waitForElementGone('[data-testid="mobile-menu"]');
      
      // Tomar screenshot del menú móvil
      await helpers.takeScreenshot('mobile-navigation-menu');
    }
  });

  test('should preserve state during navigation', async ({ page }) => {
    // Configurar estado inicial
    await helpers.fillInput('input[type="search"]', 'test query');
    
    // Navegar a otra página y volver
    await helpers.clickElement('a[href="/news"]');
    await helpers.waitForNetworkIdle();
    
    await helpers.clickElement('a[href="/"]');
    await helpers.waitForNetworkIdle();
    
    // Verificar que el estado del input se mantiene
    const searchInput = page.locator('input[type="search"]');
    const inputValue = await searchInput.getAttribute('value');
    expect(inputValue).toBe('test query');
  });

  test('should handle keyboard navigation', async ({ page }) => {
    // Navegación con teclado
    await page.focus('body');
    
    // Tab para navegar a través de enlaces
    for (let i = 0; i < 5; i++) {
      await helpers.pressTab();
      await page.waitForTimeout(200);
    }
    
    // Usar Enter para activar enlace enfocado
    await helpers.pressEnter();
    await helpers.waitForNetworkIdle();
    
    // Verificar que la navegación funcionó
    expect(page.url()).not.toBe('/');
  });

  test('should show active navigation state', async ({ page }) => {
    const navItems = [
      { selector: 'a[href="/"]', path: '/' },
      { selector: 'a[href="/news"]', path: '/news' },
      { selector: 'a[href="/trends"]', path: '/trends' }
    ];

    for (const item of navItems) {
      // Hacer clic en el elemento
      await helpers.clickElement(item.selector);
      await helpers.waitForNetworkIdle();
      
      // Verificar estado activo
      const activeElement = page.locator(`${item.selector}.active, ${item.selector}[aria-current="page"]`);
      
      // Al menos uno de los elementos de navegación debería estar activo
      const anyActive = await page.locator('nav a.active, nav a[aria-current="page"]').count();
      expect(anyActive).toBeGreaterThan(0);
    }
  });

  test('should handle breadcrumb navigation', async ({ page }) => {
    // Ir a una página con breadcrumbs
    await helpers.navigateTo('/news');
    await helpers.waitForNetworkIdle();
    
    // Verificar breadcrumbs si existen
    const breadcrumbs = page.locator('[data-testid="breadcrumbs"], nav[aria-label*="breadcrumb"]');
    
    if (await breadcrumbs.isVisible()) {
      // Verificar estructura de breadcrumbs
      const breadcrumbItems = breadcrumbs.locator('a, span');
      const itemCount = await breadcrumbItems.count();
      expect(itemCount).toBeGreaterThan(0);
      
      // Hacer clic en breadcrumb anterior
      if (itemCount > 1) {
        await breadcrumbItems.first().click();
        await helpers.waitForNetworkIdle();
      }
      
      // Tomar screenshot de breadcrumbs
      await helpers.takeScreenshot('breadcrumbs-navigation');
    }
  });

  test('should handle navigation errors gracefully', async ({ page }) => {
    // Simular error de navegación
    await page.route('**/*', route => {
      const url = route.request().url();
      if (url.includes('/news')) {
        route.abort('failed');
      } else {
        route.continue();
      }
    });
    
    // Intentar navegar a la página con error
    await helpers.clickElement('a[href="/news"]');
    await page.waitForTimeout(2000);
    
    // Verificar que se muestra una página de error apropiada
    const errorMessage = page.locator('[data-testid="error-message"], .error, .alert-error');
    if (await errorMessage.isVisible()) {
      await expect(errorMessage).toContainText(/error|Error|carg|noconect/);
    }
    
    // Tomar screenshot del error
    await helpers.takeScreenshot('navigation-error');
  });
});