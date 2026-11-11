import React from 'react';

interface QAOACircuitAnalyticsProps {
  numQubits?: number;
  circuitDepth?: number;
  numLayersP?: number;
  cnotCount?: number;
  totalGates?: number;
  shots?: number;
  backendName?: string;
}

export const QAOACircuitAnalyticsCard: React.FC<QAOACircuitAnalyticsProps> = ({
  numQubits = 4,
  circuitDepth = 8,
  numLayersP = 2,
  cnotCount = 12,
  totalGates = 28,
  shots = 1024,
  backendName = 'AerSimulator (CPU Statevector)',
}) => {
  return (
    <div
      className="p-5 bg-gradient-to-br from-indigo-50/50 to-purple-50/50 dark:from-indigo-950/20 dark:to-purple-950/20 rounded-xl border border-indigo-200 dark:border-indigo-800/50 shadow-sm"
      data-testid="qaoa-circuit-analytics-card"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
            Quantum Circuit Complexity Analytics
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Transpiled QAOA ansatz metrics and compilation attributes
          </p>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300">
          p = {numLayersP}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
        <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
          <div className="text-xl font-bold font-mono text-indigo-600 dark:text-indigo-400">
            {numQubits}
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">Active Qubits</div>
        </div>

        <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
          <div className="text-xl font-bold font-mono text-purple-600 dark:text-purple-400">
            {circuitDepth}
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">Circuit Depth</div>
        </div>

        <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
          <div className="text-xl font-bold font-mono text-blue-600 dark:text-blue-400">
            {cnotCount}
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">Entangling (CX)</div>
        </div>

        <div className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-100 dark:border-gray-700">
          <div className="text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">
            {totalGates}
          </div>
          <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">Total Gates</div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700 flex flex-wrap justify-between items-center text-xs text-gray-500">
        <div>
          Execution Target:{' '}
          <span className="font-mono text-gray-700 dark:text-gray-300 font-medium">
            {backendName}
          </span>
        </div>
        <div>
          Shots:{' '}
          <span className="font-mono text-gray-700 dark:text-gray-300 font-medium">
            {shots.toLocaleString()}
          </span>
        </div>
      </div>
    </div>
  );
};
