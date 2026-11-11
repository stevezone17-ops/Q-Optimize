import React from 'react';

export interface ObjectiveDataPoint {
  algorithm: string;
  best: number;
  mean: number;
  worst?: number;
  trials?: number;
}

interface ObjectiveComparisonChartProps {
  data: ObjectiveDataPoint[];
  optimalValue?: number;
  title?: string;
}

export const ObjectiveComparisonChart: React.FC<ObjectiveComparisonChartProps> = ({
  data,
  optimalValue,
  title = 'Objective Value Comparison',
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg">
        No objective data available for comparison.
      </div>
    );
  }

  const allVals = data.flatMap((d) => [d.best, d.mean, optimalValue].filter((v): v is number => v !== undefined));
  const maxVal = Math.max(...allVals, 1);
  const minVal = Math.min(0, Math.min(...allVals));
  const range = maxVal - minVal || 1;

  const chartHeight = 220;
  const barWidth = 36;
  const groupSpacing = 90;
  const chartWidth = Math.max(340, data.length * groupSpacing + 60);

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="objective-comparison-chart">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h3>
        {optimalValue !== undefined && (
          <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 font-mono">
            Optimum: {optimalValue.toFixed(2)}
          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <svg width={chartWidth} height={chartHeight + 40} className="mx-auto select-none">
          {/* Baseline grid */}
          <line
            x1={40}
            y1={chartHeight}
            x2={chartWidth - 20}
            y2={chartHeight}
            stroke="#94a3b8"
            strokeWidth={1}
          />

          {/* Optimal line */}
          {optimalValue !== undefined && (
            <g>
              <line
                x1={40}
                y1={chartHeight - ((optimalValue - minVal) / range) * (chartHeight - 30)}
                x2={chartWidth - 20}
                y2={chartHeight - ((optimalValue - minVal) / range) * (chartHeight - 30)}
                stroke="#10b981"
                strokeWidth={1.5}
                strokeDasharray="4 3"
              />
            </g>
          )}

          {data.map((item, idx) => {
            const x = 50 + idx * groupSpacing;
            const bestH = Math.max(4, ((item.best - minVal) / range) * (chartHeight - 30));
            const meanH = Math.max(4, ((item.mean - minVal) / range) * (chartHeight - 30));

            return (
              <g key={item.algorithm} className="transition-all duration-200 hover:opacity-90">
                {/* Mean bar (lighter) */}
                <rect
                  x={x}
                  y={chartHeight - meanH}
                  width={barWidth / 2 - 2}
                  height={meanH}
                  fill="#93c5fd"
                  rx={3}
                />
                {/* Best bar (darker/vibrant) */}
                <rect
                  x={x + barWidth / 2}
                  y={chartHeight - bestH}
                  width={barWidth / 2 - 2}
                  height={bestH}
                  fill="#3b82f6"
                  rx={3}
                />
                {/* Value label */}
                <text
                  x={x + barWidth / 2}
                  y={chartHeight - Math.max(bestH, meanH) - 6}
                  textAnchor="middle"
                  className="text-[10px] fill-gray-600 dark:fill-gray-300 font-mono font-medium"
                >
                  {item.best.toFixed(1)}
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
          <span className="w-3 h-3 rounded bg-blue-300 inline-block" />
          <span>Mean Objective</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-blue-500 inline-block" />
          <span>Best Objective</span>
        </div>
        {optimalValue !== undefined && (
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-0.5 border-t-2 border-emerald-500 border-dashed inline-block" />
            <span>Optimal Baseline</span>
          </div>
        )}
      </div>
    </div>
  );
};
