import React from 'react';
import { TrendingUp, BarChart3, PieChart, Activity } from 'lucide-react';

const Trends: React.FC = () => {
  const trends = [
    { name: "Large Language Models", growth: "+25%", sentiment: "positive" },
    { name: "AI Agents", growth: "+18%", sentiment: "positive" },
    { name: "Computer Vision", growth: "+12%", sentiment: "positive" },
    { name: "Autonomous Vehicles", growth: "+8%", sentiment: "neutral" },
    { name: "AI Ethics", growth: "+15%", sentiment: "neutral" },
    { name: "Neural Networks", growth: "+5%", sentiment: "neutral" }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Tendencias en IA</h1>
        <p className="text-gray-600">
          Análisis de las tendencias más importantes en Inteligencia Artificial basado en datos de múltiples fuentes.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Tendencias Emergentes
          </h2>
          <div className="space-y-4">
            {trends.map((trend, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="font-medium">{trend.name}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-semibold ${
                    trend.sentiment === 'positive' ? 'text-green-600' : 'text-yellow-600'
                  }`}>
                    {trend.growth}
                  </span>
                  <div className={`w-2 h-2 rounded-full ${
                    trend.sentiment === 'positive' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Distribución por Categorías
          </h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span>Procesamiento de Lenguaje Natural</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded">
                  <div className="w-16 h-2 bg-blue-500 rounded"></div>
                </div>
                <span className="text-sm text-gray-600">35%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>Computer Vision</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded">
                  <div className="w-12 h-2 bg-green-500 rounded"></div>
                </div>
                <span className="text-sm text-gray-600">25%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>Machine Learning</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded">
                  <div className="w-10 h-2 bg-purple-500 rounded"></div>
                </div>
                <span className="text-sm text-gray-600">20%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>Robótica</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded">
                  <div className="w-8 h-2 bg-orange-500 rounded"></div>
                </div>
                <span className="text-sm text-gray-600">15%</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span>Otros</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-gray-200 rounded">
                  <div className="w-2 h-2 bg-red-500 rounded"></div>
                </div>
                <span className="text-sm text-gray-600">5%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-8 bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Actividad en Tiempo Real
        </h2>
        <div className="grid md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded">
            <div className="text-2xl font-bold text-blue-600">847</div>
            <div className="text-sm text-gray-600">Artículos Publicados Hoy</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded">
            <div className="text-2xl font-bold text-green-600">156</div>
            <div className="text-sm text-gray-600">Nuevas Investigaciones</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded">
            <div className="text-2xl font-bold text-purple-600">2.3K</div>
            <div className="text-sm text-gray-600">Menciones en Redes</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Trends;