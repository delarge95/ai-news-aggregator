import React from 'react';
import { Card, CardContent } from '../ui/card';
import { 
  LayoutDashboard, 
  Newspaper, 
  BarChart3, 
  Settings, 
  Users,
  Database,
  Activity
} from 'lucide-react';
import { cn } from '../../lib/utils';

interface SidebarProps {
  activeSection?: string;
  onSectionChange?: (section: string) => void;
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({
  activeSection = 'dashboard',
  onSectionChange,
  className
}) => {
  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <LayoutDashboard className="h-5 w-5" />,
      description: 'Vista general'
    },
    {
      id: 'articles',
      label: 'Artículos',
      icon: <Newspaper className="h-5 w-5" />,
      description: 'Gestión de artículos'
    },
    {
      id: 'analytics',
      label: 'Análisis',
      icon: <BarChart3 className="h-5 w-5" />,
      description: 'Estadísticas detalladas'
    },
    {
      id: 'sources',
      label: 'Fuentes',
      icon: <Database className="h-5 w-5" />,
      description: 'Configurar fuentes'
    },
    {
      id: 'activity',
      label: 'Actividad',
      icon: <Activity className="h-5 w-5" />,
      description: 'Registro de actividad'
    },
    {
      id: 'users',
      label: 'Usuarios',
      icon: <Users className="h-5 w-5" />,
      description: 'Gestión de usuarios'
    },
    {
      id: 'settings',
      label: 'Configuración',
      icon: <Settings className="h-5 w-5" />,
      description: 'Ajustes del sistema'
    }
  ];

  return (
    <Card className={cn("w-64 h-fit", className)}>
      <CardContent className="p-0">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Navegación</h2>
          <p className="text-sm text-muted-foreground">Panel de control</p>
        </div>
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => onSectionChange?.(item.id)}
              className={cn(
                "w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors",
                activeSection === item.id
                  ? "bg-blue-50 text-blue-700 border border-blue-200"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <div className={cn(
                "flex-shrink-0",
                activeSection === item.id ? "text-blue-600" : "text-gray-400"
              )}>
                {item.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">
                  {item.label}
                </div>
                <div className="text-xs text-muted-foreground truncate">
                  {item.description}
                </div>
              </div>
            </button>
          ))}
        </nav>
      </CardContent>
    </Card>
  );
};

export default Sidebar;