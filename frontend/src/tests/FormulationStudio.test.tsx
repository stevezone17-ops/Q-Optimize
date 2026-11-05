import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { FormulationStudioPage } from '../pages/FormulationStudioPage'

describe('Formulation Studio Feature (Phase 3)', () => {
  it('renders formulation studio header and problem selector', async () => {
    render(<FormulationStudioPage />)
    expect(screen.getByText('Formulation Studio')).toBeInTheDocument()
    expect(screen.getByText('Phase 3 Active')).toBeInTheDocument()
    expect(
      screen.getByText(/Canonical upper-triangular QUBO & Ising spin Hamiltonian modeling/i)
    ).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
  })

  it('renders QUBO matrix heatmap and metadata summary upon generation', async () => {
    render(<FormulationStudioPage />)

    // Wait for the mock formulation to load
    await waitFor(() => {
      expect(screen.getByText('QUBO Upper-Triangular Matrix Inspector')).toBeInTheDocument()
    })

    // Check metadata cards
    expect(screen.getByText(/Variables \(n\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Linear Terms \(Q_ii\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Quadratic Couplings/i)).toBeInTheDocument()
    expect(screen.getByText(/Constant Offset \(c\)/i)).toBeInTheDocument()

    // Export buttons
    expect(screen.getByRole('button', { name: /Export Dense/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Export Sparse/i })).toBeInTheDocument()
  })

  it('switches between QUBO, Ising, and Verification tabs', async () => {
    render(<FormulationStudioPage />)

    await waitFor(() => {
      expect(screen.getByText('QUBO Upper-Triangular Matrix Inspector')).toBeInTheDocument()
    })

    // Switch to Ising tab
    const isingTab = screen.getByRole('button', { name: /Ising Spin Hamiltonian/i })
    fireEvent.click(isingTab)

    expect(await screen.findByText(/Convention: x_i = \(1 - Z_i\) \/ 2/i)).toBeInTheDocument()
    expect(screen.getByText(/Local Fields h_i/i)).toBeInTheDocument()
    expect(screen.getByText(/Spin Couplings J_ij/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Export LaTeX Hamiltonian/i })).toBeInTheDocument()

    // Switch to Verification tab
    const verifyTab = screen.getByRole('button', { name: /Mathematical Verification/i })
    fireEvent.click(verifyTab)

    expect(await screen.findByText(/Independent Mathematical Verification/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Verify All States/i })).toBeInTheDocument()
  })

  it('executes exhaustive mathematical verification on the verification tab', async () => {
    render(<FormulationStudioPage />)

    await waitFor(() => {
      expect(screen.getByText('QUBO Upper-Triangular Matrix Inspector')).toBeInTheDocument()
    })

    // Click Verification tab
    const verifyTab = screen.getByRole('button', { name: /Mathematical Verification/i })
    fireEvent.click(verifyTab)

    // Click Run Verification button
    const runBtn = await screen.findByRole('button', { name: /Verify All States/i })
    fireEvent.click(runBtn)

    // Verification results should be displayed
    await waitFor(() => {
      expect(screen.getByText('MATHEMATICALLY VERIFIED')).toBeInTheDocument()
    })
    expect(screen.getByText(/Exhaustively tested all 16 states/i)).toBeInTheDocument()
  })

  it('renders penalty configuration controls when selecting assignment problem preset', async () => {
    render(<FormulationStudioPage />)

    // Wait for initial load so problem list resolution doesn't overwrite selection
    await waitFor(() => {
      expect(screen.getByText('QUBO Upper-Triangular Matrix Inspector')).toBeInTheDocument()
    })

    const select = screen.getByRole('combobox')
    // Select Assignment preset
    fireEvent.change(select, { target: { value: 'preset_1' } })

    await waitFor(() => {
      expect(screen.getByText(/Constraint Penalty Parameters/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/Row Penalty \(A\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Column Penalty \(B\)/i)).toBeInTheDocument()
  })
})
