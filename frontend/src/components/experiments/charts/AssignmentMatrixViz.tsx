import React from 'react';

interface AssignmentMatrixVizProps {
  costMatrix: number[][];
  assignments?: number[]; // agent i assigned to task assignments[i]
  title?: string;
}

export const AssignmentMatrixViz: React.FC<AssignmentMatrixVizProps> = ({
  costMatrix,
  assignments,
  title = 'Assignment Cost Matrix & Matching',
}) => {
  if (!costMatrix || costMatrix.length === 0) {
    return <div className="p-4 text-xs text-gray-500">No cost matrix provided.</div>;
  }

  const numAgents = costMatrix.length;
  const numTasks = costMatrix[0].length;

  const allVals = costMatrix.flat();
  const minVal = Math.min(...allVals);
  const maxVal = Math.max(...allVals, 1);
  const range = maxVal - minVal || 1;

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm" data-testid="assignment-matrix-viz">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">{title}</h4>
        <span className="text-xs text-gray-500 font-mono">{numAgents} Agents × {numTasks} Tasks</span>
      </div>

      <div className="overflow-x-auto">
        <table className="border-collapse mx-auto text-xs">
          <thead>
            <tr>
              <th className="p-1.5 text-gray-400 font-mono text-[10px]"></th>
              {Array.from({ length: numTasks }, (_, j) => (
                <th key={j} className="p-1.5 text-gray-500 dark:text-gray-400 font-mono text-[10px] text-center">
                  T{j}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {costMatrix.map((row, i) => (
              <tr key={i}>
                <td className="p-1.5 text-gray-500 dark:text-gray-400 font-mono text-[10px] text-right font-medium">
                  A{i}
                </td>
                {row.map((cost, j) => {
                  const isAssigned = assignments && assignments[i] === j;
                  const intensity = Math.round(((cost - minVal) / range) * 60) + 10;

                  return (
                    <td
                      key={j}
                      className={`p-2.5 text-center font-mono transition-all border border-gray-100 dark:border-gray-700 ${
                        isAssigned
                          ? 'bg-emerald-500 text-white font-bold ring-2 ring-emerald-600 rounded'
                          : 'text-gray-700 dark:text-gray-300'
                      }`}
                      style={{
                        backgroundColor: isAssigned ? undefined : `rgba(59, 130, 246, ${intensity / 100})`,
                      }}
                    >
                      {cost.toFixed(1)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-center gap-4 mt-3 text-xs text-gray-500">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded bg-emerald-500 inline-block" />
          <span>Optimal Assignment</span>
        </div>
      </div>
    </div>
  );
};
