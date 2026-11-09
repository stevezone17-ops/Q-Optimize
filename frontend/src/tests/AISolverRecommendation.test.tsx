import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { SolverRecommendationPanel } from '../features/ai/SolverRecommendationPanel'
import { RecommendationAuditModal } from '../features/ai/RecommendationAuditModal'
import { SolverRecommendation } from '../types'

const mockRecommendation: SolverRecommendation = {
  problem_type: 'max_cut',
  recommended_solver: 'simulated_annealing',
  confidence_score: 0.88,
  is_confidence_calibrated: false,
  recommendation_source: 'ml_model',
  ranked_alternatives: [
    {
      solver_name: 'simulated_annealing',
      score: 0.88,
      rank: 1,
      is_compatible: true,
      reason: 'Metropolis cooling avoids local minima on large unconstrained graphs.',
      estimated_runtime_class: 'fast',
    },
    {
      solver_name: 'genetic_algorithm',
      score: 0.82,
      rank: 2,
      is_compatible: true,
      reason: 'Evolutionary search over binary chromosomes.',
      estimated_runtime_class: 'moderate',
    },
    {
      solver_name: 'exact',
      score: 0.15,
      rank: 3,
      is_compatible: false,
      reason: 'ExactSolver disabled: graph vertices exceed safety limit (n <= 18).',
      estimated_runtime_class: 'slow',
    },
  ],
  explanation: 'Recommended simulated_annealing due to large vertex count (24) and high graph density.',
  key_features_summary: {
    num_variables: 24,
    graph_density: 0.25,
    estimated_search_space_log2: 24.0,
  },
  resource_considerations: {
    required_qubits: 24,
    quantum_simulator_compatible: false,
  },
  is_out_of_distribution: false,
  known_limitations: [
    'ML predictions reflect learned empirical performance and do not guarantee optimal execution outcomes.',
  ],
  model_version: 'v1.0.0',
  timestamp: '2026-11-09T14:00:00Z',
}

describe('Intelligent Solver Recommendation Dashboard (Stage 7.8)', () => {
  it('renders recommended solver card, confidence score, source badge, and explanation', () => {
    render(<SolverRecommendationPanel recommendation={mockRecommendation} />)

    expect(screen.getByTestId('solver-recommendation-panel')).toBeInTheDocument()
    expect(screen.getAllByText(/Simulated Annealing \(Metropolis\)/i).length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText(/88.0% Match Confidence/i)).toBeInTheDocument()
    expect(screen.getByText(/ML Model \(v1.0.0\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Recommended simulated_annealing due to large vertex count/i)).toBeInTheDocument()
    expect(screen.getByText('Compatible')).toBeInTheDocument()
  })

  it('renders key problem features breakdown correctly', () => {
    render(<SolverRecommendationPanel recommendation={mockRecommendation} />)

    expect(screen.getByText('24')).toBeInTheDocument() // Decision variables
    expect(screen.getByText('24.0')).toBeInTheDocument() // Search space log2
    expect(screen.getByText('25.0%')).toBeInTheDocument() // Density
    expect(screen.getByText(/24 \(Exceeds Aer\)/i)).toBeInTheDocument() // Qubits
  })

  it('renders ranked alternatives list with scores and compatibility status', () => {
    render(<SolverRecommendationPanel recommendation={mockRecommendation} />)

    expect(screen.getByTestId('ranked-alternatives-list')).toBeInTheDocument()
    expect(screen.getByTestId('solver-alternative-simulated_annealing')).toBeInTheDocument()
    expect(screen.getByTestId('solver-alternative-genetic_algorithm')).toBeInTheDocument()
    expect(screen.getByTestId('solver-alternative-exact')).toBeInTheDocument()
    expect(screen.getByText('Incompatible')).toBeInTheDocument()
  })

  it('displays Out-of-Distribution warning banner when is_out_of_distribution is true', () => {
    const oodRec: SolverRecommendation = {
      ...mockRecommendation,
      is_out_of_distribution: true,
      recommendation_source: 'fallback',
    }
    render(<SolverRecommendationPanel recommendation={oodRec} />)

    expect(screen.getByTestId('ood-warning-banner')).toBeInTheDocument()
    expect(screen.getByText(/Out-of-Distribution Instance Detected/i)).toBeInTheDocument()
    expect(screen.getByText(/Rule-Based Safety Fallback/i)).toBeInTheDocument()
  })

  it('triggers onAcceptRecommendation with recommended solver name', () => {
    const handleAccept = vi.fn()
    render(
      <SolverRecommendationPanel
        recommendation={mockRecommendation}
        onAcceptRecommendation={handleAccept}
      />
    )

    const acceptBtn = screen.getByTestId('accept-recommendation-btn')
    fireEvent.click(acceptBtn)
    expect(handleAccept).toHaveBeenCalledWith('simulated_annealing')
  })

  it('triggers onCompareSolvers and onDismiss callbacks', () => {
    const handleCompare = vi.fn()
    const handleDismiss = vi.fn()

    render(
      <SolverRecommendationPanel
        recommendation={mockRecommendation}
        onCompareSolvers={handleCompare}
        onDismiss={handleDismiss}
      />
    )

    const compareBtn = screen.getByTestId('compare-solvers-btn')
    fireEvent.click(compareBtn)
    expect(handleCompare).toHaveBeenCalledWith([
      'simulated_annealing',
      'genetic_algorithm',
      'exact',
    ])

    const dismissBtn = screen.getByTestId('dismiss-recommendation-btn')
    fireEvent.click(dismissBtn)
    expect(handleDismiss).toHaveBeenCalled()
  })

  it('renders loading state when isLoading is true', () => {
    render(<SolverRecommendationPanel recommendation={null} isLoading={true} />)
    expect(screen.getByTestId('ai-recommendation-loading')).toBeInTheDocument()
    expect(screen.getByText(/Synthesizing Intelligent Solver Recommendation/i)).toBeInTheDocument()
  })

  it('renders audit history modal with active recommendation', () => {
    const handleClose = vi.fn()
    render(
      <RecommendationAuditModal
        isOpen={true}
        onClose={handleClose}
        currentRecommendation={mockRecommendation}
      />
    )

    expect(screen.getByTestId('recommendation-audit-modal')).toBeInTheDocument()
    expect(screen.getByText(/Solver Recommendation Audit History/i)).toBeInTheDocument()
    expect(screen.getByText(/Active Session Recommendation/i)).toBeInTheDocument()

    const closeBtn = screen.getByTestId('close-audit-modal-btn')
    fireEvent.click(closeBtn)
    expect(handleClose).toHaveBeenCalled()
  })
})
