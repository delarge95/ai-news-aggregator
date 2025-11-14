import React from 'react';
import { User, Settings, BookOpen, Bell, Shield, CreditCard } from 'lucide-react';

const Profile: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Mi Perfil</h1>
        <p className="text-gray-600">
          Gestiona tu cuenta y preferencias de AI News Aggregator
        </p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-center mb-6">
              <div className="w-20 h-20 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <User className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-xl font-semibold">Usuario Demo</h2>
              <p className="text-gray-600">usuario@ejemplo.com</p>
            </div>
            
            <nav className="space-y-2">
              <a href="#" className="flex items-center gap-3 p-3 text-blue-600 bg-blue-50 rounded-lg">
                <User className="w-4 h-4" />
                Perfil Personal
              </a>
              <a href="#" className="flex items-center gap-3 p-3 text-gray-700 hover:bg-gray-50 rounded-lg">
                <Bell className="w-4 h-4" />
                Notificaciones
              </a>
              <a href="#" className="flex items-center gap-3 p-3 text-gray-700 hover:bg-gray-50 rounded-lg">
                <BookOpen className="w-4 h-4" />
                Preferencias
              </a>
              <a href="#" className="flex items-center gap-3 p-3 text-gray-700 hover:bg-gray-50 rounded-lg">
                <Shield className="w-4 h-4" />
                Privacidad
              </a>
              <a href="#" className="flex items-center gap-3 p-3 text-gray-700 hover:bg-gray-50 rounded-lg">
                <CreditCard className="w-4 h-4" />
                Suscripción
              </a>
              <a href="#" className="flex items-center gap-3 p-3 text-gray-700 hover:bg-gray-50 rounded-lg">
                <Settings className="w-4 h-4" />
                Configuración
              </a>
            </nav>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Información Personal</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nombre</label>
                  <input
                    type="text"
                    value="Usuario Demo"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value="usuario@ejemplo.com"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    readOnly
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">País</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option>España</option>
                    <option>México</option>
                    <option>Argentina</option>
                    <option>Colombia</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    <option>Español</option>
                    <option>English</option>
                    <option>Français</option>
                  </select>
                </div>
              </div>
              <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Guardar Cambios
              </button>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold mb-4">Actividad Reciente</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm">Última sesión: Hoy a las 14:30</span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span className="text-sm">Último artículo leído: "OpenAI lanza GPT-5"</span>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span className="text-sm">Búsquedas realizadas esta semana: 23</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;