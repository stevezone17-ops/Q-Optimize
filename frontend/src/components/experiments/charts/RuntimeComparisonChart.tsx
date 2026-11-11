import React from 'react';

export interface RuntimeDataPoint {
  algorithm: string;
  mean_runtime: number;
  min_runtime?: number;
  max_runtime?: number;
  trials?: number;
}

interface RuntimeComparisonChartProps {
  data: RuntimeDataPoint[];
  title?: string;
}

export const RuntimeComparisonChart: React.FC<RuntimeComparisonChartProps> = ({
  data,
  title = 'Runtime & Execution Efficiency (s)',
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg">
        No runtime data available.
      </div>
    );
  }

  const maxVal = Math.max(...data.map((d) => d.max_runtime || d.mean_runtime), 0.001);
  const chartHeight = 200;
  const barWidth = 32;
  const groupSpacing = 85;
  const chartWidth = Math.max(340, data.length * groupSpacing + 60);

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="runtime-comparison-chart">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h3>
      </div>

      <div className="overflow-x-auto">
        <svg width={chartWidth} height={chartHeight + 40} className="mx-auto select-none">
          <line
            x1={40}
            y1={chartHeight}
            x2={chartWidth - 20}
            y2={chartHeight}
            stroke="#94a3b8"
            strokeWidth={1}
          />

          {data.map((item, idx) => {
            const x = 50 + idx * groupSpacing;
            const h = Math.max(4, (item.mean_runtime / maxVal) * (chartHeight - 30));

            return (
              <g key={item.algorithm} className="transition-all duration-200">
                <rect
                  x={x}
                  y={chartHeight - h}
                  width={barWidth}
                  height={h}
                  fill="#8b5cf6"
                  rx={3}
                />
                {/* Text for seconds */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight - h - 6}
                  textAnchor="middle"
                  className="text-[10px] fill-gray-600 dark:fill-gray-300 font-mono"
                >
                  {item.mean_runtime < 0.01 ? `${(item.mean_runtime * 1000).toFixed(1)}ms` : `${item.mean_runtime.toFixed(2)}s`}
                </text>
                {/* Algorithm label */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight + 20}
                  textAnchor="middle"
                  className="text-[11px] fill-gray-500 dark:fill-gray-400 capitalize"
                >
                  {item.algorithm.replace(/_/g, ' ').slice(0, 9)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="flex justify-center gap-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-purple-500 inline-block" />
          <span>Mean Execution Time</span>
        </div>
      </div>
    </div>
  );
};
