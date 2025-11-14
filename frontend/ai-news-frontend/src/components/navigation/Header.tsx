import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Bell, Search, User } from 'lucide-react';
import { useIsMobile } from '../../hooks/use-mobile';
import { cn } from '../../lib/utils';

interface HeaderProps {
  onMenuToggle?: () => void;
  sidebarOpen?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle, sidebarOpen = false }) => {
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const location = useLocation();
  const isMobile = useIsMobile();

  const navigationItems = [
    { path: '/', label: 'Inicio' },
    { path: '/news', label: 'Noticias' },
    { path: '/trends', label: 'Tendencias' },
    { path: '/resources', label: 'Recursos' }
  ];

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Implementar búsqueda
    console.log('Searching for:', searchQuery);
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y menú hamburger */}
          <div className="flex items-center">
            {isMobile && (
              <button
                onClick={onMenuToggle}
                className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label="Toggle menu"
              >
                {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            )}
            
            <Link to="/" className="flex items-center ml-2 md:ml-0">
              <div className="bg-blue-600 text-white p-2 rounded-lg">
                <span className="text-lg font-bold">AI</span>
              </div>
              <span className="ml-3 text-xl font-bold text-gray-900 hidden sm:block">
                News Aggregator
              </span>
            </Link>
          </div>

          {/* Navegación desktop */}
          <nav className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "text-sm font-medium transition-colors hover:text-blue-600",
                  isActivePath(item.path)
                    ? "text-blue-600 border-b-2 border-blue-600 pb-1"
                    : "text-gray-700"
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Barra de búsqueda y acciones */}
          <div className="flex items-center space-x-4">
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
                  className={cn(
                    "w-64 pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm",
                    "focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all",
                    searchFocused ? "w-80" : ""
                  )}
                  placeholder="Buscar noticias, tendencias..."
                />
              </form>
            </div>

            {/* Búsqueda mobile */}
            <button className="sm:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md">
              <Search className="h-5 w-5" />
            </button>

            {/* Notificaciones */}
            <button className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full"></span>
            </button>

            {/* Perfil de usuario */}
            <div className="flex items-center">
              <Link
                to="/profile"
                className="flex items-center space-x-2 p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md"
              >
                <User className="h-5 w-5" />
                {!isMobile && <span className="text-sm">Perfil</span>}
              </Link>
            </div>
          </div>
        </div>

        {/* Búsqueda mobile expandida */}
        {searchFocused && isMobile && (
          <div className="pb-4 sm:hidden">
            <form onSubmit={handleSearchSubmit}>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Buscar noticias, tendencias..."
                  autoFocus
                />
              </div>
            </form>
          </div>
        )}
      </div>
    </header>
  );
};

export default Header;