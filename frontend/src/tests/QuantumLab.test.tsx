import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QuantumLabPage } from '../pages/QuantumLabPage'

describe('Quantum Lab Feature (Phase 5 - Stage 5.8)', () => {
  it('renders Quantum Lab header, Phase 5 Active badge, and problem selector', async () => {
    render(<QuantumLabPage />)
    expect(screen.getByText('Quantum Optimization Lab')).toBeInTheDocument()
    expect(screen.getByText('Phase 5 Active')).toBeInTheDocument()
    expect(screen.getByText('Target Problem Instance & Backend')).toBeInTheDocument()
  })

  it('renders mandatory scientific hardware transparency notice', () => {
    render(<QuantumLabPage />)
    expect(screen.getByText('Scientific Hardware Transparency Notice')).toBeInTheDocument()
    expect(
      screen.getByText(/All executions in this Quantum Lab run on classical simulation backends/i)
    ).toBeInTheDocument()
  })

  it('renders QAOA ansatz and optimizer configuration controls', () => {
    render(<QuantumLabPage />)
    expect(screen.getByText('QAOA Ansatz & Optimizer Parameters')).toBeInTheDocument()
    expect(screen.getByText(/Ansatz Depth/i)).toBeInTheDocument()
    expect(screen.getByText(/Measurement Shots/i)).toBeInTheDocument()
    expect(screen.getByText('Simulation Mode')).toBeInTheDocument()
    expect(screen.getByText('Classical Optimizer')).toBeInTheDocument()
    expect(screen.getByText('Parameter Init Strategy')).toBeInTheDocument()
  })

  it('renders circuit blueprint and resource bounds card', () => {
    render(<QuantumLabPage />)
    expect(screen.getByText('Circuit Blueprint & Resource Bounds')).toBeInTheDocument()
    expect(screen.getByText('Estimated Qubits:')).toBeInTheDocument()
    expect(screen.getByText('Variational Parameters:')).toBeInTheDocument()
    expect(screen.getByText('Gate Decomposition:')).toBeInTheDocument()
    expect(screen.getByText('Qubit Ceiling (Aer):')).toBeInTheDocument()
  })

  it('executes QAOA simulation and displays results with independent verification', async () => {
    render(<QuantumLabPage />)

    const executeBtn = screen.getByRole('button', { name: /Execute QAOA Simulation/i })
    expect(executeBtn).toBeInTheDocument()
    fireEvent.click(executeBtn)

    await waitFor(() => {
      expect(screen.getByText('Independent Phase 2 Evaluation Verification')).toBeInTheDocument()
    })

    expect(screen.getByText('100% FEASIBLE')).toBeInTheDocument()
    expect(screen.getByText('Decoded Optimal Candidate Solution')).toBeInTheDocument()
    expect(screen.getByText('Optimizer Energy Convergence ⟨H_C⟩')).toBeInTheDocument()
    expect(screen.getByText('Quantum Bitstring Measurement Distribution')).toBeInTheDocument()
    expect(screen.getByText('★ Best Feasible Solution')).toBeInTheDocument()
    expect(screen.getByText('Backend Transparency Log:')).toBeInTheDocument()
  })

  it('switches to Execution Audit tab and displays past records', async () => {
    render(<QuantumLabPage />)

    const auditBtn = screen.getByRole('button', { name: /Execution Audit/i })
    fireEvent.click(auditBtn)

    await waitFor(() => {
      expect(screen.getByText('Persistent QAOA Execution Audit Logs')).toBeInTheDocument()
    })
    expect(screen.getByText('qexec-hist-1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Inspect Result/i })).toBeInTheDocument()
  })
})
