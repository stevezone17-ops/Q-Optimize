import React from 'react';

export interface BoxPlotItem {
  algorithm: string;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
  ciLower?: number;
  ciUpper?: number;
}

interface StatisticalBoxPlotProps {
  data: BoxPlotItem[];
  title?: string;
}

export const StatisticalBoxPlot: React.FC<StatisticalBoxPlotProps> = ({
  data,
  title = 'Empirical Distribution & Quartiles',
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg">
        No statistical quartile data available.
      </div>
    );
  }

  const allVals = data.flatMap((d) => [d.min, d.max, d.ciLower, d.ciUpper].filter((v): v is number => v !== undefined));
  const minVal = Math.min(...allVals, 0);
  const maxVal = Math.max(...allVals, 1);
  const valRange = maxVal - minVal || 1;

  const chartHeight = 200;
  const colWidth = 70;
  const chartWidth = Math.max(320, data.length * colWidth + 60);

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="statistical-box-plot">
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm mb-4">{title}</h3>

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
            const cx = 50 + idx * colWidth + 25;
            const toY = (val: number) => chartHeight - ((val - minVal) / valRange) * (chartHeight - 30);

            const yMin = toY(item.min);
            const yMax = toY(item.max);
            const yQ1 = toY(item.q1);
            const yQ3 = toY(item.q3);
            const yMed = toY(item.median);

            return (
              <g key={item.algorithm}>
                {/* Whisker line min to max */}
                <line
                  x1={cx}
                  y1={yMin}
                  x2={cx}
                  y2={yMax}
                  stroke="#64748b"
                  strokeWidth={1.5}
                />
                {/* Whisker caps */}
                <line x1={cx - 8} y1={yMin} x2={cx + 8} y2={yMin} stroke="#64748b" strokeWidth={1.5} />
                <line x1={cx - 8} y1={yMax} x2={cx + 8} y2={yMax} stroke="#64748b" strokeWidth={1.5} />

                {/* Box (Q1 to Q3) */}
                <rect
                  x={cx - 16}
                  y={Math.min(yQ1, yQ3)}
                  width={32}
                  height={Math.max(4, Math.abs(yQ1 - yQ3))}
                  fill="#c7d2fe"
                  stroke="#4f46e5"
                  strokeWidth={1.5}
                  rx={2}
                />

                {/* Median line */}
                <line
                  x1={cx - 16}
                  y1={yMed}
                  x2={cx + 16}
                  y2={yMed}
                  stroke="#312e81"
                  strokeWidth={2}
                />

                {/* CI error bar if present */}
                {item.ciLower !== undefined && item.ciUpper !== undefined && (
                  <line
                    x1={cx + 20}
                    y1={toY(item.ciLower)}
                    x2={cx + 20}
                    y2={toY(item.ciUpper)}
                    stroke="#10b981"
                    strokeWidth={2}
                  />
                )}

                {/* Algorithm label */}
                <text
                  x={cx}
                  y={chartHeight + 20}
                  textAnchor="middle"
                  className="text-[11px] fill-gray-500 capitalize"
                >
                  {item.algorithm.replace(/_/g, ' ').slice(0, 7)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <div className="flex justify-center gap-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-indigo-200 border border-indigo-600 inline-block" />
          <span>IQR (Q1 - Q3)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 bg-indigo-900 inline-block" />
          <span>Median</span>
        </div>
      </div>
    </div>
  );
};
