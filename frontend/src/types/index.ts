export type ProblemType = 'max_cut' | 'assignment' | 'tsp'

export interface MaxCutInstance {
  nodes: string[]
  edges: [string, string, number][]
}

export interface AssignmentInstance {
  agents: string[]
  tasks: string[]
  cost_matrix: number[][]
}

export interface TSPInstance {
  cities: string[]
  distance_matrix: number[][]
  start_city?: string
  coordinates?: Record<string, [number, number]>
}

export type ProblemInstance = MaxCutInstance | AssignmentInstance | TSPInstance

export interface ConstraintViolation {
  constraint_id: string
  constraint_name: string
  message: string
  expected?: unknown
  actual?: unknown
  severity: 'error' | 'warning'
}

export interface EvaluationResult {
  problem_id?: string
  problem_type: string
  objective_sense: 'minimize' | 'maximize'
  objective_value: number
  is_feasible: boolean
  violations: ConstraintViolation[]
  details: Record<string, unknown>
  evaluated_at: string
}

export interface VariableSpec {
  name: string
  var_type: 'binary' | 'integer' | 'continuous'
  count: number
  bounds: [number, number]
  description: string
}

export interface ConstraintSpec {
  name: string
  constraint_type: string
  mathematical_form: string
  is_hard: boolean
  description: string
}

export interface ObjectiveSpec {
  sense: 'minimize' | 'maximize'
  mathematical_form: string
  description: string
}

export interface ProblemValidationResponse {
  problem_id?: string
  is_valid: boolean
  status: 'valid' | 'invalid' | 'draft'
  issues: string[]
  variables: VariableSpec[]
  constraints: ConstraintSpec[]
  metadata: Record<string, unknown>
  validated_at: string
}

export interface ProblemTypeInfo {
  type: ProblemType
  name: string
  family: string
  objective_sense: 'minimize' | 'maximize'
  mathematical_form: string
  description: string
  variable_description: string
  supported_constraints: string[]
  sample_instance: Record<string, unknown>
}

export interface ProblemCreatePayload {
  name: string
  problem_type: ProblemType
  description?: string
  instance: Record<string, unknown>
}

export interface ProblemResponse {
  id: string
  owner_id: string
  name: string
  problem_type: ProblemType
  schema_version: string
  description: string
  validation_status: 'valid' | 'invalid' | 'draft'
  variables?: VariableSpec[]
  objective?: ObjectiveSpec
  constraints?: ConstraintSpec[]
  metadata?: Record<string, unknown>
  instance: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface ProblemDraftRequest {
  text: string
  problem_type_hint?: ProblemType
}

export interface ProblemDraftResponse {
  problem_type: ProblemType
  name: string
  description: string
  objective: {
    direction: 'minimize' | 'maximize'
    description: string
  }
  entities: Record<string, unknown>
  data: Record<string, unknown>
  constraints: string[]
  assumptions: string[]
  missing_information: string[]
  suggested_instance: Record<string, unknown>
  requires_user_confirmation: boolean
  confidence_score: number
  disclaimer: string
}

export interface BackendHealthResponse {
  status: string
  service: string
  version: string
  environment: string
  phase: string
  timestamp: string
  database: {
    connected: boolean
    engine: string
    message?: string
    database?: string
  }
  supported_problems: ProblemType[]
}

// -------------------------------------------------------------
// Phase 3 Formulation & Verification Types
// -------------------------------------------------------------

export interface QuboModel {
  variable_order: string[]
  linear_terms: Record<string, number>
  quadratic_terms: Record<string, number>
  offset: number
  matrix?: number[][]
  penalties: Record<string, number>
  assumptions: string[]
  metadata: Record<string, unknown>
}

export interface IsingModel {
  variable_order: string[]
  local_fields: Record<string, number>
  couplings: Record<string, number>
  offset: number
  spin_mapping: Record<string, string>
  latex_expression?: string
  metadata: Record<string, unknown>
}

export interface FormulationResponse {
  id: string
  problem_id?: string
  owner_id: string
  formulation_type: 'qubo' | 'ising'
  schema_version: string
  qubo?: QuboModel
  ising?: IsingModel
  created_at: string
}

export interface GenerateFormulationPayload {
  problem_id?: string
  problem_type?: string
  instance?: Record<string, unknown>
  penalty_coefficients?: Record<string, number>
}

export interface VerificationResult {
  is_verified: boolean
  num_states_tested: number
  max_energy_discrepancy: number
  tolerance: number
  feasible_states_count: number
  min_qubo_energy: number
  min_ising_energy: number
  optimal_bitstring: string
  feasibility_summary: string
  discrepancies: Record<string, unknown>[]
  verified_at: string
}

export interface VerifyFormulationPayload {
  formulation_id?: string
  problem_id?: string
  problem_type?: string
  instance?: Record<string, unknown>
  qubo?: QuboModel
}

export type NavigationItemKey =
  | 'overview'
  | 'problem-builder'
  | 'formulation-studio'
  | 'quantum-lab'
  | 'classical-lab'
  | 'comparison-lab'
  | 'my-experiments'
  | 'learn'
  | 'settings'

// ==========================================
// Phase 4: Classical Optimization Types
// ==========================================

export type SolverStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'TIMED_OUT'

export type OptimalityStatus = 'proven_optimal' | 'heuristic_feasible' | 'heuristic_infeasible' | 'unknown'

export interface ConvergencePoint {
  iteration: number
  best_objective: number
  current_objective?: number
  mean_fitness?: number
  temperature?: number
  timestamp_offset?: number
}

export interface SolverMetadata {
  solver_id: string
  name: string
  description: string
  supported_problem_types: ProblemType[]
  is_implemented: boolean
  stage_introduced: string
  config_schema: Record<string, unknown>
  default_parameters: Record<string, unknown>
}

export interface SolverConfiguration {
  time_limit_seconds?: number
  seed?: number
  extra_params?: Record<string, unknown>
}

export interface SolverRequest {
  solver_id: string
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, unknown>
  config?: Record<string, unknown>
  seed?: number
  background?: boolean
}

export interface SolverResult {
  execution_id: string
  solver_id: string
  solver_name: string
  problem_type: ProblemType
  status: SolverStatus
  candidate_solution: unknown
  objective_value?: number
  is_feasible: boolean
  constraint_violations: string[]
  runtime_seconds: number
  iterations: number
  evaluations: number
  seed?: number
  optimality_status: OptimalityStatus
  termination_reason: string
  convergence_history: ConvergencePoint[]
  metadata: Record<string, unknown>
  created_at: string
}

export interface ExecutionRecord {
  execution_id: string
  solver_id: string
  solver_name: string
  problem_type: ProblemType
  problem_id?: string
  status: SolverStatus
  submitted_at: string
  started_at?: string
  completed_at?: string
  runtime_seconds?: number
  result?: SolverResult
  error?: string
  seed?: number
  config: Record<string, unknown>
}

export interface ExecutionStatusResponse {
  execution_id: string
  solver_id: string
  problem_type: ProblemType
  status: SolverStatus
  runtime_seconds?: number
  is_completed: boolean
  has_failed: boolean
  error?: string
}

export interface BenchmarkRequest {
  name?: string
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, unknown>
  solver_ids: string[]
  solver_configs?: Record<string, Record<string, unknown>>
  trials?: number
  base_seed?: number
}

export interface SolverBenchmarkSummary {
  solver_id: string
  solver_name: string
  trials_count: number
  best_objective: number
  mean_objective: number
  worst_objective: number
  std_objective: number
  feasibility_rate: number
  mean_runtime_ms: number
  min_runtime_ms: number
  max_runtime_ms: number
  mean_evaluations: number
  optimality_gap_percent?: number | null
  best_solution?: unknown
  convergence_sample?: ConvergencePoint[]
}

export interface BenchmarkResult {
  benchmark_id: string
  name: string
  problem_type: ProblemType
  problem_id?: string
  exact_optimum?: number | null
  summaries: SolverBenchmarkSummary[]
  total_runtime_seconds: number
  created_at: string
}

// ---------------------------------------------------------------------------
// Phase 5: QAOA Quantum Optimization Types
// ---------------------------------------------------------------------------

export type SimulationMode = 'ideal_shots' | 'statevector' | 'depolarizing_noise'
export type ClassicalOptimizerType = 'COBYLA' | 'SLSQP' | 'Nelder-Mead' | 'L-BFGS-B'
export type ParameterInitializationStrategy = 'random' | 'zeros' | 'linear_ramp' | 'custom'

export interface QuantumBackendInfo {
  backend_id: string
  name: string
  backend_type: string
  is_simulator: boolean
  is_hardware: boolean
  hardware_transparency_note: string
  max_qubits: number
  supported_methods: string[]
  is_available: boolean
  qiskit_version?: string
  aer_version?: string
}

export interface QAOAConfiguration {
  p_depth: number
  shots: number
  simulation_mode: SimulationMode
  optimizer: ClassicalOptimizerType
  max_iterations: number
  tolerance?: number
  init_strategy: ParameterInitializationStrategy
  initial_gamma?: number[]
  initial_beta?: number[]
  noise_probability?: number
  seed?: number
  optimization_target?: string
}

export interface CircuitMetadata {
  num_qubits: number
  depth: number
  gate_counts: Record<string, number>
  num_parameters: number
  p_depth: number
  has_measurements: boolean
  creation_timestamp?: string
}

export interface QAOAOptimizationTrace {
  iteration: number
  expectation_value: number
  gamma: number[]
  beta: number[]
  variance?: number
  runtime_ms?: number
}

export interface DecodedSample {
  bitstring: string
  count: number
  probability: number
  raw_binary_vector: number[]
  decoded_solution: Record<string, unknown>
  objective_value: number
  is_feasible: boolean
  constraint_violations: string[]
  is_best_feasible: boolean
  is_most_frequent: boolean
  cut_value?: number
  partition_s?: string[]
  partition_v_minus_s?: string[]
  matching_pairs?: [string, string][]
  total_cost?: number
  tour?: string[]
  tour_length?: number
}

export interface QAOADecodingSummary {
  total_samples: number
  unique_samples: number
  feasible_samples: number
  infeasible_samples: number
  feasible_rate: number
  best_feasible_solution?: DecodedSample | null
  best_infeasible_solution?: DecodedSample | null
  most_frequent_solution: DecodedSample
  all_decoded_samples: DecodedSample[]
}

export interface QAOAExecutionResult {
  execution_id: string
  solver_id: string
  solver_name: string
  problem_type: ProblemType
  status: SolverStatus
  optimal_gamma: number[]
  optimal_beta: number[]
  optimal_expectation_value: number
  best_sample: DecodedSample
  decoding_summary: QAOADecodingSummary
  circuit_metadata: CircuitMetadata
  convergence_history: QAOAOptimizationTrace[]
  total_evaluations: number
  optimizer_iterations: number
  runtime_seconds: number
  backend_info: QuantumBackendInfo
  hardware_transparency_note: string
  termination_reason: string
  is_feasible: boolean
  constraint_violations: string[]
  independent_evaluation?: EvaluationResult
}

export interface QAOAExecutionRecord {
  execution_id: string
  solver_id: string
  solver_name: string
  problem_type: ProblemType
  problem_id?: string
  status: SolverStatus
  submitted_at: string
  started_at?: string
  completed_at?: string
  runtime_seconds?: number
  result?: QAOAExecutionResult
  error?: string
  config: QAOAConfiguration
}

export interface QAOAStatusResponse {
  execution_id: string
  solver_id: string
  problem_type: ProblemType
  status: SolverStatus
  runtime_seconds?: number
  is_completed: boolean
  has_failed: boolean
  error?: string
}

export interface QAOAValidationResponse {
  is_valid: boolean
  problem_type: ProblemType
  num_qubits: number
  p_depth: number
  shots: number
  estimated_parameters: number
  resource_check: string
  issues: string[]
  transparency_warning?: string
}

// ---------------------------------------------------------------------------
// Stage 5.9: Hybrid Quantum-Classical Benchmarking Types
// ---------------------------------------------------------------------------

export interface HybridBenchmarkRequest {
  name?: string
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, unknown>
  include_solvers?: string[]
  qaoa_config?: Partial<QAOAConfiguration>
  classical_configs?: Record<string, Record<string, unknown>>
  trials?: number
  base_seed?: number
}

export interface HybridSolverBenchmarkSummary {
  solver_id: string
  solver_name: string
  solver_category: string
  is_quantum_simulator: boolean
  trials_count: number
  best_objective: number
  mean_objective: number
  worst_objective: number
  std_objective: number
  feasibility_rate: number
  approximation_ratio?: number | null
  optimality_gap_percent?: number | null
  mean_runtime_ms: number
  min_runtime_ms: number
  max_runtime_ms: number
  mean_evaluations: number
  best_solution?: unknown
  circuit_metadata?: CircuitMetadata
  hardware_transparency_note?: string
}

export interface HybridBenchmarkResult {
  benchmark_id: string
  name: string
  problem_type: ProblemType
  problem_id?: string
  exact_optimum?: number | null
  summaries: HybridSolverBenchmarkSummary[]
  total_runtime_seconds: number
  hardware_transparency_note: string
  created_at: string
}

// ---------------------------------------------------------------------------
// Phase 6: Adaptive QAOA Research & Dynamic Strategies Types
// ---------------------------------------------------------------------------

export type AdaptiveStrategyType =
  | 'standard'
  | 'linear_ramp'
  | 'fourier'
  | 'warm_start'
  | 'dynamic_depth'
  | 'adaptive_optimizer'
  | 'full_adaptive'

export type InitializationStrategyType =
  | 'random'
  | 'linear_ramp'
  | 'fourier'
  | 'warm_start'
  | 'custom'

export type DepthGrowthStrategy = 'none' | 'fixed_incremental' | 'improvement_triggered'

export type StoppingConditionType =
  | 'converged'
  | 'stagnated'
  | 'max_iterations_reached'
  | 'max_evaluations_reached'
  | 'timeout'
  | 'target_energy_reached'
  | 'cancelled'
  | 'failed'

export type OptimizerScheduleType = 'static' | 'adaptive_fallback' | 'multi_stage'

export interface StrategyMetadata {
  strategy_id: string
  name: string
  description: string
  supported_problem_types: string[]
  default_parameters: Record<string, unknown>
  requires_prior_parameters: boolean
  supports_dynamic_depth: boolean
  supports_fourier_parameterization: boolean
}

export interface AdaptiveStrategyConfiguration {
  strategy_type: AdaptiveStrategyType
  init_strategy: InitializationStrategyType
  initial_depth: number
  max_depth: number
  depth_growth: DepthGrowthStrategy
  stagnation_patience: number
  improvement_threshold: number
  fourier_q_order: number
  primary_optimizer: ClassicalOptimizerType
  fallback_optimizer?: ClassicalOptimizerType
  optimizer_schedule: OptimizerScheduleType
  max_evaluations_total: number
  warm_start_execution_id?: string
  warm_start_parameters?: {
    gamma?: number[]
    beta?: number[]
  }
}

export interface AdaptiveQAOAConfiguration {
  shots: number
  simulation_mode?: SimulationMode
  backend_name?: string
  seed?: number
  noise_model_enabled?: boolean
  noise_error_rate?: number
  time_limit_seconds?: number
  strategy_config: AdaptiveStrategyConfiguration
}

export interface AdaptiveQAOARequest {
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, unknown>
  config: AdaptiveQAOAConfiguration
}

export interface AdaptiveIteration {
  iteration_index: number
  current_depth: number
  active_optimizer: string
  gamma: number[]
  beta: number[]
  expected_energy: number
  best_energy: number
  eval_count: number
  gradient_norm?: number
  action_taken: string
  timestamp_offset: number
}

export interface AdaptiveDecisionLog {
  timestamp_offset: number
  from_depth: number
  to_depth: number
  trigger_reason: string
  action_summary: string
  active_optimizer: string
}

export interface AdaptiveQAOAResult {
  execution_id: string
  problem_id: string
  problem_type: ProblemType
  status: SolverStatus
  strategy_type: AdaptiveStrategyType
  initial_depth: number
  final_depth: number
  stopping_reason: StoppingConditionType
  best_gamma: number[]
  best_beta: number[]
  best_bitstring: string
  best_solution: Record<string, unknown>
  objective_value: number
  expected_energy: number
  is_feasible: boolean
  constraint_violations: string[]
  approximation_ratio?: number
  exact_optimal_value?: number
  optimality_gap_percent?: number
  total_evaluations: number
  total_circuit_executions: number
  execution_time_ms: number
  iterations_log: AdaptiveIteration[]
  decisions_log: AdaptiveDecisionLog[]
  circuit_metadata?: CircuitMetadata
  hardware_transparency_note: string
  created_at: string
}

export interface AdaptiveExecutionRecord {
  execution_id: string
  problem_id: string
  problem_type: ProblemType
  status: SolverStatus
  strategy_type: AdaptiveStrategyType
  submitted_at: string
  started_at?: string
  completed_at?: string
  runtime_seconds: number
  error?: string
  config: AdaptiveQAOAConfiguration
  result?: AdaptiveQAOAResult
}

export interface AdaptiveStatusResponse {
  execution_id: string
  problem_id: string
  problem_type: ProblemType
  status: SolverStatus
  current_depth: number
  active_optimizer: string
  runtime_seconds: number
  evaluations_completed?: number
  is_completed: boolean
  has_failed: boolean
  error?: string
}

export interface TransferCompatibilityReport {
  is_compatible: boolean
  source_depth: number
  target_depth: number
  compatibility_score: number
  recommended_method: string
  notes: string[]
  confidence_score?: number
  reason?: string
}

export interface TransferParametersRequest {
  source_execution_id?: string
  source_gamma?: number[]
  source_beta?: number[]
  source_depth?: number
  target_depth: number
  transfer_method?: string
  interpolation_method?: string
  source_problem_type?: string
  target_problem_type?: string
}

export interface TransferParametersResponse {
  transferred_gamma: number[]
  transferred_beta: number[]
  target_gamma?: number[]
  target_beta?: number[]
  target_depth: number
  method_used: string
  method?: string
  compatibility_report: TransferCompatibilityReport
}

// ---------------------------------------------------------------------------
// Stage 6.9: Adaptive QAOA Research Benchmarking & Ablation Types
// ---------------------------------------------------------------------------

export type AdaptiveAblationVariant =
  | 'standard_baseline'
  | 'full_adaptive'
  | 'ablation_no_warm_start'
  | 'ablation_no_dynamic_depth'
  | 'ablation_no_optimizer_switching'
  | 'ablation_fourier'

export interface AdaptiveBenchmarkRequest {
  name?: string
  problem_id?: string
  problem_type?: ProblemType
  instance?: Record<string, unknown>
  include_variants?: AdaptiveAblationVariant[]
  initial_depth?: number
  max_depth?: number
  shots?: number
  primary_optimizer?: ClassicalOptimizerType
  fallback_optimizer?: ClassicalOptimizerType
  max_evaluations_total?: number
  trials?: number
  base_seed?: number
}

export interface AdaptiveVariantSummary {
  variant_id: string
  variant_name: string
  description: string
  trials_count: number
  initial_depth: number
  mean_final_depth: number
  best_objective: number
  mean_objective: number
  worst_objective: number
  std_objective: number
  feasibility_rate: number
  approximation_ratio?: number | null
  optimality_gap_percent?: number | null
  mean_runtime_ms: number
  min_runtime_ms: number
  max_runtime_ms: number
  mean_evaluations: number
  mean_circuit_executions: number
  depth_growth_trigger_rate: number
  optimizer_switch_trigger_rate: number
  eval_efficiency_ratio?: number | null
  quality_improvement_percent?: number | null
  best_solution?: unknown
}

export interface AdaptiveBenchmarkResult {
  benchmark_id: string
  name: string
  problem_type: ProblemType
  problem_id?: string
  exact_optimum?: number | null
  summaries: AdaptiveVariantSummary[]
  ablation_insights: string[]
  total_runtime_seconds: number
  hardware_transparency_note: string
  created_at: string
}

// ==========================================
// Phase 7: AI and Machine Learning Intelligence
// ==========================================

export interface ProblemDraftProposal {
  problem_type?: ProblemType | null
  is_supported: boolean
  name: string
  description: string
  entities: Record<string, any>
  objective: Record<string, any>
  constraints: string[]
  suggested_instance: Record<string, any>
  missing_information: string[]
  assumptions: string[]
  confidence_score: number
  is_mathematically_valid: boolean
  validation_status: string
  validation_issues: string[]
  requires_user_confirmation: boolean
  provider_used: string
  disclaimer: string
}

export interface RankedSolverAlternative {
  solver_name: string
  score: number
  rank: number
  is_compatible: boolean
  reason: string
  estimated_runtime_class?: string
}

export interface SolverRecommendation {
  problem_id?: string | null
  problem_type: ProblemType
  recommended_solver: string
  confidence_score: number
  is_confidence_calibrated: boolean
  recommendation_source: 'ml_model' | 'rule_based' | 'fallback'
  ranked_alternatives: RankedSolverAlternative[]
  explanation: string
  key_features_summary: Record<string, any>
  resource_considerations: Record<string, any>
  is_out_of_distribution: boolean
  known_limitations: string[]
  model_version?: string | null
  dataset_version?: string | null
  timestamp: string
}

export interface ModelMetadata {
  model_id: string
  model_version: string
  algorithm_name: string
  hyperparameters: Record<string, any>
  feature_schema_version: string
  features_list: string[]
  target_classes: string[]
  trained_at?: string | null
  training_sample_count: number
  is_trained: boolean
  is_active: boolean
  accuracy?: number | null
  macro_f1?: number | null
  notes?: string | null
}

export interface ModelTrainResponse {
  success: boolean
  model_metadata: ModelMetadata
  evaluation_metrics: Record<string, any>
  training_sample_count: number
  notes: string
}





