# Database Schema

## Principles
Use versioned, validated schemas. Every private resource must be queried using the authenticated user's owner ID. Do not trust owner IDs supplied by the browser.

## Collections

### users
`_id`, `email` (unique), `password_hash`, `display_name`, `role`, `created_at`, `updated_at`.

### problems
`_id`, `owner_id`, `name`, `problem_type`, `schema_version`, `description`, `instance`, `created_at`, `updated_at`.

### formulations
`_id`, `problem_id`, `owner_id`, `formulation_type`, `schema_version`, `variable_order`, `linear_terms`, `quadratic_terms`, `offset`, `penalties`, `assumptions`, `created_at`.

### experiments
`_id`, `owner_id`, `problem_id`, `formulation_id`, `status`, `solver_name`, `solver_config`, `environment`, `created_at`, `started_at`, `completed_at`, `error`.

### results
`_id`, `experiment_id`, `candidate_solution`, `objective_value`, `is_feasible`, `constraint_violations`, `runtime_seconds`, `metrics`, `raw_metadata`, `created_at`.

### executions
`_id`, `execution_id` (unique), `solver_name`, `problem_type`, `problem_id`, `status` (`PENDING`, `RUNNING`, `COMPLETED`, `CANCELLED`, `FAILED`), `config`, `result` (`candidate_solution`, `objective_value`, `is_feasible`, `runtime_seconds`, `convergence_history`, `extra_metadata`), `error`, `created_at`, `updated_at`.

### benchmarks
`_id`, `benchmark_id` (unique), `problem_type`, `problem_id`, `problem_name`, `solvers_evaluated`, `num_trials`, `random_seed`, `exact_optimum`, `summaries` (array of per-solver summary metrics: `solver_name`, `num_trials`, `feasibility_rate`, `mean_objective`, `std_objective`, `best_objective`, `worst_objective`, `mean_runtime_seconds`, `std_runtime_seconds`, `optimality_gap_percent`), `trials` (detailed individual trial outcomes), `created_at`.

### quantum_executions
`_id`, `execution_id` (unique), `solver_id` (`qaoa`), `problem_type`, `problem_id`, `status` (`PENDING`, `RUNNING`, `COMPLETED`, `CANCELLED`, `FAILED`), `config` (`p_depth`, `shots`, `simulation_mode`, `optimizer`, `max_iterations`, `init_strategy`, `noise_probability`, `seed`), `result` (`optimal_gamma`, `optimal_beta`, `optimal_expectation_value`, `best_solution`, `decoding_summary`, `circuit_metadata`, `convergence_history`, `runtime_seconds`, `hardware_transparency_note`), `submitted_at`, `started_at`, `completed_at`, `error`.

### hybrid_benchmarks
`_id`, `benchmark_id` (unique), `name`, `problem_type`, `problem_id`, `exact_optimum`, `summaries` (array of `HybridSolverBenchmarkSummary`: `solver_id`, `solver_name`, `solver_category`, `is_quantum_simulator`, `trials_count`, `best_objective`, `mean_objective`, `worst_objective`, `std_objective`, `feasibility_rate`, `approximation_ratio`, `optimality_gap_percent`, `mean_runtime_ms`, `mean_evaluations`, `best_solution`, `circuit_metadata`, `hardware_transparency_note`), `total_runtime_seconds`, `hardware_transparency_note`, `created_at`.

### reports
`_id`, `owner_id`, `experiment_id`, `format`, `storage_reference`, `created_at`.

## Indexes
- Unique index on `users.email`.
- `problems.owner_id, updated_at`.
- `experiments.owner_id, created_at`.
- `experiments.status`.
- `results.experiment_id`.
- Unique index on `executions.execution_id`.
- `executions.status, created_at`.
- `executions.solver_name, problem_type`.
- Unique index on `benchmarks.benchmark_id`.
- `benchmarks.problem_id, created_at`.
- Unique index on `quantum_executions.execution_id`.
- `quantum_executions.status, submitted_at`.
- Unique index on `hybrid_benchmarks.benchmark_id`.
- `hybrid_benchmarks.problem_type, created_at`.
- `reports.owner_id, created_at`.

## Security and evolution
Hash passwords using a modern password hashing algorithm. Never store raw passwords or API keys. Validate ownership and IDs. Version problem/formulation documents and provide migrations when schemas change.

### adaptive_executions (Phase 6)
`_id`, `execution_id` (unique), `problem_id`, `problem_type`, `status` (`PENDING`, `RUNNING`, `COMPLETED`, `CANCELLED`, `FAILED`), `strategy_type`, `submitted_at`, `started_at`, `completed_at`, `runtime_seconds`, `config` (`shots`, `simulation_mode`, `backend_name`, `strategy_config`), `result` (`strategy_type`, `initial_depth`, `final_depth`, `stopping_reason`, `best_gamma`, `best_beta`, `best_bitstring`, `best_solution`, `objective_value`, `expected_energy`, `is_feasible`, `approximation_ratio`, `optimality_gap_percent`, `total_evaluations`, `total_circuit_executions`, `execution_time_ms`, `iterations_log`, `decisions_log`, `circuit_metadata`, `hardware_transparency_note`), `error`.

### adaptive_benchmarks (Phase 6)
`_id`, `benchmark_id` (unique), `name`, `problem_type`, `problem_id`, `exact_optimum`, `summaries` (array of `AdaptiveVariantSummary`: `variant_id`, `variant_name`, `trials_count`, `initial_depth`, `mean_final_depth`, `best_objective`, `mean_objective`, `std_objective`, `feasibility_rate`, `approximation_ratio`, `optimality_gap_percent`, `mean_runtime_ms`, `mean_evaluations`, `mean_circuit_executions`, `depth_growth_trigger_rate`, `optimizer_switch_trigger_rate`, `eval_efficiency_ratio`, `quality_improvement_percent`), `ablation_insights` (array of strings), `total_runtime_seconds`, `hardware_transparency_note`, `created_at`.

## Phase 6 Indexes
- Unique index on `adaptive_executions.execution_id`.
- `adaptive_executions.status, submitted_at`.
- `adaptive_executions.strategy_type, problem_type`.
- Unique index on `adaptive_benchmarks.benchmark_id`.
- `adaptive_benchmarks.problem_type, created_at`.
