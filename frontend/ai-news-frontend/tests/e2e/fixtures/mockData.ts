// Mock data para tests E2E
export const mockNewsData = [
  {
    id: '1',
    title: 'Avances en Inteligencia Artificial 2024',
    summary: 'Nuevas innovaciones en IA que están transformando la industria tecnológica.',
    content: 'La inteligencia artificial continúa evolucionando a pasos agigantados...',
    author: 'Dr. María García',
    publishedAt: '2024-01-15T10:30:00Z',
    category: 'Tecnología',
    tags: ['IA', 'Machine Learning', 'Tecnología'],
    imageUrl: '/images/news-ai-advances.jpg',
    source: 'TechNews',
    url: 'https://example.com/news/1'
  },
  {
    id: '2',
    title: 'Nuevos Algoritmos de Búsqueda',
    summary: 'Optimización de motores de búsqueda con IA avanzada.',
    content: 'Los nuevos algoritmos están mejorando significativamente la precisión...',
    author: 'Ing. Carlos López',
    publishedAt: '2024-01-14T14:20:00Z',
    category: 'Algoritmos',
    tags: ['Búsqueda', 'Optimización', 'Algoritmos'],
    imageUrl: '/images/search-algorithms.jpg',
    source: 'AI Journal',
    url: 'https://example.com/news/2'
  },
  {
    id: '3',
    title: 'Machine Learning en Medicina',
    summary: 'Aplicaciones del ML para diagnóstico médico temprano.',
    content: 'La medicina está experimentando una revolución gracias al machine learning...',
    author: 'Dra. Ana Martín',
    publishedAt: '2024-01-13T09:15:00Z',
    category: 'Medicina',
    tags: ['Machine Learning', 'Medicina', 'Diagnóstico'],
    imageUrl: '/images/ml-medicine.jpg',
    source: 'Medical AI',
    url: 'https://example.com/news/3'
  }
];

export const mockUserData = {
  id: 'test-user-123',
  name: 'Usuario de Prueba',
  email: 'test@example.com',
  avatar: '/images/avatar-test.jpg',
  preferences: {
    language: 'es',
    theme: 'light',
    notifications: true,
    categories: ['Tecnología', 'Ciencia', 'Medicina']
  },
  savedArticles: ['1', '3'],
  recentSearches: ['inteligencia artificial', 'machine learning', 'algoritmos']
};

export const mockSearchResults = {
  query: 'inteligencia artificial',
  totalResults: 1250,
  results: [
    {
      id: '1',
      title: 'Inteligencia Artificial en 2024',
      snippet: 'La IA continúa transformando industrias...',
      url: '/news/1',
      score: 0.95,
      category: 'Tecnología'
    },
    {
      id: '2',
      title: 'Machine Learning Avanzado',
      snippet: 'Nuevos modelos de ML muestran resultados prometedores...',
      url: '/news/2',
      score: 0.87,
      category: 'Algoritmos'
    }
  ],
  facets: {
    categories: [
      { name: 'Tecnología', count: 450 },
      { name: 'Ciencia', count: 320 },
      { name: 'Medicina', count: 280 },
      { name: 'Educación', count: 200 }
    ],
    dateRanges: [
      { name: 'Último mes', count: 380 },
      { name: 'Última semana', count: 120 },
      { name: 'Hoy', count: 25 }
    ]
  }
};

export const mockDashboardMetrics = {
  totalArticles: 15847,
  articlesToday: 156,
  activeUsers: 2340,
  searchQueries: 8920,
  avgResponseTime: 245,
  uptime: 99.8,
  categories: [
    { name: 'Tecnología', value: 4200, change: 5.2 },
    { name: 'Ciencia', value: 3800, change: -2.1 },
    { name: 'Medicina', value: 2900, change: 8.7 },
    { name: 'Educación', value: 2100, change: 1.3 }
  ],
  trends: [
    { date: '2024-01-01', articles: 120 },
    { date: '2024-01-02', articles: 135 },
    { date: '2024-01-03', articles: 142 },
    { date: '2024-01-04', articles: 156 },
    { date: '2024-01-05', articles: 149 }
  ]
};

export const mockTrendsData = [
  {
    id: '1',
    keyword: 'Inteligencia Artificial',
    searchVolume: 45000,
    trend: 'up',
    change: 12.5,
    category: 'Tecnología'
  },
  {
    id: '2',
    keyword: 'Machine Learning',
    searchVolume: 38000,
    trend: 'up',
    change: 8.3,
    category: 'Algoritmos'
  },
  {
    id: '3',
    keyword: 'Blockchain',
    searchVolume: 28000,
    trend: 'down',
    change: -3.2,
    category: 'Criptografía'
  },
  {
    id: '4',
    keyword: 'Quantum Computing',
    searchVolume: 15000,
    trend: 'up',
    change: 25.7,
    category: 'Tecnología'
  }
];