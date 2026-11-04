import React from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Alert } from '../components/ui/Alert'
import { Lock } from 'lucide-react'

export const ClassicalLabPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Alert variant="info" title="Phase 4 Classical Optimization Engine (Baselines)">
        The Classical Lab will provide transparent, reproducible classical baselines executing on
        the exact same canonical problem instances used by quantum solvers. Every solution candidate will
        be independently verified for feasibility and true objective value.
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="accent">Deterministic</Badge>
              <Badge variant="outline">Ground Truth</Badge>
            </div>
            <CardTitle className="mt-2">Exact Small-Instance Solver</CardTitle>
            <CardDescription>
              Exhaustive enumeration & branch-and-bound:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <p>Guarantees mathematical global optimum on instances up to ~20 binary variables.</p>
            <p className="text-slate-400">Used as the ground truth benchmark for approximation ratio computation.</p>
          </CardContent>
        </Card>

        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="violet">Evolutionary</Badge>
              <Badge variant="outline">Population</Badge>
            </div>
            <CardTitle className="mt-2">Genetic Algorithm (GA)</CardTitle>
            <CardDescription>
              Chromosome representation with elitism:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <p>Configurable population size, two-point crossover, bit-flip mutation, and tournament selection.</p>
            <p className="text-slate-400">Multi-seed distributions reported rather than cherry-picked runs.</p>
          </CardContent>
        </Card>

        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="gold">Thermodynamic</Badge>
              <Badge variant="outline">Single-State</Badge>
            </div>
            <CardTitle className="mt-2">Simulated Annealing (SA)</CardTitle>
            <CardDescription>
              Metropolis-Hastings cooling schedule:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <p>Initial temperature T_0, geometric cooling &alpha;, 1-flip neighborhood transitions.</p>
            <p className="text-slate-400">Equivalent function evaluation budgets matched against QAOA shots.</p>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-midnight-900/40 border-scientific-border opacity-80">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Classical Solver Configuration & Dispatch</CardTitle>
            <Badge variant="warning">Scheduled for Phase 4</Badge>
          </div>
          <CardDescription>
            Multi-seed execution and convergence recording activate in Phase 4.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-8 text-center space-y-3 font-mono text-xs text-scientific-muted">
          <Lock className="h-8 w-8 mx-auto text-scientific-muted" />
          <p>No placeholder optimization metrics are reported in Phase 1.</p>
        </CardContent>
      </Card>
    </div>
  )
}
