import React, { useState } from 'react'
import { Button } from '../../components/ui/Button'
import { VerificationResult, QuboModel } from '../../types'
import { formulationService } from '../../services/formulationService'
import { CheckCircle2, XCircle, ShieldCheck, Cpu } from 'lucide-react'

interface VerificationPanelProps {
  formulationId?: string
  problemId?: string
  problemType?: string
  instance?: Record<string, unknown>
  qubo?: QuboModel
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({
  formulationId,
  problemId,
  problemType,
  instance,
  qubo,
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleRunVerification = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const res = await formulationService.verifyFormulation({
        formulation_id: formulationId,
        problem_id: problemId,
        problem_type: problemType,
        instance,
        qubo,
      })
      setResult(res)
    } catch (err) {
      setError((err as Error).message || 'Verification failed against backend verification engine.')
    } finally {
      setIsLoading(false)
    }
  }

  const numVars = qubo?.variable_order.length || 0
  const totalStates = Math.pow(2, numVars)
  const canVerifyExhaustively = numVars <= 12

  return (
    <div className="p-4 rounded-xl border border-scientific-border bg-midnight-950 space-y-4 font-mono text-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-scientific-border/40 pb-3">
        <div>
          <h4 className="font-semibold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
            Independent Mathematical Verification
          </h4>
          <p className="text-[11px] text-scientific-muted mt-0.5">
            Exhaustive enumeration of all {totalStates.toLocaleString()} states verifying E_QUBO(x) &equiv; H_Ising(Z) & C_orig(x)
          </p>
        </div>

        <Button
          type="button"
          size="sm"
          variant="primary"
          onClick={handleRunVerification}
          isLoading={isLoading}
          disabled={!canVerifyExhaustively}
          leftIcon={<Cpu className="h-3.5 w-3.5" />}
        >
          {canVerifyExhaustively ? 'Verify All States (2^n)' : 'Exceeds Limit (n > 12)'}
        </Button>
      </div>

      {!canVerifyExhaustively && (
        <div className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-lg text-xs text-amber-300">
          State space 2^{numVars} = {totalStates.toLocaleString()} exceeds the small-instance exhaustive verification threshold (n &le; 12).
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs text-rose-300">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4 pt-1 animate-in fade-in duration-200">
          {/* Status Badge & Summary */}
          <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-lg bg-midnight-900 border border-scientific-border/80">
            <div className="flex items-center gap-2">
              {result.is_verified ? (
                <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold flex items-center gap-1.5 text-xs">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  MATHEMATICALLY VERIFIED
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold flex items-center gap-1.5 text-xs">
                  <XCircle className="h-3.5 w-3.5 text-rose-400" />
                  ENERGY MISMATCH DETECTED
                </span>
              )}
            </div>

            <div className="text-right">
              <span className="text-[10px] text-scientific-muted block">Max Discrepancy</span>
              <span className="font-bold text-sky-400">{result.max_energy_discrepancy.toExponential(2)}</span>
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
            <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
              <span className="text-scientific-muted block text-[10px]">States Enumerated</span>
              <span className="font-semibold text-slate-200">{result.num_states_tested.toLocaleString()}</span>
            </div>
            <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
              <span className="text-scientific-muted block text-[10px]">Feasible States</span>
              <span className="font-semibold text-purple-400">{result.feasible_states_count}</span>
            </div>
            <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
              <span className="text-scientific-muted block text-[10px]">Min QUBO Energy</span>
              <span className="font-semibold text-sky-400">{result.min_qubo_energy.toFixed(2)}</span>
            </div>
            <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
              <span className="text-scientific-muted block text-[10px]">Min Ising Energy</span>
              <span className="font-semibold text-emerald-400">{result.min_ising_energy.toFixed(2)}</span>
            </div>
          </div>

          {/* Feasibility Summary Text */}
          <div className="p-3 bg-midnight-900/60 rounded-lg border border-scientific-border/60 text-slate-300 text-xs leading-relaxed">
            <span className="text-scientific-muted text-[10px] block mb-0.5 uppercase tracking-wider">
              Verification Proof Summary:
            </span>
            <p>{result.feasibility_summary}</p>
          </div>
        </div>
      )}
    </div>
  )
}
