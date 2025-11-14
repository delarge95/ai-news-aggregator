# Dashboard Principal - AI News Aggregator

## Descripción

Dashboard principal con métricas y KPIs para el agregador de noticias AI. Incluye visualización de datos en tiempo real, gráficos interactivos y un layout responsive profesional.

## Características

- ✅ **KPIs Principales**: Total artículos, fuentes activas, sentimiento promedio
- ✅ **Cards de Métricas**: Con iconos y tendencias visuales
- ✅ **Layout Responsive**: Grid adaptativo con Tailwind CSS
- ✅ **Integración API**: Endpoints `/analytics/dashboard` y `/analytics/stats`
- ✅ **Actualización en Tiempo Real**: Polling automático cada 30 segundos
- ✅ **Tema Profesional**: Diseño moderno con Tailwind y Radix UI
- ✅ **Gráficos Interactivos**: Recharts para visualizaciones de datos
- ✅ **Navegación**: Sidebar con secciones organizadas
- ✅ **Estado de Conexión**: Indicador visual de conectividad

## Componentes

### Dashboard.tsx
Componente principal que integra todos los elementos del dashboard.
```tsx
import { Dashboard } from './components/dashboard';

function App() {
  return <Dashboard />;
}
```

### MetricCard.tsx
Card individual para mostrar métricas con iconos y tendencias.
```tsx
import { MetricCard } from './components/dashboard';

<MetricCard
  title="Total de Artículos"
  value={12345}
  change={15.3}
  changeType="increase"
  icon={<Newspaper className="h-4 w-4" />}
  description="Artículos procesados en total"
/>
```

### KPIWidget.tsx
Widget para KPIs con gráficos de tendencia y progreso.
```tsx
import { KPIWidget } from './components/dashboard';

<KPIWidget
  title="Tendencia de Sentimiento"
  value={0.75}
  target={1.0}
  trend={trendData}
  color="blue"
/>
```

### LiveStats.tsx
Componente de estadísticas en tiempo real con polling automático.
```tsx
import { LiveStats } from './components/dashboard';

<LiveStats />
```

### Sidebar.tsx
Navegación lateral con secciones del dashboard.
```tsx
import { Sidebar } from './components/dashboard';

<Sidebar 
  activeSection="dashboard"
  onSectionChange={(section) => console.log(section)}
/>
```

### ConnectionStatus.tsx
Indicador del estado de conexión y última actualización.
```tsx
import { ConnectionStatus } from './components/dashboard';

<ConnectionStatus lastPing={new Date()} />
```

## API Endpoints

El dashboard integra con los siguientes endpoints:

- `GET /analytics/dashboard` - Métricas principales del dashboard
- `GET /analytics/stats` - Estadísticas en tiempo real
- `GET /analytics/total-articles` - Total de artículos
- `GET /analytics/active-sources` - Fuentes activas
- `GET /analytics/average-sentiment` - Sentimiento promedio
- `GET /analytics/sentiment-distribution` - Distribución de sentimiento

## Configuración

### Variables de Entorno
```bash
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_DASHBOARD_REFRESH_INTERVAL=30000
```

### Estructura de Datos

```typescript
interface DashboardMetrics {
  total_articles: number;
  active_sources: number;
  average_sentiment: number;
  articles_today: number;
  articles_this_week: number;
  articles_this_month: number;
  sentiment_distribution: {
    positive: number;
    neutral: number;
    negative: number;
  };
  top_sources: Array<{
    name: string;
    count: number;
    percentage: number;
  }>;
  sentiment_trend: Array<{
    date: string;
    sentiment_score: number;
    article_count: number;
  }>;
  categories_distribution: Array<{
    category: string;
    count: number;
    percentage: number;
  }>;
  hourly_activity: Array<{
    hour: number;
    count: number;
  }>;
}
```

## Instalación

1. **Dependencias**: Ya incluidas en `package.json`
   - React + TypeScript
   - Tailwind CSS
   - Radix UI
   - Recharts
   - Lucide Icons

2. **Configurar API**: Actualizar `VITE_API_BASE_URL` en `.env`

3. **Ejecutar**:
```bash
cd frontend/ai-news-frontend
pnpm install
pnpm dev
```

## Características del Layout

### Grid Responsive
- **Mobile**: Stack vertical de cards
- **Tablet**: Grid de 2 columnas
- **Desktop**: Grid de 3-4 columnas según el componente

### Sidebar
- **Desktop**: Fijo en la izquierda
- **Mobile**: Overlay deslizable
- **Navegación**: 7 secciones principales

### Actualización en Tiempo Real
- **Dashboard**: Polling cada 2 minutos
- **LiveStats**: Polling cada 30 segundos
- **Indicador visual**: Pulsación verde durante actualización

## Personalización

### Colores de Gráficos
```typescript
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
```

### Intervalos de Polling
```typescript
// Dashboard principal
const DASHBOARD_REFRESH = 120000; // 2 minutos

// Stats en vivo
const LIVE_STATS_REFRESH = 30000;  // 30 segundos
```

### Temas
El dashboard usa el sistema de temas de Tailwind con:
- `bg-background` - Fondo principal
- `text-foreground` - Texto principal
- `text-muted-foreground` - Texto secundario
- `border` - Bordes de componentes

## Estructura de Archivos

```
src/
├── components/
│   ├── dashboard/
│   │   ├── Dashboard.tsx
│   │   ├── MetricCard.tsx
│   │   ├── KPIWidget.tsx
│   │   ├── LiveStats.tsx
│   │   ├── Sidebar.tsx
│   │   ├── ConnectionStatus.tsx
│   │   └── index.ts
│   └── ui/
│       └── card.tsx
├── services/
│   └── dashboardService.ts
├── types/
│   └── dashboard.ts
└── hooks/
    └── usePolling.ts
```

## Próximas Mejoras

- [ ] Modo oscuro/claro
- [ ] Exportación de datos
- [ ] Notificaciones push
- [ ] Alertas configurables
- [ ] Filtros de fecha
- [ ] Comparación de períodos
- [ ] Dashboard personalizable
- [ ] Widgets drag & drop

## Soporte

Para issues o preguntas, revisar:
1. **Estado de la API**: Verificar endpoints
2. **Variables de entorno**: Validar configuración
3. **Consola del navegador**: Revisar errores de red
4. **Logs del backend**: Verificar respuestas de API