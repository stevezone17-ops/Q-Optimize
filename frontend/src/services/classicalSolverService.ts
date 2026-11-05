import { request } from './api'
import {
  SolverMetadata,
  SolverRequest,
  SolverResult,
  ProblemType,
  ExecutionRecord,
  ExecutionStatusResponse,
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
   * Execute a classical solver synchronously against a problem instance.
   */
  async executeSolver(payload: SolverRequest): Promise<SolverResult> {
    return request<SolverResult>('/solvers/classical/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Submit an asynchronous/background classical solver run.
   */
  async submitAsync(payload: SolverRequest): Promise<ExecutionRecord> {
    return request<ExecutionRecord>('/solvers/classical/execute/async', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Retrieve full execution record and results.
   */
  async getExecution(executionId: string): Promise<ExecutionRecord> {
    return request<ExecutionRecord>(`/solvers/classical/executions/${executionId}`)
  },

  /**
   * Lightweight execution status check for polling.
   */
  async getExecutionStatus(executionId: string): Promise<ExecutionStatusResponse> {
    return request<ExecutionStatusResponse>(`/solvers/classical/executions/${executionId}/status`)
  },

  /**
   * Cooperatively cancel a pending or running background execution.
   */
  async cancelExecution(executionId: string): Promise<{ execution_id: string; cancelled: boolean; message: string }> {
    return request(`/solvers/classical/executions/${executionId}/cancel`, {
      method: 'POST',
    })
  },

  /**
   * List recent execution records.
   */
  async listExecutions(limit = 50): Promise<ExecutionRecord[]> {
    return request<ExecutionRecord[]>(`/solvers/classical/executions?limit=${limit}`)
  },

  /**
   * Run a multi-solver classical benchmark suite.
   */
  async runBenchmark(payload: import('../types').BenchmarkRequest): Promise<import('../types').BenchmarkResult> {
    return request<import('../types').BenchmarkResult>('/solvers/classical/benchmark', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Retrieve a benchmark result by ID.
   */
  async getBenchmark(benchmarkId: string): Promise<import('../types').BenchmarkResult> {
    return request<import('../types').BenchmarkResult>(`/solvers/classical/benchmarks/${benchmarkId}`)
  },

  /**
   * List recent benchmark suites.
   */
  async listBenchmarks(limit = 50): Promise<import('../types').BenchmarkResult[]> {
    return request<import('../types').BenchmarkResult[]>(`/solvers/classical/benchmarks?limit=${limit}`)
  },
}

