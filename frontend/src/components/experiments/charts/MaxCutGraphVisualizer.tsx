import React from 'react';

interface MaxCutGraphVisualizerProps {
  numNodes: number;
  edgeList: number[][]; // [u, v] or [u, v, weight]
  solutionPartition?: number[]; // [0, 1, 0, 1]
  title?: string;
}

export const MaxCutGraphVisualizer: React.FC<MaxCutGraphVisualizerProps> = ({
  numNodes,
  edgeList,
  solutionPartition,
  title = 'Max-Cut Graph Partition Visualizer',
}) => {
  const width = 300;
  const height = 300;
  const cx = width / 2;
  const cy = height / 2;
  const radius = 100;

  // Calculate circular coordinates for each node
  const nodes = Array.from({ length: numNodes }, (_, i) => {
    const angle = (2 * Math.PI * i) / numNodes - Math.PI / 2;
    return {
      id: i,
      x: cx + radius * Math.cos(angle),
      y: cy + radius * Math.sin(angle),
      partition: solutionPartition ? solutionPartition[i] : 0,
    };
  });

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="max-cut-visualizer">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h4>
        <span className="text-xs text-gray-500 font-mono">|V|={numNodes}, |E|={edgeList.length}</span>
      </div>

      <svg width={width} height={height} className="mx-auto select-none">
        {/* Edges */}
        {edgeList.map(([u, v], idx) => {
          if (u >= numNodes || v >= numNodes) return null;
          const nu = nodes[u];
          const nv = nodes[v];
          const isCut = solutionPartition && solutionPartition[u] !== solutionPartition[v];

          return (
            <line
              key={idx}
              x1={nu.x}
              y1={nu.y}
              x2={nv.x}
              y2={nv.y}
              stroke={isCut ? '#ef4444' : '#cbd5e1'}
              strokeWidth={isCut ? 2.5 : 1}
              strokeDasharray={isCut ? 'none' : '3 3'}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node) => (
          <g key={node.id}>
            <circle
              cx={node.x}
              cy={node.y}
              r={16}
              fill={node.partition === 1 ? '#3b82f6' : '#10b981'}
              stroke="#ffffff"
              strokeWidth={2}
            />
            <text
              x={node.x}
              y={node.y + 4}
              textAnchor="middle"
              className="text-xs font-bold fill-white select-none pointer-events-none"
            >
              {node.id}
            </text>
          </g>
        ))}
      </svg>

      <div className="flex justify-center gap-4 mt-2 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
          <span>Partition S₀</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
          <span>Partition S₁</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 bg-red-500 inline-block" />
          <span>Cut Edge</span>
        </div>
      </div>
    </div>
  );
};
