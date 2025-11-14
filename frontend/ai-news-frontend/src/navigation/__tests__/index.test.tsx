/**
 * Test de integración para el sistema de navegación
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { 
  Layout, 
  Navbar, 
  Sidebar, 
  Breadcrumbs, 
  ProtectedRoute,
  ScrollToTop,
  ConnectionStatus,
  NotFound,
  NavigationManager,
  ROUTES
} from './index';

// Mock hook
jest.mock('../hooks/use-mobile', () => ({
  useIsMobile: () => ({ isMobile: false, width: 1024 })
}));

const renderWithRouter = (component: React.ReactNode) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Sistema de Navegación', () => {
  describe('Layout Component', () => {
    it('debe renderizar el layout principal', () => {
      renderWithRouter(
        <Layout>
          <div>Contenido de prueba</div>
        </Layout>
      );
      
      expect(screen.getByText('Contenido de prueba')).toBeInTheDocument();
    });
  });

  describe('Navbar Component', () => {
    it('debe renderizar la barra de navegación', () => {
      renderWithRouter(<Navbar />);
      
      expect(screen.getByText('AI News Aggregator')).toBeInTheDocument();
    });

    it('debe mostrar el botón de menú en móvil', () => {
      renderWithRouter(<Navbar sidebarOpen={false} />);
      
      // El botón de menú debería estar presente
      const menuButton = screen.getByRole('button', { name: /toggle menu/i });
      expect(menuButton).toBeInTheDocument();
    });
  });

  describe('Sidebar Component', () => {
    it('debe renderizar la barra lateral', () => {
      renderWithRouter(
        <Sidebar isOpen={true} onClose={() => {}} />
      );
      
      expect(screen.getByText('Inicio')).toBeInTheDocument();
      expect(screen.getByText('Noticias')).toBeInTheDocument();
    });

    it('debe mostrar indicadores PRO para rutas protegidas', () => {
      renderWithRouter(
        <Sidebar isOpen={true} onClose={() => {}} />
      );
      
      expect(screen.getByText('PRO')).toBeInTheDocument();
    });
  });

  describe('Breadcrumbs Component', () => {
    it('debe generar breadcrumbs automáticamente', () => {
      renderWithRouter(<Breadcrumbs />);
      
      // En la ruta principal, debería mostrar Inicio
      expect(screen.getByText('Inicio')).toBeInTheDocument();
    });

    it('debe usar breadcrumbs personalizados cuando se proporcionen', () => {
      const customBreadcrumbs = [
        { label: 'Inicio', path: '/', isActive: false },
        { label: 'Noticias', path: '/news', isActive: true }
      ];
      
      renderWithRouter(
        <Breadcrumbs customBreadcrumbs={customBreadcrumbs} />
      );
      
      expect(screen.getByText('Inicio')).toBeInTheDocument();
      expect(screen.getByText('Noticias')).toBeInTheDocument();
    });
  });

  describe('ProtectedRoute Component', () => {
    it('debe renderizar children cuando está autenticado', () => {
      renderWithRouter(
        <ProtectedRoute>
          <div>Contenido protegido</div>
        </ProtectedRoute>
      );
      
      expect(screen.getByText('Contenido protegido')).toBeInTheDocument();
    });
  });

  describe('ScrollToTop Component', () => {
    it('debe renderizar sin errores', () => {
      renderWithRouter(<ScrollToTop />);
      // No debería renderizar nada visible
      expect(document.body).toBeInTheDocument();
    });

    it('debe renderizar el botón de scroll to top', () => {
      renderWithRouter(<ScrollToTopButton />);
      // El botón solo aparece cuando se hace scroll
      expect(screen.queryByRole('button', { name: /scroll to top/i })).not.toBeInTheDocument();
    });
  });

  describe('ConnectionStatus Component', () => {
    it('debe mostrar el estado de conexión', () => {
      renderWithRouter(<ConnectionStatus showTimestamp />);
      
      expect(screen.getByText(/conectado|sin conexión/i)).toBeInTheDocument();
    });
  });

  describe('NavigationManager Component', () => {
    it('debe renderizar el gestor completo de navegación', () => {
      renderWithRouter(
        <NavigationManager 
          showContext={true}
          showStatus={true}
        />
      );
      
      expect(screen.getByText('AI News Aggregator')).toBeInTheDocument();
    });
  });

  describe('NotFound Component', () => {
    it('debe mostrar la página 404', () => {
      renderWithRouter(<NotFound />);
      
      expect(screen.getByText('404')).toBeInTheDocument();
      expect(screen.getByText(/página no encontrada/i)).toBeInTheDocument();
    });

    it('debe tener botones de navegación', () => {
      renderWithRouter(<NotFound />);
      
      expect(screen.getByText('Ir al inicio')).toBeInTheDocument();
      expect(screen.getByText('Volver atrás')).toBeInTheDocument();
    });
  });

  describe('Constantes y Utilidades', () => {
    it('debe tener las rutas definidas', () => {
      expect(ROUTES.HOME).toBe('/');
      expect(ROUTES.NEWS).toBe('/news');
      expect(ROUTES.TRUNDS).toBe('/trends');
    });

    it('debe tener la versión del sistema', () => {
      expect(typeof NAVIGATION_VERSION).toBe('string');
      expect(NAVIGATION_VERSION).toBe('1.0.0');
    });

    it('debe validar configuración de navegación', () => {
      expect(validateNavigationConfig({
        showContext: true,
        showStatus: false,
        breadcrumbsVariant: 'default',
        enableAnalytics: false
      })).toBe(true);

      expect(validateNavigationConfig({
        showContext: 'invalid', // Tipo incorrecto
        showStatus: true,
        breadcrumbsVariant: 'modern',
        enableAnalytics: false
      })).toBe(false);
    });

    it('debe crear breadcrumbs correctamente', () => {
      const breadcrumb = createBreadcrumb('Test', '/test', true);
      expect(breadcrumb).toEqual({
        label: 'Test',
        path: '/test',
        isActive: true
      });
    });

    it('debe crear items de navegación correctamente', () => {
      const navItem = createNavItem('test', 'Test Item', '/test', {
        protected: true,
        description: 'Test description',
        badge: 'NEW'
      });
      
      expect(navItem).toEqual({
        id: 'test',
        label: 'Test Item',
        path: '/test',
        protected: true,
        description: 'Test description',
        badge: 'NEW'
      });
    });
  });
});

// Test de integración complejo
describe('Integración del Sistema', () => {
  it('debe permitir navegación completa entre componentes', () => {
    const TestApp = () => (
      <BrowserRouter>
        <NavigationManager showContext={false}>
          <div>Página de prueba</div>
        </NavigationManager>
      </BrowserRouter>
    );

    render(<TestApp />);
    
    // Verificar que todos los componentes principales están presentes
    expect(screen.getByText('AI News Aggregator')).toBeInTheDocument();
    expect(screen.getByText('Inicio')).toBeInTheDocument();
    expect(screen.getByText('Noticias')).toBeInTheDocument();
    expect(screen.getByText('Página de prueba')).toBeInTheDocument();
  });
});

// Exportar para uso en otros tests
export * from './index';