import { request } from './api'
import {
  SolverMetadata,
  SolverRequest,
  SolverResult,
  ProblemType,
} from '../types'

export const classicalSolverService = {
  /**
   * List all registered classical optimization solvers with metadata and implementation status.
   */
  async listSolvers(): Promise<SolverMetadata[]> {
    return request<SolverMetadata[]>('/solvers/classical')
  },

  /**
   * Get metadata and configuration schema for a specific solver.
   */
  async getSolver(solverId: string): Promise<SolverMetadata> {
    return request<SolverMetadata>(`/solvers/classical/${solverId}`)
  },

  /**
   * Validate a solver configuration for a problem type.
   */
  async validateConfig(
    solverId: string,
    problemType: ProblemType,
    config: Record<string, unknown>
  ): Promise<{ is_valid: boolean; message: string; validated_config: Record<string, unknown> }> {
    return request('/solvers/classical/validate', {
      method: 'POST',
      body: JSON.stringify({
        solver_id: solverId,
        problem_type: problemType,
        config,
      }),
    })
  },

  /**
   * Execute a classical solver against a problem instance.
   */
  async executeSolver(payload: SolverRequest): Promise<SolverResult> {
    return request<SolverResult>('/solvers/classical/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}

