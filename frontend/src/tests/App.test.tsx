import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import App from '../app/App'

describe('Q-Optimize Application Shell', () => {
  it('renders landing page with hybrid quantum-classical optimization hero', () => {
    render(<App />)
    expect(screen.getByText(/Rigorous Mathematical Optimization/i)).toBeInTheDocument()
    expect(screen.getByText(/AI-Assisted Hybrid Quantum-Classical Optimization Platform/i)).toBeInTheDocument()
  })

  it('navigates from landing page to platform workspace', () => {
    render(<App />)
    const launchButtons = screen.getAllByRole('button', { name: /Launch Platform Workspace|Open Workspace/i })
    expect(launchButtons.length).toBeGreaterThan(0)
    
    fireEvent.click(launchButtons[0])

    // Should now display workspace overview and sidebar
    expect(screen.getByText('Platform Overview')).toBeInTheDocument()
    expect(screen.getByText('Quick Start Problem Templates')).toBeInTheDocument()
    expect(screen.getByText('Recent Experiment Activity')).toBeInTheDocument()
    expect(screen.getByText('No Experiments Recorded Yet')).toBeInTheDocument()
  })

  it('allows navigation across workspace tabs', () => {
    render(<App />)
    const launchButtons = screen.getAllByRole('button', { name: /Launch Platform Workspace|Open Workspace/i })
    fireEvent.click(launchButtons[0])

    // Click Problem Builder in sidebar
    const builderButton = screen.getByRole('button', { name: /Problem Builder/i })
    fireEvent.click(builderButton)

    expect(screen.getByText('Problem Metadata')).toBeInTheDocument()
    expect(screen.getByText('Canonical Problem Specification')).toBeInTheDocument()
  })
})
