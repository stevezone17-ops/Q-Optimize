import React, { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { ChevronRight } from 'lucide-react'

interface Topic {
  id: string
  title: string
  category: string
  badge: 'accent' | 'violet' | 'gold' | 'default'
  summary: string
  content: React.ReactNode
}

const TOPICS: Topic[] = [
  {
    id: 'hybrid-computing',
    title: 'Hybrid Quantum-Classical Optimization Primer',
    category: 'Foundations',
    badge: 'accent',
    summary: 'How variational quantum algorithms distribute workloads between classical and quantum processors.',
    content: (
      <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
        <p>
          Variational Quantum Algorithms (VQAs) are designed for Noisy Intermediate-Scale Quantum (NISQ)
          devices. In a variational loop, a parameterized quantum circuit (ansatz) prepares a quantum state
          whose expectation value represents an optimization objective function.
        </p>
        <p>
          A classical optimization algorithm running on a standard CPU measures this expectation value, computes
          parameter updates, and iteratively refines angles &gamma; and &beta; until convergence. This leverages
          the quantum processor for state preparation while delegating numerical parameter tuning to classical routines.
        </p>
        <div className="p-3 rounded bg-midnight-950 border border-scientific-border space-y-1">
          <span className="text-sky-400 font-semibold block text-[11px]">Key Principle:</span>
          <p className="text-scientific-muted">
            Simulator execution on classical hardware computes statevectors numerically. It does not possess physical
            quantum advantage and scales exponentially with qubit count (2^n complex amplitudes).
          </p>
        </div>
      </div>
    ),
  },
  {
    id: 'qubo-ising',
    title: 'Formulating Combinatorial Problems into QUBO and Ising',
    category: 'Mathematical Modeling',
    badge: 'violet',
    summary: 'The mathematical substitution and penalty methods required to transform discrete constraints into binary polynomials.',
    content: (
      <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
        <p>
          Combinatorial optimization problems often possess discrete constraints (e.g. vertex assignment, matching,
          order permutations). To execute them on quantum annealing or gate-based QAOA architectures, the objective and
          constraints must be expressed as Quadratic Unconstrained Binary Optimization (QUBO) models:
        </p>
        <div className="p-3 rounded bg-midnight-950 border border-scientific-border text-purple-300">
          <code>{"E(x) = \\sum_i Q_{ii} x_i + \\sum_{i < j} Q_{ij} x_i x_j + c, \\quad x_i \\in \\{0, 1\\}"}</code>
        </div>
        <p>
          Mapping to Ising spin observables uses the linear substitution x_i = (1 - s_i) / 2, yielding eigenvalues &plusmn;1
          associated with Pauli-Z operators &sigma;_z. Correct variable ordering, upper-triangular indexing, and energy offsets
          are critical to guarantee equivalence.
        </p>
      </div>
    ),
  },
  {
    id: 'qaoa-mechanics',
    title: 'Understanding QAOA Mechanics: Cost and Mixer Hamiltonians',
    category: 'Quantum Computing',
    badge: 'accent',
    summary: 'Detailed decomposition of variational depth, unitary evolution blocks, and bitstring sampling.',
    content: (
      <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
        <p>
          QAOA begins in a uniform superposition |+&rang;^{"\\otimes n"} constructed with Hadamard gates. The system evolves
          under alternating applications of the Cost Hamiltonian H_C and the Mixer Hamiltonian H_M:
        </p>
        <div className="p-3 rounded bg-midnight-950 border border-scientific-border text-sky-300">
          <code>{"|\\gamma, \\beta\\rangle = e^{-i \\beta_p H_M} e^{-i \\gamma_p H_C} \\dots e^{-i \\beta_1 H_M} e^{-i \\gamma_1 H_C} |+\\rangle^{\\otimes n}"}</code>
        </div>
        <p>
          The standard transverse mixer H_M = \sum_i X_i induces bit-flip transitions, driving quantum tunneling between
          superposed configurations while H_C applies phase shifts proportional to candidate solution costs.
        </p>
      </div>
    ),
  },
  {
    id: 'classical-baselines',
    title: 'The Indispensable Role of Classical Baselines',
    category: 'Benchmarking',
    badge: 'gold',
    summary: 'Why heuristic and exact classical solvers are required to contextualize any quantum optimization result.',
    content: (
      <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
        <p>
          A quantum algorithm cannot be declared advantageous without evaluating equivalent classical alternatives.
          In Q-Optimize, three classical baselines provide necessary benchmarks:
        </p>
        <ul className="list-disc pl-5 space-y-1.5 text-scientific-muted">
          <li>
            <strong className="text-white">Exact Enumeration / Branch & Bound:</strong> Provides ground truth optima on small instances to compute true approximation ratios.
          </li>
          <li>
            <strong className="text-white">Genetic Algorithms (GA):</strong> Represents population-based heuristic search using crossover and mutation.
          </li>
          <li>
            <strong className="text-white">Simulated Annealing (SA):</strong> Emulates physical thermal relaxation, matching QAOA function evaluation budgets.
          </li>
        </ul>
      </div>
    ),
  },
  {
    id: 'reproducibility',
    title: 'Scientific Reproducibility & Independent Evaluators',
    category: 'Scientific Standards',
    badge: 'default',
    summary: 'Protocol for preventing self-reporting bias and ensuring verifiable benchmarks.',
    content: (
      <div className="space-y-4 text-xs font-mono text-slate-300 leading-relaxed">
        <p>
          A common pitfall in heuristic optimization is trusting the solver's self-reported objective value. In Q-Optimize:
        </p>
        <div className="p-3 rounded bg-midnight-950 border border-scientific-border space-y-2">
          <p className="text-emerald-400 font-semibold">The Evaluator Rule:</p>
          <p className="text-scientific-muted">
            The candidate bitstring output by any solver (classical or quantum) is passed to an independent evaluator
            module. The objective value is recalculated directly from the canonical problem definition, and all problem
            constraints are explicitly verified.
          </p>
        </div>
        <p>
          Every benchmark preserves the exact instance JSON, generator seed, solver parameters, run seed, and dependency versions.
        </p>
      </div>
    ),
  },
]

export const LearnPage: React.FC = () => {
  const [selectedTopicId, setSelectedTopicId] = useState(TOPICS[0].id)
  const currentTopic = TOPICS.find((t) => t.id === selectedTopicId) || TOPICS[0]

  return (
    <div className="space-y-6">
      <div className="p-5 rounded-xl border border-scientific-border bg-midnight-900/60 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-white tracking-tight font-mono">
            Scientific Optimization Knowledge Base
          </h2>
          <p className="text-xs text-scientific-muted font-mono mt-0.5">
            Theoretical principles of hybrid computing, QUBO/Ising mapping, and rigorous evaluation
          </p>
        </div>
        <Badge variant="accent">5 Technical Guides</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Navigation Sidebar */}
        <div className="space-y-2">
          {TOPICS.map((topic) => {
            const isSelected = topic.id === selectedTopicId
            return (
              <button
                key={topic.id}
                type="button"
                onClick={() => setSelectedTopicId(topic.id)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between ${
                  isSelected
                    ? 'bg-scientific-hover border-scientific-accent/40 shadow-sm'
                    : 'bg-midnight-900/40 border-scientific-border/80 hover:bg-midnight-900'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-scientific-muted uppercase tracking-wider font-mono">
                      {topic.category}
                    </span>
                  </div>
                  <h4 className={`text-xs font-semibold ${isSelected ? 'text-white' : 'text-slate-300'}`}>
                    {topic.title}
                  </h4>
                </div>
                <ChevronRight
                  className={`h-4 w-4 shrink-0 transition-colors ${
                    isSelected ? 'text-scientific-accent' : 'text-slate-400'
                  }`}
                />
              </button>
            )
          })}
        </div>

        {/* Content Panel */}
        <div className="lg:col-span-2">
          <Card className="bg-midnight-900/60 border-scientific-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <Badge variant={currentTopic.badge} size="sm">
                  {currentTopic.category}
                </Badge>
                <span className="text-[10px] text-scientific-muted font-mono">Q-Optimize Technical Reference</span>
              </div>
              <CardTitle className="text-lg mt-2">{currentTopic.title}</CardTitle>
              <CardDescription>{currentTopic.summary}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-4 border-t border-scientific-border/40">
              {currentTopic.content}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
