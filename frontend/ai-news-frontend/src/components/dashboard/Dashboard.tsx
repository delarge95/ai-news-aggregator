import React from 'react';

export const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50/50">
      <div className="flex">
        <div className="flex-1 p-6">
          <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-2">Estadísticas</h3>
              <p className="text-gray-600">Información del dashboard</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;