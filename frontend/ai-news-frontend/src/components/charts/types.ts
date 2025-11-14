import { ReactNode, RefObject } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  AreaChart, 
  BarChart, 
  PieChart, 
  ComposedChart 
} from 'recharts';

// Tipos base para gráficos
export type ChartType = 
  | 'line' 
  | 'area' 
  | 'bar' 
  | 'pie' 
  | 'scatter' 
  | 'composed'
  | 'radar'
  | 'funnel'
  | 'treemap';

// Propiedades base comunes
export interface BaseChartProps {
  id?: string;
  title?: string;
  description?: string;
  data: any[];
  width?: number | string;
  height?: number | string;
  responsive?: boolean;
  animation?: boolean;
  animationDuration?: number;
  animationEasing?: 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';
  theme?: 'light' | 'dark' | 'auto';
  className?: string;
  style?: React.CSSProperties;
  onDataClick?: (data: any, index: number) => void;
  onError?: (error: Error) => void;
}

// Props específicos para gráficos de línea/área
export interface LineChartProps extends BaseChartProps {
  type: 'line';
  xAxisKey: string;
  yAxisKey?: string;
  yAxisKeys?: string[];
  showGrid?: boolean;
  showPoints?: boolean;
  showArea?: boolean;
  strokeWidth?: number;
  dotSize?: number;
  activeDotSize?: number;
  connectNulls?: boolean;
}

// Props específicos para gráficos de barras
export interface BarChartProps extends BaseChartProps {
  type: 'bar';
  xAxisKey: string;
  yAxisKey?: string;
  yAxisKeys?: string[];
  layout?: 'horizontal' | 'vertical';
  showGrid?: boolean;
  showBackground?: boolean;
  barSize?: number;
  maxBarSize?: number;
  stackId?: string;
}

// Props específicos para gráficos de pie
export interface PieChartProps extends BaseChartProps {
  type: 'pie';
  dataKey: string;
  nameKey: string;
  cx?: string | number;
  cy?: string | number;
  innerRadius?: number | string;
  outerRadius?: number | string;
  padAngle?: number;
  cornerRadius?: number;
  startAngle?: number;
  endAngle?: number;
  showLabels?: boolean;
  labelLine?: boolean;
  labelFormatter?: (value: any, name: string) => string;
}

// Props específicos para gráficos de dispersión
export interface ScatterChartProps extends BaseChartProps {
  type: 'scatter';
  xAxisKey: string;
  yAxisKey: string;
  zAxisKey?: string;
  showGrid?: boolean;
  showLine?: boolean;
  showPoints?: boolean;
  pointSize?: number;
}

// Props específicos para gráficos compuestos
export interface ComposedChartProps extends BaseChartProps {
  type: 'composed';
  xAxisKey: string;
  yAxisKey?: string;
  yAxisKeys?: string[];
  showGrid?: boolean;
  showLine?: boolean;
  showArea?: boolean;
  showBar?: boolean;
}

// Props para gráficos de radar
export interface RadarChartProps extends BaseChartProps {
  type: 'radar';
  cx?: string | number;
  cy?: string | number;
  outerRadius?: number;
  innerRadius?: number;
  dataKey: string;
  nameKey: string;
}

// Props para gráficos de embudo
export interface FunnelChartProps extends BaseChartProps {
  type: 'funnel';
  dataKey: string;
  nameKey: string;
  isAscending?: boolean;
  cx?: string | number;
  cy?: string | number;
}

// Props para mapas de árbol
export interface TreemapChartProps extends BaseChartProps {
  type: 'treemap';
  dataKey: string;
  nameKey: string;
  aspectRatio?: number;
  isAnimationActive?: boolean;
  animationDuration?: number;
}

// Unión de todas las props de gráficos
export type ChartProps = 
  | LineChartProps 
  | BarChartProps 
  | PieChartProps 
  | ScatterChartProps 
  | ComposedChartProps
  | RadarChartProps
  | FunnelChartProps
  | TreemapChartProps
  | BaseChartProps;

// Configuración del registro de gráficos
export interface ChartConfig extends ChartProps {
  id: string;
  registeredAt: Date;
  updatedAt?: Date;
  version?: string;
  category?: string;
  tags?: string[];
  dependencies?: string[];
  documentation?: {
    description?: string;
    usage?: string;
    examples?: string[];
    props?: Record<string, string>;
  };
  permissions?: {
    view: boolean;
    edit: boolean;
    delete: boolean;
  };
  metadata?: {
    createdBy?: string;
    lastModifiedBy?: string;
    version?: string;
    source?: string;
  };
}

// Props para el contenedor responsive
export interface ResponsiveContainerProps {
  width?: number | string;
  height?: number | string;
  aspect?: number;
  minHeight?: number;
  minWidth?: number;
  debounce?: number;
  children: ReactNode;
}

// Props para tooltip personalizado
export interface TooltipProps {
  active?: boolean;
  payload?: any[];
  label?: any;
  labelFormatter?: (label: any, payload: any[]) => string;
  formatter?: (value: any, name: any, props: any) => [string, string];
  itemStyle?: React.CSSProperties;
  contentStyle?: React.CSSProperties;
  separator?: string;
  offset?: number;
  filterNull?: boolean;
  itemSorter?: (item: any) => number;
  isAnimationActive?: boolean;
  animationDuration?: number;
  animationEasing?: 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';
  position?: { x: number; y: number };
}

// Props para leyenda personalizada
export interface LegendProps {
  content?: ReactNode;
  wrapperStyle?: React.CSSProperties;
  chartWidth?: number;
  chartHeight?: number;
  iconSize?: number;
  iconType?: 'line' | 'rect' | 'circle' | 'cross' | 'diamond' | 'square' | 'star' | 'triangle' | 'wye';
  layout?: 'horizontal' | 'vertical';
  align?: 'left' | 'center' | 'right';
  verticalAlign?: 'top' | 'middle' | 'bottom';
  payload?: any[];
  formatter?: (value: any, entry: any, index: number) => string;
  inactiveColor?: string;
}

// Props para ejes
export interface AxisProps {
  dataKey?: string;
  type?: 'number' | 'category';
  allowDataOverflow?: boolean;
  allowDecimals?: boolean;
  allowDuplicatedCategory?: boolean;
  axisLine?: boolean | React.CSSProperties;
  tick?: boolean | React.CSSProperties | React.ReactElement | ((props: any) => React.ReactElement);
  tickLine?: boolean | React.CSSProperties;
  tickFormatter?: (value: any) => string;
  tickMargin?: number;
  tickMaxTicks?: number;
  tickMinTicks?: number;
  tickSize?: number;
  tickCount?: number;
  unit?: string | number;
  name?: string | number;
  domain?: [number, number] | ((dataMin: number, dataMax: number) => [number, number]);
  scale?: 'auto' | 'linear' | 'pow' | 'sqrt' | 'log' | 'identity' | 'time' | 'band' | 'point' | 'ordinal' | 'quantile' | 'quantize' | 'utc' | 'sequential' | 'threshold';
  nameGap?: number;
  orientation?: 'left' | 'right' | 'bottom' | 'top';
  yAxisId?: string | number;
  xAxisId?: string | number;
  reversed?: boolean;
  label?: string | number | React.ReactElement;
  scaleToFit?: boolean;
  interval?: number | 'preserveStart' | 'preserveEnd' | 'preserveStartEnd';
}

// Props para grid
export interface GridProps {
  stroke?: string;
  strokeDasharray?: string | number;
  strokeWidth?: number;
  fill?: string;
  fillOpacity?: number;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  horizontal?: boolean;
  vertical?: boolean;
  horizontalPoints?: number[];
  verticalPoints?: number[];
  strokeOpacity?: number;
}

// Props para brush
export interface BrushProps {
  data?: any[];
  height?: number;
  dataKey?: string;
  xAxisId?: string | number;
  yAxisId?: string | number;
  travellerWidth?: number;
  gap?: number;
  fill?: string;
  stroke?: string;
  startIndex?: number;
  endIndex?: number;
  TravellerComponent?: React.ComponentType<any>;
  onChange?: (range: { startIndex: number; endIndex: number }) => void;
}

// Tipo para eventos de gráficos
export interface ChartEventHandlers {
  onClick?: (data: any, index: number) => void;
  onMouseEnter?: (data: any, index: number) => void;
  onMouseLeave?: (data: any, index: number) => void;
  onMouseMove?: (data: any, index: number) => void;
  onMouseDown?: (data: any, index: number) => void;
  onMouseUp?: (data: any, index: number) => void;
}

// Componente de referencia para gráficos
export type ChartComponentType = 
  | typeof ResponsiveContainer
  | typeof LineChart
  | typeof AreaChart
  | typeof BarChart
  | typeof PieChart
  | typeof ComposedChart;

// Referencias para gráficos
export interface ChartRefs {
  containerRef: RefObject<any>;
  chartRef: RefObject<any>;
  svgRef?: RefObject<any>;
}