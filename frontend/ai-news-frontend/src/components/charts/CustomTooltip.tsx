import React from 'react';
import {
  Tooltip,
  TooltipProps,
  TooltipContent,
  TooltipProvider,
} from '@/components/ui/tooltip';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface CustomTooltipProps extends Omit<TooltipProps, 'children'> {
  dataKey?: string;
  valueFormatter?: (value: any) => string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'neutral';
  };
  showTrend?: boolean;
  formatter?: (value: any, name: string, props: any) => [string, string];
}

export const CustomTooltip: React.FC<CustomTooltipProps> = ({
  dataKey,
  valueFormatter = (value) => String(value),
  trend,
  showTrend = false,
  formatter,
  active,
  payload,
  label,
  labelFormatter,
  itemStyle,
  contentStyle,
  ...props
}) => {
  const formatValue = (value: any, name: string) => {
    if (formatter) {
      return formatter(value, name, payload);
    }
    return [valueFormatter(value), name];
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return <TrendingUp className="w-3 h-3 text-green-500" />;
      case 'down':
        return <TrendingDown className="w-3 h-3 text-red-500" />;
      default:
        return <Minus className="w-3 h-3 text-gray-400" />;
    }
  };

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'down':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const formattedLabel = labelFormatter ? labelFormatter(label, payload) : label;

  return (
    <TooltipProvider>
      <Tooltip open={active} {...props}>
        <TooltipContent asChild>
          <Card className="p-3 shadow-lg border-0 bg-white/95 backdrop-blur-sm max-w-xs">
            {/* Header */}
            {formattedLabel && (
              <div className="mb-2 pb-2 border-b border-gray-200">
                <p className="text-sm font-semibold text-gray-900">{formattedLabel}</p>
              </div>
            )}

            {/* Trend indicator */}
            {showTrend && trend && (
              <div className={`mb-2 p-2 rounded-md border flex items-center gap-2 ${getTrendColor(trend.direction)}`}>
                {getTrendIcon(trend.direction)}
                <span className="text-xs font-medium">
                  {trend.direction === 'up' ? '+' : ''}{trend.value}%
                </span>
              </div>
            )}

            {/* Data rows */}
            <div className="space-y-1.5">
              {payload.map((entry, index) => {
                const [formattedValue, formattedName] = formatValue(entry.value, entry.dataKey || entry.name);
                
                return (
                  <div key={index} className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: entry.color }}
                      />
                      <span className="text-xs font-medium text-gray-600">
                        {formattedName}
                      </span>
                    </div>
                    <span className="text-sm font-semibold text-gray-900">
                      {formattedValue}
                    </span>
                  </div>
                );
              })}
            </div>

            {/* Footer con información adicional */}
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                {new Date().toLocaleTimeString('es-ES', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>
          </Card>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default CustomTooltip;