import React from 'react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { Alert } from '../components/ui/Alert'
import { Lock } from 'lucide-react'

export const QuantumLabPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Alert variant="info" title="Phase 5 Quantum Engine (QAOA Simulation)">
        The Quantum Lab will execute variational Quantum Approximate Optimization Algorithm (QAOA)
        circuits via Qiskit and Qiskit Aer. Simulation results will be clearly labeled as numerical simulator
        traces, distinguishing ideal statevectors, shot noise, and physical device constraints.
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="accent">Ansatz Parameters</Badge>
              <Badge variant="outline">QAOA Depth</Badge>
            </div>
            <CardTitle className="mt-2">Variational Depth (p)</CardTitle>
            <CardDescription>
              Alternating application of cost H_C and mixer H_M unitary blocks:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <p>Parameter vectors &gamma; &isin; [0, 2&pi;]^p and &beta; &isin; [0, &pi;]^p.</p>
            <p className="text-slate-400">Supported depths: p &isin; [1, 5] on classical simulators.</p>
          </CardContent>
        </Card>

        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="violet">Classical Loop</Badge>
              <Badge variant="outline">Optimizer</Badge>
            </div>
            <CardTitle className="mt-2">COBYLA & SPSA</CardTitle>
            <CardDescription>
              Derivative-free parameter optimization over expectation values:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <p>&lang;&gamma;, &beta;| H_C |&gamma;, &beta;&rang; evaluated over shots.</p>
            <p className="text-slate-400">Tolerance, max iterations, and evaluation budgets tracked.</p>
          </CardContent>
        </Card>

        <Card className="bg-midnight-900/60 border-scientific-border space-y-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="gold">Simulation Backend</Badge>
              <Badge variant="outline">Qiskit Aer</Badge>
            </div>
            <CardTitle className="mt-2">Statevector & Shots</CardTitle>
            <CardDescription>
              Qubit scaling limits and noise modeling:
            </CardDescription>
          </CardHeader>
          <CardContent className="font-mono text-xs text-scientific-muted space-y-2">
            <p>Ideal statevector calculation up to 20 qubits.</p>
            <p className="text-slate-400">Controlled depolarizing and readout noise models in Phase 8.</p>
          </CardContent>
        </Card>
      </div>

      {/* Honest Disabled Execution Workspace */}
      <Card className="bg-midnight-900/40 border-scientific-border opacity-80">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>QAOA Circuit Execution Terminal</CardTitle>
            <Badge variant="warning">Scheduled for Phase 5</Badge>
          </div>
          <CardDescription>
            Qiskit Aer integration, circuit rendering, and convergence trace recording will activate in Phase 5.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-8 text-center space-y-3 font-mono text-xs text-scientific-muted">
          <Lock className="h-8 w-8 mx-auto text-scientific-muted" />
          <p>No simulated or mock quantum results are shown in Phase 1 to preserve scientific integrity.</p>
        </CardContent>
      </Card>
    </div>
  )
}
