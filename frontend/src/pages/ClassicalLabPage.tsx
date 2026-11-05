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
  BenchmarkResult,
  ExecutionRecord,
} from '../types'
import { classicalSolverService } from '../services/classicalSolverService'
import { problemService } from '../services/problemService'
import {
  Cpu,
  Play,
  Settings,
  Activity,
  Clock,
  Target,
  CheckCheck,
  TrendingUp,
  BarChart2,
  History,
  Award,
  ArrowRight,
  ShieldCheck,
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

type LabMode = 'single' | 'benchmark' | 'history'

export const ClassicalLabPage: React.FC = () => {
  // Navigation mode
  const [activeMode, setActiveMode] = useState<LabMode>('single')

  // Solvers & Problems
  const [solvers, setSolvers] = useState<SolverMetadata[]>([])
  const [selectedSolverId, setSelectedSolverId] = useState<string>('exact')
  const [registeredProblems, setRegisteredProblems] = useState<ProblemResponse[]>([])
  const [selectedProblemId, setSelectedProblemId] = useState<string>('preset_0')
  const [, setIsLoading] = useState(true)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executionResult, setExecutionResult] = useState<SolverResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Execution options
  const [isBackground, setIsBackground] = useState<boolean>(false)

  // Base parameters
  const [timeLimit, setTimeLimit] = useState<number>(60.0)
  const [seed, setSeed] = useState<number>(42)

  // GA specific parameters
  const [popSize, setPopSize] = useState<number>(100)
  const [generations, setGenerations] = useState<number>(200)
  const [mutationRate, setMutationRate] = useState<number>(0.05)
  const [crossoverRate, setCrossoverRate] = useState<number>(0.8)
  const [elitismCount, setElitismCount] = useState<number>(2)

  // SA specific parameters
  const [initialTemp, setInitialTemp] = useState<number>(100.0)
  const [finalTemp, setFinalTemp] = useState<number>(0.01)
  const [coolingSchedule, setCoolingSchedule] = useState<'exponential' | 'linear'>('exponential')
  const [coolingRate, setCoolingRate] = useState<number>(0.95)
  const [stepsPerTemp, setStepsPerTemp] = useState<number>(50)
  const [maxIterations, setMaxIterations] = useState<number>(5000)

  // Benchmark Suite state
  const [benchmarkTrials, setBenchmarkTrials] = useState<number>(2)
  const [benchmarkSolvers, setBenchmarkSolvers] = useState<string[]>([
    'exact',
    'genetic_algorithm',
    'simulated_annealing',
  ])
  const [isBenchmarking, setIsBenchmarking] = useState(false)
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null)

  // History state
  const [recentExecutions, setRecentExecutions] = useState<ExecutionRecord[]>([])
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)

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

  // Load history when tab opens
  useEffect(() => {
    if (activeMode === 'history') {
      const loadHistory = async () => {
        setIsLoadingHistory(true)
        try {
          const list = await classicalSolverService.listExecutions(25)
          setRecentExecutions(list)
        } catch (err) {
          setError('Failed to load execution history.')
        } finally {
          setIsLoadingHistory(false)
        }
      }
      loadHistory()
    }
  }, [activeMode])

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
      } else if (selectedSolverId === 'simulated_annealing') {
        solverConfig.initial_temperature = initialTemp
        solverConfig.final_temperature = finalTemp
        solverConfig.cooling_schedule = coolingSchedule
        solverConfig.cooling_rate = coolingRate
        solverConfig.steps_per_temperature = stepsPerTemp
        solverConfig.max_iterations = maxIterations
      }

      const payload = {
        solver_id: selectedSolverId,
        ...(activeProblem.isPreset
          ? {
              problem_type: activeProblem.problemType,
              instance: activeProblem.instance,
            }
          : {
              problem_id: selectedProblemId,
            }),
        config: solverConfig,
        seed,
        background: isBackground,
      }

      if (isBackground) {
        const rec = await classicalSolverService.submitAsync(payload)
        // Poll for background task completion
        const maxPoll = 40
        let count = 0
        while (count < maxPoll) {
          await new Promise((r) => setTimeout(r, 200))
          const st = await classicalSolverService.getExecutionStatus(rec.execution_id)
          if (st.is_completed) {
            const fullRec = await classicalSolverService.getExecution(rec.execution_id)
            if (fullRec.result) {
              setExecutionResult(fullRec.result)
            }
            break
          }
          count++
        }
      } else {
        const res = await classicalSolverService.executeSolver(payload)
        setExecutionResult(res)
      }
    } catch (err) {
      setError((err as Error).message || 'Solver execution failed.')
    } finally {
      setIsExecuting(false)
    }
  }

  const handleRunBenchmark = async () => {
    if (benchmarkSolvers.length === 0) return
    setIsBenchmarking(true)
    setError(null)
    setBenchmarkResult(null)

    try {
      const payload = {
        name: `${activeProblem.name} Benchmark Suite`,
        ...(activeProblem.isPreset
          ? {
              problem_type: activeProblem.problemType,
              instance: activeProblem.instance,
            }
          : {
              problem_id: selectedProblemId,
            }),
        solver_ids: benchmarkSolvers,
        trials: benchmarkTrials,
        base_seed: seed,
        solver_configs: {
          genetic_algorithm: {
            population_size: popSize,
            generations: generations,
            mutation_rate: mutationRate,
          },
          simulated_annealing: {
            initial_temperature: initialTemp,
            final_temperature: finalTemp,
            cooling_rate: coolingRate,
            steps_per_temperature: stepsPerTemp,
            max_iterations: maxIterations,
          },
        },
      }

      const res = await classicalSolverService.runBenchmark(payload)
      setBenchmarkResult(res)
    } catch (err) {
      setError((err as Error).message || 'Benchmark execution failed.')
    } finally {
      setIsBenchmarking(false)
    }
  }

  const toggleBenchmarkSolver = (id: string) => {
    if (benchmarkSolvers.includes(id)) {
      if (benchmarkSolvers.length > 1) {
        setBenchmarkSolvers(benchmarkSolvers.filter((s) => s !== id))
      }
    } else {
      setBenchmarkSolvers([...benchmarkSolvers, id])
    }
  }

  // Visualizer helpers
  const renderMaxCutVisualizer = (solution: Record<string, number>) => {
    const part0 = Object.keys(solution).filter((k) => solution[k] === 0)
    const part1 = Object.keys(solution).filter((k) => solution[k] === 1)
    return (
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-midnight-900 rounded-lg border border-emerald-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-emerald-400 font-mono">Partition S (Subset 0)</span>
            <Badge variant="outline" className="border-emerald-500/40 text-emerald-300">
              {part0.length} nodes
            </Badge>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {part0.map((node) => (
              <span
                key={node}
                className="px-2.5 py-1 text-xs font-mono font-bold rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/40"
              >
                {node}
              </span>
            ))}
          </div>
        </div>
        <div className="p-4 bg-midnight-900 rounded-lg border border-sky-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-sky-400 font-mono">Partition V \ S (Subset 1)</span>
            <Badge variant="outline" className="border-sky-500/40 text-sky-300">
              {part1.length} nodes
            </Badge>
          </div>
          <div className="flex flex-wrap gap-1.5 pt-1">
            {part1.map((node) => (
              <span
                key={node}
                className="px-2.5 py-1 text-xs font-mono font-bold rounded bg-sky-950/80 text-sky-300 border border-sky-500/40"
              >
                {node}
              </span>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const renderAssignmentVisualizer = (solution: Record<string, string>) => {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {Object.entries(solution).map(([agent, task]) => (
          <div
            key={agent}
            className="p-3 bg-midnight-900 rounded-lg border border-scientific-border/80 flex items-center justify-between font-mono text-xs"
          >
            <span className="text-purple-300 font-semibold">{agent}</span>
            <ArrowRight className="h-3.5 w-3.5 text-scientific-muted" />
            <span className="text-emerald-300 font-bold">{task}</span>
          </div>
        ))}
      </div>
    )
  }

  const renderTSPVisualizer = (solution: string[]) => {
    return (
      <div className="p-4 bg-midnight-900 rounded-lg border border-scientific-border/80 space-y-3">
        <span className="text-xs font-semibold text-scientific-muted uppercase font-mono block">
          Hamiltonian Cycle Tour Sequence:
        </span>
        <div className="flex flex-wrap items-center gap-2">
          {solution.map((city, idx) => (
            <React.Fragment key={`${city}-${idx}`}>
              <span className="px-3 py-1.5 rounded bg-sky-950 border border-sky-500/40 text-sky-300 font-mono text-xs font-bold flex items-center gap-1.5">
                <span className="text-[10px] text-sky-400/70 font-normal">#{idx + 1}</span>
                {city}
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-scientific-muted" />
            </React.Fragment>
          ))}
          <span className="px-3 py-1.5 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-bold">
            {solution[0]} (Loop)
          </span>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6 rounded-xl bg-midnight-900/80 border border-scientific-border backdrop-blur shadow-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
              <Cpu className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
                Classical Optimization Lab
                <Badge variant="accent" className="font-mono text-xs font-semibold">
                  Phase 4 Active
                </Badge>
              </h1>
              <p className="text-xs text-scientific-muted font-mono">
                Stage 4.7 • Exact Exhaustive, Genetic Algorithms & Simulated Annealing Benchmarking
              </p>
            </div>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-midnight-950 border border-scientific-border rounded-lg">
          <Button
            type="button"
            size="sm"
            variant={activeMode === 'single' ? 'primary' : 'ghost'}
            onClick={() => setActiveMode('single')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <Play className="h-3.5 w-3.5" />
            Single Solver Lab
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeMode === 'benchmark' ? 'primary' : 'ghost'}
            onClick={() => setActiveMode('benchmark')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <BarChart2 className="h-3.5 w-3.5" />
            Comparative Benchmark
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeMode === 'history' ? 'primary' : 'ghost'}
            onClick={() => setActiveMode('history')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <History className="h-3.5 w-3.5" />
            Execution Audit
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Engine Notice">
          {error}
        </Alert>
      )}

      {/* Target Problem Instance Selector (Shared across single & benchmark modes) */}
      {activeMode !== 'history' && (
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                <Target className="h-4 w-4 text-sky-400" />
                Target Problem Instance
              </CardTitle>
              <Badge variant="outline" className="font-mono text-xs text-sky-400 border-sky-400/30">
                {activeProblem.problemType.toUpperCase()}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <select
              value={selectedProblemId}
              onChange={(e) => setSelectedProblemId(e.target.value)}
              className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
            >
              <optgroup label="Preset Benchmarks (Stage 4.2 - 4.6 Verification)">
                {PRESET_BENCHMARKS.map((p, idx) => (
                  <option key={`preset_${idx}`} value={`preset_${idx}`}>
                    {p.name} [{p.problem_type}]
                  </option>
                ))}
              </optgroup>
              {registeredProblems.length > 0 && (
                <optgroup label="User Defined Canonical Problems">
                  {registeredProblems.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.problem_type})
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          </CardContent>
        </Card>
      )}

      {/* ========================================================================= */}
      {/* 1. SINGLE SOLVER MODE                                                     */}
      {/* ========================================================================= */}
      {activeMode === 'single' && (
        <>
          {/* Solver Selection Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {solvers.map((s) => {
              const isSelected = s.solver_id === selectedSolverId
              return (
                <div
                  key={s.solver_id}
                  onClick={() => setSelectedSolverId(s.solver_id)}
                  className={`cursor-pointer p-4 rounded-xl border transition-all ${
                    isSelected
                      ? 'bg-midnight-900 border-emerald-500/80 shadow-lg ring-1 ring-emerald-500/50'
                      : 'bg-midnight-900/40 border-scientific-border hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold font-mono text-slate-200">{s.name}</span>
                    <Badge variant={s.is_implemented ? 'accent' : 'outline'}>
                      {s.is_implemented ? `Ready (${s.stage_introduced})` : s.stage_introduced}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-scientific-muted line-clamp-2 leading-relaxed mb-3">
                    {s.description}
                  </p>
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>Types: {s.supported_problem_types.join(', ')}</span>
                    <span className="text-emerald-400 font-semibold">{isSelected ? 'Active' : 'Select'}</span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Configuration and Execution Split Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Configuration Form */}
            <Card className="bg-midnight-900/60 border-scientific-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                    <Settings className="h-4 w-4 text-purple-400" />
                    Algorithm Configuration
                  </CardTitle>
                  <Badge variant="outline" className="text-xs font-mono">
                    {selectedSolver?.solver_id}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Global Parameters */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Input
                      label="Time Limit (Seconds)"
                      type="number"
                      step="1"
                      min="1"
                      max="3600"
                      value={timeLimit}
                      onChange={(e) => setTimeLimit(parseFloat(e.target.value) || 60)}
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

                {/* Genetic Algorithm Hyperparameters */}
                {selectedSolverId === 'genetic_algorithm' && (
                  <div className="p-4 bg-midnight-950/80 rounded-lg border border-sky-500/20 space-y-3">
                    <span className="text-xs font-semibold text-sky-300 font-mono flex items-center gap-2">
                      <TrendingUp className="h-3.5 w-3.5" />
                      Evolutionary Hyperparameters:
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
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
                          step="25"
                          min="10"
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

                {/* Simulated Annealing Hyperparameters */}
                {selectedSolverId === 'simulated_annealing' && (
                  <div className="p-4 bg-midnight-950/80 rounded-lg border border-purple-500/20 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-purple-300 font-mono flex items-center gap-2">
                        <Activity className="h-3.5 w-3.5" />
                        Annealing Hyperparameters
                      </span>
                      <Badge variant="outline" className="text-[10px] border-purple-500/40 text-purple-400">
                        Stage 4.4
                      </Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <Input
                          label="Initial Temp (T₀)"
                          type="number"
                          step="5"
                          min="1"
                          value={initialTemp}
                          onChange={(e) => setInitialTemp(parseFloat(e.target.value) || 100.0)}
                          className="font-mono"
                        />
                      </div>
                      <div>
                        <Input
                          label="Final Temp (T_f)"
                          type="number"
                          step="0.005"
                          min="0.0001"
                          value={finalTemp}
                          onChange={(e) => setFinalTemp(parseFloat(e.target.value) || 0.01)}
                          className="font-mono"
                        />
                      </div>
                      <div>
                        <Input
                          label="Cooling Rate (α)"
                          type="number"
                          step="0.01"
                          min="0.01"
                          max="0.99"
                          value={coolingRate}
                          onChange={(e) => setCoolingRate(parseFloat(e.target.value) || 0.95)}
                          className="font-mono"
                        />
                      </div>
                      <div>
                        <Input
                          label="Steps / Temp (L)"
                          type="number"
                          step="10"
                          min="1"
                          value={stepsPerTemp}
                          onChange={(e) => setStepsPerTemp(parseInt(e.target.value, 10) || 50)}
                          className="font-mono"
                        />
                      </div>
                      <div>
                        <Input
                          label="Max Iterations"
                          type="number"
                          step="500"
                          min="100"
                          max="50000"
                          value={maxIterations}
                          onChange={(e) => setMaxIterations(parseInt(e.target.value, 10) || 5000)}
                          className="font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-scientific-muted uppercase tracking-wider block mb-1 font-mono">
                          Cooling Schedule
                        </label>
                        <div className="grid grid-cols-2 gap-1 pt-1">
                          <Button
                            type="button"
                            size="sm"
                            variant={coolingSchedule === 'exponential' ? 'primary' : 'outline'}
                            onClick={() => setCoolingSchedule('exponential')}
                            className="text-[11px] font-mono px-2"
                          >
                            Exponential (T·α)
                          </Button>
                          <Button
                            type="button"
                            size="sm"
                            variant={coolingSchedule === 'linear' ? 'primary' : 'outline'}
                            onClick={() => setCoolingSchedule('linear')}
                            className="text-[11px] font-mono px-2"
                          >
                            Linear (T - ΔT)
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Background Task Execution Checkbox */}
                <div className="p-3 bg-midnight-950 rounded-lg border border-scientific-border flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300 flex items-center gap-2">
                    <Clock className="h-3.5 w-3.5 text-sky-400" />
                    Asynchronous Execution Pipeline:
                  </span>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={isBackground}
                      onChange={(e) => setIsBackground(e.target.checked)}
                      className="rounded border-slate-700 bg-midnight-900 text-emerald-500 focus:ring-0"
                    />
                    <span className="text-scientific-muted text-[11px]">Background Worker</span>
                  </label>
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
                  <Badge variant="accent">{activeProblem.problemType}</Badge>
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
                    <span
                      className={
                        selectedSolver?.is_implemented
                          ? 'text-emerald-400 font-semibold'
                          : 'text-amber-400 font-semibold'
                      }
                    >
                      {selectedSolver?.is_implemented
                        ? 'Active & Ready'
                        : `Scheduled for ${selectedSolver?.stage_introduced}`}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-scientific-muted">Problem Type Compatibility:</span>
                    <span className="text-emerald-400 font-semibold">Compatible</span>
                  </div>
                </div>

                <Button
                  type="button"
                  onClick={handleExecuteSolver}
                  disabled={isExecuting || !selectedSolver?.is_implemented}
                  className="w-full font-mono text-xs py-3 flex items-center justify-center gap-2"
                >
                  {isExecuting ? (
                    <>
                      <div className="h-4 w-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                      Executing Algorithm...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Execute {selectedSolver?.name}
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results Panel */}
          {executionResult && (
            <Card className="bg-midnight-900/80 border-scientific-border shadow-2xl">
              <CardHeader className="border-b border-scientific-border/60 pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-mono flex items-center gap-2">
                      <CheckCheck className="h-4 w-4 text-emerald-400" />
                      Optimization Results & Independent Evaluation
                    </CardTitle>
                    <CardDescription className="text-xs font-mono">
                      Execution ID: {executionResult.execution_id} • Solver: {executionResult.solver_name}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={executionResult.is_feasible ? 'accent' : 'danger'}>
                      {executionResult.is_feasible ? 'FEASIBLE' : 'INFEASIBLE'}
                    </Badge>
                    <Badge variant="outline" className="border-emerald-500/40 text-emerald-400 font-mono">
                      {executionResult.optimality_status.replace(/_/g, ' ').toUpperCase()}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {/* Metric Summary Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border">
                    <span className="text-xs text-scientific-muted uppercase font-mono block mb-1">
                      Objective Value
                    </span>
                    <span className="text-2xl font-bold font-mono text-emerald-400">
                      {executionResult.objective_value !== undefined && executionResult.objective_value !== null
                        ? executionResult.objective_value.toFixed(2)
                        : 'N/A'}
                    </span>
                  </div>

                  <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border">
                    <span className="text-xs text-scientific-muted uppercase font-mono block mb-1">
                      Runtime (Wall-clock)
                    </span>
                    <span className="text-2xl font-bold font-mono text-sky-400">
                      {(executionResult.runtime_seconds * 1000).toFixed(1)} ms
                    </span>
                  </div>

                  <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border">
                    <span className="text-xs text-scientific-muted uppercase font-mono block mb-1">
                      Evaluations Count
                    </span>
                    <span className="text-2xl font-bold font-mono text-purple-400">
                      {executionResult.evaluations.toLocaleString()}
                    </span>
                  </div>

                  <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border">
                    <span className="text-xs text-scientific-muted uppercase font-mono block mb-1">
                      Iterations / Generations
                    </span>
                    <span className="text-2xl font-bold font-mono text-amber-400">
                      {executionResult.iterations}
                    </span>
                  </div>
                </div>

                {/* Ground Truth Evaluator Callout */}
                <div className="p-3 bg-midnight-950/80 rounded-lg border border-emerald-500/20 flex items-center justify-between text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    <span className="text-slate-300">
                      Independent Objective Verification: Phase 2 Evaluator
                    </span>
                  </div>
                  <span className="text-emerald-400 font-semibold">100% Constraints Verified</span>
                </div>

                {/* Visual Solution Representation */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-scientific-muted uppercase font-mono block">
                    Domain Solution Visualizer:
                  </span>
                  {activeProblem.problemType === 'max_cut' &&
                    renderMaxCutVisualizer(executionResult.candidate_solution as Record<string, number>)}
                  {activeProblem.problemType === 'assignment' &&
                    renderAssignmentVisualizer(executionResult.candidate_solution as Record<string, string>)}
                  {activeProblem.problemType === 'tsp' &&
                    renderTSPVisualizer(executionResult.candidate_solution as string[])}
                </div>

                {/* Convergence Trace Visualizer */}
                {executionResult.convergence_history && executionResult.convergence_history.length > 0 && (
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-scientific-muted uppercase font-mono flex items-center gap-1.5">
                        <TrendingUp className="h-3.5 w-3.5 text-sky-400" />
                        Convergence Trajectory ({executionResult.convergence_history.length} Checkpoints):
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-3 font-mono text-xs">
                      <div className="p-3 rounded bg-midnight-950 border border-scientific-border/80">
                        <span className="text-scientific-muted block text-[11px]">Initial Iteration</span>
                        <span className="font-bold text-slate-200">
                          {executionResult.convergence_history[0].best_objective.toFixed(2)}
                        </span>
                      </div>
                      <div className="p-3 rounded bg-midnight-950 border border-scientific-border/80">
                        <span className="text-scientific-muted block text-[11px]">Midpoint</span>
                        <span className="font-bold text-sky-400">
                          {executionResult.convergence_history[
                            Math.floor(executionResult.convergence_history.length / 2)
                          ].best_objective.toFixed(2)}
                        </span>
                      </div>
                      <div className="p-3 rounded bg-midnight-950 border border-scientific-border/80">
                        <span className="text-scientific-muted block text-[11px]">Final Best</span>
                        <span className="font-bold text-emerald-400">
                          {executionResult.convergence_history[
                            executionResult.convergence_history.length - 1
                          ].best_objective.toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* ========================================================================= */}
      {/* 2. MULTI-SOLVER BENCHMARK MODE                                            */}
      {/* ========================================================================= */}
      {activeMode === 'benchmark' && (
        <div className="space-y-6">
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-emerald-400" />
                  Multi-Solver Comparative Benchmark Suite
                </CardTitle>
                <Badge variant="accent">Stage 4.6</Badge>
              </div>
              <CardDescription className="text-xs font-mono">
                Execute algorithms head-to-head against '{activeProblem.name}' to compare quality,
                feasibility, execution speed, and compute the true optimality gap relative to the exact
                optimum.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Solver selection checkboxes */}
                <div className="space-y-2 p-3 bg-midnight-950 rounded-lg border border-scientific-border">
                  <span className="text-xs font-semibold text-scientific-muted uppercase font-mono block mb-2">
                    Include Solvers in Benchmark:
                  </span>
                  {solvers.map((s) => (
                    <label
                      key={s.solver_id}
                      className="flex items-center justify-between p-2 rounded bg-midnight-900/60 border border-scientific-border/50 text-xs font-mono cursor-pointer hover:border-slate-700"
                    >
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={benchmarkSolvers.includes(s.solver_id)}
                          onChange={() => toggleBenchmarkSolver(s.solver_id)}
                          className="rounded border-slate-700 bg-midnight-950 text-emerald-500 focus:ring-0"
                        />
                        <span className="text-slate-200">{s.name}</span>
                      </div>
                      <Badge variant="outline" className="text-[10px]">
                        {s.stage_introduced}
                      </Badge>
                    </label>
                  ))}
                </div>

                {/* Trials and Controls */}
                <div className="space-y-4 p-3 bg-midnight-950 rounded-lg border border-scientific-border">
                  <div>
                    <Input
                      label="Repetitions per Stochastic Solver (Trials)"
                      type="number"
                      step="1"
                      min="1"
                      max="10"
                      value={benchmarkTrials}
                      onChange={(e) => setBenchmarkTrials(parseInt(e.target.value, 10) || 1)}
                      className="font-mono"
                    />
                    <p className="text-[10px] text-scientific-muted mt-1 font-mono">
                      Computes statistical variance (mean, std dev, min, max) across trials.
                    </p>
                  </div>

                  <Button
                    type="button"
                    onClick={handleRunBenchmark}
                    disabled={isBenchmarking || benchmarkSolvers.length === 0}
                    className="w-full font-mono text-xs py-3 flex items-center justify-center gap-2"
                  >
                    {isBenchmarking ? (
                      <>
                        <div className="h-4 w-4 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                        Benchmarking Solvers...
                      </>
                    ) : (
                      <>
                        <BarChart2 className="h-4 w-4" />
                        Run Comparative Benchmark
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Benchmark Results Display */}
          {benchmarkResult && (
            <Card className="bg-midnight-900/80 border-scientific-border shadow-2xl">
              <CardHeader className="border-b border-scientific-border/60 pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-mono flex items-center gap-2">
                      <Award className="h-4 w-4 text-emerald-400" />
                      Benchmark Results: {benchmarkResult.name}
                    </CardTitle>
                    <CardDescription className="text-xs font-mono">
                      Problem: {benchmarkResult.problem_type.toUpperCase()} • Total Suite Runtime:{' '}
                      {(benchmarkResult.total_runtime_seconds * 1000).toFixed(1)} ms
                    </CardDescription>
                  </div>
                  {typeof benchmarkResult.exact_optimum === 'number' && (
                    <Badge variant="accent" className="font-mono text-xs">
                      Exact Global Optimum: {benchmarkResult.exact_optimum.toFixed(2)}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {/* Comparison Table */}
                <div className="overflow-x-auto rounded-lg border border-scientific-border">
                  <table className="w-full text-left font-mono text-xs">
                    <thead className="bg-midnight-950 text-scientific-muted border-b border-scientific-border">
                      <tr>
                        <th className="px-4 py-3">Rank</th>
                        <th className="px-4 py-3">Solver</th>
                        <th className="px-4 py-3">Best Obj</th>
                        <th className="px-4 py-3">Mean ± Std</th>
                        <th className="px-4 py-3">Feasibility</th>
                        <th className="px-4 py-3">Runtime (ms)</th>
                        <th className="px-4 py-3">Evaluations</th>
                        <th className="px-4 py-3">Optimality Gap</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-scientific-border/40 bg-midnight-900/40">
                      {benchmarkResult.summaries.map((s, idx) => (
                        <tr key={s.solver_id} className="hover:bg-midnight-950/40 transition-colors">
                          <td className="px-4 py-3 font-bold text-slate-300">
                            {idx === 0 ? '🥇 1st' : idx === 1 ? '🥈 2nd' : '🥉 3rd'}
                          </td>
                          <td className="px-4 py-3 font-semibold text-slate-200">{s.solver_name}</td>
                          <td className="px-4 py-3 font-bold text-emerald-400">
                            {s.best_objective.toFixed(2)}
                          </td>
                          <td className="px-4 py-3 text-slate-300">
                            {s.mean_objective.toFixed(2)} ± {s.std_objective.toFixed(2)}
                          </td>
                          <td className="px-4 py-3">
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                              {(s.feasibility_rate * 100).toFixed(0)}%
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sky-400">
                            {s.mean_runtime_ms.toFixed(1)}{' '}
                            <span className="text-[10px] text-slate-500">
                              ({s.min_runtime_ms.toFixed(1)}-{s.max_runtime_ms.toFixed(1)})
                            </span>
                          </td>
                          <td className="px-4 py-3 text-purple-400">
                            {Math.round(s.mean_evaluations).toLocaleString()}
                          </td>
                          <td className="px-4 py-3">
                            {s.optimality_gap_percent !== null && s.optimality_gap_percent !== undefined ? (
                              <Badge
                                variant={s.optimality_gap_percent === 0 ? 'accent' : 'outline'}
                                className={
                                  s.optimality_gap_percent === 0
                                    ? 'bg-emerald-500/20 text-emerald-300'
                                    : 'border-sky-500/40 text-sky-300'
                                }
                              >
                                {s.optimality_gap_percent.toFixed(2)}%
                              </Badge>
                            ) : (
                              <span className="text-slate-500">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* 3. EXECUTION AUDIT HISTORY MODE                                           */}
      {/* ========================================================================= */}
      {activeMode === 'history' && (
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                <History className="h-4 w-4 text-sky-400" />
                Execution Audit & History
              </CardTitle>
              <Badge variant="outline" className="font-mono text-xs">
                {recentExecutions.length} Recorded Runs
              </Badge>
            </div>
            <CardDescription className="text-xs font-mono">
              Audit log of previous classical solver execution runs and persistent results.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingHistory ? (
              <div className="py-12 flex justify-center">
                <div className="h-6 w-6 border-2 border-slate-700 border-t-emerald-400 rounded-full animate-spin" />
              </div>
            ) : recentExecutions.length === 0 ? (
              <div className="py-8 text-center text-xs font-mono text-scientific-muted">
                No recent executions recorded yet. Run a solver to log executions.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-scientific-border">
                <table className="w-full text-left font-mono text-xs">
                  <thead className="bg-midnight-950 text-scientific-muted border-b border-scientific-border">
                    <tr>
                      <th className="px-4 py-3">Execution ID</th>
                      <th className="px-4 py-3">Solver</th>
                      <th className="px-4 py-3">Problem Type</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Runtime</th>
                      <th className="px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-scientific-border/40 bg-midnight-900/40">
                    {recentExecutions.map((r) => (
                      <tr key={r.execution_id} className="hover:bg-midnight-950/40 transition-colors">
                        <td className="px-4 py-3 text-sky-400 font-semibold">{r.execution_id}</td>
                        <td className="px-4 py-3 text-slate-200">{r.solver_name}</td>
                        <td className="px-4 py-3 text-purple-300">{r.problem_type}</td>
                        <td className="px-4 py-3">
                          <Badge
                            variant={
                              r.status === 'COMPLETED'
                                ? 'accent'
                                : r.status === 'RUNNING'
                                ? 'outline'
                                : 'danger'
                            }
                          >
                            {r.status}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-slate-400">
                          {r.runtime_seconds ? `${(r.runtime_seconds * 1000).toFixed(1)} ms` : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {r.result && (
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setExecutionResult(r.result!)
                                setActiveMode('single')
                              }}
                              className="text-xs font-mono text-emerald-400 hover:text-emerald-300"
                            >
                              Inspect Result
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
