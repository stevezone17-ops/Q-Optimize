import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Alert } from '../components/ui/Alert'
import { Input } from '../components/ui/Input'
import {
  ProblemResponse,
  FormulationResponse,
  ProblemType,
} from '../types'
import { problemService } from '../services/problemService'
import { formulationService } from '../services/formulationService'
import { QuboHeatmap } from '../features/formulation-studio/QuboHeatmap'
import { IsingInspector } from '../features/formulation-studio/IsingInspector'
import { VerificationPanel } from '../features/formulation-studio/VerificationPanel'
import {
  Layers,
  Sparkles,
  Download,
  RefreshCw,
  Cpu,
  Calculator,
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

export const FormulationStudioPage: React.FC = () => {
  const [registeredProblems, setRegisteredProblems] = useState<ProblemResponse[]>([])
  const [selectedProblemId, setSelectedProblemId] = useState<string>('preset_0')
  const [penaltyA, setPenaltyA] = useState<number>(15.0)
  const [penaltyB, setPenaltyB] = useState<number>(15.0)

  const [isGenerating, setIsGenerating] = useState(false)
  const [formulation, setFormulation] = useState<FormulationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'qubo' | 'ising' | 'verification'>('qubo')

  // Fetch problems on mount
  useEffect(() => {
    const fetchProblems = async () => {
      try {
        const list = await problemService.listProblems()
        setRegisteredProblems(list)
        if (list.length > 0) {
          setSelectedProblemId(list[0].id)
        }
      } catch (err) {
        // Fallback to presets
      }
    }
    fetchProblems()
  }, [])

  // Auto-generate formulation for default initial benchmark
  useEffect(() => {
    handleGenerateFormulation()
  }, [selectedProblemId])

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

  const handleGenerateFormulation = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      let payload
      if (!activeProblem.isPreset) {
        payload = {
          problem_id: selectedProblemId,
          penalty_coefficients: { A: penaltyA, B: penaltyB },
        }
      } else {
        payload = {
          problem_type: activeProblem.problemType,
          instance: activeProblem.instance,
          penalty_coefficients: { A: penaltyA, B: penaltyB },
        }
      }

      const res = await formulationService.generateFormulation(payload)
      setFormulation(res)
    } catch (err) {
      setError((err as Error).message || 'Failed to generate formulation.')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleExport = (format: string) => {
    if (!formulation) return
    let content = ''
    let filename = `formulation_${formulation.id.slice(0, 8)}_${format}.json`

    if (format === 'dense' && formulation.qubo?.matrix) {
      content = JSON.stringify(formulation.qubo.matrix, null, 2)
    } else if (format === 'sparse' && formulation.qubo) {
      content = JSON.stringify(
        {
          variable_order: formulation.qubo.variable_order,
          linear_terms: formulation.qubo.linear_terms,
          quadratic_terms: formulation.qubo.quadratic_terms,
          offset: formulation.qubo.offset,
        },
        null,
        2
      )
    } else if (format === 'latex' && formulation.ising) {
      filename = `hamiltonian_${formulation.id.slice(0, 8)}.txt`
      content = formulation.ising.latex_expression || ''
    } else {
      content = JSON.stringify(formulation, null, 2)
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Header and Problem Selector */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/60 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Calculator className="h-4 w-4 text-scientific-accent" />
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Formulation Studio
            </h3>
            <Badge variant="accent">Phase 3 Active</Badge>
          </div>
          <p className="text-xs text-scientific-muted font-mono">
            Canonical upper-triangular QUBO & Ising spin Hamiltonian modeling with exhaustive energy equivalence.
          </p>
        </div>

        {/* Problem Selector Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-scientific-muted font-mono shrink-0">Problem:</span>
          <select
            value={selectedProblemId}
            onChange={(e) => setSelectedProblemId(e.target.value)}
            className="text-xs font-mono px-3 py-1.5 rounded-lg bg-midnight-950 border border-scientific-border text-slate-200 focus:outline-none focus:ring-1 focus:ring-scientific-accent max-w-[280px] truncate"
          >
            <optgroup label="Registered Problems">
              {registeredProblems.map((p) => (
                <option key={`opt-reg-${p.id}`} value={p.id}>
                  {p.name} ({p.problem_type})
                </option>
              ))}
            </optgroup>
            <optgroup label="Small Benchmarks (Pre-loaded)">
              {PRESET_BENCHMARKS.map((b, idx) => (
                <option key={`opt-preset-${idx}`} value={`preset_${idx}`}>
                  {b.name}
                </option>
              ))}
            </optgroup>
          </select>

          <Button
            type="button"
            size="sm"
            variant="secondary"
            onClick={handleGenerateFormulation}
            isLoading={isGenerating}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Re-generate
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Formulation Error">
          {error}
        </Alert>
      )}

      {/* Penalty Configuration Controls (for Assignment and TSP) */}
      {activeProblem.problemType !== 'max_cut' && (
        <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-scientific-border/40 pb-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-200 uppercase tracking-wider">
                Constraint Penalty Parameters
              </span>
              <Badge variant="outline">Lagrange Multipliers</Badge>
            </div>
            <span className="text-[11px] text-scientific-muted">
              Must exceed objective thresholds to guarantee feasibility
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Input
                label={activeProblem.problemType === 'assignment' ? 'Row Penalty (A)' : 'City Penalty (A)'}
                type="number"
                step="1"
                min="1"
                value={penaltyA}
                onChange={(e) => setPenaltyA(Math.max(1, parseFloat(e.target.value) || 1))}
                className="font-mono"
              />
            </div>
            <div>
              <Input
                label={activeProblem.problemType === 'assignment' ? 'Column Penalty (B)' : 'Position Penalty (B)'}
                type="number"
                step="1"
                min="1"
                value={penaltyB}
                onChange={(e) => setPenaltyB(Math.max(1, parseFloat(e.target.value) || 1))}
                className="font-mono"
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Studio Tabs */}
      <div className="flex items-center gap-2 border-b border-scientific-border/60 pb-1">
        <button
          type="button"
          onClick={() => setActiveTab('qubo')}
          className={`text-xs px-3.5 py-1.5 rounded-lg font-mono transition-all flex items-center gap-1.5 ${
            activeTab === 'qubo'
              ? 'bg-scientific-accent text-midnight-950 font-bold shadow-sm'
              : 'text-slate-300 hover:bg-midnight-800'
          }`}
        >
          <Layers className="h-3.5 w-3.5" />
          QUBO Formalism & Matrix
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('ising')}
          className={`text-xs px-3.5 py-1.5 rounded-lg font-mono transition-all flex items-center gap-1.5 ${
            activeTab === 'ising'
              ? 'bg-scientific-accent text-midnight-950 font-bold shadow-sm'
              : 'text-slate-300 hover:bg-midnight-800'
          }`}
        >
          <Cpu className="h-3.5 w-3.5" />
          Ising Spin Hamiltonian
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('verification')}
          className={`text-xs px-3.5 py-1.5 rounded-lg font-mono transition-all flex items-center gap-1.5 ${
            activeTab === 'verification'
              ? 'bg-scientific-accent text-midnight-950 font-bold shadow-sm'
              : 'text-slate-300 hover:bg-midnight-800'
          }`}
        >
          <Sparkles className="h-3.5 w-3.5" />
          Mathematical Verification
        </button>
      </div>

      {/* Tab 1: QUBO Formalism */}
      {activeTab === 'qubo' && formulation?.qubo && (
        <div className="space-y-6">
          {/* Metadata Summary Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-3 rounded-lg bg-midnight-900 border border-scientific-border">
              <span className="text-scientific-muted block text-[10px]">Variables (n)</span>
              <span className="font-semibold text-white text-sm">{formulation.qubo.variable_order.length}</span>
            </div>
            <div className="p-3 rounded-lg bg-midnight-900 border border-scientific-border">
              <span className="text-scientific-muted block text-[10px]">Linear Terms (Q_ii)</span>
              <span className="font-semibold text-sky-400 text-sm">
                {Object.keys(formulation.qubo.linear_terms).length}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-midnight-900 border border-scientific-border">
              <span className="text-scientific-muted block text-[10px]">Quadratic Couplings</span>
              <span className="font-semibold text-purple-400 text-sm">
                {Object.keys(formulation.qubo.quadratic_terms).length}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-midnight-900 border border-scientific-border">
              <span className="text-scientific-muted block text-[10px]">Constant Offset (c)</span>
              <span className="font-semibold text-amber-400 text-sm">{formulation.qubo.offset.toFixed(2)}</span>
            </div>
          </div>

          {/* QUBO Matrix Heatmap */}
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xs uppercase tracking-wider font-mono">
                    QUBO Upper-Triangular Matrix Inspector
                  </CardTitle>
                  <CardDescription className="text-xs font-mono">
                    E(x) = &sum;_i Q_ii x_i + &sum;_{'{i < j}'} Q_ij x_i x_j + c
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleExport('dense')}
                    leftIcon={<Download className="h-3 w-3" />}
                  >
                    Export Dense
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleExport('sparse')}
                    leftIcon={<Download className="h-3 w-3" />}
                  >
                    Export Sparse
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <QuboHeatmap
                matrix={formulation.qubo.matrix || []}
                variableOrder={formulation.qubo.variable_order}
              />
            </CardContent>
          </Card>

          {/* Modeling Assumptions List */}
          {formulation.qubo.assumptions.length > 0 && (
            <div className="p-4 rounded-xl border border-scientific-border bg-midnight-950 font-mono text-xs space-y-2">
              <span className="text-[10px] text-scientific-muted uppercase block font-semibold">
                Formulation Assumptions & Guarantees:
              </span>
              <ul className="space-y-1 text-slate-300">
                {formulation.qubo.assumptions.map((assump, idx) => (
                  <li key={`assump-${idx}`} className="flex items-start gap-1.5">
                    <span className="text-sky-400">&bull;</span>
                    <span>{assump}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Ising Spin Hamiltonian */}
      {activeTab === 'ising' && formulation?.ising && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleExport('latex')}
              leftIcon={<Download className="h-3.5 w-3.5" />}
            >
              Export LaTeX Hamiltonian
            </Button>
          </div>
          <IsingInspector ising={formulation.ising} />
        </div>
      )}

      {/* Tab 3: Independent Verification */}
      {activeTab === 'verification' && formulation?.qubo && (
        <VerificationPanel
          formulationId={formulation.id}
          problemId={!activeProblem.isPreset ? selectedProblemId : undefined}
          problemType={activeProblem.problemType}
          instance={activeProblem.instance}
          qubo={formulation.qubo}
        />
      )}
    </div>
  )
}
