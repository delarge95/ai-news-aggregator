import React from 'react';
import { ChartsDemoPage } from '@/components/charts';

/**
 * Ejemplo de implementación del sistema de gráficos
 * 
 * Este componente demuestra cómo integrar el sistema completo de gráficos
 * en una aplicación real. Incluye todos los componentes principales:
 * - SentimentTrendsChart
 * - TopicDistributionChart  
 * - SourcePerformanceChart
 * - RealtimeMetricsChart
 */
const ChartsExample: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header de la página */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                AI News Aggregator - Dashboard de Análisis
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">
                Sistema de Gráficos v1.0
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal con la demostración de gráficos */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ChartsDemoPage />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Sistema de Gráficos
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Recharts integration</li>
                <li>• Responsive design</li>
                <li>• Real-time updates</li>
                <li>• Export functionality</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Características
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Custom tooltips</li>
                <li>• Interactive legends</li>
                <li>• Theme support</li>
                <li>• Animation system</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">
                Soporte
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• TypeScript support</li>
                <li>• Error handling</li>
                <li>• Performance optimized</li>
                <li>• Accessibility ready</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-8 pt-8 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-600">
              © 2024 AI News Aggregator. Desarrollado con React + TypeScript + Recharts.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default ChartsExample;