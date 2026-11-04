import React, { useState } from 'react'
import { ProblemType, ProblemInstance, MaxCutInstance, AssignmentInstance, TSPInstance } from '../../types'
import { Badge } from '../../components/ui/Badge'
import { Code, BookOpen } from 'lucide-react'

interface ProblemPreviewProps {
  problemType: ProblemType
  name: string
  description?: string
  instance: ProblemInstance
}

export const ProblemPreview: React.FC<ProblemPreviewProps> = ({
  problemType,
  name,
  description,
  instance,
}) => {
  const [activeTab, setActiveTab] = useState<'math' | 'canonical'>('math')

  // Calculate mathematical properties
  let variableCount = 0
  let objectiveType = 'Maximize'
  let formulaDisplay = ''

  if (problemType === 'max_cut') {
    const mc = instance as MaxCutInstance
    variableCount = mc.nodes.length
    objectiveType = 'Maximize Cut'
    formulaDisplay = `C(x) = \\sum_{(i,j) \\in E} w_{ij} \\cdot (x_i(1-x_j) + x_j(1-x_i)), \\quad x_i \\in \\{0, 1\\}`
  } else if (problemType === 'assignment') {
    const assign = instance as AssignmentInstance
    variableCount = assign.agents.length * assign.tasks.length
    objectiveType = 'Minimize Cost'
    formulaDisplay = `\\min \\sum_{i=1}^{n} \\sum_{j=1}^{m} C_{ij} x_{ij} \\quad \\text{s.t.} \\sum_{j} x_{ij} = 1, \\sum_{i} x_{ij} = 1`
  } else if (problemType === 'tsp') {
    const tsp = instance as TSPInstance
    variableCount = tsp.cities.length * tsp.cities.length
    objectiveType = 'Minimize Distance'
    formulaDisplay = `\\min \\sum_{i} \\sum_{j} d_{ij} x_{ij} \\quad \\text{s.t. Hamiltonian cycle constraints}`
  }

  return (
    <div className="p-5 rounded-xl border border-scientific-border bg-midnight-900/50 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-scientific-border/60 pb-3">
        <div>
          <h4 className="text-xs font-semibold text-white font-mono uppercase tracking-wider">
            Canonical Problem Specification
          </h4>
          <p className="text-[11px] text-scientific-muted">
            Independent problem definition prior to solver formulation
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-midnight-950 p-1 rounded-lg border border-scientific-border">
          <button
            type="button"
            onClick={() => setActiveTab('math')}
            className={`text-xs px-2.5 py-1 rounded font-mono transition-colors flex items-center gap-1.5 ${
              activeTab === 'math'
                ? 'bg-midnight-800 text-scientific-accent border border-scientific-accent/30 font-semibold'
                : 'text-scientific-muted hover:text-slate-300'
            }`}
          >
            <BookOpen className="h-3 w-3" />
            Math Model
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('canonical')}
            className={`text-xs px-2.5 py-1 rounded font-mono transition-colors flex items-center gap-1.5 ${
              activeTab === 'canonical'
                ? 'bg-midnight-800 text-scientific-accent border border-scientific-accent/30 font-semibold'
                : 'text-scientific-muted hover:text-slate-300'
            }`}
          >
            <Code className="h-3 w-3" />
            Canonical JSON
          </button>
        </div>
      </div>

      {/* Property Badges */}
      <div className="flex flex-wrap gap-2 text-xs font-mono">
        <Badge variant="accent">Family: {problemType.toUpperCase()}</Badge>
        <Badge variant="violet">Objective: {objectiveType}</Badge>
        <Badge variant="gold">Decision Variables: {variableCount}</Badge>
        <Badge variant="default">Schema: v1.0</Badge>
      </div>

      {/* Tab Content */}
      {activeTab === 'math' ? (
        <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border/80 font-mono text-xs space-y-3">
          <div className="text-[11px] text-scientific-muted">Mathematical Formulation:</div>
          <div className="p-3 bg-midnight-900 rounded border border-scientific-border/60 text-sky-300 overflow-x-auto">
            <code>{formulaDisplay}</code>
          </div>
          <div className="text-[11px] text-scientific-muted">Problem Scope:</div>
          <p className="text-slate-300 text-xs">
            {description || 'Standard combinatorial instance configured for independent verification.'}
          </p>
        </div>
      ) : (
        <div className="relative">
          <pre className="p-4 rounded-lg bg-midnight-950 border border-scientific-border/80 font-mono text-xs text-slate-300 max-h-60 overflow-y-auto">
            {JSON.stringify(
              {
                name,
                problem_type: problemType,
                schema_version: '1.0',
                instance,
              },
              null,
              2
            )}
          </pre>
        </div>
      )}
    </div>
  )
}
