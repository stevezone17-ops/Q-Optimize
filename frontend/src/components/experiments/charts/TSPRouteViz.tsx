import React from 'react';

interface TSPRouteVizProps {
  coordinates?: number[][]; // [[x, y], ...]
  numCities?: number;
  tour?: number[]; // [0, 2, 3, 1]
  title?: string;
}

export const TSPRouteViz: React.FC<TSPRouteVizProps> = ({
  coordinates,
  numCities = 4,
  tour,
  title = 'TSP Optimal Tour Geometry',
}) => {
  const width = 280;
  const height = 280;
  const padding = 30;

  // Generate fallback coordinates in a circle if not provided
  const cityCoords = coordinates || Array.from({ length: numCities }, (_, i) => {
    const angle = (2 * Math.PI * i) / numCities;
    return [50 + 40 * Math.cos(angle), 50 + 40 * Math.sin(angle)];
  });

  const xs = cityCoords.map((c) => c[0]);
  const ys = cityCoords.map((c) => c[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs, minX + 1);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys, minY + 1);

  const scaleX = (x: number) => padding + ((x - minX) / (maxX - minX || 1)) * (width - 2 * padding);
  const scaleY = (y: number) => padding + ((y - minY) / (maxY - minY || 1)) * (height - 2 * padding);

  const scaledCities = cityCoords.map((c, i) => ({
    id: i,
    x: scaleX(c[0]),
    y: scaleY(c[1]),
  }));

  const pathD = tour && tour.length > 1
    ? tour
        .map((cityIdx, i) => {
          const pt = scaledCities[cityIdx];
          return `${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`;
        })
        .join(' ') + ` Z`
    : '';

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="tsp-route-viz">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h4>
        <span className="text-xs text-gray-500 font-mono">{cityCoords.length} Cities</span>
      </div>

      <svg width={width} height={height} className="mx-auto select-none bg-slate-50 dark:bg-slate-900/50 rounded-lg">
        {/* Tour Path */}
        {pathD && (
          <path
            d={pathD}
            fill="none"
            stroke="#6366f1"
            strokeWidth={2}
            strokeDasharray="4 2"
          />
        )}

        {/* Cities */}
        {scaledCities.map((city) => (
          <g key={city.id}>
            <circle
              cx={city.x}
              cy={city.y}
              r={12}
              fill="#4f46e5"
              stroke="#ffffff"
              strokeWidth={2}
            />
            <text
              x={city.x}
              y={city.y + 4}
              textAnchor="middle"
              className="text-[10px] font-bold fill-white"
            >
              {city.id}
            </text>
          </g>
        ))}
      </svg>

      <div className="flex justify-center gap-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-indigo-600 inline-block" />
          <span>City Vertex</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t-2 border-indigo-500 border-dashed inline-block" />
          <span>Tour Trajectory</span>
        </div>
      </div>
    </div>
  );
};
