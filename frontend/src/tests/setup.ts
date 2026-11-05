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
