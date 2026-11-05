import React from 'react'
import { Modal } from '../../components/ui/Modal'
import { Button } from '../../components/ui/Button'
import { ProblemType, ProblemInstance, MaxCutInstance, AssignmentInstance, TSPInstance } from '../../types'
import { CheckCircle2, ShieldCheck } from 'lucide-react'

interface ConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  isSubmitting: boolean
  name: string
  problemType: ProblemType
  description?: string
  instance: ProblemInstance
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  isSubmitting,
  name,
  problemType,
  description,
  instance,
}) => {
  // Extract summaries
  let entitySummary = ''
  let constraintsSummary = ''

  if (problemType === 'max_cut') {
    const mc = instance as MaxCutInstance
    entitySummary = `${mc.nodes.length} Vertices (${mc.nodes.join(', ')}), ${mc.edges.length} Weighted Edges`
    constraintsSummary = 'Binary partition: Each vertex belongs strictly to subset S or V\\S.'
  } else if (problemType === 'assignment') {
    const assign = instance as AssignmentInstance
    entitySummary = `${assign.agents.length} Agents, ${assign.tasks.length} Tasks (${assign.agents.length * assign.tasks.length} total cost entries)`
    constraintsSummary = '1-to-1 matching: Exactly one task per agent, exactly one agent per task.'
  } else if (problemType === 'tsp') {
    const tsp = instance as TSPInstance
    entitySummary = `${tsp.cities.length} Cities (${tsp.cities.join(', ')}), ${tsp.cities.length * tsp.cities.length} pairwise distances${tsp.start_city ? `, Starting City: ${tsp.start_city}` : ''}`
    constraintsSummary = 'Closed Hamiltonian cycle: Visit each city once, return to start, no sub-tours.'
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Confirm Canonical Problem Definition"
      description="Review mathematical parameters and constraints before registering the canonical problem."
      maxWidth="max-w-2xl"
    >
      <div className="space-y-4">
        {/* Verification Banner */}
        <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded-lg flex items-center gap-2.5 text-xs text-emerald-300 font-mono">
          <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0" />
          <span>Independent schema validation passed. Please verify instance boundaries.</span>
        </div>

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 text-xs font-mono">
          <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
            <span className="text-scientific-muted block text-[10px]">Problem Name</span>
            <span className="font-semibold text-white">{name}</span>
          </div>

          <div className="p-3 rounded-lg bg-midnight-950 border border-scientific-border">
            <span className="text-scientific-muted block text-[10px]">Family & Schema</span>
            <span className="font-semibold text-sky-400 uppercase">{problemType} (v1.0)</span>
          </div>
        </div>

        {/* Entities and Constraints */}
        <div className="p-4 rounded-lg bg-midnight-950 border border-scientific-border space-y-3 font-mono text-xs">
          <div>
            <span className="text-scientific-muted text-[10px] uppercase block mb-1">
              Entities & Dimensions:
            </span>
            <p className="text-slate-200">{entitySummary}</p>
          </div>

          <div className="pt-2 border-t border-scientific-border/40">
            <span className="text-scientific-muted text-[10px] uppercase block mb-1">
              Constraint Guarantee:
            </span>
            <p className="text-purple-300">{constraintsSummary}</p>
          </div>

          {description && (
            <div className="pt-2 border-t border-scientific-border/40">
              <span className="text-scientific-muted text-[10px] uppercase block mb-1">
                Description:
              </span>
              <p className="text-slate-400">{description}</p>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-scientific-border">
          <Button variant="ghost" size="md" onClick={onClose} disabled={isSubmitting}>
            Cancel & Edit
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={onConfirm}
            isLoading={isSubmitting}
            leftIcon={<CheckCircle2 className="h-4 w-4" />}
          >
            Confirm & Save Problem
          </Button>
        </div>
      </div>
    </Modal>
  )
}
