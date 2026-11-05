import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ClassicalLabPage } from '../pages/ClassicalLabPage'

describe('Classical Lab Feature (Stage 4.1)', () => {
  it('renders classical lab header and problem selection controls', async () => {
    render(<ClassicalLabPage />)
    expect(screen.getByText('Classical Optimization Lab')).toBeInTheDocument()
    expect(screen.getByText('Phase 4 Active')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('renders classical solver cards with stage introduction badges', async () => {
    render(<ClassicalLabPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Exact Classical Solver').length).toBeGreaterThanOrEqual(1)
    })
    expect(screen.getAllByText('Genetic Algorithm (GA)').length).toBeGreaterThanOrEqual(1)
    expect(screen.getAllByText('Simulated Annealing (SA)').length).toBeGreaterThanOrEqual(1)

    expect(screen.getByText('Stage 4.2')).toBeInTheDocument()
    expect(screen.getByText('Stage 4.3')).toBeInTheDocument()
    expect(screen.getByText('Stage 4.4')).toBeInTheDocument()
  })

  it('allows selecting different classical solvers and displays config schema', async () => {
    render(<ClassicalLabPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Exact Classical Solver').length).toBeGreaterThanOrEqual(1)
    })

    // Click on Genetic Algorithm card
    const gaCard = screen.getAllByText('Genetic Algorithm (GA)')[0]
    fireEvent.click(gaCard)

    // Configuration badge updates
    expect(screen.getByText('Algorithm Configuration')).toBeInTheDocument()
    expect(screen.getByText('Solver Execution Dispatch')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Executable in Stage 4.3/i })).toBeInTheDocument()
  })
})
