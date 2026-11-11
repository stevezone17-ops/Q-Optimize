import { request } from './api';

export interface ExperimentSummary {
  experiment_id: string;
  name: string;
  status: string;
  problem_type: string;
  algorithms: string[];
  num_trials: number;
  progress: number;
  created_at: string;
  completed_at?: string;
}

export interface ExperimentListResponse {
  experiments: ExperimentSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExperimentResultItem {
  algorithm: string;
  trial_index: number;
  seed?: number;
  objective_value?: number;
  best_solution?: Record<string, unknown>;
  runtime_seconds: number;
  is_feasible: boolean;
  num_evaluations: number;
  convergence_history: number[];
  algorithm_metrics: Record<string, unknown>;
  error?: string;
  status: string;
}

export interface ExperimentDetail {
  experiment_id: string;
  name: string;
  status: string;
  configuration: {
    algorithms: string[];
    problem_type: string;
    problem_instance: Record<string, unknown>;
    num_trials: number;
    seeds?: number[];
    resource_budget: {
      max_runtime_seconds: number;
      max_shots: number;
      max_qaoa_layers: number;
      max_iterations: number;
      max_workers: number;
    };
    description: string;
    tags: string[];
  };
  metadata: {
    created_at: string;
    started_at?: string;
    completed_at?: string;
    python_version: string;
    reproducibility_hash: string;
  };
  results: ExperimentResultItem[];
  progress: number;
  error_message?: string;
}

export interface CreateExperimentPayload {
  name: string;
  problem_type: string;
  problem_instance: Record<string, unknown>;
  algorithms: string[];
  num_trials: number;
  seeds?: number[];
  description?: string;
  tags?: string[];
}

export interface BenchmarkDatasetItem {
  metadata: {
    dataset_id: string;
    name: string;
    problem_type: string;
    generator_type: string;
    fingerprint: string;
    num_instances: number;
    created_at: string;
  };
  instances: Array<{
    instance_id: string;
    problem_type: string;
    instance_data: Record<string, unknown>;
    fingerprint: string;
  }>;
}

export interface ComparisonAnalysis {
  experiment_id?: string;
  problem_type: string;
  problem_instance_summary: Record<string, unknown>;
  algorithm_summaries: Array<{
    algorithm: string;
    num_trials: number;
    best_objective?: number;
    mean_objective?: number;
    median_objective?: number;
    std_objective?: number;
    mean_runtime_seconds: number;
    feasibility_rate: number;
    optimality_gap_pct?: number;
    approximation_ratio?: number;
  }>;
  pairwise_significance: Array<Record<string, unknown>>;
  convergence_profiles: Record<string, number[]>;
  runtime_breakdowns: Record<string, {
    circuit_construction_seconds: number;
    transpilation_seconds: number;
    parameter_optimization_seconds: number;
    quantum_execution_seconds: number;
    solution_decoding_seconds: number;
    total_runtime_seconds: number;
  }>;
}

export const experimentService = {
  async listExperiments(page = 1, pageSize = 20): Promise<ExperimentListResponse> {
    return request<ExperimentListResponse>(`/experiments?page=${page}&page_size=${pageSize}`);
  },

  async getExperiment(experimentId: string): Promise<ExperimentDetail> {
    return request<ExperimentDetail>(`/experiments/${experimentId}`);
  },

  async createExperiment(payload: CreateExperimentPayload): Promise<ExperimentDetail> {
    return request<ExperimentDetail>('/experiments', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async submitExperiment(experimentId: string): Promise<{ experiment_id: string; status: string; progress: number }> {
    return request(`/experiments/${experimentId}/submit`, { method: 'POST' });
  },

  async cancelExperiment(experimentId: string): Promise<{ experiment_id: string; status: string }> {
    return request(`/experiments/${experimentId}/cancel`, { method: 'POST' });
  },

  async deleteExperiment(experimentId: string): Promise<void> {
    return request(`/experiments/${experimentId}`, { method: 'DELETE' });
  },

  async getComparison(experimentId: string, optimalValue?: number): Promise<ComparisonAnalysis> {
    const query = optimalValue !== undefined ? `?optimal_value=${optimalValue}` : '';
    return request<ComparisonAnalysis>(`/analytics/experiments/${experimentId}/compare${query}`);
  },

  async listDatasets(): Promise<BenchmarkDatasetItem[]> {
    return request<BenchmarkDatasetItem[]>('/datasets');
  },

  async generateDataset(payload: {
    problem_type: string;
    generator_type?: string;
    num_instances?: number;
    base_seed?: number;
    name?: string;
    params?: Record<string, unknown>;
  }): Promise<BenchmarkDatasetItem> {
    return request<BenchmarkDatasetItem>('/datasets/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};
