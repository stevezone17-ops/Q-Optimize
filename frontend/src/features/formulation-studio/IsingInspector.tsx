import React from 'react'
import { IsingModel } from '../../types'

interface IsingInspectorProps {
  ising: IsingModel
}

export const IsingInspector: React.FC<IsingInspectorProps> = ({ ising }) => {
  const localFieldsList = Object.entries(ising.local_fields)
  const couplingsList = Object.entries(ising.couplings)

  return (
    <div className="space-y-4 font-mono text-xs">
      {/* Mathematical Hamiltonian Expression */}
      <div className="p-3.5 rounded-lg border border-purple-500/30 bg-midnight-950/90 space-y-2">
        <div className="flex items-center justify-between text-[11px] text-purple-300">
          <span className="font-semibold uppercase tracking-wider">Ising Spin Hamiltonian</span>
          <span className="text-[10px] text-scientific-muted">Convention: x_i = (1 - Z_i) / 2</span>
        </div>
        <div className="p-2.5 bg-midnight-900 rounded border border-scientific-border overflow-x-auto text-purple-200 text-xs">
          <code>{ising.latex_expression || 'H = C + \\sum h_i Z_i + \\sum J_ij Z_i Z_j'}</code>
        </div>
        <div className="flex items-center justify-between text-[11px] text-scientific-muted pt-1">
          <span>Constant Energy Offset C:</span>
          <span className="font-bold text-sky-400">{ising.offset.toFixed(4)}</span>
        </div>
      </div>

      {/* Two-Column Grid: Fields & Couplings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Local Magnetic Fields (h_i) */}
        <div className="p-3.5 rounded-lg border border-scientific-border bg-midnight-950 space-y-2.5">
          <div className="flex items-center justify-between border-b border-scientific-border/40 pb-1.5">
            <span className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
              Local Fields h_i ({localFieldsList.length})
            </span>
            <span className="text-[10px] text-scientific-muted">&sum; h_i Z_i</span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
            {localFieldsList.length === 0 ? (
              <p className="text-scientific-muted text-[11px] py-2 text-center">No non-zero local fields.</p>
            ) : (
              localFieldsList.map(([spinName, hVal]) => (
                <div
                  key={`field-${spinName}`}
                  className="p-1.5 rounded bg-midnight-900 border border-scientific-border/50 flex items-center justify-between"
                >
                  <span className="text-sky-300 font-semibold">{spinName}</span>
                  <span className={`font-mono ${hVal >= 0 ? 'text-slate-200' : 'text-amber-400'}`}>
                    {hVal.toFixed(4)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Couplings (J_ij) */}
        <div className="p-3.5 rounded-lg border border-scientific-border bg-midnight-950 space-y-2.5">
          <div className="flex items-center justify-between border-b border-scientific-border/40 pb-1.5">
            <span className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider">
              Spin Couplings J_ij ({couplingsList.length})
            </span>
            <span className="text-[10px] text-scientific-muted">&sum; J_ij Z_i Z_j</span>
          </div>

          <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
            {couplingsList.length === 0 ? (
              <p className="text-scientific-muted text-[11px] py-2 text-center">No non-zero couplings.</p>
            ) : (
              couplingsList.map(([pairKey, jVal]) => (
                <div
                  key={`coupling-${pairKey}`}
                  className="p-1.5 rounded bg-midnight-900 border border-scientific-border/50 flex items-center justify-between"
                >
                  <span className="text-purple-300 font-semibold">{pairKey}</span>
                  <span className={`font-mono ${jVal >= 0 ? 'text-purple-400' : 'text-rose-400'}`}>
                    {jVal.toFixed(4)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
