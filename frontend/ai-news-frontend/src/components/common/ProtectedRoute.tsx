import React, { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Lock, ArrowLeft, Loader2 } from 'lucide-react';
import { ProtectedRouteProps } from '../../types';

// Mock de autenticación - en una app real esto vendría de un contexto o estado global
const useAuth = () => {
  // Simulamos autenticación - cambiar a false para probar el comportamiento de no autenticado
  const [isLoading, setIsLoading] = useState(false);
  
  // Simulación de carga de autenticación
  React.useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 500);
    
    return () => clearTimeout(timer);
  }, []);
  
  return {
    isAuthenticated: true, // Cambiar a false para probar
    isLoading,
    user: {
      id: '1',
      name: 'Usuario Demo',
      email: 'usuario@ejemplo.com'
    }
  };
};

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  fallback 
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Mostrar loading mientras se verifica la autenticación
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Verificando autenticación...</p>
        </div>
      </div>
    );
  }

  // Si no está autenticado, redirigir al login
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full text-center">
          <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200">
            <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <Lock className="w-8 h-8 text-white" />
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-3">
              Acceso Restringido
            </h2>
            
            <p className="text-gray-600 mb-8">
              Necesitas iniciar sesión para acceder a esta página. 
              Tu sesión puede haber expirado.
            </p>
            
            <div className="space-y-3">
              <button
                onClick={() => window.history.back()}
                className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all duration-200 hover:shadow-md"
              >
                <ArrowLeft className="w-4 h-4" />
                Volver atrás
              </button>
              
              <Navigate 
                to="/login" 
                state={{ from: location.pathname, message: 'Se requiere autenticación' }}
                replace
              />
            </div>
            
            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-500">
                Si tienes problemas para acceder, contacta a soporte técnico.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Si está autenticado, mostrar el contenido protegido
  return <>{children}</>;
};

export default ProtectedRoute;