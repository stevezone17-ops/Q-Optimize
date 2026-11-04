import React, { useState } from 'react'
import { TSPInstance } from '../../types'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import { Plus, Trash2, AlertTriangle } from 'lucide-react'

interface TSPEditorProps {
  value: TSPInstance
  onChange: (val: TSPInstance) => void
  error?: string | null
}

const PRESETS: { name: string; instance: TSPInstance }[] = [
  {
    name: '3-City Triangle',
    instance: {
      cities: ['Paris', 'London', 'Berlin'],
      distance_matrix: [
        [0.0, 344.0, 878.0],
        [344.0, 0.0, 933.0],
        [878.0, 933.0, 0.0],
      ],
    },
  },
  {
    name: '4-City Circuit',
    instance: {
      cities: ['Rome', 'Geneva', 'Vienna', 'Madrid'],
      distance_matrix: [
        [0.0, 698.0, 765.0, 1365.0],
        [698.0, 0.0, 804.0, 1025.0],
        [765.0, 804.0, 0.0, 1809.0],
        [1365.0, 1025.0, 1809.0, 0.0],
      ],
    },
  },
  {
    name: '5-City Metric TSP',
    instance: {
      cities: ['City_1', 'City_2', 'City_3', 'City_4', 'City_5'],
      distance_matrix: [
        [0.0, 12.0, 29.0, 22.0, 15.0],
        [12.0, 0.0, 19.0, 31.0, 25.0],
        [29.0, 19.0, 0.0, 14.0, 18.0],
        [22.0, 31.0, 14.0, 0.0, 10.0],
        [15.0, 25.0, 18.0, 10.0, 0.0],
      ],
    },
  },
]

export const TSPEditor: React.FC<TSPEditorProps> = ({
  value,
  onChange,
  error,
}) => {
  const [newCity, setNewCity] = useState('')
  const [symmetricMode, setSymmetricMode] = useState(true)
  const [localError, setLocalError] = useState<string | null>(null)

  const handleCellChange = (rowIndex: number, colIndex: number, valStr: string) => {
    if (rowIndex === colIndex) return // Keep diagonal strictly 0.0
    const num = Math.max(0, parseFloat(valStr) || 0.0)

    const newMatrix = value.distance_matrix.map((row, rIdx) =>
      row.map((cell, cIdx) => {
        if (rIdx === rowIndex && cIdx === colIndex) return num
        if (symmetricMode && rIdx === colIndex && cIdx === rowIndex) return num
        return cell
      })
    )

    onChange({
      ...value,
      distance_matrix: newMatrix,
    })
  }

  const handleAddCity = () => {
    const cName = newCity.trim() || `City_${value.cities.length + 1}`
    if (value.cities.includes(cName)) {
      setLocalError(`City "${cName}" already exists.`)
      return
    }

    setLocalError(null)
    const newCities = [...value.cities, cName]
    const n = newCities.length

    // Expand matrix
    const newMatrix = value.distance_matrix.map((row) => [...row, 25.0])
    const newRow = new Array(n).fill(25.0)
    newRow[n - 1] = 0.0
    newMatrix.push(newRow)

    onChange({
      ...value,
      cities: newCities,
      distance_matrix: newMatrix,
    })
    setNewCity('')
  }

  const handleRemoveCity = (index: number) => {
    if (value.cities.length <= 3) {
      setLocalError('TSP problem requires at least 3 cities for a valid closed tour.')
      return
    }

    const newCities = value.cities.filter((_, i) => i !== index)
    const newMatrix = value.distance_matrix
      .filter((_, i) => i !== index)
      .map((row) => row.filter((_, j) => j !== index))

    onChange({
      ...value,
      cities: newCities,
      distance_matrix: newMatrix,
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
        <span className="text-xs text-scientific-muted font-mono mr-1">TSP Presets:</span>
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

      {/* City List & Mode Controls */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Cities ({value.cities.length})
          </h4>
          <label className="flex items-center gap-2 text-xs font-mono text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={symmetricMode}
              onChange={(e) => setSymmetricMode(e.target.checked)}
              className="rounded bg-midnight-900 border-scientific-border text-scientific-accent focus:ring-0"
            />
            <span>Symmetric Distances D[i,j] = D[j,i]</span>
          </label>
        </div>

        <div className="flex gap-2">
          <Input
            placeholder="e.g. Zurich"
            value={newCity}
            onChange={(e) => setNewCity(e.target.value)}
            className="text-xs font-mono"
          />
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={handleAddCity}
            leftIcon={<Plus className="h-3.5 w-3.5" />}
          >
            Add City
          </Button>
        </div>

        {localError && (
          <p className="text-xs text-rose-400 font-mono flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" /> {localError}
          </p>
        )}
      </div>

      {/* Distance Matrix Grid */}
      <div className="p-4 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
            Distance Matrix (D[i, j])
          </h4>
          <span className="text-[11px] text-scientific-muted font-mono">
            Hamiltonian Cycle Tour Evaluation
          </span>
        </div>

        <div className="overflow-x-auto border border-scientific-border/80 rounded-lg bg-midnight-950/80">
          <table className="w-full text-xs font-mono border-collapse">
            <thead>
              <tr className="bg-midnight-900/90 border-b border-scientific-border text-scientific-muted">
                <th className="p-2.5 text-left border-r border-scientific-border/60">From \ To</th>
                {value.cities.map((city, cIdx) => (
                  <th key={`th-city-${cIdx}`} className="p-2.5 text-center min-w-[85px]">
                    <span className="text-sky-400 font-semibold">{city}</span>
                  </th>
                ))}
                <th className="p-2.5 text-center w-12">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-scientific-border/40">
              {value.cities.map((cityFrom, rIdx) => (
                <tr key={`row-${rIdx}`} className="hover:bg-midnight-900/40 transition-colors">
                  <td className="p-2.5 font-semibold text-purple-400 border-r border-scientific-border/60">
                    {cityFrom}
                  </td>
                  {value.cities.map((_, cIdx) => {
                    const isDiag = rIdx === cIdx
                    return (
                      <td key={`cell-${rIdx}-${cIdx}`} className="p-1.5 text-center">
                        <input
                          type="number"
                          step="1"
                          disabled={isDiag}
                          value={value.distance_matrix[rIdx]?.[cIdx] ?? 0}
                          onChange={(e) => handleCellChange(rIdx, cIdx, e.target.value)}
                          className={`w-20 text-center rounded border px-2 py-1 font-mono ${
                            isDiag
                              ? 'bg-midnight-950 text-slate-400 border-scientific-border/30 cursor-not-allowed'
                              : 'bg-midnight-900 border-scientific-border/80 text-slate-200 focus:outline-none focus:ring-1 focus:ring-scientific-accent'
                          }`}
                        />
                      </td>
                    )
                  })}
                  <td className="p-2 text-center">
                    <button
                      type="button"
                      onClick={() => handleRemoveCity(rIdx)}
                      className="text-slate-400 hover:text-rose-400 transition-colors p-1"
                      title="Remove city"
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
