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

  if (url.includes('/solvers/quantum/backends')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            backend_id: 'aer_simulator',
            name: 'Qiskit Aer Simulator',
            backend_type: 'aer_simulator',
            is_simulator: true,
            is_hardware: false,
            hardware_transparency_note:
              'Execution runs on classical quantum circuit simulation via Qiskit Aer. No physical quantum hardware speedup is claimed.',
            max_qubits: 20,
            supported_methods: ['statevector', 'density_matrix', 'matrix_product_state'],
            is_available: true,
            qiskit_version: '2.6.1',
            aer_version: '0.17.2',
          },
        ]),
    })
  }

  if (url.includes('/solvers/quantum/qaoa/executions') && !url.includes('/status') && !url.includes('/cancel')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            execution_id: 'qexec-hist-1',
            solver_id: 'qaoa',
            solver_name: 'Quantum Approximate Optimization Algorithm (QAOA)',
            problem_type: 'max_cut',
            status: 'COMPLETED',
            runtime_seconds: 0.12,
            submitted_at: new Date(Date.now() - 120000).toISOString(),
            config: {
              p_depth: 1,
              shots: 1024,
              simulation_mode: 'ideal_shots',
              optimizer: 'COBYLA',
              max_iterations: 30,
            },
            result: {
              execution_id: 'qexec-hist-1',
              solver_id: 'qaoa',
              solver_name: 'Quantum Approximate Optimization Algorithm (QAOA)',
              problem_type: 'max_cut',
              status: 'COMPLETED',
              optimal_gamma: [0.3927],
              optimal_beta: [0.7854],
              optimal_expectation_value: -3.5,
              best_sample: {
                bitstring: '101',
                count: 420,
                probability: 0.41,
                raw_binary_vector: [1, 0, 1],
                decoded_solution: { partition_s: ['0', '2'], partition_v_minus_s: ['1'], cut_value: 5.0 },
                objective_value: 5.0,
                is_feasible: true,
                constraint_violations: [],
                is_best_feasible: true,
                is_most_frequent: true,
                cut_value: 5.0,
                partition_s: ['0', '2'],
                partition_v_minus_s: ['1'],
              },
              decoding_summary: {
                total_samples: 1024,
                unique_samples: 8,
                feasible_samples: 1024,
                infeasible_samples: 0,
                feasible_rate: 1.0,
                best_feasible_solution: {
                  bitstring: '101',
                  count: 420,
                  probability: 0.41,
                  raw_binary_vector: [1, 0, 1],
                  decoded_solution: { partition_s: ['0', '2'], partition_v_minus_s: ['1'], cut_value: 5.0 },
                  objective_value: 5.0,
                  is_feasible: true,
                  constraint_violations: [],
                  is_best_feasible: true,
                  is_most_frequent: true,
                },
                most_frequent_solution: {
                  bitstring: '101',
                  count: 420,
                  probability: 0.41,
                  raw_binary_vector: [1, 0, 1],
                  decoded_solution: { partition_s: ['0', '2'], partition_v_minus_s: ['1'], cut_value: 5.0 },
                  objective_value: 5.0,
                  is_feasible: true,
                  constraint_violations: [],
                  is_best_feasible: true,
                  is_most_frequent: true,
                },
                all_decoded_samples: [
                  {
                    bitstring: '101',
                    count: 420,
                    probability: 0.41,
                    raw_binary_vector: [1, 0, 1],
                    decoded_solution: {},
                    objective_value: 5.0,
                    is_feasible: true,
                    constraint_violations: [],
                    is_best_feasible: true,
                    is_most_frequent: true,
                  },
                ],
              },
              circuit_metadata: {
                num_qubits: 3,
                depth: 8,
                gate_counts: { h: 3, rz: 3, rzz: 3, rx: 3 },
                num_parameters: 2,
                p_depth: 1,
                has_measurements: true,
              },
              convergence_history: [
                { iteration: 1, expectation_value: -1.2, gamma: [0.1], beta: [0.2] },
                { iteration: 2, expectation_value: -3.5, gamma: [0.3927], beta: [0.7854] },
              ],
              total_evaluations: 25,
              optimizer_iterations: 15,
              runtime_seconds: 0.12,
              backend_info: {
                backend_id: 'aer_simulator',
                name: 'Qiskit Aer Simulator',
                backend_type: 'aer_simulator',
                is_simulator: true,
                is_hardware: false,
                hardware_transparency_note: 'Simulation on Aer.',
                max_qubits: 20,
                supported_methods: ['statevector'],
                is_available: true,
              },
              hardware_transparency_note: 'Simulation run on classical Qiskit Aer simulator.',
              termination_reason: 'Optimization converged within tolerance.',
              is_feasible: true,
              constraint_violations: [],
            },
          },
        ]),
    })
  }

  if (url.includes('/solvers/quantum/qaoa/execute')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          execution_id: 'test-qexec-999',
          solver_id: 'qaoa',
          solver_name: 'Quantum Approximate Optimization Algorithm (QAOA)',
          problem_type: 'max_cut',
          status: 'COMPLETED',
          optimal_gamma: [0.3927],
          optimal_beta: [0.7854],
          optimal_expectation_value: -3.5,
          best_sample: {
            bitstring: '101',
            count: 420,
            probability: 0.41,
            raw_binary_vector: [1, 0, 1],
            decoded_solution: { partition_s: ['0', '2'], partition_v_minus_s: ['1'], cut_value: 5.0 },
            objective_value: 5.0,
            is_feasible: true,
            constraint_violations: [],
            is_best_feasible: true,
            is_most_frequent: true,
            cut_value: 5.0,
            partition_s: ['0', '2'],
            partition_v_minus_s: ['1'],
          },
          decoding_summary: {
            total_samples: 1024,
            unique_samples: 4,
            feasible_samples: 1024,
            infeasible_samples: 0,
            feasible_rate: 1.0,
            best_feasible_solution: {
              bitstring: '101',
              count: 420,
              probability: 0.41,
              raw_binary_vector: [1, 0, 1],
              decoded_solution: { partition_s: ['0', '2'], partition_v_minus_s: ['1'], cut_value: 5.0 },
              objective_value: 5.0,
              is_feasible: true,
              constraint_violations: [],
              is_best_feasible: true,
              is_most_frequent: true,
            },
            most_frequent_solution: {
              bitstring: '101',
              count: 420,
              probability: 0.41,
              raw_binary_vector: [1, 0, 1],
              decoded_solution: { partition_s: ['0', '2'], partition_v_minus_s: ['1'], cut_value: 5.0 },
              objective_value: 5.0,
              is_feasible: true,
              constraint_violations: [],
              is_best_feasible: true,
              is_most_frequent: true,
            },
            all_decoded_samples: [
              {
                bitstring: '101',
                count: 420,
                probability: 0.41,
                raw_binary_vector: [1, 0, 1],
                decoded_solution: {},
                objective_value: 5.0,
                is_feasible: true,
                constraint_violations: [],
                is_best_feasible: true,
                is_most_frequent: true,
              },
              {
                bitstring: '010',
                count: 380,
                probability: 0.37,
                raw_binary_vector: [0, 1, 0],
                decoded_solution: {},
                objective_value: 5.0,
                is_feasible: true,
                constraint_violations: [],
                is_best_feasible: false,
                is_most_frequent: false,
              },
            ],
          },
          circuit_metadata: {
            num_qubits: 3,
            depth: 8,
            gate_counts: { h: 3, rz: 3, rzz: 3, rx: 3 },
            num_parameters: 2,
            p_depth: 1,
            has_measurements: true,
          },
          convergence_history: [
            { iteration: 1, expectation_value: -1.2, gamma: [0.1], beta: [0.2] },
            { iteration: 2, expectation_value: -3.5, gamma: [0.3927], beta: [0.7854] },
          ],
          total_evaluations: 25,
          optimizer_iterations: 15,
          runtime_seconds: 0.08,
          backend_info: {
            backend_id: 'aer_simulator',
            name: 'Qiskit Aer Simulator',
            backend_type: 'aer_simulator',
            is_simulator: true,
            is_hardware: false,
            hardware_transparency_note: 'Simulation on Aer.',
            max_qubits: 20,
            supported_methods: ['statevector'],
            is_available: true,
          },
          hardware_transparency_note: 'Simulation run on classical Qiskit Aer simulator.',
          termination_reason: 'Optimization converged within tolerance.',
          is_feasible: true,
          constraint_violations: [],
        }),
    })
  }

  if (url.includes('/solvers/quantum')) {
    return Promise.resolve({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve([
          {
            solver_id: 'qaoa',
            name: 'Quantum Approximate Optimization Algorithm (QAOA)',
            category: 'quantum_variational',
            backend: 'qiskit_aer',
            supported_problem_types: ['max_cut', 'assignment', 'tsp'],
            is_simulator: true,
            stage_introduced: 'Stage 5.1',
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
