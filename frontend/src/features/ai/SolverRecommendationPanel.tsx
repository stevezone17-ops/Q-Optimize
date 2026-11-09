import React from 'react'
import {
  Sparkles,
  Cpu,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ArrowRight,
  BarChart2,
} from 'lucide-react'
import { SolverRecommendation } from '../../types'

interface SolverRecommendationPanelProps {
  recommendation: SolverRecommendation | null
  isLoading?: boolean
  error?: string | null
  onAcceptRecommendation?: (solverName: string) => void
  onCompareSolvers?: (solvers: string[]) => void
  onDismiss?: () => void
  onRefresh?: () => void
}

export const SolverRecommendationPanel: React.FC<SolverRecommendationPanelProps> = ({
  recommendation,
  isLoading = false,
  error = null,
  onAcceptRecommendation,
  onCompareSolvers,
  onDismiss,
  onRefresh,
}) => {
  if (isLoading) {
    return (
      <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-6 shadow-xl text-center animate-pulse" data-testid="ai-recommendation-loading">
        <div className="flex items-center justify-center gap-3 text-indigo-400 mb-2">
          <Sparkles className="w-5 h-5 animate-spin" />
          <span className="font-semibold text-lg">Synthesizing Intelligent Solver Recommendation...</span>
        </div>
        <p className="text-xs text-slate-400">
          Extracting graph density, search space log2, and evaluating ML & expert safety boundaries.
        </p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-950/40 border border-red-500/40 rounded-xl p-5 text-red-200" data-testid="ai-recommendation-error">
        <div className="flex items-center gap-2 font-medium mb-1">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          <span>Recommendation Engine Error</span>
        </div>
        <p className="text-xs text-red-300 mb-3">{error}</p>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-3 py-1.5 bg-red-800/60 hover:bg-red-700/60 text-xs rounded-lg transition-colors"
          >
            Retry Recommendation
          </button>
        )}
      </div>
    )
  }

  if (!recommendation) {
    return null
  }

  const {
    recommended_solver,
    confidence_score,
    recommendation_source,
    ranked_alternatives,
    explanation,
    key_features_summary,
    resource_considerations,
    is_out_of_distribution,
    known_limitations,
    model_version,
  } = recommendation

  const formatSolverName = (name: string): string => {
    switch (name) {
      case 'exact':
        return 'Exact Solver (Deterministic)'
      case 'simulated_annealing':
        return 'Simulated Annealing (Metropolis)'
      case 'genetic_algorithm':
        return 'Genetic Algorithm (Evolutionary)'
      case 'standard_qaoa':
        return 'Standard QAOA (Quantum Aer)'
      case 'adaptive_qaoa':
        return 'Adaptive QAOA (Dynamic Depth)'
      default:
        return name.replace(/_/g, ' ').toUpperCase()
    }
  }

  const getSourceBadge = () => {
    if (recommendation_source === 'ml_model') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-950/80 text-purple-300 border border-purple-500/40 flex items-center gap-1.5">
          <Cpu className="w-3 h-3 text-purple-400" />
          ML Model {model_version ? `(${model_version})` : ''}
        </span>
      )
    }
    if (recommendation_source === 'fallback') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
          <AlertTriangle className="w-3 h-3 text-amber-400" />
          Rule-Based Safety Fallback
        </span>
      )
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-950/80 text-blue-300 border border-blue-500/40 flex items-center gap-1.5">
        <Zap className="w-3 h-3 text-blue-400" />
        Expert Rule System
      </span>
    )
  }

  const primaryAlt = ranked_alternatives.find((a) => a.solver_name === recommended_solver)
  const isPrimaryCompatible = primaryAlt ? primaryAlt.is_compatible : true

  return (
    <div className="bg-slate-900 border border-indigo-500/30 rounded-xl p-5 shadow-2xl space-y-5" data-testid="solver-recommendation-panel">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Intelligent Solver Recommendation
              {getSourceBadge()}
            </h3>
            <p className="text-xs text-slate-400">Data-driven algorithm selection with complexity safeguards</p>
          </div>
        </div>

        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-xs text-slate-400 hover:text-slate-200 px-2 py-1 rounded hover:bg-slate-800 transition-colors"
            data-testid="dismiss-recommendation-btn"
          >
            Continue Without AI
          </button>
        )}
      </div>

      {/* Out-of-Distribution Warning Banner */}
      {is_out_of_distribution && (
        <div className="bg-amber-950/50 border border-amber-500/50 rounded-lg p-3 text-amber-200 text-xs flex items-start gap-2.5" data-testid="ood-warning-banner">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-semibold text-amber-300">Out-of-Distribution Instance Detected</span>
            <p className="text-amber-200/90 leading-relaxed">
              This problem’s structural characteristics (variables, density, or search space) diverge significantly from historical training benchmarks.
              The system has automatically engaged expert complexity heuristics and conservative safety limits.
            </p>
          </div>
        </div>
      )}

      {/* Recommended Solver Spotlight Card */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1.5 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-medium uppercase tracking-wider text-indigo-400">Recommended Solver</span>
            <span className="px-2 py-0.5 rounded text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              {(confidence_score * 100).toFixed(1)}% Match Confidence
            </span>
            {isPrimaryCompatible ? (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                Compatible
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-red-950/80 text-red-300 border border-red-500/30 flex items-center gap-1">
                <XCircle className="w-3 h-3 text-red-400" />
                Resource Limit Exceeded
              </span>
            )}
          </div>
          <h4 className="text-lg font-bold text-slate-100">{formatSolverName(recommended_solver)}</h4>
          <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">{explanation}</p>
        </div>

        <div className="flex flex-wrap md:flex-col gap-2 w-full md:w-auto">
          {onAcceptRecommendation && (
            <button
              onClick={() => onAcceptRecommendation(recommended_solver)}
              className="flex-1 md:flex-initial px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all"
              data-testid="accept-recommendation-btn"
            >
              <span>Accept & Preload</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          {onCompareSolvers && ranked_alternatives.length > 1 && (
            <button
              onClick={() => onCompareSolvers(ranked_alternatives.map((a) => a.solver_name))}
              className="flex-1 md:flex-initial px-3 py-2 bg-slate-700/80 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-600 flex items-center justify-center gap-1.5 transition-all"
              data-testid="compare-solvers-btn"
            >
              <BarChart2 className="w-3.5 h-3.5 text-slate-400" />
              <span>Compare Solvers</span>
            </button>
          )}
        </div>
      </div>

      {/* Key Problem Features Breakdown */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-800/40 border border-slate-800 rounded-lg p-2.5">
          <div className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Decision Variables</div>
          <div className="text-base font-bold text-slate-100">{key_features_summary.num_variables ?? 'N/A'}</div>
        </div>
        <div className="bg-slate-800/40 border border-slate-800 rounded-lg p-2.5">
          <div className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Search Space log₂</div>
          <div className="text-base font-bold text-slate-100">
            {typeof key_features_summary.estimated_search_space_log2 === 'number'
              ? key_features_summary.estimated_search_space_log2.toFixed(1)
              : 'N/A'}
          </div>
        </div>
        <div className="bg-slate-800/40 border border-slate-800 rounded-lg p-2.5">
          <div className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Graph / Density</div>
          <div className="text-base font-bold text-slate-100">
            {typeof key_features_summary.graph_density === 'number'
              ? `${(key_features_summary.graph_density * 100).toFixed(1)}%`
              : (key_features_summary.num_constraints ?? '0 constraints')}
          </div>
        </div>
        <div className="bg-slate-800/40 border border-slate-800 rounded-lg p-2.5">
          <div className="text-[10px] uppercase font-semibold text-slate-400 mb-0.5">Required Qubits</div>
          <div className="text-base font-bold text-slate-100">
            {resource_considerations.required_qubits !== undefined
              ? `${resource_considerations.required_qubits} ${resource_considerations.required_qubits <= 20 ? '(Aer OK)' : '(Exceeds Aer)'}`
              : 'N/A'}
          </div>
        </div>
      </div>

      {/* Ranked Alternatives Table */}
      {ranked_alternatives.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span>Ranked Candidate Solvers</span>
            <span className="text-[11px] font-normal text-slate-400">Evaluated against safety bounds</span>
          </div>

          <div className="space-y-1.5" data-testid="ranked-alternatives-list">
            {ranked_alternatives.map((alt) => {
              const isSelected = alt.solver_name === recommended_solver
              return (
                <div
                  key={alt.solver_name}
                  className={`p-2.5 rounded-lg border text-xs flex items-center justify-between gap-3 transition-colors ${
                    isSelected
                      ? 'bg-indigo-950/30 border-indigo-500/40 text-slate-100'
                      : 'bg-slate-800/40 border-slate-800 text-slate-300'
                  }`}
                  data-testid={`solver-alternative-${alt.solver_name}`}
                >
                  <div className="flex items-center gap-2.5 flex-1 min-w-0">
                    <span className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-400 shrink-0">
                      {alt.rank}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold truncate">{formatSolverName(alt.solver_name)}</span>
                        {isSelected && (
                          <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-1.5 py-0.2 rounded font-medium">
                            Primary
                          </span>
                        )}
                        {!alt.is_compatible && (
                          <span className="text-[10px] bg-red-950 text-red-400 border border-red-800 px-1.5 py-0.2 rounded font-medium">
                            Incompatible
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">{alt.reason}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <div className="font-semibold text-slate-200">{(alt.score * 100).toFixed(0)}%</div>
                      <div className="text-[10px] text-slate-400">{alt.estimated_runtime_class || 'heuristic'}</div>
                    </div>

                    {onAcceptRecommendation && !isSelected && alt.is_compatible && (
                      <button
                        onClick={() => onAcceptRecommendation(alt.solver_name)}
                        className="px-2 py-1 text-[11px] text-indigo-400 hover:text-indigo-300 hover:bg-slate-800 rounded transition-colors"
                      >
                        Select
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Limitations and Disclosures */}
      {known_limitations.length > 0 && (
        <div className="border-t border-slate-800/80 pt-2.5 text-[11px] text-slate-400 flex items-start gap-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            {known_limitations.map((lim, idx) => (
              <p key={idx}>{lim}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
