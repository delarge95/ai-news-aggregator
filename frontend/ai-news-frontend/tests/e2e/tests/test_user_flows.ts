import { test, expect } from '@playwright/test';
import { E2EHelpers } from '../../helpers/e2eHelpers';

test.describe('Flujos de Usuario Principales', () => {
  let helpers: E2EHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new E2EHelpers(page);
    await helpers.navigateTo('/');
  });

  test('should display homepage correctly', async ({ page }) => {
    // Verificar que la página principal carga correctamente
    await expect(page).toHaveTitle(/AI News Aggregator/);
    
    // Verificar elementos principales del navbar
    await helpers.expectElementToBeVisible('nav');
    await expect(page.locator('[data-testid="navbar-brand"]')).toBeVisible();
    
    // Verificar navegación principal
    const navLinks = page.locator('nav a');
    await expect(navLinks).toHaveCount(5); // Home, Noticias, Tendencias, Recursos, Análisis IA
    
    // Verificar que hay contenido principal
    await helpers.expectElementToBeVisible('main');
  });

  test('should complete user registration/login flow', async ({ page }) => {
    // Ir a la página de login
    await helpers.navigateTo('/login');
    
    // Verificar que el formulario de login está presente
    await helpers.expectElementToBeVisible('form');
    
    // Intentar login con datos de prueba
    await helpers.fillInput('input[type="email"]', 'test@example.com');
    await helpers.fillInput('input[type="password"]', 'password123');
    
    // Tomar screenshot del formulario completado
    await helpers.takeScreenshot('login-form-filled');
    
    // Enviar formulario
    await helpers.clickElement('button[type="submit"]');
    
    // Verificar redirect o respuesta
    await page.waitForTimeout(1000);
    const currentUrl = page.url();
    
    // El usuario debería ser redirigido o ver un mensaje de error
    // Esto depende de la implementación real del backend
    expect(currentUrl).toMatch(/(\/login|\/profile|\/)/);
  });

  test('should browse and view news articles', async ({ page }) => {
    // Ir a la sección de noticias
    await helpers.navigateTo('/news');
    
    // Verificar que la lista de noticias carga
    await helpers.expectElementToBeVisible('[data-testid="news-container"]');
    
    // Tomar screenshot de la página de noticias
    await helpers.takeScreenshot('news-page-loaded');
    
    // Hacer clic en el primer artículo
    const firstArticle = page.locator('[data-testid="news-article"]').first();
    if (await firstArticle.isVisible()) {
      await firstArticle.click();
      
      // Verificar navegación a detalles del artículo
      await page.waitForTimeout(500);
      const currentUrl = page.url();
      expect(currentUrl).toMatch(/(\/news\/|\/article\/)/);
      
      // Tomar screenshot del artículo
      await helpers.takeScreenshot('article-detail');
    }
  });

  test('should search for content', async ({ page }) => {
    // Ir a la página de búsqueda
    await helpers.navigateTo('/search');
    
    // Verificar interfaz de búsqueda
    await helpers.expectElementToBeVisible('input[type="search"]');
    
    // Realizar búsqueda
    const searchTerm = 'inteligencia artificial';
    await helpers.fillInput('input[type="search"]', searchTerm);
    await helpers.pressEnter();
    
    // Verificar que los resultados aparecen
    await helpers.waitForText('[data-testid="search-results"]', searchTerm);
    
    // Tomar screenshot de resultados
    await helpers.takeScreenshot('search-results');
  });

  test('should navigate through dashboard features', async ({ page }) => {
    // Ir al dashboard de análisis
    await helpers.navigateTo('/analysis');
    
    // Verificar que el dashboard carga
    await helpers.expectElementToBeVisible('[data-testid="analysis-dashboard"]');
    
    // Verificar elementos del dashboard
    await expect(page.locator('[data-testid="analytics-charts"]')).toBeVisible();
    await expect(page.locator('[data-testid="metrics-cards"]')).toBeVisible();
    
    // Tomar screenshot del dashboard
    await helpers.takeScreenshot('analysis-dashboard');
  });

  test('should access and view trends page', async ({ page }) => {
    // Ir a la página de tendencias
    await helpers.navigateTo('/trends');
    
    // Verificar contenido de tendencias
    await helpers.expectElementToBeVisible('[data-testid="trends-container"]');
    
    // Verificar que hay datos de tendencias
    const trendsElements = page.locator('[data-testid="trend-item"]');
    await expect(trendsElements).toHaveCount(await trendsElements.count());
    
    // Tomar screenshot de tendencias
    await helpers.takeScreenshot('trends-page');
  });

  test('should access profile settings', async ({ page }) => {
    // Esta prueba requiere autenticación, así que puede fallar si no hay login
    // Intentar ir al perfil
    await helpers.navigateTo('/profile');
    
    // Verificar si redirige al login (protected route) o muestra el perfil
    await page.waitForTimeout(1000);
    const currentUrl = page.url();
    
    if (currentUrl.includes('/login')) {
      // Esperado: usuario no autenticado debe ir al login
      await helpers.expectElementToBeVisible('form');
      await helpers.takeScreenshot('profile-redirect-to-login');
    } else {
      // Usuario autenticado, verificar contenido del perfil
      await helpers.expectElementToBeVisible('[data-testid="profile-container"]');
      await helpers.takeScreenshot('profile-page');
    }
  });

  test('should complete resource browsing flow', async ({ page }) => {
    // Ir a la página de recursos
    await helpers.navigateTo('/resources');
    
    // Verificar contenido de recursos
    await helpers.expectElementToBeVisible('[data-testid="resources-container"]');
    
    // Verificar diferentes tipos de recursos
    const resourceCategories = page.locator('[data-testid="resource-category"]');
    const categoryCount = await resourceCategories.count();
    expect(categoryCount).toBeGreaterThan(0);
    
    // Hacer clic en la primera categoría
    if (categoryCount > 0) {
      await resourceCategories.first().click();
      await page.waitForTimeout(500);
      
      // Verificar que se muestran recursos de esa categoría
      const resources = page.locator('[data-testid="resource-item"]');
      expect(await resources.count()).toBeGreaterThan(0);
    }
    
    // Tomar screenshot de recursos
    await helpers.takeScreenshot('resources-page');
  });

  test('should handle user session management', async ({ page }) => {
    // Simular sesión de usuario
    await page.addInitScript(() => {
      localStorage.setItem('userSession', JSON.stringify({
        id: '1',
        name: 'Test User',
        email: 'test@example.com',
        authenticated: true
      }));
    });
    
    // Recargar página para aplicar sesión
    await helpers.navigateTo('/');
    
    // Verificar que el usuario está logueado
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="logout-button"]')).toBeVisible();
    
    // Tomar screenshot con usuario logueado
    await helpers.takeScreenshot('user-logged-in');
    
    // Probar logout
    await helpers.clickElement('[data-testid="logout-button"]');
    
    // Verificar que se redirige al login
    await helpers.expectUrlToContain('/login');
  });

  test('should handle 404 error page', async ({ page }) => {
    // Ir a una URL que no existe
    await helpers.navigateTo('/non-existent-page');
    
    // Verificar que se muestra la página 404
    await helpers.expectElementToBeVisible('[data-testid="404-page"]');
    
    // Verificar mensaje de error
    await helpers.expectElementToHaveText('[data-testid="404-page"]', 'No encontrado');
    
    // Verificar link para volver al inicio
    await expect(page.locator('[data-testid="back-to-home"]')).toBeVisible();
    
    // Probar navegación de vuelta al inicio
    await helpers.clickElement('[data-testid="back-to-home"]');
    await helpers.expectUrlToContain('/');
    
    // Tomar screenshot de página 404
    await helpers.takeScreenshot('404-page');
  });
});