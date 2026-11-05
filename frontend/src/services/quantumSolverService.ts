import { request } from './api'
import {
  QuantumBackendInfo,
  QAOAConfiguration,
  QAOAExecutionResult,
  QAOAExecutionRecord,
  QAOAStatusResponse,
  QAOAValidationResponse,
  ProblemType,
} from '../types'

export interface QAOAExecutionPayload {
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, unknown>
  config: Partial<QAOAConfiguration>
  penalty_coefficients?: Record<string, number>
}

export const quantumSolverService = {
  /**
   * List all registered quantum optimization solvers.
   */
  async listSolvers(): Promise<any[]> {
    return request<any[]>('/solvers/quantum')
  },

  /**
   * List available quantum backends with hardware transparency metadata.
   */
  async listBackends(): Promise<QuantumBackendInfo[]> {
    return request<QuantumBackendInfo[]>('/solvers/quantum/backends')
  },

  /**
   * Get metadata and configuration schema for QAOA.
   */
  async getQaoaMetadata(): Promise<any> {
    return request<any>('/solvers/quantum/qaoa')
  },

  /**
   * Validate a QAOA execution request before dispatching.
   */
  async validateRequest(payload: QAOAExecutionPayload): Promise<QAOAValidationResponse> {
    return request<QAOAValidationResponse>('/solvers/quantum/validate', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Execute QAOA synchronously against a problem instance.
   */
  async executeSync(payload: QAOAExecutionPayload): Promise<QAOAExecutionResult> {
    return request<QAOAExecutionResult>('/solvers/quantum/qaoa/execute', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Submit an asynchronous background QAOA run.
   */
  async submitAsync(payload: QAOAExecutionPayload): Promise<QAOAStatusResponse> {
    return request<QAOAStatusResponse>('/solvers/quantum/qaoa/execute/async', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },

  /**
   * Retrieve full execution record and results by ID.
   */
  async getExecution(executionId: string): Promise<QAOAExecutionRecord> {
    return request<QAOAExecutionRecord>(`/solvers/quantum/qaoa/executions/${executionId}`)
  },

  /**
   * Lightweight execution status check for polling.
   */
  async getExecutionStatus(executionId: string): Promise<QAOAStatusResponse> {
    return request<QAOAStatusResponse>(`/solvers/quantum/qaoa/executions/${executionId}/status`)
  },

  /**
   * Cooperatively cancel a pending or running background QAOA execution.
   */
  async cancelExecution(executionId: string): Promise<QAOAStatusResponse> {
    return request<QAOAStatusResponse>(`/solvers/quantum/qaoa/executions/${executionId}/cancel`, {
      method: 'POST',
    })
  },

  /**
   * List recent QAOA execution records.
   */
  async listExecutions(limit = 25): Promise<QAOAExecutionRecord[]> {
    return request<QAOAExecutionRecord[]>(`/solvers/quantum/qaoa/executions?limit=${limit}`)
  },
}
