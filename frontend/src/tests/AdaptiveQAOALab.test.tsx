import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QuantumLabPage } from '../pages/QuantumLabPage'

describe('Adaptive QAOA Research Lab (Phase 6 - Stage 6.8)', () => {
  it('renders Adaptive QAOA Lab tab button in mode selector', () => {
    render(<QuantumLabPage />)
    expect(screen.getByRole('button', { name: /Adaptive QAOA Lab/i })).toBeInTheDocument()
  })

  it('switches to Adaptive QAOA Lab tab and displays strategy presets and controls', async () => {
    render(<QuantumLabPage />)

    const adaptiveTabBtn = screen.getByRole('button', { name: /Adaptive QAOA Lab/i })
    fireEvent.click(adaptiveTabBtn)

    expect(screen.getByText(/Target Problem Instance & Strategy Preset/i)).toBeInTheDocument()
    expect(screen.getByText('Full Adaptive QAOA')).toBeInTheDocument()
    expect(screen.getByText('Dynamic Layer Growth')).toBeInTheDocument()
    expect(screen.getByText('Fourier Parameterization')).toBeInTheDocument()
    expect(screen.getByText('Warm-Start Transfer')).toBeInTheDocument()
    expect(screen.getByText('Multi-Stage Optimizer')).toBeInTheDocument()
    expect(screen.getByText('Dynamic Depth Management')).toBeInTheDocument()
    expect(screen.getByText('Optimizer Scheduling & Arbitration')).toBeInTheDocument()
    expect(screen.getByText('Parameter Init & Sampling Controls')).toBeInTheDocument()
  })

  it('allows clicking different strategy presets to update configuration defaults', async () => {
    render(<QuantumLabPage />)

    const adaptiveTabBtn = screen.getByRole('button', { name: /Adaptive QAOA Lab/i })
    fireEvent.click(adaptiveTabBtn)

    const fourierCard = screen.getByText('Fourier Parameterization')
    fireEvent.click(fourierCard)

    // Fourier strategy triggers fourier initialization
    await waitFor(() => {
      expect(screen.getByText(/Fourier Order \(q\)/i)).toBeInTheDocument()
    })
  })

  it('executes Adaptive QAOA and renders metrics, dynamic parameters, and decision log', async () => {
    render(<QuantumLabPage />)

    const adaptiveTabBtn = screen.getByRole('button', { name: /Adaptive QAOA Lab/i })
    fireEvent.click(adaptiveTabBtn)

    const launchBtn = screen.getByRole('button', { name: /Launch Adaptive QAOA/i })
    expect(launchBtn).toBeInTheDocument()
    fireEvent.click(launchBtn)

    await waitFor(() => {
      expect(screen.getByText(/Phase 2 Independent Evaluation & Termination Verification/i)).toBeInTheDocument()
    })

    // Verify executive metrics
    expect(screen.getByText(/Depth Evolution/i)).toBeInTheDocument()
    expect(screen.getByText(/Approx Ratio \(r\)/i)).toBeInTheDocument()
    expect(screen.getByText('CONSTRAINTS SATISFIED')).toBeInTheDocument()
    expect(screen.getByText(/Dynamic Parameter Angles/i)).toBeInTheDocument()
    expect(screen.getByText(/Adaptive Decision Audit Log/i)).toBeInTheDocument()
    expect(screen.getByText(/stagnation_detected/i)).toBeInTheDocument()
    expect(screen.getByText(/Expanded QAOA circuit depth from p=1 to p=2 with warm-start interpolation/i)).toBeInTheDocument()
    expect(screen.getByText(/Convergence & Variational Energy Progression/i)).toBeInTheDocument()
    expect(screen.getByText(/Adaptive QAOA Simulation Transparency Notice/i)).toBeInTheDocument()
  })

  it('interacts with the Parameter Transfer Laboratory to check compatibility and transfer angles', async () => {
    render(<QuantumLabPage />)

    const adaptiveTabBtn = screen.getByRole('button', { name: /Adaptive QAOA Lab/i })
    fireEvent.click(adaptiveTabBtn)

    expect(screen.getByText(/Parameter Transfer & Warm-Start Laboratory/i)).toBeInTheDocument()

    const checkBtn = screen.getByRole('button', { name: /Check Compatibility/i })
    fireEvent.click(checkBtn)

    await waitFor(() => {
      expect(screen.getByText(/Transfer Compatibility: COMPATIBLE/i)).toBeInTheDocument()
    })

    const transferBtn = screen.getByRole('button', { name: /Transfer Parameters/i })
    fireEvent.click(transferBtn)

    await waitFor(() => {
      expect(screen.getByText(/Successfully Transferred to Target Depth/i)).toBeInTheDocument()
    })
  })

  it('switches to Execution Audit tab and toggles between standard QAOA and adaptive QAOA logs', async () => {
    render(<QuantumLabPage />)

    const auditBtn = screen.getByRole('button', { name: /Execution Audit/i })
    fireEvent.click(auditBtn)

    await waitFor(() => {
      expect(screen.getByText(/Quantum Optimization Audit Logs/i)).toBeInTheDocument()
    })

    const adaptiveToggleBtn = screen.getByRole('button', { name: /^Adaptive QAOA \(/i })
    fireEvent.click(adaptiveToggleBtn)

    await waitFor(() => {
      expect(screen.getByText('aqexec-hist-1')).toBeInTheDocument()
    })
    expect(screen.getAllByText('full_adaptive').length).toBeGreaterThanOrEqual(1)
  })

  it('executes Adaptive QAOA ablation benchmark study through service', async () => {
    const { adaptiveSolverService } = await import('../services/adaptiveSolverService')
    const benchRes = await adaptiveSolverService.runBenchmark({
      problem_id: 'preset_0',
      include_variants: ['standard_baseline', 'full_adaptive'],
    })

    expect(benchRes.benchmark_id).toBe('aqbench-mock-1')
    expect(benchRes.summaries.length).toBe(2)
    expect(benchRes.ablation_insights.length).toBeGreaterThan(0)
    expect(benchRes.exact_optimum).toBe(5.0)
  })
})
