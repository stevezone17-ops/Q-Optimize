import React from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Alert } from '../components/ui/Alert'
import { Lock } from 'lucide-react'

export const FormulationStudioPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Phase 3 Banner */}
      <Alert variant="info" title="Phase 3 Formulation Studio (Scheduled Next)">
        The mathematical formulation engine will convert canonical problems into upper-triangular
        QUBO matrices and Ising spin Hamiltonians. Energy equivalence between QUBO and Ising formulations
        will be exhaustively verified on all small instances.
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* QUBO Convention Card */}
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="accent">QUBO Formalism</Badge>
              <Badge variant="outline">0/1 Binary</Badge>
            </div>
            <CardTitle className="mt-2">Upper-Triangular QUBO Model</CardTitle>
            <CardDescription>
              Quadratic Unconstrained Binary Optimization standard convention:
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 font-mono text-xs">
            <div className="p-3 bg-midnight-950 rounded border border-scientific-border text-sky-300">
              <code>{"E(x) = x^T Q x + c = \\sum_i Q_{ii} x_i + \\sum_{i < j} Q_{ij} x_i x_j + c"}</code>
            </div>
            <p className="text-scientific-muted leading-relaxed">
              For constrained problems such as Assignment or TSP, equality constraints are incorporated
              via penalty terms &lambda; &middot; (&sum; x_i - 1)^2 to penalize infeasible states.
            </p>
          </CardContent>
        </Card>

        {/* Ising Hamiltonian Card */}
        <Card className="bg-midnight-900/60 border-scientific-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="violet">Ising Spin Hamiltonian</Badge>
              <Badge variant="outline">&plusmn;1 Spins</Badge>
            </div>
            <CardTitle className="mt-2">Pauli-Z Spin Transformation</CardTitle>
            <CardDescription>
              Mapping binary decision variables to spin-1/2 observables:
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 font-mono text-xs">
            <div className="p-3 bg-midnight-950 rounded border border-scientific-border text-purple-300">
              <code>{"x_i = (1 - s_i) / 2, \\quad s_i \\in \\{-1, +1\\} \\implies \\hat{H}_C = \\sum_i h_i \\hat{Z}_i + \\sum_{i < j} J_{ij} \\hat{Z}_i \\hat{Z}_j"}</code>
            </div>
            <p className="text-scientific-muted leading-relaxed">
              The cost Hamiltonian H_C drives QAOA variational evolution. Signs, energy offsets, and
              coupling constants J_ij will be verified against brute-force evaluations.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Disabled Interactive Preview Area */}
      <Card className="bg-midnight-900/40 border-scientific-border opacity-80">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Formulation Generator & Matrix Inspector</CardTitle>
            <Badge variant="warning">Activation: Phase 3</Badge>
          </div>
          <CardDescription>
            Once Phase 3 is implemented, selecting any registered problem will display its full QUBO matrix,
            variable ordering vector, penalty bounds, and Ising transformation table here.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-8 text-center space-y-3 font-mono text-xs text-scientific-muted">
          <Lock className="h-8 w-8 mx-auto text-scientific-muted" />
          <p>Register a problem in the Problem Builder to prepare for Phase 3 formulation generation.</p>
        </CardContent>
      </Card>
    </div>
  )
}
