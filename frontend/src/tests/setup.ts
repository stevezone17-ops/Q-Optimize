import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Default mock for global.fetch in tests
global.fetch = vi.fn().mockImplementation((url: string) => {
  if (url.includes('/formulations/generate')) {
    return Promise.resolve({
      ok: true,
      status: 201,
      json: () =>
        Promise.resolve({
          id: 'test-formulation-id-1234',
          problem_id: 'test-prob-id',
          owner_id: 'default_user',
          formulation_type: 'qubo',
          schema_version: '1.0',
          qubo: {
            variable_order: ['A', 'B', 'C', 'D'],
            linear_terms: { A: -3.0, B: -5.0, C: -4.0, D: -2.0 },
            quadratic_terms: { 'A,B': 4.0, 'B,C': 6.0, 'C,D': 4.0 },
            offset: 0.0,
            matrix: [
              [-3.0, 4.0, 0.0, 0.0],
              [0.0, -5.0, 6.0, 0.0],
              [0.0, 0.0, -4.0, 4.0],
              [0.0, 0.0, 0.0, -2.0],
            ],
            penalties: {},
            assumptions: ['Graph is undirected', 'Minimization QUBO minimizes negative cut'],
            metadata: { num_variables: 4 },
          },
          ising: {
            variable_order: ['Z_A', 'Z_B', 'Z_C', 'Z_D'],
            local_fields: { Z_A: 0.5, Z_B: -0.5, Z_C: 0.0, Z_D: 1.0 },
            couplings: { 'Z_A,Z_B': 1.0, 'Z_B,Z_C': 1.5, 'Z_C,Z_D': 1.0 },
            offset: -3.5,
            spin_mapping: { A: 'Z_A', B: 'Z_B', C: 'Z_C', D: 'Z_D' },
            latex_expression: 'H = -3.5000 + 0.5000 \\, Z_A - 0.5000 \\, Z_B + 1.0000 \\, Z_A Z_B',
            metadata: { num_spins: 4 },
          },
          created_at: new Date().toISOString(),
        }),
    })
  }

  if (url.includes('/formulations/verify')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          is_verified: true,
          num_states_tested: 16,
          max_energy_discrepancy: 0.0,
          tolerance: 1e-8,
          feasible_states_count: 16,
          min_qubo_energy: -14.0,
          min_ising_energy: -14.0,
          optimal_bitstring: '1010',
          feasibility_summary: 'Exhaustively tested all 16 states. QUBO and Ising energies strictly match.',
          discrepancies: [],
          verified_at: new Date().toISOString(),
        }),
    })
  }

  if (url.includes('/problems') && !url.includes('/validate') && !url.includes('/evaluate')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            id: 'test-prob-1',
            name: 'Registered Max-Cut Benchmark',
            problem_type: 'max_cut',
            instance: {
              nodes: ['A', 'B', 'C', 'D'],
              edges: [['A', 'B', 2.0], ['B', 'C', 3.0]],
            },
          },
        ]),
    })
  }

  if (url.includes('/validate')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          is_valid: true,
          status: 'valid',
          issues: [],
          variables: [{ name: 'x_v', var_type: 'binary', count: 4, bounds: [0, 1], description: 'test' }],
          constraints: [],
          metadata: {},
          validated_at: new Date().toISOString(),
        }),
    })
  }

  if (url.includes('/evaluate')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          problem_type: 'max_cut',
          objective_sense: 'maximize',
          objective_value: 14.0,
          is_feasible: true,
          violations: [],
          details: {
            crossing_edge_count: 4,
            total_edge_count: 5,
            cut_fraction: 0.8,
            partition_0: ['A', 'C'],
            partition_1: ['B', 'D'],
          },
          evaluated_at: new Date().toISOString(),
        }),
    })
  }

  if (url.includes('/solvers/classical/benchmark')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          benchmark_id: 'test-bench-123',
          name: 'Multi-Solver Classical Benchmark',
          problem_type: 'max_cut',
          exact_optimum: 14.0,
          total_runtime_seconds: 0.125,
          created_at: new Date().toISOString(),
          summaries: [
            {
              solver_id: 'exact',
              solver_name: 'Exact Classical Solver',
              trials_count: 1,
              best_objective: 14.0,
              mean_objective: 14.0,
              worst_objective: 14.0,
              std_objective: 0.0,
              feasibility_rate: 1.0,
              mean_runtime_ms: 1.5,
              min_runtime_ms: 1.5,
              max_runtime_ms: 1.5,
              mean_evaluations: 8,
              optimality_gap_percent: 0.0,
              best_solution: { A: 0, B: 1, C: 0, D: 1 },
              convergence_sample: [{ iteration: 8, best_objective: 14.0 }],
            },
            {
              solver_id: 'genetic_algorithm',
              solver_name: 'Genetic Algorithm (GA)',
              trials_count: 2,
              best_objective: 14.0,
              mean_objective: 13.5,
              worst_objective: 13.0,
              std_objective: 0.5,
              feasibility_rate: 1.0,
              mean_runtime_ms: 12.3,
              min_runtime_ms: 11.0,
              max_runtime_ms: 13.6,
              mean_evaluations: 200,
              optimality_gap_percent: 0.0,
              best_solution: { A: 0, B: 1, C: 0, D: 1 },
              convergence_sample: [{ iteration: 0, best_objective: 10.0 }, { iteration: 20, best_objective: 14.0 }],
            },
            {
              solver_id: 'simulated_annealing',
              solver_name: 'Simulated Annealing (SA)',
              trials_count: 2,
              best_objective: 14.0,
              mean_objective: 14.0,
              worst_objective: 14.0,
              std_objective: 0.0,
              feasibility_rate: 1.0,
              mean_runtime_ms: 8.7,
              min_runtime_ms: 8.0,
              max_runtime_ms: 9.4,
              mean_evaluations: 150,
              optimality_gap_percent: 0.0,
              best_solution: { A: 0, B: 1, C: 0, D: 1 },
              convergence_sample: [{ iteration: 0, best_objective: 8.0, temperature: 100.0 }, { iteration: 50, best_objective: 14.0, temperature: 0.1 }],
            },
          ],
        }),
    })
  }

  if (url.includes('/solvers/classical/executions')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            execution_id: 'exec-hist-1',
            solver_id: 'exact',
            solver_name: 'Exact Classical Solver',
            problem_type: 'max_cut',
            status: 'COMPLETED',
            runtime_seconds: 0.003,
            submitted_at: new Date(Date.now() - 60000).toISOString(),
            result: {
              execution_id: 'exec-hist-1',
              solver_id: 'exact',
              solver_name: 'Exact Classical Solver',
              problem_type: 'max_cut',
              status: 'COMPLETED',
              candidate_solution: { A: 0, B: 1, C: 0, D: 1 },
              objective_value: 14.0,
              is_feasible: true,
              constraint_violations: [],
              runtime_seconds: 0.003,
              iterations: 8,
              evaluations: 8,
              optimality_status: 'proven_optimal',
              termination_reason: 'proven_global_optimum',
              convergence_history: [],
              metadata: {},
              created_at: new Date(Date.now() - 60000).toISOString(),
            },
          },
        ]),
    })
  }

  if (url.includes('/solvers/classical/execute')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          execution_id: 'test-exec-123',
          solver_id: 'exact',
          solver_name: 'Exact Classical Solver',
          problem_type: 'max_cut',
          status: 'COMPLETED',
          candidate_solution: { A: 0, B: 1, C: 0, D: 1 },
          objective_value: 14.0,
          is_feasible: true,
          constraint_violations: [],
          runtime_seconds: 0.002,
          iterations: 8,
          evaluations: 8,
          seed: 42,
          optimality_status: 'proven_optimal',
          termination_reason: 'proven_global_optimum',
          convergence_history: [{ iteration: 8, best_objective: 14.0, timestamp_offset: 0.002 }],
          metadata: { method: 'exact_exhaustive' },
          created_at: new Date().toISOString(),
        }),
    })
  }

  if (url.includes('/solvers/classical')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            solver_id: 'exact',
            name: 'Exact Classical Solver',
            description: 'Deterministic global optimization via exhaustive enumeration and branch-and-bound.',
            supported_problem_types: ['max_cut', 'assignment', 'tsp'],
            is_implemented: true,
            stage_introduced: 'Stage 4.2',
            config_schema: { time_limit_seconds: { type: 'float', default: 60.0 } },
            default_parameters: { time_limit_seconds: 60.0 },
          },
          {
            solver_id: 'genetic_algorithm',
            name: 'Genetic Algorithm (GA)',
            description: 'Evolutionary metaheuristic with problem-specific chromosome representations.',
            supported_problem_types: ['max_cut', 'assignment', 'tsp'],
            is_implemented: true,
            stage_introduced: 'Stage 4.3',
            config_schema: { population_size: { type: 'integer', default: 100 } },
            default_parameters: { population_size: 100 },
          },
          {
            solver_id: 'simulated_annealing',
            name: 'Simulated Annealing (SA)',
            description: 'Thermodynamic single-solution trajectory with Metropolis acceptance rule.',
            supported_problem_types: ['max_cut', 'assignment', 'tsp'],
            is_implemented: true,
            stage_introduced: 'Stage 4.4',
            config_schema: { initial_temperature: { type: 'float', default: 100.0 } },
            default_parameters: { initial_temperature: 100.0 },
          },
        ]),
    })
  }

  return Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve({}),
  })
})

afterEach(() => {
  cleanup()
})
