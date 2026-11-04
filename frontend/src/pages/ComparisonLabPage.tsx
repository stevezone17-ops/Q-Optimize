import React from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Alert } from '../components/ui/Alert'
import { Lock } from 'lucide-react'

export const ComparisonLabPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Alert variant="info" title="Phase 6 & 8 Comparison Lab">
        The Comparison Lab evaluates quantum simulation against classical baselines under strictly
        controlled experimental controls. No claims of practical quantum advantage will be made from
        NISQ simulator benchmarks.
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="accent">Experimental Control</Badge>
              <Badge variant="outline">Equal Budgets</Badge>
            </div>
            <CardTitle className="mt-2">Controlled Comparison Protocol</CardTitle>
            <CardDescription>
              Rules enforced during comparative benchmarking:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <ul className="list-disc pl-5 space-y-1">
              <li>Both solvers run on the exact same canonical problem instance.</li>
              <li>Documented budgets: iterations, shots, and evaluations explicitly matched.</li>
              <li>Stochastic methods evaluated across &ge; 10 random seeds with variance bounds.</li>
              <li>Formulation generation time separated from algorithmic solver latency.</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="violet">Metric Formulations</Badge>
              <Badge variant="outline">Formulas</Badge>
            </div>
            <CardTitle className="mt-2">Core Scientific Metrics</CardTitle>
            <CardDescription>
              Defined formulas used in comparative analysis:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <ul className="list-disc pl-5 space-y-1">
              <li>Approximation Ratio: r = C_alg / C_opt (when ground truth exists).</li>
              <li>Feasibility Rate: fraction of sampled bitstrings satisfying all constraints.</li>
              <li>Convergence Trajectory: energy expectation vs evaluation counter.</li>
              <li>Recommendation Regret: difference between chosen solver and ex-post optimal.</li>
            </ul>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-midnight-900/40 border-scientific-border opacity-80">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Comparative Visualization & Benchmark Studio</CardTitle>
            <Badge variant="warning">Scheduled for Phase 6</Badge>
          </div>
          <CardDescription>
            Plotly convergence charts, distribution boxplots, and statistical confidence intervals activate in Phase 6.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-8 text-center space-y-3 font-mono text-xs text-scientific-muted">
          <Lock className="h-8 w-8 mx-auto text-scientific-muted" />
          <p>No simulated comparison data is shown until real solver modules are connected.</p>
        </CardContent>
      </Card>
    </div>
  )
}
