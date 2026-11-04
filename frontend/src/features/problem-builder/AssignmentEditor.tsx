import React, { useState } from 'react'
import { AssignmentInstance } from '../../types'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Plus, Trash2, AlertTriangle } from 'lucide-react'

interface AssignmentEditorProps {
  value: AssignmentInstance
  onChange: (val: AssignmentInstance) => void
  error?: string | null
}

const PRESETS: { name: string; instance: AssignmentInstance }[] = [
  {
    name: '2x2 Task Allocation',
    instance: {
      agents: ['Agent_1', 'Agent_2'],
      tasks: ['Job_A', 'Job_B'],
      cost_matrix: [
        [4.0, 7.0],
        [6.0, 3.0],
      ],
    },
  },
  {
    name: '3x3 Production Balancing',
    instance: {
      agents: ['Worker_A', 'Worker_B', 'Worker_C'],
      tasks: ['Assembly', 'Inspection', 'Packaging'],
      cost_matrix: [
        [9.0, 2.0, 7.0],
        [6.0, 4.0, 3.0],
        [5.0, 8.0, 1.0],
      ],
    },
  },
  {
    name: '4x4 Distributed Server Match',
    instance: {
      agents: ['VM_1', 'VM_2', 'VM_3', 'VM_4'],
      tasks: ['Ingest', 'Index', 'Compute', 'Storage'],
      cost_matrix: [
        [12.0, 8.0, 7.0, 15.0],
        [7.0, 9.0, 17.0, 14.0],
        [10.0, 14.0, 6.0, 8.0],
        [13.0, 7.0, 11.0, 9.0],
      ],
    },
  },
]

export const AssignmentEditor: React.FC<AssignmentEditorProps> = ({
  value,
  onChange,
  error,
}) => {
  const [newAgent, setNewAgent] = useState('')
  const [newTask, setNewTask] = useState('')
  const [localError, setLocalError] = useState<string | null>(null)

  const handleCellChange = (rowIndex: number, colIndex: number, valStr: string) => {
    const num = parseFloat(valStr) || 0.0
    const newMatrix = value.cost_matrix.map((row, rIdx) =>
      rIdx === rowIndex ? row.map((cell, cIdx) => (cIdx === colIndex ? num : cell)) : [...row]
    )
    onChange({
      ...value,
      cost_matrix: newMatrix,
    })
  }

  const handleAddDimension = () => {
    const aName = newAgent.trim() || `Agent_${value.agents.length + 1}`
    const tName = newTask.trim() || `Task_${value.tasks.length + 1}`

    if (value.agents.includes(aName)) {
      setLocalError(`Agent name "${aName}" already exists.`)
      return
    }
    if (value.tasks.includes(tName)) {
      setLocalError(`Task name "${tName}" already exists.`)
      return
    }

    setLocalError(null)
    const newAgents = [...value.agents, aName]
    const newTasks = [...value.tasks, tName]

    // Expand cost matrix
    const newMatrix = value.cost_matrix.map((row) => [...row, 5.0])
    newMatrix.push(new Array(newTasks.length).fill(5.0))

    onChange({
      agents: newAgents,
      tasks: newTasks,
      cost_matrix: newMatrix,
    })

    setNewAgent('')
    setNewTask('')
  }

  const handleRemoveDimension = (index: number) => {
    if (value.agents.length <= 1) {
      setLocalError('Assignment problem requires at least 1 agent and 1 task.')
      return
    }

    const newAgents = value.agents.filter((_, i) => i !== index)
    const newTasks = value.tasks.filter((_, i) => i !== index)
    const newMatrix = value.cost_matrix
      .filter((_, i) => i !== index)
      .map((row) => row.filter((_, j) => j !== index))

    onChange({
      agents: newAgents,
      tasks: newTasks,
      cost_matrix: newMatrix,
    })
    setLocalError(null)
  }

  const handleLoadPreset = (preset: (typeof PRESETS)[0]) => {
    onChange(preset.instance)
    setLocalError(null)
  }

  return (
    <div className="space-y-5">
      {/* Presets Bar */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-midnight-900/60 rounded-lg border border-scientific-border/80">
        <span className="text-xs text-scientific-muted font-mono mr-1">Cost Presets:</span>
        {PRESETS.map((p) => (
          <button
            key={p.name}
            type="button"
            onClick={() => handleLoadPreset(p)}
            className="text-xs px-2.5 py-1 rounded bg-midnight-800 hover:bg-midnight-700 text-slate-300 hover:text-white border border-scientific-border transition-colors font-mono"
          >
            {p.name}
          </button>
        ))}
      </div>

      {/* Dimension Management */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Problem Dimension: {value.agents.length} &times; {value.tasks.length}
          </h4>
          <span className="text-[11px] text-scientific-muted font-mono">
            Bipartite Matching Form
          </span>
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="Agent name (e.g. Server_A)"
            value={newAgent}
            onChange={(e) => setNewAgent(e.target.value)}
            className="text-xs font-mono"
          />
          <Input
            placeholder="Task name (e.g. Job_1)"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            className="text-xs font-mono"
          />
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleAddDimension}
            leftIcon={<Plus className="h-3.5 w-3.5" />}
          >
            Add Dimension
          </Button>
        </div>

        {localError && (
          <p className="text-xs text-rose-400 font-mono flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" /> {localError}
          </p>
        )}
      </div>

      {/* Cost Matrix Grid Editor */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Interactive Cost Matrix (C[i, j])
          </h4>
          <span className="text-[11px] text-scientific-muted font-mono">
            Objective: Minimize Total Cost &sum; C[i, j] &middot; x[i, j]
          </span>
        </div>

        <div className="overflow-x-auto border border-scientific-border/80 rounded-lg bg-midnight-950/80">
          <table className="w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-midnight-900/90 border-b border-scientific-border text-scientific-muted">
                <th className="p-2.5 text-left border-r border-scientific-border/60">
                  Agent \ Task
                </th>
                {value.tasks.map((task, tIdx) => (
                  <th key={`th-${tIdx}`} className="p-2.5 text-center min-w-[90px]">
                    <span className="text-purple-400 font-semibold">{task}</span>
                  </th>
                ))}
                <th className="p-2.5 text-center w-12">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-scientific-border/40">
              {value.agents.map((agent, rIdx) => (
                <tr key={`row-${rIdx}`} className="hover:bg-midnight-900/40 transition-colors">
                  <td className="p-2.5 font-semibold text-sky-400 border-r border-scientific-border/60">
                    {agent}
                  </td>
                  {value.tasks.map((_, cIdx) => (
                    <td key={`cell-${rIdx}-${cIdx}`} className="p-1.5 text-center">
                      <input
                        type="number"
                        step="0.5"
                        value={value.cost_matrix[rIdx]?.[cIdx] ?? 0}
                        onChange={(e) => handleCellChange(rIdx, cIdx, e.target.value)}
                        className="w-20 text-center rounded border border-scientific-border/80 bg-midnight-900 px-2 py-1 text-slate-200 focus:outline-none focus:ring-1 focus:ring-scientific-accent focus:border-scientific-accent font-mono"
                      />
                    </td>
                  ))}
                  <td className="p-2 text-center">
                    <button
                      type="button"
                      onClick={() => handleRemoveDimension(rIdx)}
                      className="text-slate-400 hover:text-rose-400 transition-colors p-1"
                      title="Remove dimension"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/30 border border-rose-500/30 rounded-lg text-xs text-rose-300 font-mono">
          {error}
        </div>
      )}
    </div>
  )
}
