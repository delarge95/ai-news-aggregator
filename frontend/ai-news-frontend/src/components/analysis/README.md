# Componentes de Análisis IA

## Descripción General

Este directorio contiene componentes de React para visualización y análisis de datos de inteligencia artificial en el proyecto AI News Aggregator.

## Componentes Disponibles

### 1. SentimentChart
- **Archivo**: `SentimentChart.tsx`
- **Descripción**: Visualiza análisis de sentimiento con gráficos de barras y donut
- **Características**:
  - Gráfico donut interactivo
  - Gráfico de barras con tooltips
  - Indicadores de tendencia con iconos
  - Tres vistas: Resumen, Distribución, Detalles
  - Color coding: Verde (positivo), Rojo (negativo), Gris (neutral)

### 2. TopicAnalysis
- **Archivo**: `TopicAnalysis.tsx`
- **Descripción**: Análisis de temas con nube de palabras y categorización
- **Características**:
  - Nube de palabras interactiva
  - Gráfico scatter para análisis comparativo
  - Lista detallada con filtros
  - Búsqueda en tiempo real
  - Filtros por categoría

### 3. RelevanceScore
- **Archivo**: `RelevanceScore.tsx`
- **Descripción**: Indicadores visuales de score de relevancia
- **Características**:
  - Score circular animado
  - Métricas por categoría (Credibilidad, Engagement, Calidad, Tendencias)
  - Comparación con benchmarks
  - Recomendaciones automáticas

### 4. AIInsights
- **Archivo**: `AIInsights.tsx`
- **Descripción**: Panel con insights y análisis de IA
- **Características**:
  - Insights categorizados por tipo
  - Sistema de confianza visual
  - Filtros por tipo e impacto
  - Modal expandido para detalles

### 5. ComparisonChart
- **Archivo**: `ComparisonChart.tsx`
- **Descripción**: Comparación de tendencias temporales
- **Características**:
  - Múltiples tipos de gráfico
  - Comparación de períodos
  - Análisis de cambios con indicadores

### 6. AnalyticsDashboard
- **Archivo**: `AnalyticsDashboard.tsx`
- **Descripción**: Dashboard principal que integra todos los componentes
- **Características**:
  - Navegación por pestañas
  - Resumen general y vistas específicas
  - Filtros de tiempo y granularidad

## Uso Básico

```tsx
import { AnalyticsDashboard } from './components/analysis';

function App() {
  return (
    <div className="App">
      <AnalyticsDashboard />
    </div>
  );
}
```

## Integración con Backend

Los componentes se integran con los siguientes endpoints:
- `GET /api/v1/analytics/comprehensive` - Datos generales de análisis
- `GET /api/v1/analytics/sentiment` - Análisis de sentimiento
- `GET /api/v1/analytics/trends` - Análisis de tendencias

## Características de Diseño

### Color Coding
- **Verde** (#10B981): Elementos positivos, éxito, crecimiento
- **Rojo** (#EF4444): Elementos negativos, alertas, declives
- **Gris** (#6B7280): Elementos neutrales, estados inactivos
- **Azul** (#3B82F6): Elementos primarios, información

### Interactividad
- Tooltips personalizados en todos los gráficos
- Filtros en tiempo real
- Búsqueda instantánea
- Navegación por pestañas
- Modales expandidos
- Indicadores de carga animados

## Estructura de Archivos

```
analysis/
├── types.ts                 # Definiciones TypeScript
├── useAnalytics.ts          # Hook principal
├── utils.ts                 # Utilidades
├── SentimentChart.tsx       # Componente de sentimiento
├── TopicAnalysis.tsx        # Componente de temas
├── RelevanceScore.tsx       # Componente de relevancia
├── AIInsights.tsx           # Componente de insights
├── ComparisonChart.tsx      # Componente de comparación
├── AnalyticsDashboard.tsx   # Dashboard principal
├── AnalyticsProvider.tsx    # Provider de contexto
├── index.ts                 # Exportaciones
└── README.md               # Este archivo
```

## Dependencias

- React 18+
- TypeScript
- Recharts (gráficos)
- Radix UI (componentes base)
- TailwindCSS (estilos)
- Lucide React (iconos)
