import React, { useState } from 'react'
import { ProblemType, ProblemDraftProposal } from '../../types'
import { aiService, DraftValidationResult } from '../../services/aiService'
import { Button } from '../../components/ui/Button'
import { Textarea } from '../../components/ui/Textarea'
import { Badge } from '../../components/ui/Badge'
import { Alert } from '../../components/ui/Alert'
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  HelpCircle,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileCode,
  Edit3,
} from 'lucide-react'

interface NaturalLanguageDraftProps {
  onApplyDraft: (draft: ProblemDraftProposal) => void
}

const SAMPLE_PROMPTS = [
  {
    title: 'Server Cluster Partition',
    type: 'max_cut' as ProblemType,
    text: 'We want to divide 4 interconnected high-performance computing servers (S1, S2, S3, S4) into two network clusters so that the weighted severed cross-cluster latency edges are maximized.',
  },
  {
    title: 'Manufacturing Task Assignment',
    type: 'assignment' as ProblemType,
    text: 'Match 4 specialized technicians to 4 assembly line stations to minimize the total operational labor cost given a 4x4 cost matrix.',
  },
  {
    title: 'Logistics Courier Tour',
    type: 'tsp' as ProblemType,
    text: 'Find the minimum-distance closed Hamiltonian round-trip circuit for a delivery drone visiting 4 distribution centers located across the region.',
  },
]

export const NaturalLanguageDraft: React.FC<NaturalLanguageDraftProps> = ({
  onApplyDraft,
}) => {
  const [description, setDescription] = useState('')
  const [selectedHint, setSelectedHint] = useState<ProblemType | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [draftResult, setDraftResult] = useState<ProblemDraftProposal | null>(null)
  const [editedInstanceJson, setEditedInstanceJson] = useState<string>('')
  const [validationResult, setValidationResult] = useState<DraftValidationResult | null>(null)
  const [isEditingInstance, setIsEditingInstance] = useState(false)

  const handleParse = async () => {
    if (!description.trim()) {
      setError('Please provide a problem description.')
      return
    }
    setError(null)
    setIsLoading(true)
    setValidationResult(null)

    try {
      const draft = await aiService.parseDescription({
        text: description,
        problem_type_hint: selectedHint,
      })
      setDraftResult(draft)
      setEditedInstanceJson(JSON.stringify(draft.suggested_instance || {}, null, 2))
    } catch (err) {
      setError((err as Error).message || 'Failed to extract draft proposal from backend.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleValidateDraft = async () => {
    if (!draftResult || !draftResult.problem_type) return

    setIsValidating(true)
    setError(null)

    try {
      let parsedInstance = draftResult.suggested_instance
      if (editedInstanceJson.trim()) {
        try {
          parsedInstance = JSON.parse(editedInstanceJson)
        } catch {
          setError('Instance data contains invalid JSON syntax.')
          setIsValidating(false)
          return
        }
      }

      const res = await aiService.validateDraftInstance({
        problem_type: draftResult.problem_type,
        instance: parsedInstance,
      })
      setValidationResult(res)

      // Update draft state
      setDraftResult({
        ...draftResult,
        suggested_instance: parsedInstance,
        is_mathematically_valid: res.is_valid,
        validation_status: res.status,
        validation_issues: res.issues,
      })
    } catch (err) {
      setError((err as Error).message || 'Validation request failed.')
    } finally {
      setIsValidating(false)
    }
  }

  const handleSelectSample = (sample: (typeof SAMPLE_PROMPTS)[0]) => {
    setDescription(sample.text)
    setSelectedHint(sample.type)
    setDraftResult(null)
    setValidationResult(null)
    setError(null)
  }

  const handleConfirmAndApply = () => {
    if (!draftResult) return
    let finalInstance = draftResult.suggested_instance
    if (editedInstanceJson.trim()) {
      try {
        finalInstance = JSON.parse(editedInstanceJson)
      } catch {
        // Fallback to existing suggested_instance
      }
    }
    onApplyDraft({
      ...draftResult,
      suggested_instance: finalInstance,
    })
  }

  return (
    <div className="space-y-6">
      {/* Notice Alert */}
      <Alert variant="warning" title="AI Optimization Assistant — Draft Protocol">
        Natural language interpretation generates an editable draft proposal. Output must pass
        independent Phase 2 mathematical validation and requires <strong>explicit human review and confirmation</strong> before
        canonical formulation.
      </Alert>

      {/* Sample Prompts */}
      <div className="space-y-2">
        <span className="text-xs text-scientific-muted font-mono">Example Problem Descriptions:</span>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          {SAMPLE_PROMPTS.map((sample) => (
            <button
              key={sample.title}
              type="button"
              onClick={() => handleSelectSample(sample)}
              className="text-left p-3 rounded-lg border border-scientific-border bg-midnight-900/60 hover:bg-midnight-800 transition-colors group"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-slate-200 group-hover:text-scientific-accent font-mono">
                  {sample.title}
                </span>
                <Badge variant="outline" size="sm">
                  {sample.type.toUpperCase()}
                </Badge>
              </div>
              <p className="text-[11px] text-scientific-muted line-clamp-2 leading-relaxed">
                {sample.text}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Input Form */}
      <div className="space-y-3">
        <Textarea
          label="Natural Language Problem Description"
          placeholder="Describe your delivery locations, assignment costs, or network graph in ordinary language..."
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          error={error || undefined}
        />

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-scientific-muted font-mono">Target Family:</span>
            {(['max_cut', 'assignment', 'tsp'] as ProblemType[]).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setSelectedHint(selectedHint === t ? undefined : t)}
                className={`text-xs px-2.5 py-1 rounded font-mono border transition-colors ${
                  selectedHint === t
                    ? 'bg-scientific-accent/10 border-scientific-accent text-scientific-accent'
                    : 'bg-midnight-900 border-scientific-border text-scientific-muted hover:text-slate-300'
                }`}
              >
                {t.toUpperCase()}
              </button>
            ))}
          </div>

          <Button
            type="button"
            variant="primary"
            onClick={handleParse}
            isLoading={isLoading}
            leftIcon={<Sparkles className="h-4 w-4" />}
          >
            Interpret & Draft Problem
          </Button>
        </div>
      </div>

      {/* Draft Result Inspection Panel */}
      {draftResult && (
        <div className="p-5 rounded-xl border border-sky-500/30 bg-midnight-900/80 space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-scientific-border/60 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-sky-400" />
              <div>
                <h4 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                  {draftResult.name}
                </h4>
                <span className="text-[11px] text-scientific-muted font-mono">
                  Engine: {draftResult.provider_used}
                </span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={draftResult.is_supported ? 'accent' : 'danger'} size="sm">
                {draftResult.is_supported ? `Confidence ${(draftResult.confidence_score * 100).toFixed(0)}%` : 'Unsupported'}
              </Badge>
              {draftResult.is_mathematically_valid ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  <CheckCircle2 className="h-3 w-3" /> Phase 2 Valid
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  <AlertTriangle className="h-3 w-3" /> Pending Review
                </span>
              )}
            </div>
          </div>

          {/* Missing Information Alerts */}
          {draftResult.missing_information && draftResult.missing_information.length > 0 && (
            <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs font-mono space-y-1">
              <div className="flex items-center gap-1.5 text-amber-400 font-bold">
                <AlertTriangle className="h-4 w-4" />
                <span>Detected Missing Information (Please Review):</span>
              </div>
              <ul className="list-disc pl-5 text-amber-200/90 space-y-0.5">
                {draftResult.missing_information.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Assumptions */}
          {draftResult.assumptions && draftResult.assumptions.length > 0 && (
            <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border/40 text-xs font-mono space-y-1">
              <span className="text-scientific-muted text-[11px] font-bold block">Assumptions Made:</span>
              <ul className="list-disc pl-5 text-slate-300 space-y-0.5">
                {draftResult.assumptions.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Entities & Objective Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="space-y-2 p-3 rounded bg-midnight-950 border border-scientific-border/40">
              <span className="text-scientific-muted text-[11px] block">Objective Function:</span>
              <p className="text-slate-200">
                <span className="text-amber-400 font-bold uppercase">{draftResult.objective.direction || 'OPTIMIZE'}</span>{' '}
                — {draftResult.objective.description}
              </p>
            </div>

            <div className="space-y-2 p-3 rounded bg-midnight-950 border border-scientific-border/40">
              <span className="text-scientific-muted text-[11px] block">Extracted Entities:</span>
              <pre className="text-purple-300 text-[11px] overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(draftResult.entities, null, 2)}
              </pre>
            </div>
          </div>

          {/* Constraints */}
          {draftResult.constraints && draftResult.constraints.length > 0 && (
            <div className="space-y-1.5">
              <span className="text-xs font-semibold text-slate-300 font-mono">Constraints:</span>
              <ul className="list-disc pl-5 text-xs text-scientific-muted space-y-0.5 font-mono">
                {draftResult.constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Suggested Instance & Interactive Editor */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 font-mono flex items-center gap-1.5">
                <FileCode className="h-3.5 w-3.5 text-scientific-accent" />
                Canonical Instance Representation:
              </span>
              <button
                type="button"
                onClick={() => setIsEditingInstance(!isEditingInstance)}
                className="text-[11px] text-scientific-accent hover:underline font-mono flex items-center gap-1"
              >
                <Edit3 className="h-3 w-3" />
                {isEditingInstance ? 'Hide Raw JSON Editor' : 'Edit Instance JSON'}
              </button>
            </div>

            {isEditingInstance ? (
              <textarea
                value={editedInstanceJson}
                onChange={(e) => setEditedInstanceJson(e.target.value)}
                rows={8}
                className="w-full bg-midnight-950 border border-scientific-border font-mono text-xs text-emerald-400 p-3 rounded-lg focus:outline-none focus:border-scientific-accent"
              />
            ) : (
              <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border/40 max-h-48 overflow-y-auto font-mono text-[11px] text-slate-300">
                <pre>{editedInstanceJson}</pre>
              </div>
            )}
          </div>

          {/* Validation Feedback */}
          {validationResult && (
            <div
              className={`p-3 rounded-lg border text-xs font-mono space-y-1 ${
                validationResult.is_valid
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                  : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
              }`}
            >
              <div className="flex items-center gap-1.5 font-bold">
                {validationResult.is_valid ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : (
                  <XCircle className="h-4 w-4 text-rose-400" />
                )}
                <span>
                  Phase 2 Validation: {validationResult.status.toUpperCase()} ({validationResult.num_variables} variables, {validationResult.num_constraints} constraints)
                </span>
              </div>
              {validationResult.issues.length > 0 && (
                <ul className="list-disc pl-5 space-y-0.5">
                  {validationResult.issues.map((iss, idx) => (
                    <li key={idx}>{iss}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Action Footer */}
          <div className="pt-3 border-t border-scientific-border/60 flex flex-wrap items-center justify-between gap-3">
            <span className="text-[11px] text-amber-300/80 font-mono flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5" />
              Confirmation required before canonical formulation
            </span>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={handleValidateDraft}
                isLoading={isValidating}
              >
                Validate Draft
              </Button>

              <Button
                type="button"
                variant="primary"
                size="sm"
                onClick={handleConfirmAndApply}
                rightIcon={<ArrowRight className="h-4 w-4" />}
              >
                Confirm & Apply to Editor
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
