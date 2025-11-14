import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from '../navigation/Navbar';
import Sidebar from '../navigation/Sidebar';
import Breadcrumbs from '../navigation/Breadcrumbs';
import ScrollToTop, { ScrollToTopButton } from '../common/ScrollToTop';
import { useIsMobile } from '../../hooks/use-mobile';
import { updatePageTitle, scrollToTop } from '../../lib/navigation';

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useIsMobile();
  const location = useLocation();

  // Actualizar título de página en cambios de ruta
  useEffect(() => {
    updatePageTitle(location.pathname);
  }, [location.pathname]);

  // Scroll automático al top en cambios de ruta
  useEffect(() => {
    scrollToTop('auto');
  }, [location.pathname]);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Scroll to top en cambios de ruta */}
      <ScrollToTop />
      
      {/* Navbar */}
      <Navbar 
        onMenuToggle={handleMenuToggle}
        sidebarOpen={sidebarOpen}
      />
      
      <div className="flex flex-1">
        {/* Sidebar - Solo visible en desktop, overlay en mobile */}
        <div className={`${isMobile ? 'w-0' : 'w-64'} flex-shrink-0`}>
          {!isMobile && (
            <Sidebar 
              isOpen={true}
              onClose={() => {}}
            />
          )}
          {isMobile && (
            <Sidebar 
              isOpen={sidebarOpen}
              onClose={handleSidebarClose}
            />
          )}
        </div>
        
        {/* Contenido principal */}
        <main className="flex-1 overflow-x-hidden">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {/* Breadcrumbs */}
              <Breadcrumbs />
              
              {/* Contenido de la página */}
              <div className="min-h-[calc(100vh-200px)]">
                <Outlet />
              </div>
            </div>
          </div>
        </main>
      </div>
      
      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="bg-blue-600 text-white p-2 rounded-lg">
                  <span className="text-lg font-bold">AI</span>
                </div>
                <span className="text-xl font-bold text-gray-900">
                  News Aggregator
                </span>
              </div>
              <p className="text-gray-600 text-sm">
                Tu fuente confiable de noticias y tendencias en Inteligencia Artificial. 
                Mantente actualizado con las últimas novedades del mundo de la IA.
              </p>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Navegación</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="/" className="hover:text-blue-600">Inicio</a></li>
                <li><a href="/news" className="hover:text-blue-600">Noticias</a></li>
                <li><a href="/trends" className="hover:text-blue-600">Tendencias</a></li>
                <li><a href="/resources" className="hover:text-blue-600">Recursos</a></li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">Soporte</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li><a href="/help" className="hover:text-blue-600">Ayuda</a></li>
                <li><a href="/contact" className="hover:text-blue-600">Contacto</a></li>
                <li><a href="/privacy" className="hover:text-blue-600">Privacidad</a></li>
                <li><a href="/terms" className="hover:text-blue-600">Términos</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-200 mt-8 pt-8 text-center">
            <p className="text-gray-600 text-sm">
              © 2025 AI News Aggregator. Todos los derechos reservados.
            </p>
          </div>
        </div>
      </footer>
      
      {/* Botón de scroll to top */}
      <ScrollToTopButton />
    </div>
  );
};

export default Layout;