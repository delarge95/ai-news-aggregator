import React from 'react';
import { Search, Tag, Filter } from 'lucide-react';

const Resources: React.FC = () => {
  const categories = [
    { name: "Herramientas de IA", count: 45 },
    { name: "Cursos Online", count: 32 },
    { name: "Datasets", count: 28 },
    { name: "Papers Académicos", count: 156 },
    { name: "Frameworks", count: 23 },
    { name: "APIs", count: 19 }
  ];

  const resources = [
    {
      title: "ChatGPT API",
      category: "APIs",
      description: "API oficial de OpenAI para integrar ChatGPT en tus aplicaciones",
      type: "API",
      difficulty: "Intermedio"
    },
    {
      title: "TensorFlow",
      category: "Frameworks",
      description: "Biblioteca de código abierto para machine learning",
      type: "Framework",
      difficulty: "Avanzado"
    },
    {
      title: "Coursera AI Course",
      category: "Cursos Online",
      description: "Curso completo de Inteligencia Artificial por Stanford",
      type: "Curso",
      difficulty: "Principiante"
    },
    {
      title: "ImageNet Dataset",
      category: "Datasets",
      description: "Base de datos de imágenes etiquetadas para computer vision",
      type: "Dataset",
      difficulty: "Intermedio"
    }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Recursos de IA</h1>
        <p className="text-gray-600 mb-6">
          Encuentra herramientas, cursos, datasets y más recursos útiles para trabajar con IA.
        </p>
        
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar recursos..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
            <Filter className="w-4 h-4" />
            Filtros
          </button>
        </div>
      </div>

      <div className="grid lg:grid-cols-4 gap-8">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold mb-4">Categorías</h2>
            <div className="space-y-2">
              {categories.map((category, index) => (
                <button
                  key={index}
                  className="w-full flex items-center justify-between p-2 text-left hover:bg-gray-50 rounded"
                >
                  <span className="text-sm">{category.name}</span>
                  <span className="text-xs bg-gray-200 px-2 py-1 rounded">{category.count}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="grid md:grid-cols-2 gap-6">
            {resources.map((resource, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-center gap-2 mb-2">
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                    {resource.category}
                  </span>
                  <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                    {resource.type}
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{resource.title}</h3>
                <p className="text-gray-600 text-sm mb-4">{resource.description}</p>
                <div className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-1 rounded ${
                    resource.difficulty === 'Principiante' ? 'bg-green-100 text-green-800' :
                    resource.difficulty === 'Intermedio' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {resource.difficulty}
                  </span>
                  <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Ver más
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Resources;