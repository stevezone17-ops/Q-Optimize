import React, { useState } from 'react'
import {
  ProblemType,
  ProblemInstance,
  MaxCutInstance,
  AssignmentInstance,
  TSPInstance,
  ProblemDraftResponse,
  ProblemResponse,
} from '../types'
import { problemService } from '../services/problemService'
import { MaxCutEditor } from '../features/problem-builder/MaxCutEditor'
import { AssignmentEditor } from '../features/problem-builder/AssignmentEditor'
import { TSPEditor } from '../features/problem-builder/TSPEditor'
import { NaturalLanguageDraft } from '../features/problem-builder/NaturalLanguageDraft'
import { ProblemPreview } from '../features/problem-builder/ProblemPreview'
import { ConfirmationModal } from '../features/problem-builder/ConfirmationModal'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Alert } from '../components/ui/Alert'
import {
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react'

const DEFAULT_MAX_CUT: MaxCutInstance = {
  nodes: ['A', 'B', 'C', 'D'],
  edges: [
    ['A', 'B', 1.0],
    ['B', 'C', 1.0],
    ['C', 'D', 1.0],
    ['D', 'A', 1.0],
    ['A', 'C', 1.0],
  ],
}

const DEFAULT_ASSIGNMENT: AssignmentInstance = {
  agents: ['Agent_1', 'Agent_2', 'Agent_3'],
  tasks: ['Task_1', 'Task_2', 'Task_3'],
  cost_matrix: [
    [4.0, 7.0, 3.0],
    [2.0, 6.0, 8.0],
    [5.0, 3.0, 4.0],
  ],
}

const DEFAULT_TSP: TSPInstance = {
  cities: ['London', 'Paris', 'Berlin', 'Rome'],
  distance_matrix: [
    [0.0, 344.0, 933.0, 1435.0],
    [344.0, 0.0, 878.0, 1106.0],
    [933.0, 878.0, 0.0, 1184.0],
    [1435.0, 1106.0, 1184.0, 0.0],
  ],
}

export const ProblemBuilderPage: React.FC = () => {
  const [entryMode, setEntryMode] = useState<'structured' | 'natural_language'>('structured')
  const [problemType, setProblemType] = useState<ProblemType>('max_cut')
  const [problemName, setProblemName] = useState('Benchmark Max-Cut Graph')
  const [problemDescription, setProblemDescription] = useState(
    'Canonical 4-node cycle with cross-diagonal for initial partition benchmarking.'
  )

  // Instances per type
  const [maxCutData, setMaxCutData] = useState<MaxCutInstance>(DEFAULT_MAX_CUT)
  const [assignmentData, setAssignmentData] = useState<AssignmentInstance>(DEFAULT_ASSIGNMENT)
  const [tspData, setTspData] = useState<TSPInstance>(DEFAULT_TSP)

  // Validation & Submission state
  const [validationError, setValidationError] = useState<string | null>(null)
  const [isConfirmationOpen, setIsConfirmationOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [savedProblem, setSavedProblem] = useState<ProblemResponse | null>(null)

  // Active instance getter
  const getCurrentInstance = (): ProblemInstance => {
    switch (problemType) {
      case 'max_cut':
        return maxCutData
      case 'assignment':
        return assignmentData
      case 'tsp':
        return tspData
    }
  }

  // Client-side validation before opening review modal
  const handleValidateAndReview = () => {
    setValidationError(null)
    setSavedProblem(null)

    if (!problemName.trim()) {
      setValidationError('Problem name is required.')
      return
    }

    if (problemType === 'max_cut') {
      if (maxCutData.nodes.length < 2) {
        setValidationError('Max-Cut requires at least 2 nodes.')
        return
      }
      if (maxCutData.edges.length === 0) {
        setValidationError('Please define at least one edge in the graph.')
        return
      }
    } else if (problemType === 'assignment') {
      if (assignmentData.agents.length < 1 || assignmentData.tasks.length < 1) {
        setValidationError('Assignment requires at least 1 agent and 1 task.')
        return
      }
      if (assignmentData.cost_matrix.length !== assignmentData.agents.length) {
        setValidationError('Cost matrix rows do not match agent count.')
        return
      }
    } else if (problemType === 'tsp') {
      if (tspData.cities.length < 3) {
        setValidationError('TSP requires at least 3 cities for a closed cycle.')
        return
      }
    }

    setIsConfirmationOpen(true)
  }

  // Final confirmation to backend API
  const handleConfirmAndSave = async () => {
    setIsSubmitting(true)
    setValidationError(null)

    try {
      const payload = {
        name: problemName,
        problem_type: problemType,
        description: problemDescription,
        instance: getCurrentInstance() as unknown as Record<string, unknown>,
      }

      const response = await problemService.createProblem(payload)
      setSavedProblem(response)
      setIsConfirmationOpen(false)
    } catch (err) {
      setValidationError((err as Error).message || 'Failed to persist problem to backend.')
      setIsConfirmationOpen(false)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Draft callback from Natural Language parser
  const handleApplyDraft = (draft: ProblemDraftResponse) => {
    setProblemType(draft.problem_type)
    setProblemName(draft.name)
    setProblemDescription(draft.description)

    if (draft.problem_type === 'max_cut') {
      setMaxCutData(draft.suggested_instance as unknown as MaxCutInstance)
    } else if (draft.problem_type === 'assignment') {
      setAssignmentData(draft.suggested_instance as unknown as AssignmentInstance)
    } else if (draft.problem_type === 'tsp') {
      setTspData(draft.suggested_instance as unknown as TSPInstance)
    }

    setEntryMode('structured')
  }

  return (
    <div className="space-y-6">
      {/* Top Controls: Mode Switcher & Family Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl border border-scientific-border bg-midnight-900/60">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setEntryMode('structured')}
            className={`text-xs px-3.5 py-1.5 rounded-lg font-mono transition-all flex items-center gap-1.5 ${
              entryMode === 'structured'
                ? 'bg-scientific-accent text-midnight-950 font-semibold shadow-sm'
                : 'bg-midnight-800 text-slate-300 hover:bg-midnight-700'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            Structured Builder
          </button>
          <button
            type="button"
            onClick={() => setEntryMode('natural_language')}
            className={`text-xs px-3.5 py-1.5 rounded-lg font-mono transition-all flex items-center gap-1.5 ${
              entryMode === 'natural_language'
                ? 'bg-scientific-accent text-midnight-950 font-semibold shadow-sm'
                : 'bg-midnight-800 text-slate-300 hover:bg-midnight-700'
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Natural Language Draft
          </button>
        </div>

        {entryMode === 'structured' && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-scientific-muted font-mono">Problem Type:</span>
            <div className="flex rounded-lg border border-scientific-border bg-midnight-950 p-1">
              <button
                type="button"
                onClick={() => setProblemType('max_cut')}
                className={`text-xs px-3 py-1 rounded font-mono transition-colors ${
                  problemType === 'max_cut'
                    ? 'bg-midnight-800 text-sky-400 font-semibold'
                    : 'text-scientific-muted hover:text-slate-300'
                }`}
              >
                Max-Cut
              </button>
              <button
                type="button"
                onClick={() => setProblemType('assignment')}
                className={`text-xs px-3 py-1 rounded font-mono transition-colors ${
                  problemType === 'assignment'
                    ? 'bg-midnight-800 text-purple-400 font-semibold'
                    : 'text-scientific-muted hover:text-slate-300'
                }`}
              >
                Assignment
              </button>
              <button
                type="button"
                onClick={() => setProblemType('tsp')}
                className={`text-xs px-3 py-1 rounded font-mono transition-colors ${
                  problemType === 'tsp'
                    ? 'bg-midnight-800 text-amber-400 font-semibold'
                    : 'text-scientific-muted hover:text-slate-300'
                }`}
              >
                TSP
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Main Builder Content */}
      {entryMode === 'natural_language' ? (
        <NaturalLanguageDraft onApplyDraft={handleApplyDraft} />
      ) : (
        <div className="space-y-6">
          {/* Problem Metadata Header */}
          <div className="p-5 rounded-xl border border-scientific-border bg-midnight-900/40 space-y-4">
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider font-mono">
              Problem Metadata
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Problem Name"
                placeholder="e.g. Server Partitioning Benchmark"
                value={problemName}
                onChange={(e) => setProblemName(e.target.value)}
                className="font-mono"
              />
              <Input
                label="Instance Description & Notes"
                placeholder="Document experimental assumptions or generator seed..."
                value={problemDescription}
                onChange={(e) => setProblemDescription(e.target.value)}
              />
            </div>
          </div>

          {/* Active Family Editor */}
          {problemType === 'max_cut' && (
            <MaxCutEditor
              value={maxCutData}
              onChange={setMaxCutData}
              error={validationError}
            />
          )}

          {problemType === 'assignment' && (
            <AssignmentEditor
              value={assignmentData}
              onChange={setAssignmentData}
              error={validationError}
            />
          )}

          {problemType === 'tsp' && (
            <TSPEditor
              value={tspData}
              onChange={setTspData}
              error={validationError}
            />
          )}

          {/* Canonical Preview & Schema Specification */}
          <ProblemPreview
            problemType={problemType}
            name={problemName}
            description={problemDescription}
            instance={getCurrentInstance()}
          />

          {/* Error Message Alert */}
          {validationError && (
            <Alert variant="error" title="Validation Failed">
              {validationError}
            </Alert>
          )}

          {/* Saved Success Alert */}
          {savedProblem && (
            <Alert variant="success" title="Canonical Problem Registered Successfully">
              Canonical problem <strong>{savedProblem.name}</strong> registered with ID{' '}
              <code className="text-emerald-300 font-mono">{savedProblem.id}</code>. Ready for formulation and solver execution.
            </Alert>
          )}

          {/* Bottom Action Footer */}
          <div className="flex items-center justify-between p-4 rounded-xl border border-scientific-border bg-midnight-900/60">
            <div className="flex items-center gap-2 text-xs text-scientific-muted font-mono">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Independent Pydantic schema validation runs on review</span>
            </div>

            <Button
              variant="primary"
              size="md"
              onClick={handleValidateAndReview}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Review & Confirm Problem
            </Button>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={isConfirmationOpen}
        onClose={() => setIsConfirmationOpen(false)}
        onConfirm={handleConfirmAndSave}
        isSubmitting={isSubmitting}
        name={problemName}
        problemType={problemType}
        description={problemDescription}
        instance={getCurrentInstance()}
      />
    </div>
  )
}
