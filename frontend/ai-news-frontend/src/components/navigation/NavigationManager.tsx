import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Breadcrumbs, { ModernBreadcrumbs } from './Breadcrumbs';
import NavigationContext from './NavigationContext';
import ConnectionStatus from '../common/ConnectionStatus';
import { useIsMobile } from '../../hooks/use-mobile';
import { useNavigation } from '../../hooks/useNavigation';

interface NavigationManagerProps {
  showContext?: boolean;
  showStatus?: boolean;
  breadcrumbsVariant?: 'default' | 'modern';
}

const NavigationManager: React.FC<NavigationManagerProps> = ({
  showContext = true,
  showStatus = true,
  breadcrumbsVariant = 'default'
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const isMobile = useIsMobile();
  const location = useLocation();
  
  // Usar el hook de navegación personalizado
  const { 
    breadcrumbs, 
    navigate, 
    goBack, 
    canGoBack,
    isLoading 
  } = useNavigation({
    updateTitle: true,
    scrollToTop: true,
    generateBreadcrumbs: true
  });

  // Cerrar sidebar cuando cambia la ruta en móvil
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [location.pathname, isMobile]);

  const handleMenuToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    setSidebarOpen(false);
  };

  const BreadcrumbComponent = breadcrumbsVariant === 'modern' ? ModernBreadcrumbs : Breadcrumbs;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navbar principal */}
      <Navbar 
        onMenuToggle={handleMenuToggle}
        sidebarOpen={sidebarOpen}
      />

      <div className="flex">
        {/* Sidebar */}
        <div className={`${isMobile ? 'w-0' : 'w-64'} flex-shrink-0`}>
          {!isMobile ? (
            <Sidebar 
              isOpen={true}
              onClose={() => {}}
            />
          ) : (
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
              {/* Estado de carga global */}
              {isLoading && (
                <div className="mb-4">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      <span className="text-blue-800 text-sm">Cargando contenido...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Barra de estado y navegación contextual */}
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
                {/* Breadcrumbs */}
                <div className="flex-1">
                  <BreadcrumbComponent 
                    customBreadcrumbs={breadcrumbs}
                    showHome={true}
                  />
                </div>

                {/* Estado de conexión */}
                {showStatus && (
                  <div className="flex items-center gap-4">
                    {canGoBack && (
                      <button
                        onClick={goBack}
                        className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                      >
                        ← Volver
                      </button>
                    )}
                    <ConnectionStatus showTimestamp />
                  </div>
                )}
              </div>

              {/* Navegación contextual */}
              {showContext && <NavigationContext />}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default NavigationManager;