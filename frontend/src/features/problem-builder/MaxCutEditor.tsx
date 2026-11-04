import React, { useState } from 'react'
import { MaxCutInstance } from '../../types'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Plus, Trash2, AlertTriangle } from 'lucide-react'

interface MaxCutEditorProps {
  value: MaxCutInstance
  onChange: (val: MaxCutInstance) => void
  error?: string | null
}

const PRESETS: { name: string; instance: MaxCutInstance }[] = [
  {
    name: 'Triangle Graph (K3)',
    instance: {
      nodes: ['0', '1', '2'],
      edges: [
        ['0', '1', 1.0],
        ['1', '2', 1.0],
        ['2', '0', 1.0],
      ],
    },
  },
  {
    name: 'Complete Graph (K4)',
    instance: {
      nodes: ['A', 'B', 'C', 'D'],
      edges: [
        ['A', 'B', 1.0],
        ['A', 'C', 1.0],
        ['A', 'D', 1.0],
        ['B', 'C', 1.0],
        ['B', 'D', 1.0],
        ['C', 'D', 1.0],
      ],
    },
  },
  {
    name: '5-Cycle Ring (C5)',
    instance: {
      nodes: ['V1', 'V2', 'V3', 'V4', 'V5'],
      edges: [
        ['V1', 'V2', 2.0],
        ['V2', 'V3', 2.0],
        ['V3', 'V4', 2.0],
        ['V4', 'V5', 2.0],
        ['V5', 'V1', 2.0],
      ],
    },
  },
  {
    name: 'Weighted Butterfly Graph',
    instance: {
      nodes: ['Center', 'L1', 'L2', 'R1', 'R2'],
      edges: [
        ['Center', 'L1', 3.0],
        ['Center', 'L2', 3.0],
        ['L1', 'L2', 1.5],
        ['Center', 'R1', 2.5],
        ['Center', 'R2', 2.5],
        ['R1', 'R2', 1.0],
      ],
    },
  },
]

export const MaxCutEditor: React.FC<MaxCutEditorProps> = ({
  value,
  onChange,
  error,
}) => {
  const [newNodeName, setNewNodeName] = useState('')
  const [edgeSource, setEdgeSource] = useState(value.nodes[0] || '')
  const [edgeTarget, setEdgeTarget] = useState(value.nodes[1] || '')
  const [edgeWeight, setEdgeWeight] = useState('1.0')
  const [edgeError, setEdgeError] = useState<string | null>(null)

  const handleAddNode = () => {
    const trimmed = newNodeName.trim()
    if (!trimmed) return
    if (value.nodes.includes(trimmed)) {
      setEdgeError(`Node "${trimmed}" already exists.`)
      return
    }
    setEdgeError(null)
    const updatedNodes = [...value.nodes, trimmed]
    onChange({
      ...value,
      nodes: updatedNodes,
    })
    setNewNodeName('')
    if (!edgeSource) setEdgeSource(trimmed)
    else if (!edgeTarget) setEdgeTarget(trimmed)
  }

  const handleRemoveNode = (nodeToRemove: string) => {
    if (value.nodes.length <= 2) {
      setEdgeError('Max-Cut problem requires at least 2 nodes.')
      return
    }
    const updatedNodes = value.nodes.filter((n) => n !== nodeToRemove)
    const updatedEdges = value.edges.filter(
      ([u, v]) => u !== nodeToRemove && v !== nodeToRemove
    )
    onChange({
      nodes: updatedNodes,
      edges: updatedEdges,
    })
    setEdgeError(null)
  }

  const handleAddEdge = () => {
    if (!edgeSource || !edgeTarget) {
      setEdgeError('Please select both source and target nodes.')
      return
    }
    if (edgeSource === edgeTarget) {
      setEdgeError('Self-loops are not permitted in Max-Cut.')
      return
    }
    const weightNum = parseFloat(edgeWeight)
    if (isNaN(weightNum)) {
      setEdgeError('Edge weight must be a valid number.')
      return
    }

    // Check duplicate
    const exists = value.edges.some(
      ([u, v]) =>
        (u === edgeSource && v === edgeTarget) || (u === edgeTarget && v === edgeSource)
    )
    if (exists) {
      setEdgeError(`An edge already exists between ${edgeSource} and ${edgeTarget}.`)
      return
    }

    setEdgeError(null)
    onChange({
      ...value,
      edges: [...value.edges, [edgeSource, edgeTarget, weightNum]],
    })
  }

  const handleRemoveEdge = (index: number) => {
    const updated = [...value.edges]
    updated.splice(index, 1)
    onChange({ ...value, edges: updated })
  }

  const handleLoadPreset = (preset: (typeof PRESETS)[0]) => {
    onChange(preset.instance)
    setEdgeSource(preset.instance.nodes[0] || '')
    setEdgeTarget(preset.instance.nodes[1] || '')
    setEdgeError(null)
  }

  // Calculate live statistics
  const numNodes = value.nodes.length
  const numEdges = value.edges.length
  const maxPossibleEdges = (numNodes * (numNodes - 1)) / 2
  const density = maxPossibleEdges > 0 ? (numEdges / maxPossibleEdges).toFixed(2) : '0'
  const totalWeight = value.edges.reduce((sum, [, , w]) => sum + w, 0).toFixed(1)

  return (
    <div className="space-y-5">
      {/* Presets Bar */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-midnight-900/60 rounded-lg border border-scientific-border/80">
        <span className="text-xs text-scientific-muted font-mono mr-1">Instance Presets:</span>
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

      {/* Grid: Graph Parameters & Interactive Edge List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Nodes Section */}
        <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Graph Vertices ({numNodes})
            </h4>
            <span className="text-[11px] text-scientific-muted font-mono">Min: 2 Nodes</span>
          </div>

          <div className="flex gap-2">
            <Input
              placeholder="e.g. Node_X"
              value={newNodeName}
              onChange={(e) => setNewNodeName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddNode()}
              className="text-xs font-mono"
            />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleAddNode}
              leftIcon={<Plus className="h-3.5 w-3.5" />}
            >
              Add Node
            </Button>
          </div>

          <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-1">
            {value.nodes.map((node) => (
              <span
                key={node}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-midnight-800 border border-scientific-border text-xs font-mono text-slate-200 group"
              >
                <span>{node}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveNode(node)}
                  className="text-slate-400 hover:text-rose-400 transition-colors ml-1"
                  title="Remove node"
                >
                  &times;
                </button>
              </span>
            ))}
          </div>

          {/* Graph Metrics */}
          <div className="pt-3 border-t border-scientific-border/60 grid grid-cols-4 gap-2 text-center">
            <div className="p-2 rounded bg-midnight-950 border border-scientific-border/40">
              <div className="text-[10px] text-scientific-muted font-mono">Nodes |V|</div>
              <div className="text-sm font-semibold text-scientific-accent font-mono">{numNodes}</div>
            </div>
            <div className="p-2 rounded bg-midnight-950 border border-scientific-border/40">
              <div className="text-[10px] text-scientific-muted font-mono">Edges |E|</div>
              <div className="text-sm font-semibold text-sky-400 font-mono">{numEdges}</div>
            </div>
            <div className="p-2 rounded bg-midnight-950 border border-scientific-border/40">
              <div className="text-[10px] text-scientific-muted font-mono">Density</div>
              <div className="text-sm font-semibold text-purple-400 font-mono">{density}</div>
            </div>
            <div className="p-2 rounded bg-midnight-950 border border-scientific-border/40">
              <div className="text-[10px] text-scientific-muted font-mono">Total W</div>
              <div className="text-sm font-semibold text-amber-400 font-mono">{totalWeight}</div>
            </div>
          </div>
        </div>

        {/* Edges Section */}
        <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Graph Edges ({numEdges})
            </h4>
            <span className="text-[11px] text-scientific-muted font-mono">Undirected Triplet (u, v, w)</span>
          </div>

          {/* Add Edge Row */}
          <div className="grid grid-cols-4 gap-2 items-center">
            <select
              value={edgeSource}
              onChange={(e) => setEdgeSource(e.target.value)}
              className="h-9 rounded-lg border border-scientific-border bg-midnight-900 px-2 text-xs font-mono text-slate-200"
            >
              {value.nodes.map((n) => (
                <option key={`src-${n}`} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <select
              value={edgeTarget}
              onChange={(e) => setEdgeTarget(e.target.value)}
              className="h-9 rounded-lg border border-scientific-border bg-midnight-900 px-2 text-xs font-mono text-slate-200"
            >
              {value.nodes.map((n) => (
                <option key={`tgt-${n}`} value={n}>
                  {n}
                </option>
              ))}
            </select>
            <Input
              type="number"
              step="0.5"
              placeholder="Weight"
              value={edgeWeight}
              onChange={(e) => setEdgeWeight(e.target.value)}
              className="text-xs font-mono h-9"
            />
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleAddEdge}
              leftIcon={<Plus className="h-3.5 w-3.5" />}
              className="h-9"
            >
              Add
            </Button>
          </div>

          {edgeError && (
            <p className="text-xs text-rose-400 font-mono flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" /> {edgeError}
            </p>
          )}

          {/* Edge List Table */}
          <div className="max-h-48 overflow-y-auto border border-scientific-border/80 rounded-lg divide-y divide-scientific-border/40 bg-midnight-950/60">
            {value.edges.length === 0 ? (
              <div className="p-4 text-center text-xs text-scientific-muted font-mono">
                No edges added yet. Add an edge above to connect nodes.
              </div>
            ) : (
              value.edges.map(([u, v, w], idx) => (
                <div
                  key={`${u}-${v}-${idx}`}
                  className="flex items-center justify-between px-3 py-2 text-xs font-mono hover:bg-midnight-900/60 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sky-400 font-semibold">{u}</span>
                    <span className="text-scientific-muted">&harr;</span>
                    <span className="text-purple-400 font-semibold">{v}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                      w = {w}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemoveEdge(idx)}
                      className="text-slate-400 hover:text-rose-400 transition-colors p-1"
                      title="Remove edge"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* SVG Canvas Graph Visualization */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/30">
        <h4 className="text-xs font-semibold text-slate-300 font-mono mb-3">
          Interactive Topological Preview
        </h4>
        <div className="h-56 w-full flex items-center justify-center bg-midnight-950/80 rounded-lg border border-scientific-border/60 relative overflow-hidden">
          <svg className="w-full h-full" viewBox="0 0 500 220">
            {/* Draw Graph in circle */}
            {(() => {
              const cx = 250
              const cy = 110
              const r = Math.min(cx, cy) - 35
              const nodePositions: Record<string, { x: number; y: number }> = {}

              value.nodes.forEach((node, i) => {
                const angle = (2 * Math.PI * i) / value.nodes.length - Math.PI / 2
                nodePositions[node] = {
                  x: cx + r * Math.cos(angle),
                  y: cy + r * Math.sin(angle),
                }
              })

              return (
                <>
                  {/* Edges */}
                  {value.edges.map(([u, v, w], idx) => {
                    const p1 = nodePositions[u]
                    const p2 = nodePositions[v]
                    if (!p1 || !p2) return null
                    const midX = (p1.x + p2.x) / 2
                    const midY = (p1.y + p2.y) / 2
                    return (
                      <g key={`edge-line-${idx}`}>
                        <line
                          x1={p1.x}
                          y1={p1.y}
                          x2={p2.x}
                          y2={p2.y}
                          stroke="#38BDF8"
                          strokeWidth="1.8"
                          strokeOpacity="0.6"
                        />
                        <rect
                          x={midX - 12}
                          y={midY - 8}
                          width="24"
                          height="16"
                          rx="4"
                          fill="#0A0F1D"
                          stroke="#1E293B"
                          strokeWidth="1"
                        />
                        <text
                          x={midX}
                          y={midY + 3}
                          textAnchor="middle"
                          fill="#F59E0B"
                          fontSize="9"
                          fontFamily="monospace"
                        >
                          {w}
                        </text>
                      </g>
                    )
                  })}

                  {/* Nodes */}
                  {value.nodes.map((node) => {
                    const pos = nodePositions[node]
                    if (!pos) return null
                    return (
                      <g key={`node-circle-${node}`}>
                        <circle
                          cx={pos.x}
                          cy={pos.y}
                          r="16"
                          fill="#131D32"
                          stroke="#8B5CF6"
                          strokeWidth="2"
                        />
                        <text
                          x={pos.x}
                          y={pos.y + 4}
                          textAnchor="middle"
                          fill="#FFFFFF"
                          fontSize="11"
                          fontWeight="bold"
                          fontFamily="monospace"
                        >
                          {node}
                        </text>
                      </g>
                    )
                  })}
                </>
              )
            })()}
          </svg>
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
