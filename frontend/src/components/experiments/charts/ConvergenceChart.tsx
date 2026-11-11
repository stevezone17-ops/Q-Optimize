import React from 'react';

interface ConvergenceChartProps {
  series: Record<string, number[]>;
  title?: string;
}

const ALGO_COLORS: Record<string, string> = {
  exact: '#10b981',
  simulated_annealing: '#3b82f6',
  genetic_algorithm: '#f59e0b',
  qaoa: '#8b5cf6',
  adaptive_qaoa: '#ec4899',
};

export const ConvergenceChart: React.FC<ConvergenceChartProps> = ({
  series,
  title = 'Convergence History (Objective vs Iterations)',
}) => {
  const algos = Object.keys(series);
  if (algos.length === 0 || Object.values(series).every((arr) => arr.length === 0)) {
    return (
      <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg">
        No convergence data recorded.
      </div>
    );
  }

  const allVals = Object.values(series).flat();
  const maxVal = Math.max(...allVals, 1);
  const minVal = Math.min(...allVals, 0);
  const valRange = maxVal - minVal || 1;

  const maxPoints = Math.max(...Object.values(series).map((s) => s.length), 2);

  const width = 500;
  const height = 220;
  const padding = { top: 20, right: 30, bottom: 40, left: 45 };

  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="convergence-chart">
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm mb-4">{title}</h3>

      <div className="overflow-x-auto">
        <svg width={width} height={height} className="mx-auto select-none">
          {/* Axes */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="#94a3b8"
            strokeWidth={1}
          />
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={height - padding.bottom}
            stroke="#94a3b8"
            strokeWidth={1}
          />

          {/* Y ticks & labels */}
          {[0, 0.5, 1.0].map((ratio) => {
            const val = minVal + ratio * valRange;
            const y = height - padding.bottom - ratio * plotH;
            return (
              <g key={ratio}>
                <line
                  x1={padding.left - 4}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="2 2"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3}
                  textAnchor="end"
                  className="text-[9px] fill-gray-400 font-mono"
                >
                  {val.toFixed(1)}
                </text>
              </g>
            );
          })}

          {/* Lines for each algorithm */}
          {algos.map((algo) => {
            const points = series[algo];
            if (!points || points.length === 0) return null;
            const color = ALGO_COLORS[algo] || '#64748b';

            const coords = points.map((v, i) => {
              const x = padding.left + (i / (maxPoints - 1 || 1)) * plotW;
              const y = height - padding.bottom - ((v - minVal) / valRange) * plotH;
              return `${x.toFixed(1)},${y.toFixed(1)}`;
            });

            return (
              <g key={algo}>
                <polyline
                  fill="none"
                  stroke={color}
                  strokeWidth={2}
                  points={coords.join(' ')}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </g>
            );
          })}

          {/* X axis label */}
          <text
            x={padding.left + plotW / 2}
            y={height - 10}
            textAnchor="middle"
            className="text-[10px] fill-gray-500 font-medium"
          >
            Evaluations / Iterations
          </text>
        </svg>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap justify-center gap-3 mt-3 text-xs">
        {algos.map((algo) => (
          <div key={algo} className="flex items-center gap-1.5">
            <span
              className="w-3 h-0.5 inline-block"
              style={{ backgroundColor: ALGO_COLORS[algo] || '#64748b' }}
            />
            <span className="capitalize text-gray-600 dark:text-gray-300">
              {algo.replace(/_/g, ' ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
