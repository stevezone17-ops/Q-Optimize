import React from 'react';

interface DepthProgression {
  step: number;
  depth: number;
  energy: number;
}

interface AdaptiveQAOAAnalyticsChartProps {
  depthProgression?: DepthProgression[];
  finalP?: number;
  totalAdaptations?: number;
  title?: string;
}

export const AdaptiveQAOAAnalyticsChart: React.FC<AdaptiveQAOAAnalyticsChartProps> = ({
  depthProgression = [
    { step: 1, depth: 1, energy: 6.2 },
    { step: 2, depth: 2, energy: 7.8 },
    { step: 3, depth: 3, energy: 8.9 },
  ],
  finalP = 3,
  totalAdaptations = 2,
  title = 'Adaptive QAOA Dynamic Layer Evolution',
}) => {
  return (
    <div
      className="p-5 bg-white dark:bg-gray-800 rounded-xl border border-pink-200 dark:border-pink-900/50 shadow-sm"
      data-testid="adaptive-qaoa-analytics-chart"
    >
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h3>
          <p className="text-xs text-gray-500">
            Iterative depth scaling with warm-start parameter transfer
          </p>
        </div>
        <div className="flex gap-2">
          <span className="text-xs px-2 py-0.5 rounded bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300 font-mono font-medium">
            Final p = {finalP}
          </span>
          <span className="text-xs px-2 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 font-mono">
            {totalAdaptations} Adaptations
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {depthProgression.map((item) => (
          <div key={item.step} className="flex items-center gap-3">
            <span className="w-16 text-xs font-mono text-gray-500">Step {item.step}</span>
            <div className="flex-1 bg-gray-100 dark:bg-gray-700 h-6 rounded-md overflow-hidden flex items-center px-3 relative">
              <div
                className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-pink-500 to-rose-400 rounded-md transition-all duration-300"
                style={{ width: `${Math.min(100, item.depth * 25)}%` }}
              />
              <span className="relative z-10 text-[11px] font-medium text-white drop-shadow-sm font-mono">
                p = {item.depth}
              </span>
            </div>
            <span className="w-20 text-right text-xs font-mono text-gray-700 dark:text-gray-300 font-semibold">
              E = {item.energy.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
