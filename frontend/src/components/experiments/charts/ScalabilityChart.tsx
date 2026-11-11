import React from 'react';

export interface ScalabilityPoint {
  problem_size: number;
  algorithm: string;
  mean_runtime_seconds: number;
}

interface ScalabilityChartProps {
  data: ScalabilityPoint[];
  title?: string;
}

export const ScalabilityChart: React.FC<ScalabilityChartProps> = ({
  data,
  title = 'Empirical Scalability (Problem Size vs Runtime)',
}) => {
  if (!data || data.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg">
        No scalability data points available.
      </div>
    );
  }

  const byAlgo: Record<string, ScalabilityPoint[]> = {};
  data.forEach((pt) => {
    if (!byAlgo[pt.algorithm]) byAlgo[pt.algorithm] = [];
    byAlgo[pt.algorithm].push(pt);
  });

  const allSizes = data.map((d) => d.problem_size);
  const minSize = Math.min(...allSizes);
  const maxSize = Math.max(...allSizes, minSize + 1);
  const maxRt = Math.max(...data.map((d) => d.mean_runtime_seconds), 0.001);

  const width = 480;
  const height = 220;
  const padding = { top: 20, right: 30, bottom: 40, left: 50 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;

  const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899'];

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="scalability-chart">
      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm mb-4">{title}</h3>

      <div className="overflow-x-auto">
        <svg width={width} height={height} className="mx-auto select-none">
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

          {Object.entries(byAlgo).map(([algo, pts], idx) => {
            const sorted = [...pts].sort((a, b) => a.problem_size - b.problem_size);
            const color = colors[idx % colors.length];

            const coords = sorted.map((p) => {
              const x = padding.left + ((p.problem_size - minSize) / (maxSize - minSize || 1)) * plotW;
              const y = height - padding.bottom - (p.mean_runtime_seconds / maxRt) * plotH;
              return { x, y, size: p.problem_size, rt: p.mean_runtime_seconds };
            });

            return (
              <g key={algo}>
                <polyline
                  fill="none"
                  stroke={color}
                  strokeWidth={2}
                  points={coords.map((c) => `${c.x.toFixed(1)},${c.y.toFixed(1)}`).join(' ')}
                />
                {coords.map((c, cIdx) => (
                  <circle
                    key={cIdx}
                    cx={c.x}
                    cy={c.y}
                    r={3.5}
                    fill={color}
                  />
                ))}
              </g>
            );
          })}

          <text
            x={padding.left + plotW / 2}
            y={height - 10}
            textAnchor="middle"
            className="text-[10px] fill-gray-500 font-medium"
          >
            Problem Size (Nodes / Variables)
          </text>
        </svg>
      </div>

      <div className="flex flex-wrap justify-center gap-3 mt-3 text-xs">
        {Object.keys(byAlgo).map((algo, idx) => (
          <div key={algo} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-full inline-block"
              style={{ backgroundColor: colors[idx % colors.length] }}
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
