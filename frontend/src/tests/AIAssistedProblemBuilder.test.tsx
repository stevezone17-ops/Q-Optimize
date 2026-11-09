import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NaturalLanguageDraft } from '../features/problem-builder/NaturalLanguageDraft'
import { aiService } from '../services/aiService'
import { ProblemDraftProposal } from '../types'

vi.mock('../services/aiService', () => ({
  aiService: {
    parseDescription: vi.fn(),
    validateDraftInstance: vi.fn(),
  },
}))

describe('AI-Assisted Problem Builder (Stage 7.7)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders natural language input, example prompt chips, and target family buttons', () => {
    render(<NaturalLanguageDraft onApplyDraft={vi.fn()} />)

    expect(screen.getByText(/AI Optimization Assistant — Draft Protocol/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Describe your delivery locations/i)).toBeInTheDocument()
    expect(screen.getByText('Server Cluster Partition')).toBeInTheDocument()
    expect(screen.getByText('Logistics Courier Tour')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Interpret & Draft Problem/i })).toBeInTheDocument()
  })

  it('populates description when clicking an example prompt chip', () => {
    render(<NaturalLanguageDraft onApplyDraft={vi.fn()} />)

    const exampleBtn = screen.getByText('Logistics Courier Tour')
    fireEvent.click(exampleBtn)

    const textarea = screen.getByPlaceholderText(/Describe your delivery locations/i) as HTMLTextAreaElement
    expect(textarea.value).toContain('Hamiltonian round-trip circuit')
  })

  it('calls aiService.parseDescription and displays structured draft proposal with missing info and assumptions', async () => {
    const mockDraft: ProblemDraftProposal = {
      is_supported: true,
      problem_type: 'tsp',
      name: 'Drone Courier Delivery Tour (4 Locations)',
      description: 'Find minimum distance closed loop tour.',
      entities: { cities: ['C1', 'C2', 'C3', 'C4'] },
      objective: { direction: 'minimize', description: 'Minimize total travel distance' },
      constraints: ['Visit each city once', 'Return to origin'],
      missing_information: ['Pairwise distance matrix was not provided in text; generated metric proposal.'],
      assumptions: ['Assumed symmetric Euclidean distances between locations.'],
      suggested_instance: {
        cities: ['C1', 'C2', 'C3', 'C4'],
        distance_matrix: [
          [0, 10, 15, 20],
          [10, 0, 20, 25],
          [15, 20, 0, 10],
          [20, 25, 10, 0],
        ],
      },
      confidence_score: 0.88,
      is_mathematically_valid: true,
      validation_status: 'valid',
      validation_issues: [],
      requires_user_confirmation: true,
      provider_used: 'deterministic_fallback',
      disclaimer: 'Draft only.',
    }

    vi.mocked(aiService.parseDescription).mockResolvedValueOnce(mockDraft)

    render(<NaturalLanguageDraft onApplyDraft={vi.fn()} />)

    const textarea = screen.getByPlaceholderText(/Describe your delivery locations/i)
    fireEvent.change(textarea, { target: { value: 'Find the shortest tour for 4 cities.' } })

    const interpretBtn = screen.getByRole('button', { name: /Interpret & Draft Problem/i })
    fireEvent.click(interpretBtn)

    await waitFor(() => {
      expect(screen.getByText(/Drone Courier Delivery Tour/i)).toBeInTheDocument()
      expect(screen.getByText(/Confidence 88%/i)).toBeInTheDocument()
      expect(screen.getByText(/Phase 2 Valid/i)).toBeInTheDocument()
      expect(screen.getByText(/Detected Missing Information/i)).toBeInTheDocument()
      expect(screen.getByText(/Assumed symmetric Euclidean distances/i)).toBeInTheDocument()
    })
  })

  it('validates edited draft instance against Phase 2 validator on button click', async () => {
    const mockDraft: ProblemDraftProposal = {
      is_supported: true,
      problem_type: 'assignment',
      name: 'Technician Assignment',
      description: 'Assign workers to jobs.',
      entities: { agents: ['A1', 'A2'], tasks: ['T1', 'T2'] },
      objective: { direction: 'minimize', description: 'Minimize total labor cost' },
      constraints: ['1-to-1 matching'],
      missing_information: [],
      assumptions: [],
      suggested_instance: {
        agents: ['A1', 'A2'],
        tasks: ['T1', 'T2'],
        cost_matrix: [[5, 2], [3, 8]],
      },
      confidence_score: 0.95,
      is_mathematically_valid: true,
      validation_status: 'valid',
      validation_issues: [],
      requires_user_confirmation: true,
      provider_used: 'gemini',
      disclaimer: 'Draft only.',
    }

    vi.mocked(aiService.parseDescription).mockResolvedValueOnce(mockDraft)
    vi.mocked(aiService.validateDraftInstance).mockResolvedValueOnce({
      is_valid: true,
      status: 'valid',
      issues: [],
      num_variables: 4,
      num_constraints: 4,
      metadata: {},
    })

    render(<NaturalLanguageDraft onApplyDraft={vi.fn()} />)

    const textarea = screen.getByPlaceholderText(/Describe your delivery locations/i)
    fireEvent.change(textarea, { target: { value: 'Assign 2 workers to 2 tasks.' } })

    fireEvent.click(screen.getByRole('button', { name: /Interpret & Draft Problem/i }))

    await waitFor(() => {
      expect(screen.getByText(/Technician Assignment/i)).toBeInTheDocument()
    })

    const validateBtn = screen.getByRole('button', { name: /Validate Draft/i })
    fireEvent.click(validateBtn)

    await waitFor(() => {
      expect(aiService.validateDraftInstance).toHaveBeenCalledWith({
        problem_type: 'assignment',
        instance: mockDraft.suggested_instance,
      })
      expect(screen.getByText(/Phase 2 Validation: VALID/i)).toBeInTheDocument()
    })
  })

  it('triggers onApplyDraft callback when confirming draft', async () => {
    const mockApply = vi.fn()
    const mockDraft: ProblemDraftProposal = {
      is_supported: true,
      problem_type: 'max_cut',
      name: 'Cluster Partition',
      description: 'Split nodes.',
      entities: { nodes: ['A', 'B'] },
      objective: { direction: 'maximize', description: 'max cut' },
      constraints: [],
      missing_information: [],
      assumptions: [],
      suggested_instance: { nodes: ['A', 'B'], edges: [['A', 'B', 1.0]] },
      confidence_score: 0.9,
      is_mathematically_valid: true,
      validation_status: 'valid',
      validation_issues: [],
      requires_user_confirmation: true,
      provider_used: 'deterministic_fallback',
      disclaimer: 'Draft only.',
    }

    vi.mocked(aiService.parseDescription).mockResolvedValueOnce(mockDraft)

    render(<NaturalLanguageDraft onApplyDraft={mockApply} />)

    fireEvent.change(screen.getByPlaceholderText(/Describe your delivery locations/i), {
      target: { value: 'Split 2 nodes.' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Interpret & Draft Problem/i }))

    await waitFor(() => {
      expect(screen.getByText(/Cluster Partition/i)).toBeInTheDocument()
    })

    const confirmBtn = screen.getByRole('button', { name: /Confirm & Apply to Editor/i })
    fireEvent.click(confirmBtn)

    expect(mockApply).toHaveBeenCalledWith(expect.objectContaining({
      name: 'Cluster Partition',
      problem_type: 'max_cut',
    }))
  })
})

