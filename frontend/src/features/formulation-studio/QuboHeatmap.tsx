import React from 'react'

interface QuboHeatmapProps {
  matrix: number[][]
  variableOrder: string[]
}

export const QuboHeatmap: React.FC<QuboHeatmapProps> = ({ matrix, variableOrder }) => {
  if (!matrix || matrix.length === 0 || !variableOrder || variableOrder.length === 0) {
    return (
      <div className="p-8 text-center text-xs font-mono text-scientific-muted">
        No matrix data available.
      </div>
    )
  }

  const n = variableOrder.length

  // Find max absolute value for dynamic color scaling
  let maxAbs = 0.0
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      const val = Math.abs(matrix[i]?.[j] ?? 0.0)
      if (val > maxAbs) maxAbs = val
    }
  }
  if (maxAbs === 0.0) maxAbs = 1.0

  const getCellColor = (val: number, i: number, j: number) => {
    if (j < i) {
      // Lower triangle (zero in upper-triangular storage)
      return 'bg-midnight-950/40 text-slate-700'
    }
    if (Math.abs(val) < 1e-9) {
      return 'bg-midnight-900 text-slate-500'
    }

    const intensity = Math.min(1.0, Math.abs(val) / maxAbs)

    if (i === j) {
      // Diagonal linear term: blue/violet
      return val > 0
        ? `bg-sky-500/${Math.max(20, Math.round(intensity * 70))} text-sky-300 font-bold border border-sky-400/30`
        : `bg-amber-500/${Math.max(20, Math.round(intensity * 70))} text-amber-300 font-bold border border-amber-400/30`
    }

    // Off-diagonal quadratic term
    return val > 0
      ? `bg-purple-500/${Math.max(15, Math.round(intensity * 60))} text-purple-300`
      : `bg-rose-500/${Math.max(15, Math.round(intensity * 60))} text-rose-300`
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-[11px] font-mono text-scientific-muted">
        <span>Upper-Triangular QUBO Matrix Q (n = {n})</span>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-sky-500/50 inline-block"></span>
            Diagonal (Linear)
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded bg-purple-500/50 inline-block"></span>
            Quadratic (+ Interaction)
          </span>
        </div>
      </div>

      <div className="overflow-x-auto border border-scientific-border/80 rounded-lg bg-midnight-950 p-2">
        <table className="border-collapse text-xs font-mono select-none">
          <thead>
            <tr>
              <th className="p-1.5 text-left text-[10px] text-scientific-muted border-b border-r border-scientific-border/40">
                i \ j
              </th>
              {variableOrder.map((vName, jIdx) => (
                <th
                  key={`th-col-${vName}-${jIdx}`}
                  className="p-1.5 text-center min-w-[55px] max-w-[85px] truncate text-[10px] text-sky-400 font-semibold border-b border-scientific-border/40"
                  title={vName}
                >
                  {vName.length > 8 ? `${vName.slice(0, 7)}…` : vName}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {variableOrder.map((rowVar, iIdx) => (
              <tr key={`tr-row-${rowVar}-${iIdx}`}>
                <td
                  className="p-1.5 text-right font-semibold text-purple-400 border-r border-scientific-border/40 text-[10px] min-w-[60px] truncate"
                  title={rowVar}
                >
                  {rowVar.length > 8 ? `${rowVar.slice(0, 7)}…` : rowVar}
                </td>
                {variableOrder.map((_, jIdx) => {
                  const val = matrix[iIdx]?.[jIdx] ?? 0.0
                  return (
                    <td
                      key={`cell-${iIdx}-${jIdx}`}
                      className={`p-1.5 text-center text-[11px] transition-colors ${getCellColor(
                        val,
                        iIdx,
                        jIdx
                      )}`}
                      title={`Q[${variableOrder[iIdx]}, ${variableOrder[jIdx]}] = ${val}`}
                    >
                      {jIdx < iIdx ? '-' : val.toFixed(1)}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
