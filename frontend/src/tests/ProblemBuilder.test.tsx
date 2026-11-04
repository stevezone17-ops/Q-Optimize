import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ProblemBuilderPage } from '../pages/ProblemBuilderPage'

describe('Problem Builder Feature', () => {
  it('renders default Max-Cut problem builder with node and edge metrics', () => {
    render(<ProblemBuilderPage />)
    expect(screen.getByText('Problem Metadata')).toBeInTheDocument()
    expect(screen.getByText(/Graph Vertices/i)).toBeInTheDocument()
    expect(screen.getByText(/Graph Edges/i)).toBeInTheDocument()
    expect(screen.getByText(/Nodes \|V\|/i)).toBeInTheDocument()
  })

  it('allows switching to Assignment and TSP problem families', () => {
    render(<ProblemBuilderPage />)
    
    // Switch to Assignment
    const assignmentTab = screen.getByRole('button', { name: 'Assignment' })
    fireEvent.click(assignmentTab)
    expect(screen.getByText(/Bipartite Matching Form/i)).toBeInTheDocument()
    expect(screen.getByText(/Interactive Cost Matrix/i)).toBeInTheDocument()

    // Switch to TSP
    const tspTab = screen.getByRole('button', { name: 'TSP' })
    fireEvent.click(tspTab)
    expect(screen.getByText(/Distance Matrix \(D\[i, j\]\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Hamiltonian Cycle Tour Evaluation/i)).toBeInTheDocument()
  })

  it('opens confirmation modal when clicking review button', () => {
    render(<ProblemBuilderPage />)
    const reviewBtn = screen.getByRole('button', { name: /Review & Confirm Problem/i })
    fireEvent.click(reviewBtn)

    expect(screen.getByText('Confirm Canonical Problem Definition')).toBeInTheDocument()
    expect(screen.getByText('Confirm & Save Problem')).toBeInTheDocument()
  })
})
