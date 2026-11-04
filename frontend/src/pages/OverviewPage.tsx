import React from 'react'
import { NavigationItemKey, ProblemType } from '../types'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { HealthStatus } from '../hooks/useBackendHealth'
import {
  Plus,
  CheckCircle2,
  HelpCircle,
  ArrowRight,
  FolderOpen,
} from 'lucide-react'

interface OverviewPageProps {
  onNavigate: (tab: NavigationItemKey) => void
  onSelectProblemType: (type: ProblemType) => void
  healthStatus: HealthStatus
  backendVersion?: string
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  onNavigate,
  onSelectProblemType,
  healthStatus,
  backendVersion,
}) => {
  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="p-6 rounded-2xl border border-scientific-border bg-gradient-to-r from-midnight-900 via-midnight-900/80 to-midnight-850 relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-sky-500/5 to-transparent pointer-events-none" />
        <div className="max-w-3xl space-y-3 relative z-10">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono uppercase tracking-wider text-scientific-accent font-semibold">
              Research Computing Platform
            </span>
            <span className="text-scientific-muted">&bull;</span>
            <Badge variant="accent" size="sm">
              Phase 1 Active
            </Badge>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            Welcome to Q-Optimize
          </h2>
          <p className="text-xs text-scientific-muted leading-relaxed font-mono">
            Define combinatorial optimization problems, inspect mathematical formulations, run
            exact classical algorithms and QAOA quantum simulations, and evaluate outcomes with
            independent verification.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => onNavigate('problem-builder')}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Build New Problem
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate('learn')}
              leftIcon={<HelpCircle className="h-4 w-4" />}
            >
              Explore Knowledge Base
            </Button>
          </div>
        </div>
      </div>

      {/* Quick Start Actions */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
            Quick Start Problem Templates
          </h3>
          <span className="text-[11px] text-scientific-muted font-mono">
            Select a template to configure in Problem Builder
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            type="button"
            onClick={() => {
              onSelectProblemType('max_cut')
              onNavigate('problem-builder')
            }}
            className="text-left p-4 rounded-xl border border-scientific-border bg-midnight-900/60 hover:bg-midnight-850 hover:border-sky-500/40 transition-all group"
          >
            <div className="flex items-center justify-between mb-2">
              <Badge variant="accent" size="sm">
                MAX-CUT
              </Badge>
              <ArrowRight className="h-3.5 w-3.5 text-scientific-muted group-hover:text-scientific-accent transition-colors" />
            </div>
            <h4 className="text-sm font-semibold text-white group-hover:text-sky-300 transition-colors">
              Graph Max-Cut
            </h4>
            <p className="text-xs text-scientific-muted mt-1 leading-relaxed">
              Define graph vertices and weighted edges. Formulates directly to QUBO without penalty terms.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              onSelectProblemType('assignment')
              onNavigate('problem-builder')
            }}
            className="text-left p-4 rounded-xl border border-scientific-border bg-midnight-900/60 hover:bg-midnight-850 hover:border-purple-500/40 transition-all group"
          >
            <div className="flex items-center justify-between mb-2">
              <Badge variant="violet" size="sm">
                ASSIGNMENT
              </Badge>
              <ArrowRight className="h-3.5 w-3.5 text-scientific-muted group-hover:text-purple-400 transition-colors" />
            </div>
            <h4 className="text-sm font-semibold text-white group-hover:text-purple-300 transition-colors">
              Linear Assignment
            </h4>
            <p className="text-xs text-scientific-muted mt-1 leading-relaxed">
              Define agents, tasks, and cost matrix. Formulates with strict one-to-one matching constraints.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              onSelectProblemType('tsp')
              onNavigate('problem-builder')
            }}
            className="text-left p-4 rounded-xl border border-scientific-border bg-midnight-900/60 hover:bg-midnight-850 hover:border-amber-500/40 transition-all group"
          >
            <div className="flex items-center justify-between mb-2">
              <Badge variant="gold" size="sm">
                TSP
              </Badge>
              <ArrowRight className="h-3.5 w-3.5 text-scientific-muted group-hover:text-amber-400 transition-colors" />
            </div>
            <h4 className="text-sm font-semibold text-white group-hover:text-amber-300 transition-colors">
              Travelling Salesperson
            </h4>
            <p className="text-xs text-scientific-muted mt-1 leading-relaxed">
              Define cities and inter-city distance matrix. Formulates tour with subtour elimination penalties.
            </p>
          </button>
        </div>
      </div>

      {/* Grid: System Status & Honest Recent Experiments Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Experiments (Honest Empty State) */}
        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
            Recent Experiment Activity
          </h3>

          <div className="p-8 rounded-xl border border-scientific-border bg-midnight-900/40 flex flex-col items-center justify-center text-center space-y-3">
            <div className="p-3 rounded-full bg-midnight-800 border border-scientific-border text-scientific-muted">
              <FolderOpen className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white">No Experiments Recorded Yet</h4>
              <p className="text-xs text-scientific-muted max-w-md mx-auto mt-1 leading-relaxed font-mono">
                Solver engines and background experiment logging will activate in Phases 4 & 5.
                Start by constructing a canonical problem definition in the Problem Builder.
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onNavigate('problem-builder')}
              leftIcon={<Plus className="h-3.5 w-3.5" />}
            >
              Create First Problem
            </Button>
          </div>
        </div>

        {/* System & Architecture Status */}
        <div className="space-y-3">
          <h3 className="text-xs font-semibold text-slate-300 font-mono uppercase tracking-wider">
            Engine Readiness
          </h3>

          <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-scientific-border/60">
              <span className="text-scientific-muted">Platform Core</span>
              <Badge variant="accent" size="sm">
                v{backendVersion || '0.1.0'}
              </Badge>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">FastAPI Engine</span>
                <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
                  <CheckCircle2 className="h-3 w-3" /> Ready
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300">Problem Validation</span>
                <span className="text-emerald-400 flex items-center gap-1 text-[11px]">
                  <CheckCircle2 className="h-3 w-3" /> Phase 1 Active
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300">QUBO/Ising Engine</span>
                <span className="text-slate-400 text-[11px]">Phase 3</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300">Classical Solvers</span>
                <span className="text-slate-400 text-[11px]">Phase 4</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300">QAOA Simulator</span>
                <span className="text-slate-400 text-[11px]">Phase 5</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-300">Adaptive Scheduler</span>
                <span className="text-slate-400 text-[11px]">Phase 6</span>
              </div>
            </div>

            <div className="pt-2 border-t border-scientific-border/60 text-[11px] text-scientific-muted">
              Connected: {healthStatus === 'connected' ? 'Active Localhost' : 'Connecting...'}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
