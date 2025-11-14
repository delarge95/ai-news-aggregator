import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Menu, X, Search, Bell, User, ChevronDown } from 'lucide-react';
import { useIsMobile } from '../../hooks/use-mobile';
import { cn } from '../../lib/utils';

interface NavbarProps {
  onMenuToggle?: () => void;
  sidebarOpen?: boolean;
  className?: string;
}

const Navbar: React.FC<NavbarProps> = ({ onMenuToggle, sidebarOpen = false, className }) => {
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const isMobile = useIsMobile();

  const navigationItems = [
    { path: '/', label: 'Inicio' },
    { path: '/news', label: 'Noticias' },
    { path: '/trends', label: 'Tendencias' },
    { path: '/resources', label: 'Recursos' },
    { path: '/analysis', label: 'Análisis IA' }
  ];

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      setSearchFocused(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setSearchFocused(false);
    }
  };

  // Mock de notificaciones
  const notifications = [
    { id: 1, title: 'Nueva tendencia detectada', message: 'GPT-5 ha sido lanzado', time: '2 min' },
    { id: 2, title: 'Análisis completado', message: 'Tu reporte de sentiment está listo', time: '1 hora' },
    { id: 3, title: 'Actualización de fuentes', message: '5 nuevas fuentes agregadas', time: '2 horas' }
  ];

  return (
    <nav className={cn("bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50", className)}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y menú hamburger */}
          <div className="flex items-center">
            {isMobile && (
              <button
                onClick={onMenuToggle}
                className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                aria-label="Toggle menu"
                aria-expanded={sidebarOpen}
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            )}
            
            <Link to="/" className="flex items-center ml-2 md:ml-0 group">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-2 rounded-lg group-hover:from-blue-700 group-hover:to-purple-700 transition-all">
                <span className="text-lg font-bold">AI</span>
              </div>
              <span className="ml-3 text-xl font-bold text-gray-900 hidden sm:block">
                News Aggregator
              </span>
            </Link>
          </div>

          {/* Navegación desktop */}
          <div className="hidden lg:flex items-center space-x-8">
            {navigationItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "text-sm font-medium transition-all duration-200 hover:text-blue-600 relative",
                  isActivePath(item.path)
                    ? "text-blue-600"
                    : "text-gray-700"
                )}
              >
                {item.label}
                {isActivePath(item.path) && (
                  <div className="absolute -bottom-6 left-0 right-0 h-0.5 bg-blue-600 rounded-full" />
                )}
              </Link>
            ))}
          </div>

          {/* Acciones del usuario */}
          <div className="flex items-center space-x-3">
            {/* Barra de búsqueda - Desktop */}
            <div className="hidden sm:block">
              <form onSubmit={handleSearchSubmit} className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setSearchFocused(true)}
                  onBlur={() => setSearchFocused(false)}
                  onKeyDown={handleKeyDown}
                  className={cn(
                    "w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm",
                    "focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all",
                    "placeholder-gray-500",
                    searchFocused ? "w-80 shadow-lg" : "shadow-sm"
                  )}
                  placeholder="Buscar noticias, tendencias..."
                />
              </form>
            </div>

            {/* Búsqueda mobile */}
            <button 
              onClick={() => navigate('/search')}
              className="sm:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              aria-label="Buscar"
            >
              <Search className="h-5 w-5" />
            </button>

            {/* Notificaciones */}
            <div className="relative">
              <button 
                onClick={() => setNotificationOpen(!notificationOpen)}
                className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                aria-label="Notificaciones"
              >
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full animate-pulse"></span>
              </button>

              {/* Dropdown de notificaciones */}
              {notificationOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-4 border-b border-gray-200">
                    <h3 className="text-sm font-semibold text-gray-900">Notificaciones</h3>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {notifications.map((notification) => (
                      <div key={notification.id} className="p-4 hover:bg-gray-50 border-b border-gray-100 last:border-b-0">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900">{notification.title}</p>
                            <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                          </div>
                          <span className="text-xs text-gray-500">{notification.time}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="p-3 border-t border-gray-200">
                    <Link 
                      to="/notifications" 
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                      onClick={() => setNotificationOpen(false)}
                    >
                      Ver todas las notificaciones
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Perfil de usuario */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center space-x-2 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
              >
                <div className="bg-blue-100 p-1 rounded-full">
                  <User className="h-4 w-4 text-blue-600" />
                </div>
                {!isMobile && (
                  <>
                    <span className="text-sm font-medium">Usuario</span>
                    <ChevronDown className="h-4 w-4" />
                  </>
                )}
              </button>

              {/* Dropdown del usuario */}
              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  <div className="p-4 border-b border-gray-200">
                    <p className="text-sm font-medium text-gray-900">Usuario Demo</p>
                    <p className="text-sm text-gray-600">usuario@ejemplo.com</p>
                  </div>
                  <div className="py-2">
                    <Link 
                      to="/profile" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Mi Perfil
                    </Link>
                    <Link 
                      to="/settings" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Configuración
                    </Link>
                    <Link 
                      to="/privacy" 
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Privacidad
                    </Link>
                    <div className="border-t border-gray-200 my-2"></div>
                    <button 
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                      onClick={() => {
                        setUserMenuOpen(false);
                        // Aquí iría la lógica de logout
                      }}
                    >
                      Cerrar Sesión
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Búsqueda mobile expandida */}
        {searchFocused && isMobile && (
          <div className="pb-4 animate-in slide-in-from-top-2 duration-200">
            <form onSubmit={handleSearchSubmit}>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Buscar noticias, tendencias..."
                  autoFocus
                />
              </div>
            </form>
          </div>
        )}

        {/* Navegación móvil horizontal */}
        {isMobile && (
          <div className="pb-4 lg:hidden">
            <div className="flex space-x-1 overflow-x-auto scrollbar-hide">
              {navigationItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex-shrink-0 px-4 py-2 text-xs font-medium rounded-full transition-colors",
                    isActivePath(item.path)
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  )}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Overlay para cerrar dropdowns al hacer click fuera */}
      {(notificationOpen || userMenuOpen) && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => {
            setNotificationOpen(false);
            setUserMenuOpen(false);
          }}
        />
      )}
    </nav>
  );
};

export default Navbar;