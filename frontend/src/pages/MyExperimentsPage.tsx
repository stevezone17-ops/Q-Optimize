import React from 'react'
import { Card, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { FolderKanban, Search, Filter } from 'lucide-react'

export const MyExperimentsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Top Filter Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-scientific-border bg-midnight-900/60">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-3 top-2.5 text-scientific-muted" />
            <input
              type="text"
              disabled
              placeholder="Filter experiments by ID or solver..."
              className="h-9 pl-9 pr-3 rounded-lg border border-scientific-border bg-midnight-950 text-xs font-mono text-slate-300 placeholder:text-slate-600 focus:outline-none w-64 cursor-not-allowed opacity-60"
            />
          </div>

          <button
            type="button"
            disabled
            className="flex items-center gap-1.5 h-9 px-3 rounded-lg border border-scientific-border bg-midnight-950 text-xs font-mono text-scientific-muted cursor-not-allowed opacity-60"
          >
            <Filter className="h-3.5 w-3.5" />
            <span>All Solvers</span>
          </button>
        </div>

        <Badge variant="outline" size="md">
          Phase 8 Provenance Tracking
        </Badge>
      </div>

      {/* Honest Empty State */}
      <Card className="bg-midnight-900/40 border-scientific-border">
        <CardContent className="py-16 flex flex-col items-center justify-center text-center space-y-4">
          <div className="p-4 rounded-full bg-midnight-800 border border-scientific-border text-scientific-muted">
            <FolderKanban className="h-8 w-8" />
          </div>

          <div className="space-y-1">
            <h3 className="text-sm font-semibold text-white">No Experiments Logged Yet</h3>
            <p className="text-xs text-scientific-muted max-w-md mx-auto leading-relaxed font-mono">
              In Phase 8, background Celery/Redis worker queues will persist complete experiment runs
              including solver configurations, random seeds, hardware metadata, and raw bitstring measurements.
            </p>
          </div>

          <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border/60 max-w-lg text-left text-xs font-mono text-slate-400 space-y-1.5">
            <span className="text-sky-400 font-semibold text-[11px] uppercase block">
              Planned Provenance Record Fields:
            </span>
            <div className="flex justify-between">
              <span>&bull; experiment_id</span>
              <span className="text-slate-400">UUIDv4</span>
            </div>
            <div className="flex justify-between">
              <span>&bull; problem_snapshot</span>
              <span className="text-slate-400">Canonical JSON instance</span>
            </div>
            <div className="flex justify-between">
              <span>&bull; random_seed</span>
              <span className="text-slate-400">Integer control</span>
            </div>
            <div className="flex justify-between">
              <span>&bull; solver_version & environment</span>
              <span className="text-slate-400">Qiskit/NumPy versions</span>
            </div>
            <div className="flex justify-between">
              <span>&bull; independent_evaluator_result</span>
              <span className="text-emerald-400">Recomputed objective & feasibility</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
