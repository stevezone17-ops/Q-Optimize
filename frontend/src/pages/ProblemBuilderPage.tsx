import React, { useState } from 'react'
import {
  ProblemType,
  ProblemInstance,
  MaxCutInstance,
  AssignmentInstance,
  TSPInstance,
  ProblemDraftProposal,
  ProblemDraftResponse,
  ProblemResponse,
  SolverRecommendation,
} from '../types'
import { problemService } from '../services/problemService'
import { aiService } from '../services/aiService'
import { MaxCutEditor } from '../features/problem-builder/MaxCutEditor'
import { AssignmentEditor } from '../features/problem-builder/AssignmentEditor'
import { TSPEditor } from '../features/problem-builder/TSPEditor'
import { NaturalLanguageDraft } from '../features/problem-builder/NaturalLanguageDraft'
import { ProblemPreview } from '../features/problem-builder/ProblemPreview'
import { ConfirmationModal } from '../features/problem-builder/ConfirmationModal'
import { SolutionEvaluatorModal } from '../features/problem-builder/SolutionEvaluatorModal'
import { SolverRecommendationPanel } from '../features/ai/SolverRecommendationPanel'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Alert } from '../components/ui/Alert'
import {
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  Play,
  Cpu,
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
  const [isEvaluatorOpen, setIsEvaluatorOpen] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [savedProblem, setSavedProblem] = useState<ProblemResponse | null>(null)

  // AI Recommendation State
  const [recommendation, setRecommendation] = useState<SolverRecommendation | null>(null)
  const [isRecommending, setIsRecommending] = useState(false)
  const [recommendationError, setRecommendationError] = useState<string | null>(null)
  const [recommendationAcceptedNotice, setRecommendationAcceptedNotice] = useState<string | null>(null)

  const handleGetRecommendation = async () => {
    setIsRecommending(true)
    setRecommendationError(null)
    setRecommendationAcceptedNotice(null)
    try {
      const rec = await aiService.recommendSolver({
        problem_id: savedProblem ? savedProblem.id : undefined,
        problem_type: problemType,
        instance: getCurrentInstance() as unknown as Record<string, any>,
      })
      setRecommendation(rec)
    } catch (err: any) {
      setRecommendationError(err.message || 'Failed to generate solver recommendation.')
    } finally {
      setIsRecommending(false)
    }
  }

  const handleAcceptRecommendation = (solverName: string) => {
    setRecommendationAcceptedNotice(
      `Accepted recommendation for '${solverName}'. Preloaded parameters and solver profile ready for execution.`
    )
  }

  const handleCompareSolvers = (solvers: string[]) => {
    setRecommendationAcceptedNotice(
      `Solvers queued for comparison: [${solvers.join(', ')}]. Transition to Comparative Benchmark tab to execute.`
    )
  }

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

  // Backend mathematical and schema validation before opening review modal
  const handleValidateAndReview = async () => {
    setValidationError(null)
    setSavedProblem(null)

    if (!problemName.trim()) {
      setValidationError('Problem name is required.')
      return
    }

    setIsValidating(true)
    try {
      const valRes = await problemService.validateProblemDirect(
        problemType,
        getCurrentInstance() as unknown as Record<string, unknown>
      )

      if (!valRes.is_valid) {
        setValidationError(
          valRes.issues.join(' | ') || 'Problem definition failed backend mathematical validation.'
        )
        return
      }

      setIsConfirmationOpen(true)
    } catch (err) {
      setValidationError(
        (err as Error).message || 'Failed to connect to backend validation service.'
      )
    } finally {
      setIsValidating(false)
    }
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
  const handleApplyDraft = (draft: ProblemDraftProposal | ProblemDraftResponse) => {
    if (draft.problem_type) {
      setProblemType(draft.problem_type)
    }
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

          {/* AI Solver Recommendation Section */}
          <div className="space-y-3 p-4 rounded-xl border border-indigo-500/20 bg-indigo-950/10" data-testid="problem-builder-ai-recommendation-section">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <span className="text-xs font-semibold text-slate-200 font-mono uppercase tracking-wider flex items-center gap-2">
                  <Cpu className="h-4 w-4 text-indigo-400" />
                  Intelligent Solver Strategy
                </span>
                <p className="text-[11px] text-slate-400">
                  Evaluate whether exact polynomial algorithms, heuristic annealing, or QAOA simulation is best suited for this instance.
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleGetRecommendation}
                isLoading={isRecommending}
                leftIcon={<Sparkles className="h-3.5 w-3.5 text-indigo-400" />}
                className="font-mono text-xs shrink-0"
                data-testid="get-ai-recommendation-btn"
              >
                {recommendation ? 'Refresh Recommendation' : 'Get AI Recommendation'}
              </Button>
            </div>

            {recommendationAcceptedNotice && (
              <Alert variant="info" title="Solver Configuration Preloaded">
                {recommendationAcceptedNotice}
              </Alert>
            )}

            {(recommendation || isRecommending || recommendationError) && (
              <SolverRecommendationPanel
                recommendation={recommendation}
                isLoading={isRecommending}
                error={recommendationError}
                onAcceptRecommendation={handleAcceptRecommendation}
                onCompareSolvers={handleCompareSolvers}
                onDismiss={() => setRecommendation(null)}
                onRefresh={handleGetRecommendation}
              />
            )}
          </div>

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
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-xl border border-scientific-border bg-midnight-900/60">
            <div className="flex items-center gap-2 text-xs text-scientific-muted font-mono">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Independent Pydantic schema validation runs on review</span>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="md"
                onClick={() => setIsEvaluatorOpen(true)}
                leftIcon={<Play className="h-4 w-4 text-sky-400" />}
              >
                Test / Evaluate Solution
              </Button>

              <Button
                variant="primary"
                size="md"
                onClick={handleValidateAndReview}
                isLoading={isValidating}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Review & Confirm Problem
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Independent Solution Evaluator Modal */}
      <SolutionEvaluatorModal
        isOpen={isEvaluatorOpen}
        onClose={() => setIsEvaluatorOpen(false)}
        problemType={problemType}
        instance={getCurrentInstance()}
        problemName={problemName}
      />

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
