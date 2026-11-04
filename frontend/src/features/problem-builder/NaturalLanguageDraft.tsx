import React, { useState } from 'react'
import { ProblemType, ProblemDraftResponse } from '../../types'
import { problemService } from '../../services/problemService'
import { Button } from '../../components/ui/Button'
import { Textarea } from '../../components/ui/Textarea'
import { Badge } from '../../components/ui/Badge'
import { Alert } from '../../components/ui/Alert'
import { Sparkles, ArrowRight, ShieldCheck, HelpCircle } from 'lucide-react'

interface NaturalLanguageDraftProps {
  onApplyDraft: (draft: ProblemDraftResponse) => void
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
    text: 'Match 3 specialized technicians to 3 assembly line stations to minimize the total operational labor cost given a 3x3 cost matrix.',
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
  const [error, setError] = useState<string | null>(null)
  const [draftResult, setDraftResult] = useState<ProblemDraftResponse | null>(null)

  const handleParse = async () => {
    if (!description.trim()) {
      setError('Please provide a problem description.')
      return
    }
    setError(null)
    setIsLoading(true)

    try {
      const draft = await problemService.parseDraft({
        text: description,
        problem_type_hint: selectedHint,
      })
      setDraftResult(draft)
    } catch (err) {
      setError((err as Error).message || 'Failed to extract draft proposal from backend.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectSample = (sample: (typeof SAMPLE_PROMPTS)[0]) => {
    setDescription(sample.text)
    setSelectedHint(sample.type)
    setDraftResult(null)
    setError(null)
  }

  return (
    <div className="space-y-6">
      {/* Notice Alert */}
      <Alert variant="warning" title="Draft-Only AI Parsing Protocol">
        Natural language translation produces a candidate draft proposal. All extracted entities,
        variables, and matrices are provisional and <strong>require explicit human review and confirmation</strong> before
        a canonical problem model is created.
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
          placeholder="Describe your optimization problem, constraints, entities, and objective in natural language..."
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          error={error || undefined}
        />

        <div className="flex items-center justify-between">
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
            Extract Draft Model
          </Button>
        </div>
      </div>

      {/* Draft Result Inspection Panel */}
      {draftResult && (
        <div className="p-5 rounded-xl border border-sky-500/30 bg-midnight-900/80 space-y-4">
          <div className="flex items-center justify-between border-b border-scientific-border/60 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-sky-400" />
              <h4 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                Extracted Draft: {draftResult.name}
              </h4>
            </div>
            <Badge variant="accent" size="sm">
              Confidence {(draftResult.confidence_score * 100).toFixed(0)}%
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="space-y-2 p-3 rounded bg-midnight-950 border border-scientific-border/40">
              <span className="text-scientific-muted text-[11px] block">Objective Function:</span>
              <p className="text-slate-200">
                <span className="text-amber-400 font-bold uppercase">{draftResult.objective.direction}</span>{' '}
                — {draftResult.objective.description}
              </p>
            </div>

            <div className="space-y-2 p-3 rounded bg-midnight-950 border border-scientific-border/40">
              <span className="text-scientific-muted text-[11px] block">Extracted Entities:</span>
              <p className="text-purple-300">
                {JSON.stringify(draftResult.entities)}
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-300 font-mono">Extracted Constraints:</span>
            <ul className="list-disc pl-5 text-xs text-scientific-muted space-y-1 font-mono">
              {draftResult.constraints.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>

          <div className="space-y-2">
            <span className="text-xs font-semibold text-slate-300 font-mono">Explicit Assumptions:</span>
            <ul className="list-disc pl-5 text-xs text-slate-400 space-y-1 font-mono">
              {draftResult.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>

          <div className="pt-3 border-t border-scientific-border/60 flex items-center justify-between">
            <span className="text-[11px] text-amber-300/80 font-mono flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5" />
              Confirmation required before canonical formulation
            </span>

            <Button
              type="button"
              variant="primary"
              onClick={() => onApplyDraft(draftResult)}
              rightIcon={<ArrowRight className="h-4 w-4" />}
            >
              Apply to Editor & Review
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
