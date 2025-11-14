import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Home, 
  Newspaper, 
  TrendingUp, 
  BookOpen, 
  User, 
  Settings, 
  Shield,
  BarChart3,
  X
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { useIsMobile } from '../../hooks/use-mobile';
import MobileNavigationOverlay from './MobileNavigationOverlay';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const isMobile = useIsMobile();

  const navigationItems = [
    {
      section: 'Principal',
      items: [
        { path: '/', label: 'Inicio', icon: Home },
        { path: '/news', label: 'Noticias', icon: Newspaper },
        { path: '/trends', label: 'Tendencias', icon: TrendingUp },
        { path: '/resources', label: 'Recursos', icon: BookOpen },
        { path: '/analysis', label: 'Análisis IA', icon: BarChart3 }
      ]
    },
    {
      section: 'Cuenta',
      items: [
        { path: '/profile', label: 'Mi Perfil', icon: User, protected: true },
        { path: '/settings', label: 'Configuración', icon: Settings, protected: true },
        { path: '/privacy', label: 'Privacidad', icon: Shield, protected: true }
      ]
    }
  ];

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleLinkClick = () => {
    if (isMobile) {
      onClose();
    }
  };

  // En desktop, el sidebar siempre está abierto, en mobile se sobrepone
  const sidebarContent = (
    <div className="h-full flex flex-col">
      {/* Header del sidebar */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <Link to="/" className="flex items-center space-x-2" onClick={handleLinkClick}>
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-2 rounded-lg">
            <span className="text-lg font-bold">AI</span>
          </div>
          <span className="text-lg font-bold text-gray-900">News</span>
        </Link>
        
        <button
          onClick={onClose}
          className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
          aria-label="Cerrar menú"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navegación */}
      <nav className="flex-1 overflow-y-auto py-4">
        {navigationItems.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-6">
            <h3 className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              {section.section}
            </h3>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = isActivePath(item.path);
                
                return (
                  <li key={item.path}>
                    <Link
                      to={item.path}
                      onClick={handleLinkClick}
                      className={cn(
                        "flex items-center px-4 py-3 text-sm font-medium transition-all",
                        "hover:bg-gray-50 hover:text-gray-900 hover:translate-x-1",
                        isActive 
                          ? "text-blue-600 bg-blue-50 border-r-2 border-blue-600 shadow-sm" 
                          : "text-gray-700"
                      )}
                    >
                      <Icon className="w-5 h-5 mr-3 flex-shrink-0" />
                      {item.label}
                      {item.protected && (
                        <span className="ml-auto bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded-full font-medium">
                          PRO
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Footer del sidebar */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="text-xs text-gray-500 space-y-1">
          <p className="font-medium">AI News Aggregator</p>
          <p>© 2025 Todos los derechos reservados</p>
          <div className="flex space-x-2 mt-3">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs text-gray-600">Sistema activo</span>
          </div>
        </div>
      </div>
    </div>
  );

  // En desktop, mostrar normalmente; en mobile, usar overlay
  if (isMobile) {
    return (
      <MobileNavigationOverlay isOpen={isOpen} onClose={onClose}>
        <aside className="bg-white h-full w-full shadow-xl">
          {sidebarContent}
        </aside>
      </MobileNavigationOverlay>
    );
  }

  return (
    <aside className="bg-white border-r border-gray-200 h-full w-64 flex-shrink-0">
      {sidebarContent}
    </aside>
  );
};

export default Sidebar;