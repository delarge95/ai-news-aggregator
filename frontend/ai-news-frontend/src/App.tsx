import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Loading from './components/common/Loading';
import RoutingErrorBoundary from './components/common/RoutingErrorBoundary';
import ProtectedRoute from './components/common/ProtectedRoute';
import { ErrorBoundary } from './components/ErrorBoundary';
// import { NAVIGATION_CONFIG } from './lib/navigation';

// Lazy loading de componentes para mejor rendimiento
const Home = React.lazy(() => import('./pages/Home'));
// Usar el nuevo sistema de noticias con IA
import NewsExample from './components/news/NewsExample';
const News = React.lazy(() => Promise.resolve({ default: NewsExample }));
const Trends = React.lazy(() => import('./pages/Trends'));
const Resources = React.lazy(() => import('./pages/Resources'));
const Profile = React.lazy(() => import('./pages/Profile'));
const Login = React.lazy(() => import('./pages/Login'));
const NotFound = React.lazy(() => import('./pages/NotFound'));

// Componente de análisis IA
const Analysis = React.lazy(() => 
  import('./components/analysis/AnalyticsDashboard').then(module => ({ 
    default: module.AnalyticsDashboard 
  }))
);

// Componente de búsqueda
import { SearchInterface } from './components/search/SearchInterface';
const Search = React.lazy(() => 
  Promise.resolve({ 
    default: () => (
      <div className="container mx-auto py-8">
        <SearchInterface 
          showSavedSearches={true}
          showHistory={true}
          showFilters={true}
          onArticleClick={(article) => {
            console.log('Article clicked:', article);
          }}
        />
      </div>
    )
  })
);

const Settings = React.lazy(() => 
  import('./pages/Profile').then(module => ({ default: () => (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Configuración</h1>
      <p className="text-gray-600">Página de configuración en desarrollo...</p>
    </div>
  )}))
);

const Privacy = React.lazy(() => 
  import('./pages/Profile').then(module => ({ default: () => (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Privacidad</h1>
      <p className="text-gray-600">Política de privacidad en desarrollo...</p>
    </div>
  )}))
);

// Componente de carga con suspense
const PageLoader: React.FC = () => (
  <Loading fullScreen text="Cargando página..." />
);

// Componente principal de la aplicación
function App() {
  return (
    <div className="App">
      <Router>
        <ErrorBoundary>
          <RoutingErrorBoundary>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                {/* Rutas principales con layout */}
                <Route path="/" element={<Layout />}>
                  <Route index element={<Home />} />
                  <Route path="news" element={<News />} />
                  <Route path="search" element={<Search />} />
                  <Route path="trends" element={<Trends />} />
                  <Route path="analysis" element={<Analysis />} />
                  <Route path="resources" element={<Resources />} />
                  
                  {/* Rutas de búsqueda */}
                  <Route path="search" element={<Search />} />
                  
                  {/* Rutas protegidas */}
                  <Route 
                    path="profile" 
                    element={
                      <ProtectedRoute>
                        <Profile />
                      </ProtectedRoute>
                    } 
                  />
                  
                  <Route 
                    path="settings" 
                    element={
                      <ProtectedRoute>
                        <Settings />
                      </ProtectedRoute>
                    } 
                  />
                  
                  <Route 
                    path="privacy" 
                    element={
                      <ProtectedRoute>
                        <Privacy />
                      </ProtectedRoute>
                    } 
                  />
                </Route>
                
                {/* Rutas sin layout (pantallas completas) */}
                <Route 
                  path="/login" 
                  element={
                    <Suspense fallback={<Loading fullScreen text="Cargando..." />}>
                      <Login />
                    </Suspense>
                  } 
                />
                
                {/* Ruta 404 */}
                <Route 
                  path="*" 
                  element={
                    <Suspense fallback={<Loading fullScreen text="Cargando..." />}>
                      <NotFound />
                    </Suspense>
                  } 
                />
              </Routes>
            </Suspense>
          </RoutingErrorBoundary>
        </ErrorBoundary>
      </Router>
    </div>
  );
}

export default App;