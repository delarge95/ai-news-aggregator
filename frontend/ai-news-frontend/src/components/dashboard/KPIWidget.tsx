import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { KPIWidgetProps } from '../../types/dashboard';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { cn } from '../../lib/utils';

const colorMap = {
  blue: '#3b82f6',
  green: '#10b981',
  purple: '#8b5cf6',
  orange: '#f59e0b',
  red: '#ef4444'
};

const KPIWidget: React.FC<KPIWidgetProps> = ({
  title,
  value,
  target,
  unit = '',
  trend,
  color = 'blue'
}) => {
  const formattedValue = typeof value === 'number' ? value.toLocaleString() : value;
  const progress = target ? (value / target) * 100 : null;
  const chartColor = colorMap[color];

  return (
    <Card className="transition-all duration-200 hover:shadow-lg">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-baseline space-x-2">
            <div className="text-2xl font-bold">
              {formattedValue}
              {unit && <span className="text-sm text-muted-foreground ml-1">{unit}</span>}
            </div>
            {target && (
              <div className="text-xs text-muted-foreground">
                / {target.toLocaleString()}
              </div>
            )}
          </div>
          
          {progress && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={cn(
                  "h-2 rounded-full transition-all duration-300",
                  color === 'blue' && 'bg-blue-500',
                  color === 'green' && 'bg-green-500',
                  color === 'purple' && 'bg-purple-500',
                  color === 'orange' && 'bg-orange-500',
                  color === 'red' && 'bg-red-500'
                )}
                style={{ width: `${Math.min(progress, 100)}%` }}
              />
            </div>
          )}

          {trend && trend.length > 0 && (
            <div className="h-16">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trend}>
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={chartColor}
                    strokeWidth={2}
                    fill={chartColor}
                    fillOpacity={0.1}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default KPIWidget;