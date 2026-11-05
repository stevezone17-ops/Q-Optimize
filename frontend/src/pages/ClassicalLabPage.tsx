import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Alert'
import { Input } from '../components/ui/Input'
import {
  ProblemType,
  ProblemResponse,
  SolverMetadata,
  SolverResult,
} from '../types'
import { classicalSolverService } from '../services/classicalSolverService'
import { problemService } from '../services/problemService'
import {
  Cpu,
  Play,
  Settings,
  AlertCircle,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Target,
  CheckCheck,
  TrendingUp,
} from 'lucide-react'

// Built-in small benchmark presets
const PRESET_BENCHMARKS = [
  {
    name: 'Max-Cut 4-Node Cycle (Benchmark)',
    problem_type: 'max_cut' as ProblemType,
    instance: {
      nodes: ['A', 'B', 'C', 'D'],
      edges: [
        ['A', 'B', 2.0],
        ['B', 'C', 3.0],
        ['C', 'D', 4.0],
        ['D', 'A', 5.0],
        ['A', 'C', 1.0],
      ],
    },
  },
  {
    name: 'Assignment 2x2 Resource Matching (Benchmark)',
    problem_type: 'assignment' as ProblemType,
    instance: {
      agents: ['Agent_1', 'Agent_2'],
      tasks: ['Task_A', 'Task_B'],
      cost_matrix: [
        [4.0, 7.0],
        [2.0, 5.0],
      ],
    },
  },
  {
    name: 'TSP 3-City Triangle (Benchmark)',
    problem_type: 'tsp' as ProblemType,
    instance: {
      cities: ['Paris', 'London', 'Berlin'],
      distance_matrix: [
        [0.0, 344.0, 878.0],
        [344.0, 0.0, 933.0],
        [878.0, 933.0, 0.0],
      ],
    },
  },
]

export const ClassicalLabPage: React.FC = () => {
  const [solvers, setSolvers] = useState<SolverMetadata[]>([])
  const [selectedSolverId, setSelectedSolverId] = useState<string>('exact')
  const [registeredProblems, setRegisteredProblems] = useState<ProblemResponse[]>([])
  const [selectedProblemId, setSelectedProblemId] = useState<string>('preset_0')
  const [, setIsLoading] = useState(true)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<SolverResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Base parameters
  const [timeLimit, setTimeLimit] = useState<number>(60.0)
  const [seed, setSeed] = useState<number>(42)

  // GA specific parameters
  const [popSize, setPopSize] = useState<number>(100)
  const [generations, setGenerations] = useState<number>(200)
  const [mutationRate, setMutationRate] = useState<number>(0.05)
  const [crossoverRate, setCrossoverRate] = useState<number>(0.8)
  const [elitismCount, setElitismCount] = useState<number>(2)

  // Fetch solvers and problems
  useEffect(() => {
    const initData = async () => {
      setIsLoading(true)
      try {
        const [solversList, problemsList] = await Promise.all([
          classicalSolverService.listSolvers(),
          problemService.listProblems(),
        ])
        setSolvers(solversList)
        setRegisteredProblems(problemsList)
      } catch (err) {
        setError('Failed to load classical solver metadata.')
      } finally {
        setIsLoading(false)
      }
    }
    initData()
  }, [])

  const selectedSolver = solvers.find((s) => s.solver_id === selectedSolverId)

  const getActiveProblemData = () => {
    if (selectedProblemId.startsWith('preset_')) {
      const idx = parseInt(selectedProblemId.replace('preset_', ''), 10)
      return {
        isPreset: true,
        name: PRESET_BENCHMARKS[idx]?.name || 'Benchmark',
        problemType: PRESET_BENCHMARKS[idx]?.problem_type || 'max_cut',
        instance: PRESET_BENCHMARKS[idx]?.instance || {},
      }
    }
    const found = registeredProblems.find((p) => p.id === selectedProblemId)
    if (found) {
      return {
        isPreset: false,
        name: found.name,
        problemType: found.problem_type,
        instance: found.instance,
      }
    }
    return {
      isPreset: true,
      name: PRESET_BENCHMARKS[0].name,
      problemType: PRESET_BENCHMARKS[0].problem_type,
      instance: PRESET_BENCHMARKS[0].instance,
    }
  }

  const activeProblem = getActiveProblemData()

  const handleExecuteSolver = async () => {
    if (!selectedSolver?.is_implemented) return
    setIsExecuting(true)
    setError(null)
    setExecutionResult(null)

    try {
      const solverConfig: Record<string, unknown> = {
        time_limit_seconds: timeLimit,
        seed,
      }
      if (selectedSolverId === 'genetic_algorithm') {
        solverConfig.population_size = popSize
        solverConfig.generations = generations
        solverConfig.mutation_rate = mutationRate
        solverConfig.crossover_rate = crossoverRate
        solverConfig.elitism_count = elitismCount
      }

      let payload
      if (!activeProblem.isPreset) {
        payload = {
          solver_id: selectedSolverId,
          problem_id: selectedProblemId,
          config: solverConfig,
          seed,
        }
      } else {
        payload = {
          solver_id: selectedSolverId,
          problem_type: activeProblem.problemType,
          instance: activeProblem.instance,
          config: solverConfig,
          seed,
        }
      }
      const res = await classicalSolverService.executeSolver(payload)
      setExecutionResult(res)
    } catch (err) {
      setError((err as Error).message || 'Solver execution failed.')
    } finally {
      setIsExecuting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-scientific-accent" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Classical Optimization Lab
            </h3>
            <Badge variant="accent">Phase 4 Active</Badge>
          </div>
          <p className="text-xs text-scientific-muted font-mono">
            High-performance classical optimization baselines, exact search, metaheuristics, and benchmark suites.
          </p>
        </div>

        {/* Problem Selector Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-scientific-muted font-mono shrink-0">Problem:</span>
          <select
            value={selectedProblemId}
            onChange={(e) => {
              setSelectedProblemId(e.target.value)
              setExecutionResult(null)
            }}
            className="text-xs font-mono px-3 py-1.5 rounded-lg bg-midnight-950 border border-scientific-border text-slate-200 focus:outline-none focus:ring-1 focus:ring-scientific-accent max-w-[280px] truncate"
          >
            <optgroup label="Small Benchmarks (Pre-loaded)">
              {PRESET_BENCHMARKS.map((b, idx) => (
                <option key={`preset-${idx}`} value={`preset_${idx}`}>
                  {b.name}
                </option>
              ))}
            </optgroup>
            {registeredProblems.length > 0 && (
              <optgroup label="Registered Problems">
                {registeredProblems.map((p) => (
                  <option key={`reg-${p.id}`} value={p.id}>
                    {p.name} ({p.problem_type})
                  </option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Classical Lab Error">
          {error}
        </Alert>
      )}

      {/* Solver Selection Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {solvers.map((solver) => {
          const isSelected = solver.solver_id === selectedSolverId
          return (
            <div
              key={solver.solver_id}
              onClick={() => {
                setSelectedSolverId(solver.solver_id)
                setExecutionResult(null)
              }}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'border-scientific-accent bg-midnight-900/90 shadow-md ring-1 ring-scientific-accent/30'
                  : 'border-scientific-border bg-midnight-950/60 hover:bg-midnight-900/40'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-xs font-semibold text-slate-200">
                  {solver.name}
                </span>
                {solver.is_implemented ? (
                  <Badge variant="accent">Ready ({solver.stage_introduced})</Badge>
                ) : (
                  <Badge variant="outline">{solver.stage_introduced}</Badge>
                )}
              </div>
              <p className="font-mono text-[11px] text-scientific-muted line-clamp-2 leading-relaxed">
                {solver.description}
              </p>
              <div className="mt-3 pt-2.5 border-t border-scientific-border/40 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>Supported:</span>
                <span>{solver.supported_problem_types.join(', ')}</span>
              </div>
            </div>
          )
        })}
      </div>

      {/* Two-Column Setup: Configuration & Execution Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Configuration Form */}
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                <Settings className="h-4 w-4 text-scientific-accent" />
                Algorithm Configuration
              </CardTitle>
              <Badge variant="outline">
                {selectedSolver?.name || 'Selected Algorithm'}
              </Badge>
            </div>
            <CardDescription className="text-xs font-mono">
              Configurable parameters and stopping criteria for {selectedSolver?.name}.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 font-mono text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Input
                  label="Execution Time Limit (s)"
                  type="number"
                  step="1"
                  min="0.5"
                  max="3600"
                  value={timeLimit}
                  onChange={(e) => setTimeLimit(parseFloat(e.target.value) || 60.0)}
                  className="font-mono"
                />
              </div>
              <div>
                <Input
                  label="Random Seed"
                  type="number"
                  step="1"
                  value={seed}
                  onChange={(e) => setSeed(parseInt(e.target.value, 10) || 42)}
                  className="font-mono"
                />
              </div>
            </div>

            {/* Genetic Algorithm Specific Controls */}
            {selectedSolverId === 'genetic_algorithm' && (
              <div className="pt-2 border-t border-scientific-border/40 space-y-3">
                <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider block">
                  Evolutionary Hyperparameters:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  <div>
                    <Input
                      label="Population"
                      type="number"
                      step="10"
                      min="10"
                      max="1000"
                      value={popSize}
                      onChange={(e) => setPopSize(parseInt(e.target.value, 10) || 100)}
                      className="font-mono"
                    />
                  </div>
                  <div>
                    <Input
                      label="Generations"
                      type="number"
                      step="20"
                      min="5"
                      max="5000"
                      value={generations}
                      onChange={(e) => setGenerations(parseInt(e.target.value, 10) || 200)}
                      className="font-mono"
                    />
                  </div>
                  <div>
                    <Input
                      label="Mutation (p_m)"
                      type="number"
                      step="0.01"
                      min="0.0"
                      max="1.0"
                      value={mutationRate}
                      onChange={(e) => setMutationRate(parseFloat(e.target.value) || 0.05)}
                      className="font-mono"
                    />
                  </div>
                  <div>
                    <Input
                      label="Crossover (p_c)"
                      type="number"
                      step="0.05"
                      min="0.0"
                      max="1.0"
                      value={crossoverRate}
                      onChange={(e) => setCrossoverRate(parseFloat(e.target.value) || 0.8)}
                      className="font-mono"
                    />
                  </div>
                  <div>
                    <Input
                      label="Elitism (N)"
                      type="number"
                      step="1"
                      min="0"
                      max="20"
                      value={elitismCount}
                      onChange={(e) => setElitismCount(parseInt(e.target.value, 10) || 2)}
                      className="font-mono"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Parameter Schema Preview */}
            <div className="p-3 bg-midnight-950 rounded-lg border border-scientific-border text-[11px] space-y-2">
              <span className="text-scientific-muted uppercase block font-semibold">
                Parameter Schema Preview:
              </span>
              <pre className="text-sky-300 font-mono text-[10px] overflow-x-auto">
                {JSON.stringify(selectedSolver?.config_schema || {}, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>

        {/* Right: Execution Dispatch Panel */}
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-400" />
                Solver Execution Dispatch
              </CardTitle>
              <Badge variant="accent">
                {activeProblem.problemType}
              </Badge>
            </div>
            <CardDescription className="text-xs font-mono">
              Problem: {activeProblem.name}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 font-mono text-xs">
            <div className="p-4 bg-midnight-950 rounded-lg border border-scientific-border space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-scientific-muted">Target Solver:</span>
                <span className="text-slate-200 font-semibold">{selectedSolver?.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-scientific-muted">Implementation Status:</span>
                <span className={selectedSolver?.is_implemented ? 'text-emerald-400 font-semibold' : 'text-amber-400 font-semibold'}>
                  {selectedSolver?.is_implemented ? 'Active & Ready' : `Scheduled for ${selectedSolver?.stage_introduced}`}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-scientific-muted">Problem Type Compatibility:</span>
                <span className="text-emerald-400 font-semibold">Compatible</span>
              </div>
            </div>

            <Button
              type="button"
              variant="primary"
              className="w-full"
              disabled={!selectedSolver?.is_implemented || isExecuting}
              isLoading={isExecuting}
              onClick={handleExecuteSolver}
              leftIcon={<Play className="h-4 w-4" />}
            >
              {selectedSolver?.is_implemented
                ? `Execute ${selectedSolver.name}`
                : `Executable in ${selectedSolver?.stage_introduced}`}
            </Button>

            {!selectedSolver?.is_implemented && (
              <div className="p-3 bg-midnight-950/80 rounded border border-scientific-border/60 text-[11px] text-scientific-muted flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
                <span>
                  This algorithm will activate in {selectedSolver?.stage_introduced}. You can execute the
                  Exact Classical Solver or Genetic Algorithm right now!
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Execution Results Section */}
      {executionResult && (
        <Card className="bg-midnight-900/80 border-emerald-500/30 font-mono text-xs space-y-4 animate-in fade-in duration-200">
          <CardHeader className="border-b border-scientific-border/40 pb-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <CheckCheck className="h-4 w-4 text-emerald-400" />
                  <CardTitle className="text-sm uppercase tracking-wider text-slate-100">
                    Optimization Results & Independent Evaluation
                  </CardTitle>
                </div>
                <p className="text-[11px] text-scientific-muted">
                  Execution ID: <span className="text-slate-300 font-mono">{executionResult.execution_id}</span>
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {executionResult.is_feasible ? (
                  <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold flex items-center gap-1 text-[11px]">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    FEASIBLE
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold flex items-center gap-1 text-[11px]">
                    <XCircle className="h-3.5 w-3.5" />
                    INFEASIBLE
                  </span>
                )}

                {executionResult.optimality_status === 'proven_optimal' ? (
                  <span className="px-2.5 py-1 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/40 font-bold text-[11px]">
                    PROVEN OPTIMAL
                  </span>
                ) : (
                  <span className="px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/40 font-bold text-[11px]">
                    HEURISTIC FEASIBLE
                  </span>
                )}
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6 pt-2">
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
                <span className="text-[10px] text-scientific-muted uppercase block">Objective Value</span>
                <span className="font-bold text-sky-400 text-lg">
                  {executionResult.objective_value !== undefined ? executionResult.objective_value.toFixed(2) : 'N/A'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
                <span className="text-[10px] text-scientific-muted uppercase block">Runtime</span>
                <span className="font-semibold text-white text-lg flex items-center justify-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-scientific-muted" />
                  {(executionResult.runtime_seconds * 1000).toFixed(1)} ms
                </span>
              </div>
              <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
                <span className="text-[10px] text-scientific-muted uppercase block">Evaluations</span>
                <span className="font-semibold text-purple-400 text-lg">
                  {executionResult.evaluations.toLocaleString()}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
                <span className="text-[10px] text-scientific-muted uppercase block">Termination</span>
                <span className="font-semibold text-emerald-400 text-xs mt-1 block">
                  {executionResult.termination_reason}
                </span>
              </div>
            </div>

            {/* Convergence Trace Summary if available */}
            {executionResult.convergence_history && executionResult.convergence_history.length > 1 && (
              <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border space-y-2.5">
                <span className="text-[11px] text-scientific-muted uppercase font-semibold flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5 text-purple-400" />
                  Convergence Checkpoints ({executionResult.convergence_history.length} recorded):
                </span>
                <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                  <div className="p-2 rounded bg-midnight-900 border border-scientific-border/40">
                    <span className="text-scientific-muted block">Gen 0 Initial</span>
                    <span className="font-bold text-slate-300">
                      {executionResult.convergence_history[0].best_objective.toFixed(2)}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-midnight-900 border border-scientific-border/40">
                    <span className="text-scientific-muted block">Midpoint</span>
                    <span className="font-bold text-sky-400">
                      {executionResult.convergence_history[Math.floor(executionResult.convergence_history.length / 2)].best_objective.toFixed(2)}
                    </span>
                  </div>
                  <div className="p-2 rounded bg-midnight-900 border border-scientific-border/40">
                    <span className="text-scientific-muted block">Final Best</span>
                    <span className="font-bold text-emerald-400">
                      {executionResult.convergence_history[executionResult.convergence_history.length - 1].best_objective.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Candidate Solution Inspection */}
            <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border space-y-2">
              <span className="text-[11px] text-scientific-muted uppercase font-semibold flex items-center gap-1.5">
                <Target className="h-3.5 w-3.5 text-scientific-accent" />
                Solution Candidate Details:
              </span>
              <pre className="p-3 bg-midnight-900 rounded border border-scientific-border/80 text-sky-300 font-mono text-xs overflow-x-auto">
                {JSON.stringify(executionResult.candidate_solution, null, 2)}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
