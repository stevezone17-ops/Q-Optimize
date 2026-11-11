import React from 'react'
import {
  Layers,
  Cpu,
  Atom,
  Sliders,
  Scale,
  FolderKanban,
  BookOpen,
  Settings,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import { NavigationItemKey } from '../../types'
import { HealthStatus } from '../../hooks/useBackendHealth'
import { cn } from '../../utils/cn'

interface SidebarProps {
  activeTab: NavigationItemKey
  onSelectTab: (tab: NavigationItemKey) => void
  healthStatus: HealthStatus
  backendVersion?: string
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  healthStatus,
  backendVersion,
}) => {
  const navItems: { key: NavigationItemKey; label: string; icon: React.ReactNode; phaseBadge?: string }[] = [
    { key: 'overview', label: 'Overview', icon: <Layers className="h-4 w-4" /> },
    { key: 'problem-builder', label: 'Problem Builder', icon: <Cpu className="h-4 w-4" />, phaseBadge: 'Active' },
    { key: 'formulation-studio', label: 'Formulation Studio', icon: <Sliders className="h-4 w-4" />, phaseBadge: 'Phase 3' },
    { key: 'quantum-lab', label: 'Quantum Lab', icon: <Atom className="h-4 w-4" />, phaseBadge: 'Phase 5' },
    { key: 'classical-lab', label: 'Classical Lab', icon: <Cpu className="h-4 w-4" />, phaseBadge: 'Phase 4' },
    { key: 'comparison-lab', label: 'Comparison Lab', icon: <Scale className="h-4 w-4" />, phaseBadge: 'Phase 6' },
    { key: 'my-experiments', label: 'Experiments & Benchmarks', icon: <FolderKanban className="h-4 w-4" />, phaseBadge: 'Phase 8' },
    { key: 'learn', label: 'Learn', icon: <BookOpen className="h-4 w-4" /> },
    { key: 'settings', label: 'Settings', icon: <Settings className="h-4 w-4" /> },
  ]

  return (
    <aside className="w-64 border-r border-scientific-border bg-midnight-950 flex flex-col h-screen select-none shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-scientific-border/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-midnight-800 to-midnight-700 border border-scientific-border flex items-center justify-center p-1.5 shadow-sm">
            <img src="/logo.svg" alt="Q-Optimize Logo" className="h-full w-full object-contain" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-sm tracking-tight text-white font-mono">Q-Optimize</span>
              <span className="text-[10px] bg-sky-500/10 text-sky-400 font-mono px-1.5 py-0.5 rounded border border-sky-500/20">
                P1
              </span>
            </div>
            <p className="text-[10px] text-scientific-muted">Hybrid Quantum Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
          Workspace
        </div>

        {navItems.map((item) => {
          const isActive = activeTab === item.key
          return (
            <button
              key={item.key}
              onClick={() => onSelectTab(item.key)}
              className={cn(
                'w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group',
                isActive
                  ? 'bg-scientific-hover text-white shadow-sm border border-scientific-accent/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-midnight-900'
              )}
            >
              <div className="flex items-center gap-2.5">
                <span
                  className={cn(
                    'transition-colors',
                    isActive ? 'text-scientific-accent' : 'text-slate-400 group-hover:text-slate-200'
                  )}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
              {item.phaseBadge && (
                <span
                  className={cn(
                    'text-[9px] font-mono px-1.5 py-0.2 rounded',
                    item.phaseBadge === 'Active'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                      : 'bg-midnight-800 text-slate-400 border border-scientific-border/80'
                  )}
                >
                  {item.phaseBadge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Backend Status Bar */}
      <div className="p-3 border-t border-scientific-border/80 bg-midnight-900/60">
        <div className="rounded-lg border border-scientific-border/60 p-2.5 bg-midnight-950/70">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[11px] font-mono text-slate-400">FastAPI Backend</span>
            {healthStatus === 'connected' && (
              <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400">
                <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                Connected
              </span>
            )}
            {healthStatus === 'checking' && (
              <span className="inline-flex items-center gap-1 text-[10px] font-mono text-sky-400">
                <Loader2 className="h-3 w-3 animate-spin text-sky-400" />
                Checking
              </span>
            )}
            {healthStatus === 'disconnected' && (
              <span className="inline-flex items-center gap-1 text-[10px] font-mono text-rose-400">
                <AlertCircle className="h-3 w-3 text-rose-400" />
                Offline
              </span>
            )}
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>v{backendVersion || '0.1.0'}</span>
            <span className="text-slate-400">Port 8000</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
