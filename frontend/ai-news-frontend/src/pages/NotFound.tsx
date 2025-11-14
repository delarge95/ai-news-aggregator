import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Home, Search, ArrowLeft, Bug, RefreshCw } from 'lucide-react';

const NotFound: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions] = useState([
    { path: '/', label: 'Inicio', description: 'Página principal' },
    { path: '/news', label: 'Noticias', description: 'Últimas noticias de IA' },
    { path: '/trends', label: 'Tendencias', description: 'Tendencias en IA' },
    { path: '/resources', label: 'Recursos', description: 'Recursos útiles' },
    { path: '/analysis', label: 'Análisis IA', description: 'Análisis inteligente' },
    { path: '/profile', label: 'Perfil', description: 'Mi perfil de usuario' }
  ]);
  
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleGoHome = () => {
    navigate('/');
  };

  const handleGoBack = () => {
    window.history.back();
  };

  // Efecto de animación
  useEffect(() => {
    document.title = '404 - Página no encontrada - AI News Aggregator';
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center px-4">
      <div className="max-w-2xl w-full text-center">
        {/* Animación 404 */}
        <div className="mb-8 animate-pulse">
          <h1 className="text-9xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 mb-4">
            404
          </h1>
          <div className="flex justify-center mb-4">
            <Bug className="w-16 h-16 text-gray-400" />
          </div>
        </div>
        
        <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            ¡Oops! Página no encontrada
          </h2>
          <p className="text-gray-600 mb-8 text-lg">
            Lo sentimos, la página que buscas no existe o ha sido movida a otra ubicación. 
            Mientras tanto, puedes explorar nuestras secciones principales.
          </p>
          
          {/* Barra de búsqueda */}
          <form onSubmit={handleSearch} className="mb-8">
            <div className="relative max-w-md mx-auto">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Buscar noticias, tendencias..."
              />
            </div>
          </form>
          
          {/* Botones de acción */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <button 
              onClick={handleGoBack}
              className="flex items-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-all duration-200 hover:shadow-md"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver atrás
            </button>
            
            <button 
              onClick={handleGoHome}
              className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all duration-200 hover:shadow-md"
            >
              <Home className="w-4 h-4" />
              Ir al inicio
            </button>
            
            <button 
              onClick={() => window.location.reload()}
              className="flex items-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all duration-200 hover:shadow-md"
            >
              <RefreshCw className="w-4 h-4" />
              Recargar
            </button>
          </div>
          
          {/* Sugerencias de navegación */}
          <div className="border-t border-gray-200 pt-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-6">Navegación sugerida</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {suggestions.map((suggestion) => (
                <Link
                  key={suggestion.path}
                  to={suggestion.path}
                  className="group p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 text-left"
                >
                  <h4 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                    {suggestion.label}
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">{suggestion.description}</p>
                </Link>
              ))}
            </div>
          </div>
        </div>
        
        {/* Información adicional */}
        <div className="mt-8 text-sm text-gray-500">
          <p>
            ¿Crees que esto es un error?{' '}
            <Link 
              to="/contact" 
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              Contáctanos
            </Link>
          </p>
          <p className="mt-2">
            Código de error: <code className="bg-gray-100 px-2 py-1 rounded text-xs">404_NOT_FOUND</code>
          </p>
        </div>
      </div>
    </div>
  );
};

export default NotFound;