import React from 'react';

const Home: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          AI News Aggregator
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Las últimas noticias y tendencias en Inteligencia Artificial
        </p>
        <div className="grid md:grid-cols-3 gap-6 mt-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Noticias Recientes</h3>
            <p className="text-gray-600">Mantente al día con las últimas noticias de IA</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Análisis de Tendencias</h3>
            <p className="text-gray-600">Descubre las tendencias más importantes del sector</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold mb-2">Recursos Útiles</h3>
            <p className="text-gray-600">Encuentra herramientas y recursos de IA</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;