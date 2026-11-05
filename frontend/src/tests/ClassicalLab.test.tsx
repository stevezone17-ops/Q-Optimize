import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ClassicalLabPage } from '../pages/ClassicalLabPage'

describe('Classical Lab Feature (Stages 4.1 - 4.4)', () => {
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

    expect(screen.getByText('Ready (Stage 4.2)')).toBeInTheDocument()
    expect(screen.getByText('Ready (Stage 4.3)')).toBeInTheDocument()
    expect(screen.getByText('Ready (Stage 4.4)')).toBeInTheDocument()
  })

  it('allows selecting Genetic Algorithm and displays evolutionary hyperparameters', async () => {
    render(<ClassicalLabPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Exact Classical Solver').length).toBeGreaterThanOrEqual(1)
    })

    // Click on Genetic Algorithm card
    const gaCard = screen.getAllByText('Genetic Algorithm (GA)')[0]
    fireEvent.click(gaCard)

    // Configuration badge and GA specific controls
    expect(screen.getByText('Algorithm Configuration')).toBeInTheDocument()
    expect(screen.getByText('Evolutionary Hyperparameters:')).toBeInTheDocument()
    expect(screen.getByText('Solver Execution Dispatch')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Execute Genetic Algorithm/i })).toBeInTheDocument()
  })

  it('allows selecting Simulated Annealing and displays annealing hyperparameters', async () => {
    render(<ClassicalLabPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Exact Classical Solver').length).toBeGreaterThanOrEqual(1)
    })

    // Click on Simulated Annealing card
    const saCard = screen.getAllByText('Simulated Annealing (SA)')[0]
    fireEvent.click(saCard)

    // Configuration badge and SA specific controls
    expect(screen.getByText('Algorithm Configuration')).toBeInTheDocument()
    expect(screen.getByText('Annealing Hyperparameters')).toBeInTheDocument()
    expect(screen.getByText('Exponential (T·α)')).toBeInTheDocument()
    expect(screen.getByText('Linear (T - ΔT)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Execute Simulated Annealing/i })).toBeInTheDocument()
  })

  it('executes exact classical solver and renders results panel with proven optimal status', async () => {
    render(<ClassicalLabPage />)

    await waitFor(() => {
      expect(screen.getAllByText('Exact Classical Solver').length).toBeGreaterThanOrEqual(1)
    })

    const executeBtn = screen.getByRole('button', { name: /Execute Exact Classical Solver/i })
    fireEvent.click(executeBtn)

    await waitFor(() => {
      expect(screen.getByText('Optimization Results & Independent Evaluation')).toBeInTheDocument()
    })
    expect(screen.getByText('PROVEN OPTIMAL')).toBeInTheDocument()
    expect(screen.getByText('FEASIBLE')).toBeInTheDocument()
    expect(screen.getByText('14.00')).toBeInTheDocument()
  })
})
