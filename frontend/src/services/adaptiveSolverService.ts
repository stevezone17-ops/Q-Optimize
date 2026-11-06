import { request } from './api'
import {
  StrategyMetadata,
  AdaptiveQAOARequest,
  AdaptiveQAOAResult,
  AdaptiveExecutionRecord,
  AdaptiveStatusResponse,
  TransferParametersRequest,
  TransferParametersResponse,
  TransferCompatibilityReport,
  AdaptiveBenchmarkRequest,
  AdaptiveBenchmarkResult,
} from '../types'

export const adaptiveSolverService = {
  /**
   * List all registered adaptive QAOA strategies and their metadata.
   */
  async listStrategies(): Promise<StrategyMetadata[]> {
    return request<StrategyMetadata[]>('/solvers/quantum/adaptive/strategies')
  },

  /**
   * Retrieve metadata for a specific adaptive strategy.
   */
  async getStrategy(strategyId: string): Promise<StrategyMetadata> {
    return request<StrategyMetadata>(`/solvers/quantum/adaptive/strategies/${strategyId}`)
  },

  /**
   * Validate an adaptive QAOA execution configuration.
   */
  async validateConfiguration(req: AdaptiveQAOARequest): Promise<{ is_valid: boolean; message: string }> {
    return request<{ is_valid: boolean; message: string }>('/solvers/quantum/adaptive/validate', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * Check parameter transfer compatibility across depths or problem instances.
   */
  async checkTransfer(req: TransferParametersRequest): Promise<TransferCompatibilityReport> {
    return request<TransferCompatibilityReport>('/solvers/quantum/adaptive/transfer/check', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * Execute parameter transfer producing initial angles for target depth.
   */
  async transferParameters(req: TransferParametersRequest): Promise<TransferParametersResponse> {
    return request<TransferParametersResponse>('/solvers/quantum/adaptive/transfer/parameters', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * Execute an adaptive QAOA experiment synchronously.
   */
  async executeSync(req: AdaptiveQAOARequest): Promise<AdaptiveQAOAResult> {
    return request<AdaptiveQAOAResult>('/solvers/quantum/adaptive/execute', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * Asynchronously dispatch an adaptive QAOA experiment to background worker pool.
   */
  async executeAsync(req: AdaptiveQAOARequest): Promise<AdaptiveExecutionRecord> {
    return request<AdaptiveExecutionRecord>('/solvers/quantum/adaptive/execute/async', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * List recent adaptive QAOA execution records.
   */
  async listExecutions(limit: number = 25): Promise<AdaptiveExecutionRecord[]> {
    return request<AdaptiveExecutionRecord[]>(`/solvers/quantum/adaptive/executions?limit=${limit}`)
  },

  /**
   * Retrieve full execution record and results for an adaptive experiment.
   */
  async getExecution(executionId: string): Promise<AdaptiveExecutionRecord> {
    return request<AdaptiveExecutionRecord>(`/solvers/quantum/adaptive/executions/${executionId}`)
  },

  /**
   * Lightweight polling endpoint for execution lifecycle status.
   */
  async getStatus(executionId: string): Promise<AdaptiveStatusResponse> {
    return request<AdaptiveStatusResponse>(`/solvers/quantum/adaptive/executions/${executionId}/status`)
  },

  /**
   * Trigger cooperative cancellation of an in-flight adaptive task.
   */
  async cancelExecution(executionId: string): Promise<AdaptiveStatusResponse> {
    return request<AdaptiveStatusResponse>(`/solvers/quantum/adaptive/executions/${executionId}/cancel`, {
      method: 'POST',
    })
  },

  /**
   * Run an Adaptive QAOA comparative ablation study benchmark.
   */
  async runBenchmark(req: AdaptiveBenchmarkRequest): Promise<AdaptiveBenchmarkResult> {
    return request<AdaptiveBenchmarkResult>('/solvers/quantum/adaptive/benchmarks', {
      method: 'POST',
      body: JSON.stringify(req),
    })
  },

  /**
   * List recent Adaptive QAOA ablation benchmarks.
   */
  async listBenchmarks(limit: number = 25): Promise<Array<{ benchmark_id: string; name: string; problem_type: string; created_at: string; total_runtime_seconds: number }>> {
    return request<Array<{ benchmark_id: string; name: string; problem_type: string; created_at: string; total_runtime_seconds: number }>>(
      `/solvers/quantum/adaptive/benchmarks?limit=${limit}`
    )
  },

  /**
   * Retrieve detailed results and ablation insights for a benchmark study.
   */
  async getBenchmark(benchmarkId: string): Promise<AdaptiveBenchmarkResult> {
    return request<AdaptiveBenchmarkResult>(`/solvers/quantum/adaptive/benchmarks/${benchmarkId}`)
  },
}
