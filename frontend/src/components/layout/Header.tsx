import React from 'react'
import { NavigationItemKey } from '../../types'
import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'
import { Plus, ExternalLink, HelpCircle } from 'lucide-react'

interface HeaderProps {
  activeTab: NavigationItemKey
  onSelectTab: (tab: NavigationItemKey) => void
  onOpenLanding: () => void
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onSelectTab,
  onOpenLanding,
}) => {
  const titles: Record<NavigationItemKey, { title: string; subtitle: string }> = {
    overview: {
      title: 'Platform Overview',
      subtitle: 'System readiness, canonical models, and rapid workflows',
    },
    'problem-builder': {
      title: 'Problem Builder',
      subtitle: 'Define, validate, and preview structured combinatorial optimization problems',
    },
    'formulation-studio': {
      title: 'Formulation Studio',
      subtitle: 'Inspect QUBO matrices, Ising spin terms, and penalty parameters',
    },
    'quantum-lab': {
      title: 'Quantum Lab',
      subtitle: 'QAOA parameterization, ansatz depth, and Qiskit circuit simulation',
    },
    'classical-lab': {
      title: 'Classical Lab',
      subtitle: 'Exact branch-and-bound, Genetic Algorithm, and Simulated Annealing baselines',
    },
    'comparison-lab': {
      title: 'Comparison Lab',
      subtitle: 'Controlled benchmark comparisons on identical canonical problem instances',
    },
    'my-experiments': {
      title: 'My Experiments',
      subtitle: 'Reproducible experiment runs, seeds, raw traces, and provenance',
    },
    learn: {
      title: 'Knowledge Base',
      subtitle: 'Theoretical foundations of hybrid optimization and rigorous benchmarking',
    },
    settings: {
      title: 'Platform Settings',
      subtitle: 'API endpoints, database status, and environment configuration',
    },
  }

  const current = titles[activeTab] || { title: 'Workspace', subtitle: '' }

  return (
    <header className="h-16 border-b border-scientific-border bg-midnight-950/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0 z-20">
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-sm font-semibold text-white tracking-tight">{current.title}</h1>
          <Badge variant="outline" size="sm">
            Phase 1
          </Badge>
        </div>
        <p className="text-[11px] text-scientific-muted">{current.subtitle}</p>
      </div>

      <div className="flex items-center gap-2.5">
        <Button
          variant="ghost"
          size="sm"
          onClick={onOpenLanding}
          leftIcon={<ExternalLink className="h-3.5 w-3.5" />}
        >
          Product Overview
        </Button>

        {activeTab !== 'problem-builder' && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSelectTab('problem-builder')}
            leftIcon={<Plus className="h-3.5 w-3.5" />}
          >
            New Problem
          </Button>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => onSelectTab('learn')}
          leftIcon={<HelpCircle className="h-3.5 w-3.5" />}
        >
          Docs
        </Button>
      </div>
    </header>
  )
}
