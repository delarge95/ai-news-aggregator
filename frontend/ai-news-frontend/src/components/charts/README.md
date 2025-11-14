# Sistema de Gráficos - AI News Aggregator

Sistema completo de gráficos interactivos y responsivos construido con Recharts para el agregador de noticias AI.

## 🚀 Características Principales

### ✅ Funcionalidades Implementadas

- **📊 ChartsRegistry**: Registro centralizado para componentes reutilizables
- **📈 SentimentTrendsChart**: Gráfico de líneas para tendencias de sentimiento
- **🥧 TopicDistributionChart**: Gráfico de pie/barras para distribución de temas
- **📊 SourcePerformanceChart**: Gráfico comparativo de rendimiento de fuentes
- **⚡ RealtimeMetricsChart**: Gráfico con actualizaciones en tiempo real
- **💬 CustomTooltip**: Tooltip personalizado con información rica
- **🏷️ CustomLegend**: Leyenda interactiva con controles
- **🎨 Responsive Design**: Diseño adaptativo a todos los dispositivos
- **🌙 Theme Integration**: Integración con temas claro/oscuro
- **✨ Animations**: Animaciones y transiciones suaves
- **📤 Export Functionality**: Exportación a PNG y SVG

## 📁 Estructura del Proyecto

```
src/components/charts/
├── index.ts                    # Exportaciones principales
├── ChartsRegistry.tsx          # Registro de componentes
├── ChartsDemo.tsx             # Demostración completa
├── types.ts                   # Tipos TypeScript
├── theme.ts                   # Sistema de temas
├── useChartTheme.ts           # Hook para gestión de temas
├── exportUtils.ts             # Utilidades de exportación
├── CustomTooltip.tsx          # Tooltip personalizado
├── CustomLegend.tsx           # Leyenda personalizada
├── SentimentTrendsChart.tsx   # Gráfico de tendencias
├── TopicDistributionChart.tsx # Gráfico de distribución
├── SourcePerformanceChart.tsx # Gráfico de rendimiento
└── RealtimeMetricsChart.tsx   # Gráfico en tiempo real
```

## 🛠️ Instalación y Configuración

### Dependencias Requeridas

```bash
# Recharts (ya instalado)
pnpm add recharts

# Dependencias de UI (ya disponibles)
pnpm add @radix-ui/react-tooltip
pnpm add lucide-react
pnpm add class-variance-authority
pnpm add clsx
pnpm add tailwind-merge
```

### Uso Básico

```tsx
import { 
  ChartsRegistryProvider, 
  SentimentTrendsChart,
  TopicDistributionChart 
} from '@/components/charts';

function App() {
  return (
    <ChartsRegistryProvider>
      <div className="p-6">
        <SentimentTrendsChart
          data={sentimentData}
          height={400}
          showBrush={true}
          showTrendLine={true}
          onDataPointClick={(data, index) => console.log('Clicked:', data)}
        />
        
        <TopicDistributionChart
          data={topicData}
          chartType="both"
          height={500}
          onTopicClick={(topic) => console.log('Topic:', topic)}
        />
      </div>
    </ChartsRegistryProvider>
  );
}
```

## 📊 Componentes de Gráficos

### 1. SentimentTrendsChart

Gráfico de líneas para visualizar tendencias de sentimiento a lo largo del tiempo.

```tsx
<SentimentTrendsChart
  data={[
    { 
      date: '2024-01-01', 
      positive: 65, 
      negative: 20, 
      neutral: 15, 
      average: 72,
      trend: 'up'
    }
  ]}
  height={400}
  showBrush={true}
  showTrendLine={true}
  showAverageLine={true}
  showVolume={true}
  onDataPointClick={handleDataClick}
  showExport={true}
/>
```

**Props principales:**
- `data`: Array de datos de sentimiento
- `height`: Altura del gráfico (default: 400)
- `showBrush`: Mostrar brush para navegación temporal
- `showTrendLine`: Mostrar líneas de tendencia
- `onDataPointClick`: Callback al hacer clic en puntos de datos

### 2. TopicDistributionChart

Gráfico de pie/barras para mostrar la distribución de temas.

```tsx
<TopicDistributionChart
  data={[
    { name: 'Tecnología', value: 350, percentage: 35, trend: 5.2 }
  ]}
  chartType="both" // 'pie', 'bar', 'both'
  height={500}
  showPercentage={true}
  showTrend={true}
  showLabels={true}
  onTopicClick={handleTopicClick}
  showExport={true}
/>
```

**Props principales:**
- `data`: Array de datos de temas
- `chartType`: Tipo de gráfico ('pie', 'bar', 'both')
- `showPercentage`: Mostrar porcentajes
- `showTrend`: Mostrar indicadores de tendencia
- `onTopicClick`: Callback al hacer clic en temas

### 3. SourcePerformanceChart

Gráfico comparativo para analizar el rendimiento de fuentes de noticias.

```tsx
<SourcePerformanceChart
  data={[
    { 
      name: 'CNN Español', 
      articles: 450, 
      engagement: 8500, 
      quality: 85,
      responseTime: 1.2,
      trend: 8.5,
      verified: true
    }
  ]}
  height={600}
  showBrush={true}
  showTrend={true}
  showQualityMetrics={true}
  sortBy="engagement"
  onSourceClick={handleSourceClick}
  showExport={true}
/>
```

**Props principales:**
- `data`: Array de datos de fuentes
- `sortBy`: Campo para ordenar ('engagement', 'articles', 'quality', 'reach')
- `showQualityMetrics`: Mostrar métricas de calidad
- `showComparison`: Mostrar comparaciones

### 4. RealtimeMetricsChart

Gráfico con actualizaciones en tiempo real para métricas del sistema.

```tsx
<RealtimeMetricsChart
  height={400}
  maxDataPoints={100}
  updateInterval={5000} // 5 segundos
  autoStart={true}
  showAlerts={true}
  showTrends={true}
  metrics={['engagement', 'error_rate', 'response_time']}
  onDataUpdate={handleDataUpdate}
  onAlert={handleAlert}
/>
```

**Props principales:**
- `maxDataPoints`: Máximo número de puntos de datos
- `updateInterval`: Intervalo de actualización en ms
- `showAlerts`: Mostrar alertas basadas en umbrales
- `metrics`: Lista de métricas a mostrar
- `onDataUpdate`: Callback para actualizaciones de datos

## 🎨 Sistema de Temas

El sistema soporta temas claro y oscuro automáticamente.

```tsx
import { useChartTheme } from '@/components/charts';

function MyChartComponent() {
  const { theme, updateTheme } = useChartTheme();
  
  return (
    <div style={{ color: theme.colors.foreground }}>
      {/* Tu contenido */}
    </div>
  );
}
```

**Colores disponibles:**
- `primary`, `secondary`, `accent`
- `success`, `warning`, `error`, `info`
- `background`, `foreground`, `border`

## 📤 Funcionalidad de Exportación

### Exportar gráfico individual

```tsx
import { exportChart } from '@/components/charts';

const handleExport = async () => {
  try {
    await exportChart(chartRef, {
      filename: 'chart-export',
      format: 'png', // 'png' | 'svg'
      backgroundColor: '#ffffff',
      pixelRatio: 2
    });
  } catch (error) {
    console.error('Export failed:', error);
  }
};
```

### Copiar al portapapeles

```tsx
import { copyChartToClipboard } from '@/components/charts';

const handleCopy = async () => {
  try {
    await copyChartToClipboard(chartRef);
  } catch (error) {
    console.error('Copy failed:', error);
  }
};
```

## 🔧 CustomTooltip y CustomLegend

### CustomTooltip

Tooltip personalizado con información rica y formateo flexible.

```tsx
<CustomTooltip
  formatter={(value, name, props) => [
    formatValue(value),
    name
  ]}
  trend={{
    value: 5.2,
    direction: 'up'
  }}
  showTrend={true}
/>
```

### CustomLegend

Leyenda interactiva con checkboxes y filtros.

```tsx
<CustomLegend
  showCheckboxes={true}
  showFilters={false}
  maxItems={10}
  onItemClick={(dataKey) => console.log('Clicked:', dataKey)}
  onFilterChange={(selectedItems) => console.log('Filtered:', selectedItems)}
/>
```

## 📱 Responsive Design

Todos los gráficos son completamente responsivos:

- **Mobile**: Optimizado para pantallas pequeñas
- **Tablet**: Layout adaptativo intermedio  
- **Desktop**: Aprovecha todo el espacio disponible
- **Large screens**: Diseño fluido con márgenes apropiados

## 🎭 Animaciones

Las animaciones están habilitadas por defecto con opciones configurables:

```tsx
<ChartComponent
  animation={true}
  animationDuration={1000}
  animationEasing="ease-out"
/>
```

**Easing disponibles:**
- `ease`, `ease-in`, `ease-out`, `ease-in-out`, `linear`

## 🚦 Manejo de Estados

El sistema incluye manejo completo de estados de error, carga y vacío:

```tsx
// Ejemplo de manejo de errores
const handleError = (error: Error) => {
  console.error('Chart error:', error);
  // Mostrar mensaje de error al usuario
};

// Ejemplo de estado de carga
const [loading, setLoading] = useState(true);

// Datos vacíos
if (!data || data.length === 0) {
  return <div>No hay datos disponibles</div>;
}
```

## 🔍 Búsqueda y Filtros

Los gráficos incluyen capacidades de búsqueda y filtrado:

```tsx
// Filtro por período de tiempo
const [selectedPeriod, setSelectedPeriod] = useState<'7d' | '30d' | 'all'>('all');

// Filtro por categoría
const [selectedCategory, setSelectedCategory] = useState<string>('all');

// Filtro por métricas visibles
const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(new Set());
```

## 📈 Métricas y KPIs

Sistema integrado para mostrar métricas clave:

```tsx
<div className="grid grid-cols-2 md:grid-cols-4 gap-4">
  <KpiCard title="Total Engagement" value={24567} trend={12.5} />
  <KpiCard title="Fuentes Activas" value={127} trend={8} />
  <KpiCard title="Engagement Promedio" value="78.4%" trend={3.2} />
  <KpiCard title="Tiempo de Respuesta" value="1.2s" trend={-0.3} />
</div>
```

## 🧪 Demostración

Para ver todos los gráficos en acción:

```tsx
import { ChartsDemoPage } from '@/components/charts';

function App() {
  return <ChartsDemoPage />;
}
```

## 🔮 Próximas Funcionalidades

- [ ] **PDF Export**: Exportación directa a PDF
- [ ] **3D Charts**: Gráficos tridimensionales con WebGL
- [ ] **ML Predictions**: Análisis predictivo con machine learning
- [ ] **Custom Dashboards**: Dashboards personalizables drag & drop
- [ ] **Smart Alerts**: Sistema de alertas inteligentes
- [ ] **Real-time Collaboration**: Colaboración en tiempo real
- [ ] **Data Streaming**: Streaming de datos en tiempo real
- [ ] **Custom Themes**: Editor de temas personalizados

## 🐛 Resolución de Problemas

### Problemas Comunes

**1. Error de importación:**
```tsx
// ❌ Incorrecto
import { Chart } from '@/components/charts';

// ✅ Correcto  
import { SentimentTrendsChart } from '@/components/charts';
```

**2. Datos no se muestran:**
```tsx
// Verificar estructura de datos
console.log('Data structure:', data);
// Asegurar que los datos tienen la forma correcta
```

**3. Exportación falla:**
```tsx
// Verificar que el ref es válido
if (chartRef.current) {
  await exportChart(chartRef);
}
```

**4. Tema no cambia:**
```tsx
// Verificar que useChartTheme se está usando correctamente
const { theme } = useChartTheme();
// Asegurar que theme.colors.foreground existe
```

## 📚 Documentación Adicional

- [Recharts Documentation](https://recharts.org/)
- [TypeScript Best Practices](https://www.typescriptlang.org/docs/)
- [React Hooks Guide](https://reactjs.org/docs/hooks-intro.html)
- [Tailwind CSS](https://tailwindcss.com/docs)

## 🤝 Contribuir

Para contribuir al sistema de gráficos:

1. Fork del repositorio
2. Crear una rama para la funcionalidad
3. Implementar cambios con tests
4. Documentar la nueva funcionalidad
5. Enviar pull request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

---

**Desarrollado para AI News Aggregator** 🚀