import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Alert'
import { Input } from '../components/ui/Input'
import {
  ProblemType,
  ProblemResponse,
  QuantumBackendInfo,
  QAOAExecutionResult,
  QAOAExecutionRecord,
  SimulationMode,
  ClassicalOptimizerType,
  ParameterInitializationStrategy,
  HybridBenchmarkResult,
  AdaptiveStrategyType,
  InitializationStrategyType,
  DepthGrowthStrategy,
  OptimizerScheduleType,
  StrategyMetadata,
  AdaptiveQAOARequest,
  AdaptiveQAOAResult,
  AdaptiveExecutionRecord,
  TransferCompatibilityReport,
  TransferParametersResponse,
} from '../types'
import { quantumSolverService, QAOAExecutionPayload } from '../services/quantumSolverService'
import { adaptiveSolverService } from '../services/adaptiveSolverService'
import { problemService } from '../services/problemService'
import {
  Play,
  Settings,
  Activity,
  Clock,
  Target,
  CheckCheck,
  TrendingUp,
  BarChart2,
  History,
  ArrowRight,
  ShieldCheck,
  Layers,
  Cpu,
  RefreshCw,
  XCircle,
  Binary,
  AlertTriangle,
  Info,
  Award,
  Zap,
  GitBranch,
  Sliders,
  Sparkles,
} from 'lucide-react'

// Built-in small benchmark presets
const PRESET_BENCHMARKS = [
  {
    name: 'Max-Cut 3-Node Triangle (3 Qubits)',
    problem_type: 'max_cut' as ProblemType,
    instance: {
      nodes: ['0', '1', '2'],
      edges: [
        ['0', '1', 2.0],
        ['1', '2', 3.0],
        ['0', '2', 1.0],
      ],
    },
  },
  {
    name: 'Max-Cut 4-Node Cycle (4 Qubits)',
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
    name: 'Assignment 2x2 Resource Matching (4 Qubits)',
    problem_type: 'assignment' as ProblemType,
    instance: {
      agents: ['Worker_A', 'Worker_B'],
      tasks: ['Job_1', 'Job_2'],
      cost_matrix: [
        [4.0, 7.0],
        [2.0, 5.0],
      ],
    },
  },
  {
    name: 'TSP 3-City Triangle (9 Qubits)',
    problem_type: 'tsp' as ProblemType,
    instance: {
      cities: ['City_0', 'City_1', 'City_2'],
      distance_matrix: [
        [0.0, 10.0, 15.0],
        [10.0, 0.0, 20.0],
        [15.0, 20.0, 0.0],
      ],
    },
  },
]

type LabTab = 'lab' | 'adaptive' | 'benchmark' | 'history'

export const QuantumLabPage: React.FC = () => {
  // Navigation
  const [activeTab, setActiveTab] = useState<LabTab>('lab')

  // Backends & Problems
  const [backends, setBackends] = useState<QuantumBackendInfo[]>([])
  const [selectedBackendId, setSelectedBackendId] = useState<string>('aer_simulator')
  const [registeredProblems, setRegisteredProblems] = useState<ProblemResponse[]>([])
  const [selectedProblemId, setSelectedProblemId] = useState<string>('preset_0')
  const [historyRecords, setHistoryRecords] = useState<QAOAExecutionRecord[]>([])

  // Execution & Status
  const [isExecuting, setIsExecuting] = useState<boolean>(false)
  const [isBackground, setIsBackground] = useState<boolean>(false)
  const [currentExecutionId, setCurrentExecutionId] = useState<string | null>(null)
  const [pollingStatus, setPollingStatus] = useState<string | null>(null)
  const [executionResult, setExecutionResult] = useState<QAOAExecutionResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Adaptive QAOA State (Phase 6)
  const [adaptiveStrategies, setAdaptiveStrategies] = useState<StrategyMetadata[]>([])
  const [selectedStrategyType, setSelectedStrategyType] = useState<AdaptiveStrategyType>('full_adaptive')
  const [adaptiveInitStrategy, setAdaptiveInitStrategy] = useState<InitializationStrategyType>('linear_ramp')
  const [initialDepth, setInitialDepth] = useState<number>(1)
  const [maxDepth, setMaxDepth] = useState<number>(2)
  const [depthGrowth, setDepthGrowth] = useState<DepthGrowthStrategy>('improvement_triggered')
  const [stagnationPatience, setStagnationPatience] = useState<number>(2)
  const [improvementThreshold, setImprovementThreshold] = useState<number>(0.001)
  const [fourierQOrder, setFourierQOrder] = useState<number>(2)
  const [primaryOptimizer, setPrimaryOptimizer] = useState<ClassicalOptimizerType>('COBYLA')
  const [fallbackOptimizer, setFallbackOptimizer] = useState<ClassicalOptimizerType>('Nelder-Mead')
  const [optimizerSchedule, setOptimizerSchedule] = useState<OptimizerScheduleType>('adaptive_fallback')
  const [maxEvaluationsTotal, setMaxEvaluationsTotal] = useState<number>(60)
  const [adaptiveShots, setAdaptiveShots] = useState<number>(1024)
  const [adaptiveSeed, setAdaptiveSeed] = useState<number>(42)
  const [adaptiveIsBackground, setAdaptiveIsBackground] = useState<boolean>(false)
  const [isAdaptiveExecuting, setIsAdaptiveExecuting] = useState<boolean>(false)
  const [adaptiveExecutionId, setAdaptiveExecutionId] = useState<string | null>(null)
  const [adaptivePollingStatus, setAdaptivePollingStatus] = useState<string | null>(null)
  const [adaptiveExecutionResult, setAdaptiveExecutionResult] = useState<AdaptiveQAOAResult | null>(null)
  const [adaptiveHistory, setAdaptiveHistory] = useState<AdaptiveExecutionRecord[]>([])
  const [adaptiveError, setAdaptiveError] = useState<string | null>(null)

  // Parameter Transfer Lab State (Stage 6.3)
  const [transferSourceGamma, setTransferSourceGamma] = useState<string>('0.35, 0.72')
  const [transferSourceBeta, setTransferSourceBeta] = useState<string>('0.65, 0.28')
  const [transferTargetDepth, setTransferTargetDepth] = useState<number>(3)
  const [transferMethod, setTransferMethod] = useState<'linear_interpolation' | 'layer_padding' | 'adiabatic_extension'>('linear_interpolation')
  const [transferReport, setTransferReport] = useState<TransferCompatibilityReport | null>(null)
  const [transferResult, setTransferResult] = useState<TransferParametersResponse | null>(null)
  const [isTransferring, setIsTransferring] = useState<boolean>(false)

  // Execution History View Mode
  const [historyViewMode, setHistoryViewMode] = useState<'qaoa' | 'adaptive'>('qaoa')

  // Hybrid Benchmarking State (Stage 5.9)
  const [hybridResult, setHybridResult] = useState<HybridBenchmarkResult | null>(null)
  const [isBenchmarking, setIsBenchmarking] = useState<boolean>(false)
  const [benchSolvers, setBenchSolvers] = useState<string[]>([
    'exact',
    'genetic_algorithm',
    'simulated_annealing',
    'qaoa',
  ])
  const [benchTrials, setBenchTrials] = useState<number>(2)

  // QAOA Hyperparameters
  const [pDepth, setPDepth] = useState<number>(1)
  const [shots, setShots] = useState<number>(1024)
  const [simulationMode, setSimulationMode] = useState<SimulationMode>('ideal_shots')
  const [optimizer, setOptimizer] = useState<ClassicalOptimizerType>('COBYLA')
  const [maxIterations, setMaxIterations] = useState<number>(30)
  const [initStrategy, setInitStrategy] = useState<ParameterInitializationStrategy>('linear_ramp')
  const [noiseProbability, setNoiseProbability] = useState<number>(0.01)
  const [seed, setSeed] = useState<number>(42)

  // Resolve active problem instance
  const getActiveProblem = () => {
    if (selectedProblemId.startsWith('preset_')) {
      const idx = parseInt(selectedProblemId.replace('preset_', ''), 10)
      const p = PRESET_BENCHMARKS[idx] || PRESET_BENCHMARKS[0]
      return {
        isPreset: true,
        name: p.name,
        problemType: p.problem_type,
        instance: p.instance,
      }
    }
    const found = registeredProblems.find((p) => p.id === selectedProblemId)
    if (found) {
      return {
        isPreset: false,
        name: found.name,
        problemType: found.problem_type,
        instance: (found as any).instance || {},
      }
    }
    return {
      isPreset: true,
      name: PRESET_BENCHMARKS[0].name,
      problemType: PRESET_BENCHMARKS[0].problem_type,
      instance: PRESET_BENCHMARKS[0].instance,
    }
  }

  const activeProblem = getActiveProblem()

  // Initial Load: backends, problems, execution history
  useEffect(() => {
    const initData = async () => {
      try {
        const [bkList, probList, histList, stratList, adHistList] = await Promise.all([
          quantumSolverService.listBackends().catch(() => []),
          problemService.listProblems().catch(() => []),
          quantumSolverService.listExecutions(30).catch(() => []),
          adaptiveSolverService.listStrategies().catch(() => []),
          adaptiveSolverService.listExecutions(30).catch(() => []),
        ])
        setBackends(bkList)
        if (bkList.length > 0) {
          setSelectedBackendId(bkList[0].backend_id)
        }
        setRegisteredProblems(probList)
        setHistoryRecords(histList)
        setAdaptiveStrategies(stratList)
        setAdaptiveHistory(adHistList)
      } catch (err: any) {
        setError(err.message || 'Failed to initialize Quantum Lab data.')
      }
    }
    initData()
  }, [])

  // Execute QAOA (Sync or Async)
  const handleExecute = async () => {
    setError(null)
    setIsExecuting(true)
    setExecutionResult(null)
    setPollingStatus('Initializing QAOA circuit...')

    const payload: QAOAExecutionPayload = {
      problem_id: activeProblem.isPreset ? undefined : selectedProblemId,
      problem_type: activeProblem.problemType,
      instance: activeProblem.instance,
      config: {
        p_depth: pDepth,
        shots,
        simulation_mode: simulationMode,
        optimizer,
        max_iterations: maxIterations,
        init_strategy: initStrategy,
        noise_probability: simulationMode === 'depolarizing_noise' ? noiseProbability : 0.0,
        seed,
      },
    }

    try {
      if (isBackground) {
        const dispatchResp = await quantumSolverService.submitAsync(payload)
        setCurrentExecutionId(dispatchResp.execution_id)
        setPollingStatus('Task queued in background. Polling execution status...')

        // Poll until completion
        const execId = dispatchResp.execution_id
        let finished = false
        let attempts = 0

        while (!finished && attempts < 60) {
          await new Promise((resolve) => setTimeout(resolve, 1500))
          attempts += 1
          const status = await quantumSolverService.getExecutionStatus(execId)
          setPollingStatus(`Execution Status: ${status.status} (${(status.runtime_seconds || 0).toFixed(2)}s)`)

          if (status.is_completed) {
            finished = true
            const fullRecord = await quantumSolverService.getExecution(execId)
            if (fullRecord.result) {
              setExecutionResult(fullRecord.result)
            } else if (fullRecord.error) {
              setError(`Execution failed: ${fullRecord.error}`)
            }
          }
        }

        if (!finished) {
          setError('Background execution polling timed out after 90 seconds.')
        }

        // Refresh history
        const refreshedHistory = await quantumSolverService.listExecutions(30).catch(() => [])
        setHistoryRecords(refreshedHistory)
      } else {
        setPollingStatus('Simulating QAOA variational loop in Qiskit Aer...')
        const res = await quantumSolverService.executeSync(payload)
        setExecutionResult(res)

        // Refresh history
        const refreshedHistory = await quantumSolverService.listExecutions(30).catch(() => [])
        setHistoryRecords(refreshedHistory)
      }
    } catch (err: any) {
      setError(err.message || 'QAOA execution failed.')
    } finally {
      setIsExecuting(false)
      setPollingStatus(null)
      setCurrentExecutionId(null)
    }
  }

  // Cancel background execution
  const handleCancel = async () => {
    if (!currentExecutionId) return
    try {
      setPollingStatus('Sending cooperative cancellation request...')
      await quantumSolverService.cancelExecution(currentExecutionId)
      setError('QAOA execution was cooperatively cancelled by user.')
    } catch (err: any) {
      setError(err.message || 'Failed to cancel execution.')
    } finally {
      setIsExecuting(false)
      setPollingStatus(null)
      setCurrentExecutionId(null)
    }
  }

  // Load past execution from history
  const handleInspectHistory = (record: QAOAExecutionRecord) => {
    if (record.result) {
      setExecutionResult(record.result)
      setActiveTab('lab')
    }
  }

  // Select Adaptive Strategy Preset
  const handleSelectStrategyPreset = (stratType: AdaptiveStrategyType) => {
    setSelectedStrategyType(stratType)
    if (stratType === 'full_adaptive') {
      setAdaptiveInitStrategy('linear_ramp')
      setDepthGrowth('improvement_triggered')
      setOptimizerSchedule('adaptive_fallback')
      setInitialDepth(1)
      setMaxDepth(3)
    } else if (stratType === 'dynamic_depth') {
      setAdaptiveInitStrategy('linear_ramp')
      setDepthGrowth('improvement_triggered')
      setOptimizerSchedule('static')
      setInitialDepth(1)
      setMaxDepth(3)
    } else if (stratType === 'fourier') {
      setAdaptiveInitStrategy('fourier')
      setDepthGrowth('none')
      setOptimizerSchedule('static')
      setInitialDepth(2)
      setMaxDepth(2)
      setFourierQOrder(2)
    } else if (stratType === 'warm_start') {
      setAdaptiveInitStrategy('warm_start')
      setDepthGrowth('fixed_incremental')
      setOptimizerSchedule('static')
      setInitialDepth(1)
      setMaxDepth(3)
    } else if (stratType === 'adaptive_optimizer') {
      setAdaptiveInitStrategy('linear_ramp')
      setDepthGrowth('none')
      setOptimizerSchedule('multi_stage')
      setInitialDepth(2)
      setMaxDepth(2)
    }
  }

  // Execute Adaptive QAOA
  const handleExecuteAdaptive = async () => {
    setAdaptiveError(null)
    setIsAdaptiveExecuting(true)
    setAdaptiveExecutionResult(null)
    setAdaptivePollingStatus('Initializing Adaptive QAOA engine...')

    const req: AdaptiveQAOARequest = {
      problem_id: activeProblem.isPreset ? undefined : selectedProblemId,
      problem_type: activeProblem.problemType,
      instance: activeProblem.instance,
      config: {
        shots: adaptiveShots,
        simulation_mode: 'ideal_shots',
        backend_name: 'aer_simulator',
        seed: adaptiveSeed,
        noise_model_enabled: false,
        noise_error_rate: 0.0,
        time_limit_seconds: 60.0,
        strategy_config: {
          strategy_type: selectedStrategyType,
          init_strategy: adaptiveInitStrategy,
          initial_depth: initialDepth,
          max_depth: maxDepth,
          depth_growth: depthGrowth,
          stagnation_patience: stagnationPatience,
          improvement_threshold: improvementThreshold,
          fourier_q_order: fourierQOrder,
          primary_optimizer: primaryOptimizer,
          fallback_optimizer: fallbackOptimizer,
          optimizer_schedule: optimizerSchedule,
          max_evaluations_total: maxEvaluationsTotal,
        },
      },
    }

    try {
      if (adaptiveIsBackground) {
        const dispatchResp = await adaptiveSolverService.executeAsync(req)
        setAdaptiveExecutionId(dispatchResp.execution_id)
        setAdaptivePollingStatus('Adaptive optimization running in background worker pool...')

        const execId = dispatchResp.execution_id
        let finished = false
        let attempts = 0

        while (!finished && attempts < 60) {
          await new Promise((resolve) => setTimeout(resolve, 1500))
          attempts += 1
          const status = await adaptiveSolverService.getStatus(execId)
          setAdaptivePollingStatus(
            `Status: ${status.status} • Depth: p=${status.current_depth} • Active: ${status.active_optimizer} (${(status.runtime_seconds || 0).toFixed(2)}s)`
          )

          if (status.is_completed) {
            finished = true
            const fullRecord = await adaptiveSolverService.getExecution(execId)
            if (fullRecord.result) {
              setAdaptiveExecutionResult(fullRecord.result)
            } else if (fullRecord.error) {
              setAdaptiveError(`Adaptive QAOA failed: ${fullRecord.error}`)
            }
          }
        }

        if (!finished) {
          setAdaptiveError('Background adaptive execution polling timed out after 90 seconds.')
        }

        const refreshed = await adaptiveSolverService.listExecutions(30).catch(() => [])
        setAdaptiveHistory(refreshed)
      } else {
        setAdaptivePollingStatus('Simulating Adaptive QAOA variational loop in Qiskit Aer...')
        const res = await adaptiveSolverService.executeSync(req)
        setAdaptiveExecutionResult(res)

        const refreshed = await adaptiveSolverService.listExecutions(30).catch(() => [])
        setAdaptiveHistory(refreshed)
      }
    } catch (err: any) {
      setAdaptiveError(err.message || 'Adaptive QAOA execution failed.')
    } finally {
      setIsAdaptiveExecuting(false)
      setAdaptivePollingStatus(null)
      setAdaptiveExecutionId(null)
    }
  }

  // Cancel background adaptive execution
  const handleCancelAdaptive = async () => {
    if (!adaptiveExecutionId) return
    try {
      setAdaptivePollingStatus('Sending cancellation request...')
      await adaptiveSolverService.cancelExecution(adaptiveExecutionId)
      setAdaptiveError('Adaptive QAOA execution cancelled by user.')
    } catch (err: any) {
      setAdaptiveError(err.message || 'Failed to cancel execution.')
    } finally {
      setIsAdaptiveExecuting(false)
      setAdaptivePollingStatus(null)
      setAdaptiveExecutionId(null)
    }
  }

  // Inspect past adaptive execution
  const handleInspectAdaptiveHistory = (record: AdaptiveExecutionRecord) => {
    if (record.result) {
      setAdaptiveExecutionResult(record.result)
      setActiveTab('adaptive')
    }
  }

  // Parameter Transfer Utilities
  const parseAngles = (str: string): number[] => {
    return str
      .split(',')
      .map((s) => parseFloat(s.trim()))
      .filter((n) => !isNaN(n))
  }

  const handleCheckTransfer = async () => {
    try {
      setIsTransferring(true)
      const gamma = parseAngles(transferSourceGamma)
      const beta = parseAngles(transferSourceBeta)
      const res = await adaptiveSolverService.checkTransfer({
        source_depth: gamma.length,
        target_depth: transferTargetDepth,
        source_gamma: gamma,
        source_beta: beta,
        interpolation_method: transferMethod,
      })
      setTransferReport(res)
    } catch (err: any) {
      setAdaptiveError(err.message || 'Transfer check failed.')
    } finally {
      setIsTransferring(false)
    }
  }

  const handleExecuteTransfer = async () => {
    try {
      setIsTransferring(true)
      const gamma = parseAngles(transferSourceGamma)
      const beta = parseAngles(transferSourceBeta)
      const res = await adaptiveSolverService.transferParameters({
        source_depth: gamma.length,
        target_depth: transferTargetDepth,
        source_gamma: gamma,
        source_beta: beta,
        interpolation_method: transferMethod,
      })
      setTransferResult(res)
    } catch (err: any) {
      setAdaptiveError(err.message || 'Transfer execution failed.')
    } finally {
      setIsTransferring(false)
    }
  }

  // Run Hybrid Benchmark Suite (Stage 5.9)
  const handleRunHybridBenchmark = async () => {
    setError(null)
    setIsBenchmarking(true)
    setHybridResult(null)

    try {
      const res = await quantumSolverService.runHybridBenchmark({
        name: `Hybrid Quantum-Classical Benchmark - ${activeProblem.name}`,
        problem_id: activeProblem.isPreset ? undefined : selectedProblemId,
        problem_type: activeProblem.problemType,
        instance: activeProblem.instance,
        include_solvers: benchSolvers,
        qaoa_config: {
          p_depth: pDepth,
          shots,
          optimizer,
          max_iterations: maxIterations,
          seed,
        },
        trials: benchTrials,
        base_seed: seed,
      })
      setHybridResult(res)
    } catch (err: any) {
      setError(err.message || 'Hybrid benchmark failed.')
    } finally {
      setIsBenchmarking(false)
    }
  }

  // Render Domain-Specific Solution
  const renderDomainSolution = (sample: any) => {
    const sol = sample.decoded_solution || {}

    if (activeProblem.problemType === 'max_cut') {
      const partS: string[] = sample.partition_s || sol.partition_s || []
      const partVminusS: string[] = sample.partition_v_minus_s || sol.partition_v_minus_s || []
      const cutVal = sample.cut_value ?? sol.cut_value ?? sample.objective_value

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-midnight-950 border border-scientific-border">
            <span className="text-xs font-mono text-slate-300">Total Cut Weight:</span>
            <span className="text-sm font-mono font-bold text-emerald-400">
              {typeof cutVal === 'number' ? cutVal.toFixed(2) : cutVal}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30 space-y-2">
              <span className="text-xs font-mono font-semibold text-emerald-300 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Partition Set S ({partS.length} nodes)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {partS.map((node) => (
                  <span
                    key={node}
                    className="px-2 py-0.5 rounded bg-emerald-900/60 border border-emerald-500/40 text-emerald-200 font-mono text-xs"
                  >
                    {node}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-sky-950/30 border border-sky-500/30 space-y-2">
              <span className="text-xs font-mono font-semibold text-sky-300 flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-sky-400" />
                Partition Set V \ S ({partVminusS.length} nodes)
              </span>
              <div className="flex flex-wrap gap-1.5">
                {partVminusS.map((node) => (
                  <span
                    key={node}
                    className="px-2 py-0.5 rounded bg-sky-900/60 border border-sky-500/40 text-sky-200 font-mono text-xs"
                  >
                    {node}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )
    }

    if (activeProblem.problemType === 'assignment') {
      const pairs: [string, string][] = sample.matching_pairs || sol.matching_pairs || []
      const totalCost = sample.total_cost ?? sol.total_cost ?? sample.objective_value

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-midnight-950 border border-scientific-border">
            <span className="text-xs font-mono text-slate-300">Total Assignment Cost:</span>
            <span className="text-sm font-mono font-bold text-sky-400">
              {typeof totalCost === 'number' ? totalCost.toFixed(2) : totalCost}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {pairs.map(([agent, task], idx) => (
              <div
                key={idx}
                className="p-3 rounded-lg bg-midnight-950 border border-sky-500/30 flex items-center justify-between text-xs font-mono"
              >
                <span className="text-sky-300 font-semibold">{agent}</span>
                <ArrowRight className="h-3.5 w-3.5 text-scientific-muted" />
                <span className="text-emerald-300 font-semibold">{task}</span>
              </div>
            ))}
          </div>
        </div>
      )
    }

    if (activeProblem.problemType === 'tsp') {
      const tour: string[] = sample.tour || sol.tour || []
      const tourLen = sample.tour_length ?? sol.tour_length ?? sample.objective_value

      return (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg bg-midnight-950 border border-scientific-border">
            <span className="text-xs font-mono text-slate-300">Total Tour Length:</span>
            <span className="text-sm font-mono font-bold text-purple-400">
              {typeof tourLen === 'number' ? tourLen.toFixed(2) : tourLen}
            </span>
          </div>

          <div className="p-4 bg-midnight-950 rounded-lg border border-purple-500/30 flex flex-wrap items-center gap-2">
            {tour.map((city, idx) => (
              <React.Fragment key={`${city}-${idx}`}>
                <span className="px-3 py-1 rounded bg-purple-950 border border-purple-500/40 text-purple-300 font-mono text-xs font-bold flex items-center gap-1.5">
                  <span className="text-[10px] text-purple-400/70 font-normal">#{idx + 1}</span>
                  {city}
                </span>
                <ArrowRight className="h-3.5 w-3.5 text-scientific-muted" />
              </React.Fragment>
            ))}
            {tour.length > 0 && (
              <span className="px-3 py-1 rounded bg-emerald-950 border border-emerald-500/40 text-emerald-300 font-mono text-xs font-bold">
                {tour[0]} (Loop)
              </span>
            )}
          </div>
        </div>
      )
    }

    return (
      <pre className="p-3 bg-midnight-950 rounded text-xs font-mono text-slate-300 overflow-x-auto">
        {JSON.stringify(sol, null, 2)}
      </pre>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 p-6 rounded-xl bg-midnight-900/80 border border-scientific-border backdrop-blur shadow-2xl">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center">
              <Cpu className="h-5 w-5 text-sky-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
                Quantum Optimization Lab
                <Badge variant="accent" className="font-mono text-xs font-semibold">
                  Phase 5 & 6 Active
                </Badge>
              </h1>
              <p className="text-xs text-scientific-muted font-mono">
                Variational Quantum Optimization (QAOA & Adaptive QAOA) • Qiskit Aer Engine
              </p>
            </div>
          </div>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-midnight-950 border border-scientific-border rounded-lg">
          <Button
            type="button"
            size="sm"
            variant={activeTab === 'lab' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('lab')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <Play className="h-3.5 w-3.5" />
            QAOA Simulator
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === 'adaptive' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('adaptive')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <Zap className="h-3.5 w-3.5 text-amber-400" />
            Adaptive QAOA Lab
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === 'benchmark' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('benchmark')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <BarChart2 className="h-3.5 w-3.5" />
            Comparative Benchmark
          </Button>
          <Button
            type="button"
            size="sm"
            variant={activeTab === 'history' ? 'primary' : 'ghost'}
            onClick={() => setActiveTab('history')}
            className="text-xs font-mono flex items-center gap-1.5"
          >
            <History className="h-3.5 w-3.5" />
            Execution Audit ({historyRecords.length + adaptiveHistory.length})
          </Button>
        </div>
      </div>

      {/* Mandatory Scientific Hardware Transparency Banner */}
      <Alert variant="info" title="Scientific Hardware Transparency Notice">
        All executions in this Quantum Lab run on classical simulation backends (Qiskit Aer CPU simulation).
        Quantum statevectors and sampling statistics are computed numerically. No physical quantum hardware speedup
        or quantum supremacy is claimed, adhering strictly to the platform scientific integrity standard.
      </Alert>

      {error && (
        <Alert variant="error" title="Quantum Engine Notice">
          {error}
        </Alert>
      )}

      {/* TAB 1: QAOA SIMULATOR & VISUALIZER */}
      {activeTab === 'lab' && (
        <div className="space-y-6">
          {/* Target Problem Instance Selector */}
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <Target className="h-4 w-4 text-sky-400" />
                  Target Problem Instance & Backend
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono text-xs text-sky-400 border-sky-400/30">
                    {activeProblem.problemType.toUpperCase()}
                  </Badge>
                  <Badge variant="accent" className="font-mono text-xs">
                    {selectedBackendId}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Select Problem Instance</label>
                  <select
                    value={selectedProblemId}
                    onChange={(e) => setSelectedProblemId(e.target.value)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <optgroup label="Preset Benchmarks (Stages 5.1 - 5.7)">
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
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Quantum Backend Target</label>
                  <select
                    value={selectedBackendId}
                    onChange={(e) => setSelectedBackendId(e.target.value)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    {backends.map((b) => (
                      <option key={b.backend_id} value={b.backend_id}>
                        {b.name} (Max {b.max_qubits} Qubits • {b.backend_type})
                      </option>
                    ))}
                    {backends.length === 0 && (
                      <option value="aer_simulator">Qiskit Aer Simulator (Classical AerSimulator)</option>
                    )}
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Hyperparameters & Circuit Preview Split Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: QAOA Configuration Form */}
            <Card className="bg-midnight-900/60 border-scientific-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                    <Settings className="h-4 w-4 text-purple-400" />
                    QAOA Ansatz & Optimizer Parameters
                  </CardTitle>
                  <Badge variant="outline" className="text-xs font-mono">
                    Depth p = {pDepth}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* p depth & shots */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1">
                      Ansatz Depth (p layers): {pDepth}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      step="1"
                      value={pDepth}
                      onChange={(e) => setPDepth(parseInt(e.target.value, 10))}
                      className="w-full h-2 bg-midnight-950 rounded-lg appearance-none cursor-pointer accent-sky-400"
                    />
                    <span className="text-[10px] text-scientific-muted font-mono">Alternating (H_C, H_M) blocks</span>
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1">
                      Measurement Shots: {shots}
                    </label>
                    <input
                      type="range"
                      min="100"
                      max="10000"
                      step="100"
                      value={shots}
                      onChange={(e) => setShots(parseInt(e.target.value, 10))}
                      className="w-full h-2 bg-midnight-950 rounded-lg appearance-none cursor-pointer accent-sky-400"
                    />
                    <span className="text-[10px] text-scientific-muted font-mono">Finite sampling statistics</span>
                  </div>
                </div>

                {/* Simulation Mode & Classical Optimizer */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1.5">Simulation Mode</label>
                    <select
                      value={simulationMode}
                      onChange={(e) => setSimulationMode(e.target.value as SimulationMode)}
                      className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                    >
                      <option value="ideal_shots">Ideal Shots (Sampling Noise)</option>
                      <option value="statevector">Statevector (Exact Expectation)</option>
                      <option value="depolarizing_noise">Depolarizing Noise Model</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1.5">Classical Optimizer</label>
                    <select
                      value={optimizer}
                      onChange={(e) => setOptimizer(e.target.value as ClassicalOptimizerType)}
                      className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                    >
                      <option value="COBYLA">COBYLA (Derivative-free)</option>
                      <option value="SLSQP">SLSQP (Sequential Least Squares)</option>
                      <option value="Nelder-Mead">Nelder-Mead (Simplex)</option>
                      <option value="L-BFGS-B">L-BFGS-B (Bounded quasi-Newton)</option>
                    </select>
                  </div>
                </div>

                {/* Noise rate slider when depolarizing noise active */}
                {simulationMode === 'depolarizing_noise' && (
                  <div className="p-3 bg-amber-950/20 border border-amber-500/30 rounded-lg space-y-2">
                    <label className="block text-xs font-mono text-amber-300">
                      Depolarizing Noise Rate: {(noiseProbability * 100).toFixed(1)}%
                    </label>
                    <input
                      type="range"
                      min="0.001"
                      max="0.05"
                      step="0.001"
                      value={noiseProbability}
                      onChange={(e) => setNoiseProbability(parseFloat(e.target.value))}
                      className="w-full h-2 bg-midnight-950 rounded-lg appearance-none cursor-pointer accent-amber-400"
                    />
                  </div>
                )}

                {/* Optimizer Iterations & Init Strategy */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Input
                      label="Max Optimizer Iterations"
                      type="number"
                      step="5"
                      min="5"
                      max="200"
                      value={maxIterations}
                      onChange={(e) => setMaxIterations(parseInt(e.target.value, 10) || 30)}
                      className="font-mono text-xs"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1.5">Parameter Init Strategy</label>
                    <select
                      value={initStrategy}
                      onChange={(e) => setInitStrategy(e.target.value as ParameterInitializationStrategy)}
                      className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                    >
                      <option value="linear_ramp">Linear Ramp (Trotterized)</option>
                      <option value="random">Random Sampling</option>
                      <option value="zeros">Zeros [0, 0]</option>
                    </select>
                  </div>
                </div>

                {/* Seed and Async Option */}
                <div className="grid grid-cols-2 gap-4 items-center pt-2">
                  <Input
                    label="Reproducibility Seed"
                    type="number"
                    step="1"
                    value={seed}
                    onChange={(e) => setSeed(parseInt(e.target.value, 10) || 42)}
                    className="font-mono text-xs"
                  />

                  <div className="flex items-center gap-2 pt-5">
                    <input
                      type="checkbox"
                      id="bgExec"
                      checked={isBackground}
                      onChange={(e) => setIsBackground(e.target.checked)}
                      className="rounded bg-midnight-950 border-scientific-border text-sky-500 focus:ring-0"
                    />
                    <label htmlFor="bgExec" className="text-xs font-mono text-slate-300 cursor-pointer">
                      Run Asynchronously (Background Thread)
                    </label>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="pt-4 flex items-center gap-3">
                  <Button
                    type="button"
                    onClick={handleExecute}
                    disabled={isExecuting}
                    className="flex-1 text-xs font-mono font-bold flex items-center justify-center gap-2 py-2.5 bg-sky-600 hover:bg-sky-500"
                  >
                    {isExecuting ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin text-white" />
                        Simulating Circuit...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 fill-white text-white" />
                        Execute QAOA Simulation
                      </>
                    )}
                  </Button>

                  {isExecuting && isBackground && (
                    <Button
                      type="button"
                      variant="danger"
                      onClick={handleCancel}
                      className="text-xs font-mono flex items-center gap-1.5"
                    >
                      <XCircle className="h-4 w-4" />
                      Cancel
                    </Button>
                  )}
                </div>

                {pollingStatus && (
                  <div className="p-3 bg-midnight-950 rounded-lg border border-sky-500/30 flex items-center gap-2 text-xs font-mono text-sky-300 animate-pulse">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-sky-400" />
                    <span>{pollingStatus}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Right: Circuit Structural Metadata Preview */}
            <Card className="bg-midnight-900/60 border-scientific-border space-y-4">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                    <Layers className="h-4 w-4 text-emerald-400" />
                    Circuit Blueprint & Resource Bounds
                  </CardTitle>
                  <Badge variant="outline" className="text-xs font-mono text-emerald-400 border-emerald-400/30">
                    Qiskit Aer
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
                    <span className="text-[10px] text-scientific-muted uppercase block">Estimated Qubits:</span>
                    <span className="text-lg font-bold text-slate-100">
                      {activeProblem.problemType === 'max_cut'
                        ? (activeProblem.instance as any).nodes?.length || 3
                        : activeProblem.problemType === 'assignment'
                        ? ((activeProblem.instance as any).agents?.length || 2) ** 2
                        : ((activeProblem.instance as any).cities?.length || 3) ** 2}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
                    <span className="text-[10px] text-scientific-muted uppercase block">Variational Parameters:</span>
                    <span className="text-lg font-bold text-sky-400">
                      2p = {2 * pDepth} (γ, β)
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-midnight-950 rounded-lg border border-scientific-border space-y-2">
                  <span className="text-[10px] text-scientific-muted uppercase block">Gate Decomposition:</span>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                    <div className="flex items-center justify-between">
                      <span>Hadamard (H):</span>
                      <span className="font-bold text-slate-100">n gates</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>R_ZZ(2γ J_ij):</span>
                      <span className="font-bold text-sky-300">p × |E| gates</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>R_Z(2γ h_i):</span>
                      <span className="font-bold text-purple-300">p × |V| gates</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>R_X(2β):</span>
                      <span className="font-bold text-emerald-300">p × n gates</span>
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-midnight-950 rounded-lg border border-scientific-border space-y-1.5">
                  <span className="text-[10px] text-scientific-muted uppercase block">Hardware Safety Guardrails:</span>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Qubit Ceiling (Aer):</span>
                    <span className="text-emerald-400 font-bold">≤ 20 Qubits</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Max Depth (p):</span>
                    <span className="text-emerald-400 font-bold">≤ 10 Layers</span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-slate-400">Shot Ceiling:</span>
                    <span className="text-emerald-400 font-bold">≤ 50,000 Shots</span>
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 italic">
                  * Parameter vector angles: γ ∈ [0, 2π]^p and β ∈ [0, π]^p.
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ========================================================================= */}
          {/* RESULTS DISPLAY                                                           */}
          {/* ========================================================================= */}
          {executionResult && (
            <div className="space-y-6">
              {/* Executive Metrics Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Activity className="h-3 w-3 text-emerald-400" />
                    Status
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-400 mt-1 block">
                    {executionResult.status}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Clock className="h-3 w-3 text-sky-400" />
                    Runtime
                  </span>
                  <span className="text-sm font-bold font-mono text-slate-100 mt-1 block">
                    {executionResult.runtime_seconds.toFixed(3)}s
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Target className="h-3 w-3 text-amber-400" />
                    Best Objective
                  </span>
                  <span className="text-sm font-bold font-mono text-amber-300 mt-1 block">
                    {executionResult.best_sample.objective_value.toFixed(2)}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 text-emerald-400" />
                    Feasible Rate
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-300 mt-1 block">
                    {(executionResult.decoding_summary.feasible_rate * 100).toFixed(1)}%
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <TrendingUp className="h-3 w-3 text-purple-400" />
                    Evaluations
                  </span>
                  <span className="text-sm font-bold font-mono text-purple-300 mt-1 block">
                    {executionResult.total_evaluations} ({executionResult.optimizer_iterations} iters)
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Binary className="h-3 w-3 text-sky-400" />
                    Qubits / Depth
                  </span>
                  <span className="text-sm font-bold font-mono text-sky-300 mt-1 block">
                    {executionResult.circuit_metadata.num_qubits}q • p={executionResult.circuit_metadata.p_depth}
                  </span>
                </Card>
              </div>

              {/* Independent Verification & Constraint Check */}
              <div className="p-4 rounded-xl bg-midnight-900/80 border border-scientific-border space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-200 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    Independent Phase 2 Evaluation Verification
                  </span>
                  <Badge variant={executionResult.is_feasible ? 'accent' : 'warning'}>
                    {executionResult.is_feasible ? '100% FEASIBLE' : 'INFEASIBLE CONSTRAINTS'}
                  </Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono text-scientific-muted">
                  <p>
                    <span className="text-slate-400">Optimization Direction:</span>{' '}
                    <span className="text-slate-200 uppercase font-bold">
                      {executionResult.independent_evaluation?.objective_sense || 'OPTIMIZE'}
                    </span>
                  </p>
                  <p>
                    <span className="text-slate-400">Verified Objective Value:</span>{' '}
                    <span className="text-emerald-400 font-bold">
                      {executionResult.best_sample.objective_value}
                    </span>
                  </p>
                </div>
                {executionResult.constraint_violations.length > 0 && (
                  <div className="p-3 bg-rose-950/30 border border-rose-500/40 rounded-lg text-xs font-mono text-rose-300 space-y-1">
                    <div className="flex items-center gap-1.5 font-bold">
                      <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
                      <span>Violations detected:</span>
                    </div>
                    <ul className="list-disc list-inside">
                      {executionResult.constraint_violations.map((v, i) => (
                        <li key={i}>{v}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Domain Specific Visualizer */}
              <Card className="bg-midnight-900/60 border-scientific-border">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                      <CheckCheck className="h-4 w-4 text-emerald-400" />
                      Decoded Optimal Candidate Solution
                    </CardTitle>
                    <Badge variant="outline" className="font-mono text-xs">
                      Bitstring: {executionResult.best_sample.bitstring}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {renderDomainSolution(executionResult.best_sample)}
                </CardContent>
              </Card>

              {/* Classical Optimizer Convergence & Optimal Parameters */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-midnight-900/60 border-scientific-border">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-sky-400" />
                        Optimizer Energy Convergence ⟨H_C⟩
                      </CardTitle>
                      <Badge variant="outline" className="font-mono text-xs">
                        {executionResult.convergence_history.length} trace points
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1 font-mono text-xs">
                      {executionResult.convergence_history.map((pt) => (
                        <div
                          key={pt.iteration}
                          className="flex items-center justify-between p-2 rounded bg-midnight-950 border border-scientific-border/60"
                        >
                          <span className="text-scientific-muted">Iter #{pt.iteration}</span>
                          <span className="font-bold text-slate-200">
                            ⟨H_C⟩ = {pt.expectation_value.toFixed(4)}
                          </span>
                        </div>
                      ))}
                      {executionResult.convergence_history.length === 0 && (
                        <p className="text-scientific-muted italic">No intermediate trace recorded.</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                        <Settings className="h-4 w-4 text-purple-400" />
                        Optimal Variational Angles (γ*, β*)
                      </CardTitle>
                      <Badge variant="outline" className="font-mono text-xs text-purple-400 border-purple-400/30">
                        {executionResult.termination_reason}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 font-mono text-xs">
                    <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border space-y-1">
                      <span className="text-[10px] text-scientific-muted uppercase block">Optimal Gamma (γ*):</span>
                      <div className="flex flex-wrap gap-2">
                        {executionResult.optimal_gamma.map((g, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-sky-950 border border-sky-500/40 text-sky-300">
                            γ_{i + 1} = {g.toFixed(4)} rad
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border space-y-1">
                      <span className="text-[10px] text-scientific-muted uppercase block">Optimal Beta (β*):</span>
                      <div className="flex flex-wrap gap-2">
                        {executionResult.optimal_beta.map((b, i) => (
                          <span key={i} className="px-2 py-0.5 rounded bg-purple-950 border border-purple-500/40 text-purple-300">
                            β_{i + 1} = {b.toFixed(4)} rad
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border text-[11px] text-slate-300">
                      <span className="text-scientific-muted block text-[10px] uppercase">Final Variational Expectation:</span>
                      <span className="font-bold text-emerald-400 text-sm">
                        {executionResult.optimal_expectation_value.toFixed(4)}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Quantum Measurement Histogram */}
              <Card className="bg-midnight-900/60 border-scientific-border">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                      <BarChart2 className="h-4 w-4 text-emerald-400" />
                      Quantum Bitstring Measurement Distribution
                    </CardTitle>
                    <div className="flex items-center gap-2 text-xs font-mono">
                      <span className="text-scientific-muted">
                        Total Samples: {executionResult.decoding_summary.total_samples}
                      </span>
                      <Badge variant="accent">
                        {executionResult.decoding_summary.unique_samples} Unique States
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-1 gap-2 max-h-80 overflow-y-auto pr-1">
                    {executionResult.decoding_summary.all_decoded_samples.map((s, idx) => {
                      const isBest = s.is_best_feasible
                      const isMostFreq = s.is_most_frequent
                      const percent = (s.probability * 100).toFixed(2)

                      return (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg border font-mono text-xs transition-all ${
                            isBest
                              ? 'bg-emerald-950/40 border-emerald-500 shadow-md ring-1 ring-emerald-500/50'
                              : isMostFreq
                              ? 'bg-sky-950/30 border-sky-500/60'
                              : 'bg-midnight-950 border-scientific-border/80'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1.5">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-slate-100">{s.bitstring}</span>
                              {isBest && (
                                <Badge variant="accent" className="text-[10px]">
                                  ★ Best Feasible Solution
                                </Badge>
                              )}
                              {isMostFreq && (
                                <Badge variant="outline" className="text-[10px] text-sky-400 border-sky-400/40">
                                  Most Frequent
                                </Badge>
                              )}
                              <Badge variant={s.is_feasible ? 'outline' : 'warning'} className="text-[10px]">
                                {s.is_feasible ? 'Feasible' : 'Infeasible'}
                              </Badge>
                            </div>

                            <div className="flex items-center gap-3 text-slate-300">
                              <span>
                                Count: <strong className="text-slate-100">{s.count}</strong> ({percent}%)
                              </span>
                              <span>
                                Obj: <strong className="text-emerald-400">{s.objective_value.toFixed(2)}</strong>
                              </span>
                            </div>
                          </div>

                          {/* Probability Bar */}
                          <div className="w-full bg-midnight-900 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full ${
                                isBest ? 'bg-emerald-400' : isMostFreq ? 'bg-sky-400' : 'bg-slate-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(2, parseFloat(percent)))}%` }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {executionResult.decoding_summary.best_feasible_solution &&
                    executionResult.decoding_summary.most_frequent_solution &&
                    executionResult.decoding_summary.best_feasible_solution.bitstring !==
                      executionResult.decoding_summary.most_frequent_solution.bitstring && (
                      <div className="p-3 bg-amber-950/30 border border-amber-500/40 rounded-lg text-xs font-mono text-amber-300 flex items-center gap-2">
                        <Info className="h-4 w-4 text-amber-400 flex-shrink-0" />
                        <span>
                          <strong>Scientific Note:</strong> The most frequent bitstring (
                          {executionResult.decoding_summary.most_frequent_solution.bitstring}) is not the best
                          feasible solution ({executionResult.decoding_summary.best_feasible_solution.bitstring}).
                          The engine independently evaluated each state and selected the true optimal candidate.
                        </span>
                      </div>
                    )}
                </CardContent>
              </Card>

              {/* Hardware Transparency Footer */}
              <div className="p-4 rounded-xl bg-midnight-950 border border-scientific-border space-y-2 text-xs font-mono text-scientific-muted">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">
                  Backend Transparency Log:
                </span>
                <p>{executionResult.hardware_transparency_note}</p>
                <div className="flex items-center gap-4 text-[10px] text-slate-500 pt-1">
                  <span>Backend ID: {executionResult.backend_info.backend_id}</span>
                  <span>Qiskit: {executionResult.backend_info.qiskit_version || '2.6.1'}</span>
                  <span>Aer: {executionResult.backend_info.aer_version || '0.17.2'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: ADAPTIVE QAOA RESEARCH LAB (Phase 6)                               */}
      {/* ========================================================================= */}
      {activeTab === 'adaptive' && (
        <div className="space-y-6">
          {/* Target Problem Instance & Strategy Selector */}
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-400" />
                  Target Problem Instance & Strategy Preset
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="font-mono text-xs text-amber-400 border-amber-400/30">
                    {activeProblem.problemType.toUpperCase()}
                  </Badge>
                  <Badge variant="accent" className="font-mono text-xs">
                    {selectedBackendId}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Select Problem Instance</label>
                  <select
                    value={selectedProblemId}
                    onChange={(e) => setSelectedProblemId(e.target.value)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <optgroup label="Preset Benchmarks (Stages 5.1 - 5.7)">
                      {PRESET_BENCHMARKS.map((p, idx) => (
                        <option key={`preset_ad_${idx}`} value={`preset_${idx}`}>
                          {p.name} [{p.problem_type}]
                        </option>
                      ))}
                    </optgroup>
                    {registeredProblems.length > 0 && (
                      <optgroup label="User Defined Canonical Problems">
                        {registeredProblems.map((p) => (
                          <option key={`reg_ad_${p.id}`} value={p.id}>
                            {p.name} ({p.problem_type})
                          </option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Simulation Target Backend</label>
                  <div className="px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-emerald-300 flex items-center justify-between">
                    <span>Qiskit Aer Simulator (Classical CPU Emulation)</span>
                    <Badge variant="outline" className="text-[10px] text-emerald-400 border-emerald-500/30">
                      Ideal & Noise Capable
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Research Strategy Preset Buttons */}
              <div className="pt-2">
                <label className="block text-xs font-mono text-slate-300 mb-2">
                  Select Adaptive Architecture Paradigm ({adaptiveStrategies.length > 0 ? `${adaptiveStrategies.length} Backend Strategies Registered` : '6 Built-in Presets'}):
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {[
                    {
                      id: 'full_adaptive' as AdaptiveStrategyType,
                      title: 'Full Adaptive QAOA',
                      desc: 'Dynamic layer growth + warm-start angle transfer + adaptive fallback optimizer.',
                      badge: 'Recommended',
                    },
                    {
                      id: 'dynamic_depth' as AdaptiveStrategyType,
                      title: 'Dynamic Layer Growth',
                      desc: 'Monitors energy stagnation; automatically expands circuit depth p → p+1.',
                      badge: 'Stage 6.5',
                    },
                    {
                      id: 'fourier' as AdaptiveStrategyType,
                      title: 'Fourier Parameterization',
                      desc: 'Optimizes discrete cosine/sine frequency components (u, v) rather than 2p angles.',
                      badge: 'Stage 6.2',
                    },
                    {
                      id: 'warm_start' as AdaptiveStrategyType,
                      title: 'Warm-Start Transfer',
                      desc: 'Transfers and interpolates variational angles across depths or related instances.',
                      badge: 'Stage 6.3',
                    },
                    {
                      id: 'adaptive_optimizer' as AdaptiveStrategyType,
                      title: 'Multi-Stage Optimizer',
                      desc: 'Global coarse search transitioning to high-precision local gradient/simplex descent.',
                      badge: 'Stage 6.4',
                    },
                    {
                      id: 'standard' as AdaptiveStrategyType,
                      title: 'Standard Fixed Depth',
                      desc: 'Fixed-depth baseline QAOA optimization for comparative research.',
                      badge: 'Baseline',
                    },
                  ].map((s) => {
                    const isSelected = selectedStrategyType === s.id
                    return (
                      <div
                        key={s.id}
                        onClick={() => handleSelectStrategyPreset(s.id)}
                        className={`p-3 rounded-lg border cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-amber-950/30 border-amber-500/60 shadow-lg shadow-amber-500/5 ring-1 ring-amber-500/30'
                            : 'bg-midnight-950/60 border-scientific-border hover:border-slate-600'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span
                            className={`text-xs font-mono font-bold ${
                              isSelected ? 'text-amber-300' : 'text-slate-200'
                            }`}
                          >
                            {s.title}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-midnight-900 border border-scientific-border text-slate-400 font-mono">
                            {s.badge}
                          </span>
                        </div>
                        <p className="text-[11px] text-scientific-muted leading-relaxed font-mono">
                          {s.desc}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Hyperparameter Configuration Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Panel 1: Depth Management */}
            <Card className="bg-midnight-900/60 border-scientific-border space-y-4">
              <CardHeader>
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <Layers className="h-4 w-4 text-sky-400" />
                  Dynamic Depth Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 font-mono text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Input
                      label="Initial Depth (p_init)"
                      type="number"
                      min="1"
                      max="10"
                      value={initialDepth}
                      onChange={(e) => setInitialDepth(Math.max(1, parseInt(e.target.value, 10) || 1))}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div>
                    <Input
                      label="Max Depth (p_max)"
                      type="number"
                      min="1"
                      max="10"
                      value={maxDepth}
                      onChange={(e) => setMaxDepth(Math.max(1, Math.min(10, parseInt(e.target.value, 10) || 3)))}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Depth Growth Protocol</label>
                  <select
                    value={depthGrowth}
                    onChange={(e) => setDepthGrowth(e.target.value as DepthGrowthStrategy)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <option value="improvement_triggered">Improvement Triggered (Expand on stagnation)</option>
                    <option value="fixed_incremental">Fixed Incremental (Grow every fixed cycle)</option>
                    <option value="none">None (Fixed Depth Baseline)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Input
                      label="Stagnation Patience"
                      type="number"
                      min="1"
                      max="20"
                      value={stagnationPatience}
                      onChange={(e) => setStagnationPatience(parseInt(e.target.value, 10) || 2)}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div>
                    <Input
                      label="Min Imprv. Threshold (ε)"
                      type="number"
                      step="0.0005"
                      min="0.0001"
                      value={improvementThreshold}
                      onChange={(e) => setImprovementThreshold(parseFloat(e.target.value) || 0.001)}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="p-2.5 rounded bg-midnight-950 border border-sky-500/20 text-[11px] text-slate-400">
                  Depth ceiling enforced: <strong className="text-sky-300">p ≤ 10</strong>. When depth grows, parameters are warm-start interpolated.
                </div>
              </CardContent>
            </Card>

            {/* Panel 2: Classical Optimizer Scheduling */}
            <Card className="bg-midnight-900/60 border-scientific-border space-y-4">
              <CardHeader>
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-purple-400" />
                  Optimizer Scheduling & Arbitration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 font-mono text-xs">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Optimizer Schedule</label>
                  <select
                    value={optimizerSchedule}
                    onChange={(e) => setOptimizerSchedule(e.target.value as OptimizerScheduleType)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <option value="adaptive_fallback">Adaptive Fallback (Switch optimizer on stagnation)</option>
                    <option value="multi_stage">Multi-Stage (Coarse search → Fine local descent)</option>
                    <option value="static">Static (Single fixed classical optimizer)</option>
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1.5">Primary Optimizer</label>
                    <select
                      value={primaryOptimizer}
                      onChange={(e) => setPrimaryOptimizer(e.target.value as ClassicalOptimizerType)}
                      className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                    >
                      <option value="COBYLA">COBYLA</option>
                      <option value="SLSQP">SLSQP</option>
                      <option value="Nelder-Mead">Nelder-Mead</option>
                      <option value="L-BFGS-B">L-BFGS-B</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-mono text-slate-300 mb-1.5">Fallback Optimizer</label>
                    <select
                      value={fallbackOptimizer}
                      onChange={(e) => setFallbackOptimizer(e.target.value as ClassicalOptimizerType)}
                      className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                    >
                      <option value="Nelder-Mead">Nelder-Mead</option>
                      <option value="COBYLA">COBYLA</option>
                      <option value="SLSQP">SLSQP</option>
                      <option value="L-BFGS-B">L-BFGS-B</option>
                    </select>
                  </div>
                </div>

                <div>
                  <Input
                    label="Max Total Evaluations Budget"
                    type="number"
                    min="10"
                    max="500"
                    value={maxEvaluationsTotal}
                    onChange={(e) => setMaxEvaluationsTotal(parseInt(e.target.value, 10) || 60)}
                    className="font-mono text-xs"
                  />
                </div>

                <div className="p-2.5 rounded bg-midnight-950 border border-purple-500/20 text-[11px] text-slate-400">
                  Switch condition: Stagnation over patience window triggers graceful transition to fallback solver.
                </div>
              </CardContent>
            </Card>

            {/* Panel 3: Initialization & Execution Controls */}
            <Card className="bg-midnight-900/60 border-scientific-border space-y-4">
              <CardHeader>
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  Parameter Init & Sampling Controls
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 font-mono text-xs">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Parameter Initialization</label>
                  <select
                    value={adaptiveInitStrategy}
                    onChange={(e) => setAdaptiveInitStrategy(e.target.value as InitializationStrategyType)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <option value="linear_ramp">Linear Ramp (Adiabatic Trotterized schedule)</option>
                    <option value="fourier">Fourier Transform Parameterization (u, v)</option>
                    <option value="warm_start">Warm-Start Interpolation</option>
                    <option value="random">Uniform Random Sampling</option>
                    <option value="zeros">Zeros [0, 0]</option>
                  </select>
                </div>

                {adaptiveInitStrategy === 'fourier' && (
                  <div>
                    <Input
                      label="Fourier Order (q)"
                      type="number"
                      min="1"
                      max="5"
                      value={fourierQOrder}
                      onChange={(e) => setFourierQOrder(parseInt(e.target.value, 10) || 2)}
                      className="font-mono text-xs"
                    />
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Input
                      label="Measurement Shots"
                      type="number"
                      step="256"
                      min="100"
                      max="10000"
                      value={adaptiveShots}
                      onChange={(e) => setAdaptiveShots(parseInt(e.target.value, 10) || 1024)}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div>
                    <Input
                      label="Random Seed"
                      type="number"
                      value={adaptiveSeed}
                      onChange={(e) => setAdaptiveSeed(parseInt(e.target.value, 10) || 42)}
                      className="font-mono text-xs"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="adaptiveBgExec"
                    checked={adaptiveIsBackground}
                    onChange={(e) => setAdaptiveIsBackground(e.target.checked)}
                    className="rounded bg-midnight-950 border-scientific-border text-amber-500 focus:ring-0"
                  />
                  <label htmlFor="adaptiveBgExec" className="text-xs font-mono text-slate-300 cursor-pointer">
                    Run in Background Thread Pool
                  </label>
                </div>

                {/* Launch Button */}
                <div className="pt-2 flex items-center gap-3">
                  <Button
                    type="button"
                    onClick={handleExecuteAdaptive}
                    disabled={isAdaptiveExecuting}
                    className="flex-1 text-xs font-mono font-bold flex items-center justify-center gap-2 py-2.5 bg-amber-600 hover:bg-amber-500 text-slate-900"
                  >
                    {isAdaptiveExecuting ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin text-slate-900" />
                        Optimizing...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4 text-slate-900" />
                        Launch Adaptive QAOA
                      </>
                    )}
                  </Button>

                  {isAdaptiveExecuting && (
                    <Button
                      type="button"
                      variant="danger"
                      onClick={handleCancelAdaptive}
                      className="text-xs font-mono flex items-center gap-1.5"
                    >
                      <XCircle className="h-4 w-4" />
                      Cancel
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Polling / Status Banner */}
          {adaptivePollingStatus && (
            <div className="p-3.5 rounded-xl bg-amber-950/30 border border-amber-500/40 flex items-center gap-3">
              <RefreshCw className="h-4 w-4 animate-spin text-amber-400" />
              <span className="text-xs font-mono text-amber-200">{adaptivePollingStatus}</span>
            </div>
          )}

          {adaptiveError && (
            <Alert variant="error" title="Adaptive QAOA Engine Notice">
              {adaptiveError}
            </Alert>
          )}

          {/* ========================================================================= */}
          {/* ADAPTIVE RESULTS DISPLAY                                                  */}
          {/* ========================================================================= */}
          {adaptiveExecutionResult && (
            <div className="space-y-6">
              {/* Executive Metrics Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Activity className="h-3 w-3 text-emerald-400" />
                    Status
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-400 mt-1 block">
                    {adaptiveExecutionResult.status}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Layers className="h-3 w-3 text-amber-400" />
                    Depth Evolution
                  </span>
                  <span className="text-sm font-bold font-mono text-amber-300 mt-1 block">
                    p = {adaptiveExecutionResult.initial_depth} → {adaptiveExecutionResult.final_depth}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Clock className="h-3 w-3 text-sky-400" />
                    Runtime
                  </span>
                  <span className="text-sm font-bold font-mono text-slate-100 mt-1 block">
                    {adaptiveExecutionResult.execution_time_ms.toFixed(1)} ms
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Target className="h-3 w-3 text-emerald-400" />
                    Best Objective
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-400 mt-1 block">
                    {adaptiveExecutionResult.objective_value.toFixed(2)}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <Award className="h-3 w-3 text-purple-400" />
                    Approx Ratio (r)
                  </span>
                  <span className="text-sm font-bold font-mono text-purple-300 mt-1 block">
                    {adaptiveExecutionResult.approximation_ratio != null
                      ? (adaptiveExecutionResult.approximation_ratio * 100).toFixed(1) + '%'
                      : 'N/A'}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <ShieldCheck className="h-3 w-3 text-emerald-400" />
                    Feasibility
                  </span>
                  <span className="text-sm font-bold font-mono text-emerald-300 mt-1 block">
                    {adaptiveExecutionResult.is_feasible ? '100% FEASIBLE' : 'VIOLATIONS'}
                  </span>
                </Card>

                <Card className="bg-midnight-900/60 border-scientific-border p-3">
                  <span className="text-[10px] font-mono uppercase text-scientific-muted block flex items-center gap-1">
                    <TrendingUp className="h-3 w-3 text-sky-400" />
                    Evaluations
                  </span>
                  <span className="text-sm font-bold font-mono text-sky-300 mt-1 block">
                    {adaptiveExecutionResult.total_evaluations} ({adaptiveExecutionResult.total_circuit_executions} runs)
                  </span>
                </Card>
              </div>

              {/* Independent Solution Verification & Stopping Reason */}
              <div className="p-4 rounded-xl bg-midnight-900/80 border border-scientific-border space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-slate-200 flex items-center gap-2">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    Phase 2 Independent Evaluation & Termination Verification
                  </span>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs font-mono text-amber-400 border-amber-400/30">
                      Stopping: {adaptiveExecutionResult.stopping_reason.toUpperCase()}
                    </Badge>
                    <Badge variant={adaptiveExecutionResult.is_feasible ? 'accent' : 'warning'}>
                      {adaptiveExecutionResult.is_feasible ? 'CONSTRAINTS SATISFIED' : 'VIOLATIONS DETECTED'}
                    </Badge>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono text-scientific-muted">
                  <p>
                    <span className="text-slate-400">Best Bitstring:</span>{' '}
                    <span className="text-slate-100 font-bold px-2 py-0.5 rounded bg-midnight-950 border border-scientific-border">
                      |{adaptiveExecutionResult.best_bitstring}⟩
                    </span>
                  </p>
                  <p>
                    <span className="text-slate-400">Expected Energy ⟨H_C⟩:</span>{' '}
                    <span className="text-purple-300 font-bold">
                      {adaptiveExecutionResult.expected_energy.toFixed(4)}
                    </span>
                  </p>
                  <p>
                    <span className="text-slate-400">Optimality Gap:</span>{' '}
                    <span className="text-emerald-400 font-bold">
                      {adaptiveExecutionResult.optimality_gap_percent != null
                        ? adaptiveExecutionResult.optimality_gap_percent.toFixed(2) + '%'
                        : '0.00%'}
                    </span>
                  </p>
                </div>
              </div>

              {/* Dynamic Parameter Trajectory (γ, β) & Layer Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="bg-midnight-900/60 border-scientific-border">
                  <CardHeader>
                    <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                      <Binary className="h-4 w-4 text-amber-400" />
                      Dynamic Parameter Angles (Final Depth p={adaptiveExecutionResult.final_depth})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3 font-mono text-xs">
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs font-mono text-left">
                        <thead>
                          <tr className="border-b border-scientific-border text-scientific-muted">
                            <th className="pb-2">Layer (l)</th>
                            <th className="pb-2">Gamma (γ_l rad)</th>
                            <th className="pb-2">Beta (β_l rad)</th>
                            <th className="pb-2">Gamma (deg)</th>
                            <th className="pb-2">Beta (deg)</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-scientific-border/40 text-slate-300">
                          {adaptiveExecutionResult.best_gamma.map((g, idx) => {
                            const b = adaptiveExecutionResult.best_beta[idx] ?? 0.0
                            return (
                              <tr key={idx} className="hover:bg-midnight-950/60">
                                <td className="py-2 font-bold text-amber-400">Layer {idx + 1}</td>
                                <td className="py-2 text-sky-300">{g.toFixed(4)}</td>
                                <td className="py-2 text-purple-300">{b.toFixed(4)}</td>
                                <td className="py-2 text-slate-400">{((g * 180) / Math.PI).toFixed(1)}°</td>
                                <td className="py-2 text-slate-400">{((b * 180) / Math.PI).toFixed(1)}°</td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>

                {/* Decoded Domain Solution */}
                <Card className="bg-midnight-900/60 border-scientific-border">
                  <CardHeader>
                    <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                      <CheckCheck className="h-4 w-4 text-emerald-400" />
                      Optimal Candidate Solution Partition
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {renderDomainSolution({
                      decoded_solution: adaptiveExecutionResult.best_solution,
                      objective_value: adaptiveExecutionResult.objective_value,
                      candidate_solution: adaptiveExecutionResult.best_solution,
                    })}
                  </CardContent>
                </Card>
              </div>

              {/* Decision Audit Log Table */}
              <Card className="bg-midnight-900/60 border-scientific-border">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                      <History className="h-4 w-4 text-sky-400" />
                      Adaptive Decision Audit Log ({adaptiveExecutionResult.decisions_log.length} Events)
                    </CardTitle>
                    <Badge variant="outline" className="text-xs font-mono text-sky-400 border-sky-400/30">
                      Scientific Verification
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {adaptiveExecutionResult.decisions_log.length === 0 ? (
                    <p className="text-xs font-mono text-scientific-muted py-4 text-center">
                      No layer growth or optimizer transitions were triggered during this run (converged at initial depth).
                    </p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs font-mono text-left">
                        <thead>
                          <tr className="border-b border-scientific-border text-scientific-muted">
                            <th className="pb-2">Time Offset</th>
                            <th className="pb-2">Transition</th>
                            <th className="pb-2">Trigger Reason</th>
                            <th className="pb-2">Action Summary</th>
                            <th className="pb-2">Active Optimizer</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-scientific-border/40 text-slate-300">
                          {adaptiveExecutionResult.decisions_log.map((d, idx) => (
                            <tr key={idx} className="hover:bg-midnight-950/60">
                              <td className="py-2.5 text-slate-400">{d.timestamp_offset.toFixed(3)}s</td>
                              <td className="py-2.5 font-bold text-amber-400">
                                p={d.from_depth} → p={d.to_depth}
                              </td>
                              <td className="py-2.5">
                                <span className="px-2 py-0.5 rounded bg-midnight-950 border border-scientific-border text-slate-300">
                                  {d.trigger_reason}
                                </span>
                              </td>
                              <td className="py-2.5 text-slate-200">{d.action_summary}</td>
                              <td className="py-2.5 text-purple-300 font-bold">{d.active_optimizer}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Energy Iteration Trajectory */}
              <Card className="bg-midnight-900/60 border-scientific-border">
                <CardHeader>
                  <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-purple-400" />
                    Convergence & Variational Energy Progression ({adaptiveExecutionResult.iterations_log.length} Iterations)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto max-h-64">
                    <table className="w-full text-xs font-mono text-left">
                      <thead>
                        <tr className="border-b border-scientific-border text-scientific-muted sticky top-0 bg-midnight-900">
                          <th className="pb-2">Iter</th>
                          <th className="pb-2">Depth</th>
                          <th className="pb-2">Optimizer</th>
                          <th className="pb-2">Expected Energy ⟨H_C⟩</th>
                          <th className="pb-2">Best Energy</th>
                          <th className="pb-2">Evals</th>
                          <th className="pb-2">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-scientific-border/40 text-slate-300">
                        {adaptiveExecutionResult.iterations_log.map((it) => (
                          <tr key={it.iteration_index} className="hover:bg-midnight-950/60">
                            <td className="py-2 font-bold text-slate-200">#{it.iteration_index}</td>
                            <td className="py-2 text-amber-300">p={it.current_depth}</td>
                            <td className="py-2 text-purple-300">{it.active_optimizer}</td>
                            <td className="py-2 text-slate-100">{it.expected_energy.toFixed(4)}</td>
                            <td className="py-2 font-bold text-emerald-400">{it.best_energy.toFixed(4)}</td>
                            <td className="py-2 text-slate-400">{it.eval_count}</td>
                            <td className="py-2 text-slate-400 text-[11px]">{it.action_taken}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>

              {/* Backend Transparency Card */}
              <div className="p-4 rounded-xl bg-midnight-950 border border-scientific-border space-y-2 text-xs font-mono text-scientific-muted">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">
                  Adaptive QAOA Simulation Transparency Notice:
                </span>
                <p>{adaptiveExecutionResult.hardware_transparency_note}</p>
                <div className="flex items-center gap-4 text-[10px] text-slate-500 pt-1">
                  <span>Qiskit Aer CPU Simulation</span>
                  <span>Total Circuit Runs: {adaptiveExecutionResult.total_circuit_executions}</span>
                  <span>Evaluations: {adaptiveExecutionResult.total_evaluations}</span>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================================= */}
          {/* PARAMETER TRANSFER LABORATORY (Stage 6.3)                                 */}
          {/* ========================================================================= */}
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-sky-400" />
                  Parameter Transfer & Warm-Start Laboratory
                </CardTitle>
                <Badge variant="outline" className="text-xs font-mono text-sky-400 border-sky-400/30">
                  Inter-Depth Warm-Start
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 font-mono text-xs">
              <p className="text-scientific-muted text-xs">
                Test and verify parameter transfer functions (linear interpolation, layer padding, adiabatic extension)
                to map optimized angles from depth p to p+1 or across related problem topologies.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Source Gamma (γ)</label>
                  <Input
                    type="text"
                    value={transferSourceGamma}
                    onChange={(e) => setTransferSourceGamma(e.target.value)}
                    placeholder="0.35, 0.72"
                    className="font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Source Beta (β)</label>
                  <Input
                    type="text"
                    value={transferSourceBeta}
                    onChange={(e) => setTransferSourceBeta(e.target.value)}
                    placeholder="0.65, 0.28"
                    className="font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Target Depth (p_target)</label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    value={transferTargetDepth}
                    onChange={(e) => setTransferTargetDepth(parseInt(e.target.value, 10) || 3)}
                    className="font-mono text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Interpolation Method</label>
                  <select
                    value={transferMethod}
                    onChange={(e) => setTransferMethod(e.target.value as any)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <option value="linear_interpolation">Linear Interpolation</option>
                    <option value="layer_padding">Layer Padding (Zeros)</option>
                    <option value="adiabatic_extension">Adiabatic Extension</option>
                  </select>
                </div>
              </div>

              <div className="flex items-center gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleCheckTransfer}
                  disabled={isTransferring}
                  className="text-xs font-mono flex items-center gap-1.5"
                >
                  <ShieldCheck className="h-3.5 w-3.5" />
                  Check Compatibility
                </Button>
                <Button
                  type="button"
                  onClick={handleExecuteTransfer}
                  disabled={isTransferring}
                  className="text-xs font-mono flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500"
                >
                  <ArrowRight className="h-3.5 w-3.5" />
                  Transfer Parameters
                </Button>
              </div>

              {/* Transfer Report Display */}
              {transferReport && (
                <div className="p-3.5 rounded-lg bg-midnight-950 border border-sky-500/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-sky-300">
                      Transfer Compatibility: {transferReport.is_compatible ? 'COMPATIBLE' : 'INCOMPATIBLE'}
                    </span>
                    <Badge variant={transferReport.is_compatible ? 'accent' : 'warning'}>
                      Score: {(transferReport.compatibility_score * 100).toFixed(0)}%
                    </Badge>
                  </div>
                  <p className="text-[11px] text-slate-300">
                    Recommended: {transferReport.recommended_method || 'linear_interpolation'} •{' '}
                    {transferReport.notes && transferReport.notes.length > 0
                      ? transferReport.notes.join('; ')
                      : transferReport.reason || 'Parameter vectors are dimensionally compatible.'}
                  </p>
                </div>
              )}

              {/* Transferred Angles Display */}
              {transferResult && (
                <div className="p-3.5 rounded-lg bg-midnight-950 border border-emerald-500/30 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-400">
                      Successfully Transferred to Target Depth p={transferResult.target_depth}
                    </span>
                    <Badge variant="accent">
                      {transferResult.method_used}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border space-y-1">
                      <span className="text-[10px] text-slate-400 block uppercase">Target Gamma (γ):</span>
                      <span className="text-sky-300 font-bold block">
                        [{transferResult.transferred_gamma.map((g: number) => g.toFixed(4)).join(', ')}]
                      </span>
                    </div>
                    <div className="p-2.5 rounded bg-midnight-900 border border-scientific-border space-y-1">
                      <span className="text-[10px] text-slate-400 block uppercase">Target Beta (β):</span>
                      <span className="text-purple-300 font-bold block">
                        [{transferResult.transferred_beta.map((b: number) => b.toFixed(4)).join(', ')}]
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: COMPARATIVE HYBRID BENCHMARKING (Stage 5.9) */}
      {activeTab === 'benchmark' && (
        <div className="space-y-6">
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-emerald-400" />
                  Comparative Hybrid Benchmark Setup
                </CardTitle>
                <Badge variant="outline" className="font-mono text-xs text-sky-400">
                  {activeProblem.problemType.toUpperCase()}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-slate-300 mb-1.5">Target Problem</label>
                  <select
                    value={selectedProblemId}
                    onChange={(e) => setSelectedProblemId(e.target.value)}
                    className="w-full px-3 py-2 bg-midnight-950 border border-scientific-border rounded-lg text-xs font-mono text-slate-200 focus:outline-none focus:border-scientific-accent"
                  >
                    <optgroup label="Preset Benchmarks">
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
                </div>

                <div>
                  <Input
                    label="Stochastic Trials (Per Heuristic / QAOA)"
                    type="number"
                    min="1"
                    max="5"
                    step="1"
                    value={benchTrials}
                    onChange={(e) => setBenchTrials(parseInt(e.target.value, 10) || 1)}
                    className="font-mono text-xs"
                  />
                </div>
              </div>

              {/* Solvers Included */}
              <div className="p-3 bg-midnight-950 rounded-lg border border-scientific-border space-y-2">
                <span className="text-xs font-mono font-semibold text-slate-300 block">
                  Select Solvers to Benchmark:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono text-slate-300">
                  {[
                    { id: 'exact', name: 'Exact Solver (Baseline)' },
                    { id: 'genetic_algorithm', name: 'Genetic Algorithm' },
                    { id: 'simulated_annealing', name: 'Simulated Annealing' },
                    { id: 'qaoa', name: 'QAOA (Qiskit Aer)' },
                  ].map((s) => {
                    const isChecked = benchSolvers.includes(s.id)
                    return (
                      <label key={s.id} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setBenchSolvers([...benchSolvers, s.id])
                            } else {
                              setBenchSolvers(benchSolvers.filter((x) => x !== s.id))
                            }
                          }}
                          className="rounded bg-midnight-900 border-scientific-border text-sky-500 focus:ring-0"
                        />
                        <span>{s.name}</span>
                      </label>
                    )
                  })}
                </div>
              </div>

              {/* Action Button */}
              <Button
                type="button"
                onClick={handleRunHybridBenchmark}
                disabled={isBenchmarking || benchSolvers.length === 0}
                className="w-full text-xs font-mono font-bold flex items-center justify-center gap-2 py-2.5 bg-emerald-600 hover:bg-emerald-500"
              >
                {isBenchmarking ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin text-white" />
                    Executing Hybrid Benchmark Suite...
                  </>
                ) : (
                  <>
                    <BarChart2 className="h-4 w-4 fill-white text-white" />
                    Run Comparative Benchmark ({benchSolvers.length} Solvers)
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Benchmark Results */}
          {hybridResult && (
            <div className="space-y-4">
              <Card className="bg-midnight-900/60 border-scientific-border">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-sm font-bold font-mono text-slate-100 flex items-center gap-2">
                        <Award className="h-4 w-4 text-amber-400" />
                        {hybridResult.name}
                      </CardTitle>
                      <span className="text-[11px] font-mono text-scientific-muted">
                        Total Benchmark Runtime: {hybridResult.total_runtime_seconds.toFixed(2)}s • Exact Optimum:{' '}
                        <strong className="text-emerald-400">
                          {hybridResult.exact_optimum !== null ? hybridResult.exact_optimum : 'N/A'}
                        </strong>
                      </span>
                    </div>
                    <Badge variant="accent" className="font-mono text-xs">
                      {hybridResult.benchmark_id}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs font-mono text-left">
                      <thead>
                        <tr className="border-b border-scientific-border text-scientific-muted">
                          <th className="pb-2">Rank</th>
                          <th className="pb-2">Solver</th>
                          <th className="pb-2">Category</th>
                          <th className="pb-2">Best Obj</th>
                          <th className="pb-2">Approx Ratio (r)</th>
                          <th className="pb-2">Optimality Gap</th>
                          <th className="pb-2">Feasible %</th>
                          <th className="pb-2">Mean Runtime</th>
                          <th className="pb-2">Evaluations</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-scientific-border/40 text-slate-300">
                        {hybridResult.summaries.map((s, idx) => {
                          const rankIcon = idx === 0 ? '🥇 1st' : idx === 1 ? '🥈 2nd' : idx === 2 ? '🥉 3rd' : `#${idx + 1}`
                          return (
                            <tr key={s.solver_id} className="hover:bg-midnight-950/60">
                              <td className="py-2.5 font-bold text-slate-100">{rankIcon}</td>
                              <td className="py-2.5">
                                <span className="font-bold text-slate-200">{s.solver_name}</span>
                                {s.is_quantum_simulator && (
                                  <Badge variant="outline" className="ml-2 text-[10px] text-sky-400 border-sky-400/40">
                                    Qiskit Aer
                                  </Badge>
                                )}
                              </td>
                              <td className="py-2.5">
                                <span className="text-[10px] uppercase text-scientific-muted">
                                  {s.solver_category.replace('_', ' ')}
                                </span>
                              </td>
                              <td className="py-2.5 font-bold text-emerald-400">
                                {s.best_objective.toFixed(2)}
                              </td>
                              <td className="py-2.5 text-sky-300 font-bold">
                                {s.approximation_ratio !== null && s.approximation_ratio !== undefined
                                  ? s.approximation_ratio.toFixed(3)
                                  : '—'}
                              </td>
                              <td className="py-2.5">
                                {s.optimality_gap_percent !== null && s.optimality_gap_percent !== undefined ? (
                                  <span
                                    className={
                                      s.optimality_gap_percent === 0
                                        ? 'text-emerald-400 font-bold'
                                        : 'text-amber-400'
                                    }
                                  >
                                    {s.optimality_gap_percent.toFixed(2)}%
                                  </span>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td className="py-2.5 text-slate-200">
                                {(s.feasibility_rate * 100).toFixed(0)}%
                              </td>
                              <td className="py-2.5 text-slate-200">
                                {s.mean_runtime_ms.toFixed(1)} ms
                              </td>
                              <td className="py-2.5 text-slate-200">{s.mean_evaluations}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Scientific Disclaimer */}
                  <div className="mt-4 p-3 bg-midnight-950 rounded border border-scientific-border text-[11px] font-mono text-scientific-muted">
                    <span className="text-slate-400 font-bold uppercase block mb-1">
                      Platform Transparency Standard:
                    </span>
                    <p>{hybridResult.hardware_transparency_note}</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: EXECUTION AUDIT HISTORY */}
      {activeTab === 'history' && (
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <CardTitle className="text-xs uppercase tracking-wider font-mono flex items-center gap-2">
                  <History className="h-4 w-4 text-sky-400" />
                  Quantum Optimization Audit Logs
                </CardTitle>
                <div className="flex items-center gap-1 p-0.5 rounded-lg bg-midnight-950 border border-scientific-border">
                  <button
                    type="button"
                    onClick={() => setHistoryViewMode('qaoa')}
                    className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                      historyViewMode === 'qaoa'
                        ? 'bg-sky-600 text-white font-bold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Standard QAOA ({historyRecords.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => setHistoryViewMode('adaptive')}
                    className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors ${
                      historyViewMode === 'adaptive'
                        ? 'bg-amber-600 text-slate-900 font-bold'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Adaptive QAOA ({adaptiveHistory.length})
                  </button>
                </div>
              </div>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={async () => {
                  const [refreshedQ, refreshedA] = await Promise.all([
                    quantumSolverService.listExecutions(30).catch(() => []),
                    adaptiveSolverService.listExecutions(30).catch(() => []),
                  ])
                  setHistoryRecords(refreshedQ)
                  setAdaptiveHistory(refreshedA)
                }}
                className="text-xs font-mono flex items-center gap-1"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {historyViewMode === 'qaoa' ? (
              historyRecords.length === 0 ? (
                <div className="text-center py-8 text-scientific-muted font-mono text-xs space-y-2">
                  <History className="h-8 w-8 mx-auto text-scientific-muted/40" />
                  <p>No recorded QAOA executions found in storage.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono text-left">
                    <thead>
                      <tr className="border-b border-scientific-border text-scientific-muted">
                        <th className="pb-2">Execution ID</th>
                        <th className="pb-2">Problem Type</th>
                        <th className="pb-2">Status</th>
                        <th className="pb-2">p Depth</th>
                        <th className="pb-2">Shots</th>
                        <th className="pb-2">Runtime</th>
                        <th className="pb-2">Best Objective</th>
                        <th className="pb-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-scientific-border/40 text-slate-300">
                      {historyRecords.map((r) => (
                        <tr key={r.execution_id} className="hover:bg-midnight-950/60">
                          <td className="py-2.5 font-bold text-slate-200">{r.execution_id}</td>
                          <td className="py-2.5 uppercase">{r.problem_type}</td>
                          <td className="py-2.5">
                            <Badge
                              variant={
                                r.status === 'COMPLETED'
                                  ? 'accent'
                                  : r.status === 'RUNNING'
                                  ? 'outline'
                                  : 'warning'
                              }
                              className="text-[10px]"
                            >
                              {r.status}
                            </Badge>
                          </td>
                          <td className="py-2.5">p = {r.config.p_depth}</td>
                          <td className="py-2.5">{r.config.shots}</td>
                          <td className="py-2.5">{(r.runtime_seconds || 0).toFixed(2)}s</td>
                          <td className="py-2.5 font-bold text-emerald-400">
                            {r.result?.best_sample.objective_value ?? '—'}
                          </td>
                          <td className="py-2.5 text-right">
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => handleInspectHistory(r)}
                              disabled={!r.result}
                              className="text-[10px] text-sky-400 hover:text-sky-300 font-mono"
                            >
                              Inspect Result
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            ) : (
              adaptiveHistory.length === 0 ? (
                <div className="text-center py-8 text-scientific-muted font-mono text-xs space-y-2">
                  <Zap className="h-8 w-8 mx-auto text-scientific-muted/40" />
                  <p>No recorded Adaptive QAOA executions found in storage.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono text-left">
                    <thead>
                      <tr className="border-b border-scientific-border text-scientific-muted">
                        <th className="pb-2">Execution ID</th>
                        <th className="pb-2">Strategy</th>
                        <th className="pb-2">Problem</th>
                        <th className="pb-2">Status</th>
                        <th className="pb-2">Depth Evolution</th>
                        <th className="pb-2">Runtime</th>
                        <th className="pb-2">Best Objective</th>
                        <th className="pb-2">Approx Ratio</th>
                        <th className="pb-2 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-scientific-border/40 text-slate-300">
                      {adaptiveHistory.map((r) => (
                        <tr key={r.execution_id} className="hover:bg-midnight-950/60">
                          <td className="py-2.5 font-bold text-slate-200">{r.execution_id}</td>
                          <td className="py-2.5">
                            <Badge variant="outline" className="text-[10px] text-amber-400 border-amber-400/30">
                              {r.strategy_type}
                            </Badge>
                          </td>
                          <td className="py-2.5 uppercase">{r.problem_type}</td>
                          <td className="py-2.5">
                            <Badge
                              variant={
                                r.status === 'COMPLETED'
                                  ? 'accent'
                                  : r.status === 'RUNNING'
                                  ? 'outline'
                                  : 'warning'
                              }
                              className="text-[10px]"
                            >
                              {r.status}
                            </Badge>
                          </td>
                          <td className="py-2.5 text-amber-300">
                            p = {r.result?.initial_depth ?? r.config.strategy_config.initial_depth} → {r.result?.final_depth ?? r.config.strategy_config.max_depth}
                          </td>
                          <td className="py-2.5">{(r.runtime_seconds || 0).toFixed(2)}s</td>
                          <td className="py-2.5 font-bold text-emerald-400">
                            {r.result?.objective_value != null ? r.result.objective_value.toFixed(2) : '—'}
                          </td>
                          <td className="py-2.5 text-purple-300">
                            {r.result?.approximation_ratio != null
                              ? (r.result.approximation_ratio * 100).toFixed(1) + '%'
                              : '—'}
                          </td>
                          <td className="py-2.5 text-right">
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              onClick={() => handleInspectAdaptiveHistory(r)}
                              disabled={!r.result}
                              className="text-[10px] text-amber-400 hover:text-amber-300 font-mono"
                            >
                              Inspect Result
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
