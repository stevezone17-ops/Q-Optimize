import React from 'react'
import { Button } from '../components/ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import {
  ArrowRight,
  Atom,
  Cpu,
  CheckCircle2,
} from 'lucide-react'

interface LandingPageProps {
  onEnterWorkspace: () => void
}

export const LandingPage: React.FC<LandingPageProps> = ({ onEnterWorkspace }) => {
  return (
    <div className="min-h-screen bg-midnight-950 text-scientific-text selection:bg-scientific-accent/30 selection:text-scientific-text">
      {/* Top Navigation */}
      <header className="border-b border-scientific-border/80 bg-midnight-950/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-midnight-800 to-midnight-700 border border-scientific-border flex items-center justify-center p-1.5 shadow-sm">
              <img src="/logo.svg" alt="Q-Optimize Logo" className="h-full w-full object-contain" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight text-white font-mono">Q-Optimize</span>
              <span className="text-[10px] ml-2 bg-sky-500/10 text-sky-400 font-mono px-2 py-0.5 rounded border border-sky-500/20">
                Phase 1 Foundation
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="#workflow"
              className="text-xs text-scientific-muted hover:text-white transition-colors font-mono"
            >
              Workflow
            </a>
            <a
              href="#problems"
              className="text-xs text-scientific-muted hover:text-white transition-colors font-mono"
            >
              Problems
            </a>
            <a
              href="#solvers"
              className="text-xs text-scientific-muted hover:text-white transition-colors font-mono"
            >
              Solvers
            </a>
            <a
              href="#research"
              className="text-xs text-scientific-muted hover:text-white transition-colors font-mono"
            >
              Research
            </a>
            <Button variant="primary" size="sm" onClick={onEnterWorkspace} rightIcon={<ArrowRight className="h-3.5 w-3.5" />}>
              Open Workspace
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-24 px-6 overflow-hidden bg-grid-pattern">
        {/* Glow backdrop */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-sky-500/10 blur-[120px] pointer-events-none rounded-full" />
        <div className="absolute top-1/3 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[250px] bg-purple-500/10 blur-[100px] pointer-events-none rounded-full" />

        <div className="max-w-4xl mx-auto text-center relative z-10 space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-midnight-900 border border-scientific-border text-xs font-mono text-sky-300">
            <Atom className="h-3.5 w-3.5 text-scientific-accent animate-spin" style={{ animationDuration: '8s' }} />
            <span>AI-Assisted Hybrid Quantum-Classical Optimization Platform</span>
          </div>

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-tight">
            Rigorous Mathematical Optimization, <br />
            <span className="bg-gradient-to-r from-sky-400 via-purple-400 to-amber-400 bg-clip-text text-transparent">
              From QUBO to Quantum Circuit
            </span>
          </h1>

          <p className="text-base md:text-lg text-scientific-muted max-w-2xl mx-auto leading-relaxed">
            Q-Optimize bridges canonical problem definitions, quadratic unconstrained binary
            optimization (QUBO), variational QAOA simulation via Qiskit, and exact classical baselines
            with reproducible scientific rigor.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Button
              variant="primary"
              size="lg"
              onClick={onEnterWorkspace}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Launch Platform Workspace
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                const el = document.getElementById('workflow')
                el?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              Inspect Architecture
            </Button>
          </div>

          {/* Principle badges */}
          <div className="pt-8 flex flex-wrap items-center justify-center gap-3 text-xs font-mono text-scientific-muted">
            <span className="flex items-center gap-1.5 bg-midnight-900/60 px-3 py-1 rounded border border-scientific-border">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Mathematical Correctness
            </span>
            <span className="flex items-center gap-1.5 bg-midnight-900/60 px-3 py-1 rounded border border-scientific-border">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Independent Evaluator Truth
            </span>
            <span className="flex items-center gap-1.5 bg-midnight-900/60 px-3 py-1 rounded border border-scientific-border">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              Zero Fabricated Metrics
            </span>
          </div>
        </div>
      </section>

      {/* Optimization Workflow Section */}
      <section id="workflow" className="py-20 px-6 border-t border-scientific-border/80 bg-midnight-900/20">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <Badge variant="accent" size="sm">
              Methodology
            </Badge>
            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              The 4-Stage Optimization Pipeline
            </h2>
            <p className="text-sm text-scientific-muted max-w-xl mx-auto">
              Every combinatorial problem follows a deterministic workflow ensuring mathematical
              integrity and full reproducibility.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card glow className="bg-midnight-900/70 border-scientific-border">
              <CardHeader>
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-400 font-mono text-xs font-bold mb-2">
                  01
                </div>
                <CardTitle>Canonical Problem Definition</CardTitle>
                <CardDescription>
                  Define Max-Cut, Assignment, or TSP via structured input forms or human-confirmed natural language drafts.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-midnight-900/70 border-scientific-border">
              <CardHeader>
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400 font-mono text-xs font-bold mb-2">
                  02
                </div>
                <CardTitle>QUBO & Ising Formulation</CardTitle>
                <CardDescription>
                  Construct quadratic unconstrained binary models and map binary variables to spin-1/2 Pauli-Z Hamiltonians.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-midnight-900/70 border-scientific-border">
              <CardHeader>
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 font-mono text-xs font-bold mb-2">
                  03
                </div>
                <CardTitle>Dual-Track Solving</CardTitle>
                <CardDescription>
                  Simulate QAOA statevector circuits alongside exact enumeration, Genetic Algorithms, and Simulated Annealing.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-midnight-900/70 border-scientific-border">
              <CardHeader>
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-mono text-xs font-bold mb-2">
                  04
                </div>
                <CardTitle>Independent Verification</CardTitle>
                <CardDescription>
                  Recompute objective values and check feasibility independently without trusting solver self-reporting.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Supported Problems Section */}
      <section id="problems" className="py-20 px-6 border-t border-scientific-border/80">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <Badge variant="violet" size="sm">
              Problem Families
            </Badge>
            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              Combinatorial Problem Families
            </h2>
            <p className="text-sm text-scientific-muted max-w-xl mx-auto">
              Fully validated input schemas, independent objective evaluators, and exact baseline verification.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="bg-midnight-900/60 border-scientific-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="accent">Graph Partitioning</Badge>
                  <span className="text-[10px] text-scientific-muted font-mono">NP-Complete</span>
                </div>
                <CardTitle className="mt-2">Max-Cut Problem</CardTitle>
                <CardDescription>
                  Partition vertices of an undirected weighted graph into two subsets S and V\S such that the sum of weights of severed edges is maximized.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 font-mono text-xs text-scientific-muted border-t border-scientific-border/40 pt-4">
                <div className="flex justify-between">
                  <span>Decision Variables:</span>
                  <span className="text-white">|V| binary spins</span>
                </div>
                <div className="flex justify-between">
                  <span>Quadratic Terms:</span>
                  <span className="text-white">Pairwise edge couplings</span>
                </div>
                <div className="flex justify-between">
                  <span>Constraint Type:</span>
                  <span className="text-emerald-400">Unconstrained naturally</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-midnight-900/60 border-scientific-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="violet">Bipartite Matching</Badge>
                  <span className="text-[10px] text-scientific-muted font-mono">Polynomial (Exact)</span>
                </div>
                <CardTitle className="mt-2">Linear Assignment</CardTitle>
                <CardDescription>
                  Assign N agents to M tasks with specified costs such that each agent gets exactly one task and total cost is minimized.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 font-mono text-xs text-scientific-muted border-t border-scientific-border/40 pt-4">
                <div className="flex justify-between">
                  <span>Decision Variables:</span>
                  <span className="text-white">N &times; M binary flags</span>
                </div>
                <div className="flex justify-between">
                  <span>Penalty Coefficients:</span>
                  <span className="text-amber-400">Row/Column penalties &lambda;</span>
                </div>
                <div className="flex justify-between">
                  <span>Constraint Type:</span>
                  <span className="text-sky-400">Strict 1-to-1 matching</span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-midnight-900/60 border-scientific-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="gold">Routing & Tour</Badge>
                  <span className="text-[10px] text-scientific-muted font-mono">NP-Hard</span>
                </div>
                <CardTitle className="mt-2">Travelling Salesperson</CardTitle>
                <CardDescription>
                  Find the shortest possible closed circuit visiting each city exactly once and returning to the starting point.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 font-mono text-xs text-scientific-muted border-t border-scientific-border/40 pt-4">
                <div className="flex justify-between">
                  <span>Decision Variables:</span>
                  <span className="text-white">N &times; N permutation</span>
                </div>
                <div className="flex justify-between">
                  <span>Subtour Elimination:</span>
                  <span className="text-purple-400">Position order penalty</span>
                </div>
                <div className="flex justify-between">
                  <span>Instance Limit:</span>
                  <span className="text-slate-300">Small instances (N &le; 10)</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Solvers & Scientific Rigor */}
      <section id="solvers" className="py-20 px-6 border-t border-scientific-border/80 bg-midnight-900/30">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center space-y-3">
            <Badge variant="accent" size="sm">
              Solver Architecture
            </Badge>
            <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
              Quantum & Classical Baselines
            </h2>
            <p className="text-sm text-scientific-muted max-w-xl mx-auto">
              Fair, controlled comparisons under identical budgets, seeds, and instance definitions.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="p-6 rounded-2xl border border-sky-500/20 bg-midnight-900/60 space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  <Atom className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Quantum Engine (QAOA)</h3>
                  <p className="text-xs text-scientific-muted">Qiskit Aer Statevector Simulation</p>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                Implements variational Quantum Approximate Optimization Algorithm (QAOA) parameterized by depth p,
                cost Hamiltonian H_C, and mixer Hamiltonian H_M. Classical optimizers (COBYLA, SPSA) tune parameters
                while independent evaluators assess measured bitstring probability distributions.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-purple-500/20 bg-midnight-900/60 space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <Cpu className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Classical Engine (Baselines)</h3>
                  <p className="text-xs text-scientific-muted">Exact & Heuristic Solvers</p>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                Provides verifiable baselines using exact exhaustive branch-and-bound for small instances,
                Genetic Algorithms with tournament selection and crossover, and Simulated Annealing with documented
                cooling schedules. Every candidate is evaluated on the exact same instance under identical budgets.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Research & Reproducibility */}
      <section id="research" className="py-20 px-6 border-t border-scientific-border/80">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <Badge variant="gold" size="sm">
            Research Scope
          </Badge>
          <h2 className="text-3xl font-bold text-white tracking-tight">
            Built for Transparent Scientific Research
          </h2>
          <p className="text-sm text-scientific-muted leading-relaxed">
            Q-Optimize was engineered to evaluate five key research questions covering QAOA quality across
            problem topology, adaptive parameter initialization schedules, machine learning solver recommendation
            regret, and noise sensitivity. We make no unsubstantiated claims of practical quantum advantage on NISQ simulators.
          </p>

          <div className="pt-4">
            <Button variant="primary" size="lg" onClick={onEnterWorkspace} rightIcon={<ArrowRight className="h-4 w-4" />}>
              Enter Platform Workspace
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 px-6 border-t border-scientific-border bg-midnight-950 text-xs font-mono text-scientific-muted">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-semibold">Q-Optimize</span>
            <span>&bull;</span>
            <span>AI-Assisted Hybrid Quantum-Classical Optimization</span>
          </div>
          <div className="flex items-center gap-4">
            <span>FastAPI & React & TypeScript</span>
            <span>&bull;</span>
            <span>Phase 1 Platform Foundation</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
