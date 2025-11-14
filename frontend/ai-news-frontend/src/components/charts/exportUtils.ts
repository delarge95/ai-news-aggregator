import { RefObject } from 'react';
import { exportToPNG, exportToSVG } from 'recharts-to-png';
import { saveAs } from 'file-saver';

// Tipos para datos de gráficos
export interface ChartData {
  name?: string;
  [key: string]: any;
}

export interface ExportOptions {
  filename?: string;
  backgroundColor?: string;
  pixelRatio?: number;
  quality?: number;
  format?: 'png' | 'svg';
}

// Fallback si recharts-to-png no está disponible
const createCanvasFromSVG = (svgElement: SVGSVGElement, options?: { pixelRatio?: number; backgroundColor?: string }) => {
  const pixelRatio = options?.pixelRatio || 2;
  const backgroundColor = options?.backgroundColor || '#ffffff';

  return new Promise<string>((resolve) => {
    const svgData = new XMLSerializer().serializeToString(svgElement);
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Canvas context not available');
    }

    const img = new Image();
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      const width = svgElement.clientWidth * pixelRatio;
      const height = svgElement.clientHeight * pixelRatio;
      
      canvas.width = width;
      canvas.height = height;
      
      // Configurar fondo blanco
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, width, height);
      
      // Dibujar la imagen SVG escalada
      ctx.drawImage(img, 0, 0, width, height);
      
      URL.revokeObjectURL(url);
      
      const dataURL = canvas.toDataURL('image/png');
      resolve(dataURL);
    };

    img.src = url;
  });
};

export const exportChart = async (
  chartRef: RefObject<any>,
  options: ExportOptions = {}
): Promise<void> => {
  const {
    filename = 'chart',
    backgroundColor = '#ffffff',
    pixelRatio = 2,
    format = 'png'
  } = options;

  if (!chartRef?.current) {
    throw new Error('Chart reference is not available');
  }

  try {
    let dataURL: string;
    let mimeType: string;
    let fileExtension: string;

    if (format === 'svg') {
      // Para SVG, serializar directamente el SVG
      const svgElement = chartRef.current.querySelector('svg');
      if (!svgElement) {
        throw new Error('SVG element not found in chart');
      }
      
      const svgData = new XMLSerializer().serializeToString(svgElement);
      dataURL = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgData);
      mimeType = 'image/svg+xml';
      fileExtension = 'svg';
    } else {
      // Para PNG, usar la librería de exportación o fallback
      const svgElement = chartRef.current.querySelector('svg');
      if (!svgElement) {
        throw new Error('SVG element not found in chart');
      }

      // Intentar usar recharts-to-png primero
      try {
        dataURL = await exportToPNG(chartRef.current, { 
          backgroundColor,
          pixelRatio 
        });
      } catch (error) {
        // Fallback al método manual
        console.warn('recharts-to-png failed, using fallback method:', error);
        dataURL = await createCanvasFromSVG(svgElement, { 
          pixelRatio, 
          backgroundColor 
        });
      }
      
      mimeType = 'image/png';
      fileExtension = 'png';
    }

    // Crear blob y descargar
    const response = await fetch(dataURL);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${filename}.${fileExtension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error exporting chart:', error);
    throw new Error(`Failed to export chart: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};

export const exportChartAsPDF = async (
  chartRef: RefObject<any>,
  options: ExportOptions = {}
): Promise<void> => {
  // Implementación básica para PDF - requeriría jsPDF
  // Por ahora, exportamos como PNG y el usuario puede incluir en PDF
  const { filename = 'chart' } = options;
  await exportChart(chartRef, { ...options, filename, format: 'png' });
};

export const getChartData = (chartRef: RefObject<any>): ChartData[] => {
  if (!chartRef?.current) {
    return [];
  }

  // Extraer datos del gráfico si están disponibles
  try {
    return chartRef.current?.props?.data || [];
  } catch (error) {
    console.warn('Could not extract chart data:', error);
    return [];
  }
};

export const copyChartToClipboard = async (
  chartRef: RefObject<any>,
  options: ExportOptions = {}
): Promise<void> => {
  if (!navigator.clipboard || !navigator.clipboard.write) {
    throw new Error('Clipboard API not available');
  }

  try {
    const dataURL = await exportChart(chartRef, { ...options, format: 'png' });
    const response = await fetch(dataURL);
    const blob = await response.blob();
    
    await navigator.clipboard.write([
      new ClipboardItem({ [blob.type]: blob })
    ]);
  } catch (error) {
    console.error('Error copying chart to clipboard:', error);
    throw new Error(`Failed to copy chart: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
};