import React, { useState } from 'react'
import { Modal } from '../../components/ui/Modal'
import { Button } from '../../components/ui/Button'
import {
  ProblemType,
  ProblemInstance,
  MaxCutInstance,
  AssignmentInstance,
  TSPInstance,
  EvaluationResult,
} from '../../types'
import { problemService } from '../../services/problemService'
import {
  CheckCircle2,
  XCircle,
  Play,
  RotateCcw,
  Sparkles,
  Info,
} from 'lucide-react'

interface SolutionEvaluatorModalProps {
  isOpen: boolean
  onClose: () => void
  problemType: ProblemType
  instance: ProblemInstance
  problemName: string
}

export const SolutionEvaluatorModal: React.FC<SolutionEvaluatorModalProps> = ({
  isOpen,
  onClose,
  problemType,
  instance,
  problemName,
}) => {
  // Candidate representation states
  // Max-Cut: dict { [node]: 0 | 1 }
  const [maxCutCandidate, setMaxCutCandidate] = useState<Record<string, number>>({})
  // Assignment: dict { [agent]: task }
  const [assignmentCandidate, setAssignmentCandidate] = useState<Record<string, string>>({})
  // TSP: list of city names
  const [tspCandidate, setTspCandidate] = useState<string[]>([])

  const [isLoading, setIsLoading] = useState(false)
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null)
  const [evalError, setEvalError] = useState<string | null>(null)

  // Initialize candidate when opened
  React.useEffect(() => {
    if (!isOpen) {
      setEvalResult(null)
      setEvalError(null)
      return
    }

    if (problemType === 'max_cut') {
      const mc = instance as MaxCutInstance
      const init: Record<string, number> = {}
      mc.nodes.forEach((n, idx) => {
        init[n] = idx % 2 === 0 ? 0 : 1 // Alternating partition default
      })
      setMaxCutCandidate(init)
    } else if (problemType === 'assignment') {
      const assign = instance as AssignmentInstance
      const init: Record<string, string> = {}
      assign.agents.forEach((a, idx) => {
        if (idx < assign.tasks.length) {
          init[a] = assign.tasks[idx]
        }
      })
      setAssignmentCandidate(init)
    } else if (problemType === 'tsp') {
      const tsp = instance as TSPInstance
      setTspCandidate([...tsp.cities])
    }
  }, [isOpen, problemType, instance])

  const handleEvaluate = async () => {
    setIsLoading(true)
    setEvalError(null)

    let candidatePayload: unknown
    if (problemType === 'max_cut') {
      candidatePayload = maxCutCandidate
    } else if (problemType === 'assignment') {
      candidatePayload = assignmentCandidate
    } else if (problemType === 'tsp') {
      candidatePayload = tspCandidate
    }

    try {
      const result = await problemService.evaluateDirect(
        problemType,
        instance as unknown as Record<string, unknown>,
        candidatePayload
      )
      setEvalResult(result)
    } catch (err) {
      setEvalError((err as Error).message || 'Evaluation failed against backend engine.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Independent Objective & Constraint Evaluator"
      description={`Test a candidate solution for "${problemName}" against the independent mathematical evaluator engine.`}
      maxWidth="max-w-3xl"
    >
      <div className="space-y-5">
        {/* Input Configuration Panel */}
        <div className="p-4 rounded-xl border border-scientific-border bg-midnight-950 space-y-4">
          <div className="flex items-center justify-between border-b border-scientific-border/40 pb-2">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-scientific-accent" />
              Candidate Solution Configuration
            </h4>
            <span className="text-[11px] text-scientific-muted font-mono">
              Independent of solver self-reporting
            </span>
          </div>

          {/* Max-Cut Candidate Editor */}
          {problemType === 'max_cut' && (
            <div className="space-y-3 font-mono text-xs">
              <p className="text-slate-400">
                Assign each vertex to Partition <strong className="text-sky-400">S (0)</strong> or Partition <strong className="text-purple-400">V\S (1)</strong>:
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {(instance as MaxCutInstance).nodes.map((node) => {
                  const part = maxCutCandidate[node] ?? 0
                  return (
                    <div
                      key={`cand-node-${node}`}
                      className="p-2.5 rounded-lg border border-scientific-border/80 bg-midnight-900 flex items-center justify-between"
                    >
                      <span className="font-semibold text-white">{node}</span>
                      <div className="flex rounded border border-scientific-border bg-midnight-950 p-0.5">
                        <button
                          type="button"
                          onClick={() => setMaxCutCandidate({ ...maxCutCandidate, [node]: 0 })}
                          className={`px-2 py-0.5 rounded text-[11px] ${
                            part === 0
                              ? 'bg-sky-500/20 text-sky-400 font-bold border border-sky-500/40'
                              : 'text-scientific-muted hover:text-slate-300'
                          }`}
                        >
                          S (0)
                        </button>
                        <button
                          type="button"
                          onClick={() => setMaxCutCandidate({ ...maxCutCandidate, [node]: 1 })}
                          className={`px-2 py-0.5 rounded text-[11px] ${
                            part === 1
                              ? 'bg-purple-500/20 text-purple-400 font-bold border border-purple-500/40'
                              : 'text-scientific-muted hover:text-slate-300'
                          }`}
                        >
                          V\S (1)
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Assignment Candidate Editor */}
          {problemType === 'assignment' && (
            <div className="space-y-3 font-mono text-xs">
              <p className="text-slate-400">
                Designate task matching for each agent (1-to-1 matching constraint):
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(instance as AssignmentInstance).agents.map((agent) => (
                  <div
                    key={`assign-agent-${agent}`}
                    className="p-2.5 rounded-lg border border-scientific-border/80 bg-midnight-900 flex items-center justify-between gap-2"
                  >
                    <span className="font-semibold text-purple-400">{agent}</span>
                    <select
                      value={assignmentCandidate[agent] || ''}
                      onChange={(e) =>
                        setAssignmentCandidate({
                          ...assignmentCandidate,
                          [agent]: e.target.value,
                        })
                      }
                      className="text-xs px-2 py-1 rounded bg-midnight-950 border border-scientific-border text-slate-200 focus:outline-none"
                    >
                      <option value="">(Unassigned)</option>
                      {(instance as AssignmentInstance).tasks.map((task) => (
                        <option key={`task-opt-${task}`} value={task}>
                          {task}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TSP Candidate Editor */}
          {problemType === 'tsp' && (
            <div className="space-y-3 font-mono text-xs">
              <p className="text-slate-400">
                Tour visit sequence (closed Hamiltonian cycle):
              </p>
              <div className="flex flex-wrap items-center gap-2 p-3 bg-midnight-900 rounded-lg border border-scientific-border">
                {tspCandidate.map((city, idx) => (
                  <div
                    key={`tsp-tour-step-${city}-${idx}`}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-midnight-950 border border-scientific-border text-slate-200"
                  >
                    <span className="text-[10px] text-amber-400 font-bold">{idx + 1}.</span>
                    <span>{city}</span>
                  </div>
                ))}
                <span className="text-xs text-scientific-muted">
                  &rarr; returns to {tspCandidate[0] || 'start'}
                </span>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => setTspCandidate([...(instance as TSPInstance).cities])}
                  leftIcon={<RotateCcw className="h-3 w-3" />}
                >
                  Reset Sequence
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="ghost"
                  onClick={() => setTspCandidate([...tspCandidate].reverse())}
                >
                  Reverse Tour
                </Button>
              </div>
            </div>
          )}

          {/* Evaluate Action Trigger */}
          <div className="pt-2 border-t border-scientific-border/40 flex justify-end">
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleEvaluate}
              isLoading={isLoading}
              leftIcon={<Play className="h-3.5 w-3.5" />}
            >
              Evaluate Objective & Feasibility
            </Button>
          </div>
        </div>

        {/* Evaluation Output Section */}
        {evalError && (
          <div className="p-3 bg-rose-950/30 border border-rose-500/40 rounded-lg text-xs text-rose-300 font-mono">
            {evalError}
          </div>
        )}

        {evalResult && (
          <div className="p-4 rounded-xl border border-scientific-border bg-midnight-950 space-y-4 font-mono text-xs animate-in fade-in duration-200">
            {/* Status Header */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-scientific-border/40 pb-3">
              <div className="flex items-center gap-2">
                {evalResult.is_feasible ? (
                  <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-semibold flex items-center gap-1.5 text-xs">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    FEASIBLE SOLUTION
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/40 font-semibold flex items-center gap-1.5 text-xs">
                    <XCircle className="h-3.5 w-3.5" />
                    INFEASIBLE CANDIDATE ({evalResult.violations.length} Violations)
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2">
                <span className="text-scientific-muted text-[11px] uppercase">
                  Objective Value:
                </span>
                <span className="text-base font-bold text-sky-400">
                  {evalResult.objective_value}
                </span>
                <span className="text-[10px] text-scientific-muted">
                  ({evalResult.objective_sense})
                </span>
              </div>
            </div>

            {/* Constraint Violations (if infeasible) */}
            {evalResult.violations.length > 0 && (
              <div className="space-y-2 p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg">
                <span className="text-[11px] font-semibold text-rose-300 uppercase block">
                  Constraint Violations:
                </span>
                <div className="space-y-1.5">
                  {evalResult.violations.map((v, idx) => (
                    <div key={`viol-${idx}`} className="text-xs text-rose-200 flex items-start gap-1.5">
                      <span className="text-rose-400">&bull;</span>
                      <div>
                        <strong>[{v.constraint_id}]</strong>: {v.message}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Domain-Specific Details */}
            {problemType === 'max_cut' && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-center">
                <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
                  <span className="text-scientific-muted block text-[10px]">Crossing Edges</span>
                  <span className="font-semibold text-emerald-400">
                    {Number(evalResult.details.crossing_edge_count || 0)} / {Number(evalResult.details.total_edge_count || 0)}
                  </span>
                </div>
                <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
                  <span className="text-scientific-muted block text-[10px]">Cut Fraction</span>
                  <span className="font-semibold text-sky-400">
                    {(Number(evalResult.details.cut_fraction || 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
                  <span className="text-scientific-muted block text-[10px]">Partition S0</span>
                  <span className="font-semibold text-slate-200">
                    {Array.isArray(evalResult.details.partition_0) ? evalResult.details.partition_0.join(', ') : '-'}
                  </span>
                </div>
                <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border/60">
                  <span className="text-scientific-muted block text-[10px]">Partition S1</span>
                  <span className="font-semibold text-purple-300">
                    {Array.isArray(evalResult.details.partition_1) ? evalResult.details.partition_1.join(', ') : '-'}
                  </span>
                </div>
              </div>
            )}

            {problemType === 'assignment' && (
              <div className="space-y-2 pt-1">
                <span className="text-scientific-muted text-[10px] uppercase block">
                  Assignment Pair Costs:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {Array.isArray(evalResult.details.assignments) &&
                    evalResult.details.assignments.map((item: Record<string, unknown>, idx: number) => (
                      <div
                        key={`assign-card-${idx}`}
                        className="p-2 rounded bg-midnight-900 border border-scientific-border/60 flex items-center justify-between"
                      >
                        <span className="text-slate-300">
                          {String(item.agent)} &rarr; {String(item.task)}
                        </span>
                        <span className="font-bold text-purple-400">
                          {Number(item.cost)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {problemType === 'tsp' && (
              <div className="space-y-2 pt-1">
                <span className="text-scientific-muted text-[10px] uppercase block">
                  Hamiltonian Cycle Legs:
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {Array.isArray(evalResult.details.legs) &&
                    evalResult.details.legs.map((leg: Record<string, unknown>, idx: number) => (
                      <div
                        key={`leg-${idx}`}
                        className="p-2 rounded bg-midnight-900 border border-scientific-border/60 flex items-center justify-between"
                      >
                        <span className="text-slate-300">
                          Leg {idx + 1}: {String(leg.from)} &rarr; {String(leg.to)}
                        </span>
                        <span className="font-bold text-amber-400">
                          {Number(leg.distance)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-scientific-border/40">
          <div className="flex items-center gap-1.5 text-xs text-scientific-muted font-mono">
            <Info className="h-3.5 w-3.5 text-sky-400" />
            <span>Independent evaluator ensures solver outputs are verified accurately.</span>
          </div>
          <Button variant="secondary" size="sm" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  )
}
