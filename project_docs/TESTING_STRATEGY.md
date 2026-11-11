# Testing Strategy & Quality Assurance

## 1. Testing Philosophy
Mathematical correctness is an absolute release blocker. A beautiful, dark-first scientific UI cannot compensate for an incorrect objective sign, inverted Ising spin mapping, double-counted quadratic coefficient, or violated constraint. Every layer of the platform is validated against independent analytical benchmarks and small-instance ground truths.

---

## 2. Test Suites Overview (Phases 1–8 Active)

| Suite | Runner | Test Files | Total Tests | Status |
|---|---|---|---|---|
| Backend Domain, Formulas, Solvers & Experiments | Pytest (Python 3.12) | 30 test modules | 337 tests | **100% Passing** |
| Frontend Component, Lab & Visualization Suite | Vitest + RTL | 10 test suites | 60 tests | **100% Passing** |
| Production Build Check | Vite + TypeScript | `tsc && vite build` | 0 errors | **Clean Build** |

---

## 3. Backend Test Coverage Breakdown (117 Pytest Tests)

### 3.1 Phase 4 Classical Optimization Engine Test Modules (37 New Tests)
1. **Classical Architecture & Registry (`test_classical_solver_architecture.py` - 8 tests):**
   - Validates `IClassicalSolver` interface compliance, abstract base class contracts, and parameter schema extraction.
   - Tests `ClassicalSolverRegistry` registration, retrieval, and error handling for unknown solvers.
   - Tests `ClassicalSolverFactory` instantiation and configuration overrides.
   - Tests `GET /api/v1/solvers/classical` solver discovery endpoint and parameter introspection.

2. **Exact Classical Solver (`test_exact_solver.py` - 6 tests):**
   - Max-Cut exact enumeration with $2^{n-1}$ symmetry reduction (pinning $x_0 = 0$).
   - Assignment problem exact global optimum via the Hungarian algorithm ($O(n^3)$ via SciPy).
   - TSP exact global optimum via permutation enumeration with start city pinning.
   - Verification of `is_optimal=True` flag and safety bounds ($n \le 18$ for Max-Cut, $n \le 10$ for TSP) rejecting intractable instances with explicit HTTP 400.
   - Verification against Phase 2 independent evaluators (`MaxCutEvaluator`, `AssignmentEvaluator`, `TSPEvaluator`).

3. **Genetic Algorithm Solver (`test_genetic_algorithm.py` - 6 tests):**
   - Binary chromosome representation and single-point/uniform crossover for Max-Cut.
   - Permutation chromosome representation with Order Crossover (OX) and swap/inversion mutations for Assignment and TSP, guaranteeing 100% feasibility by construction.
   - Deterministic seed reproducibility across multi-run executions.
   - Convergence history tracking monotonically non-deteriorating best-so-far fitness curves.
   - REST endpoint execution via `POST /api/v1/solvers/classical/execute`.

4. **Simulated Annealing Solver (`test_simulated_annealing.py` - 6 tests):**
   - Metropolis acceptance probability $P(\Delta E, T) = \exp(-\Delta E / T)$ for uphill exploratory moves.
   - Exponential cooling schedule ($T_{k+1} = \alpha T_k$) and linear cooling schedule ($T_{k+1} = T_k - \beta$).
   - Domain-specific neighborhood operators: 1-flip for Max-Cut, pairwise agent swap for Assignment, and 2-opt edge inversion / vertex swap for TSP.
   - Convergence history tracking with step-by-step temperature decay curves.
   - Independent solution evaluation cross-checking.

5. **Classical Execution Pipeline (`test_classical_execution_pipeline.py` - 6 tests):**
   - Decoupled background execution via `ThreadPoolExecutor(max_workers=8)` and `threading.Event`.
   - Full lifecycle state transitions: `PENDING` $\to$ `RUNNING` $\to$ `COMPLETED` / `CANCELLED` / `FAILED`.
   - Cooperative cancellation tokens stopping iterative heuristics cleanly mid-run.
   - Storage persistence across in-memory dictionary and MongoDB.
   - REST endpoints: `POST /execute`, `POST /execute/async`, `GET /executions`, `GET /executions/{id}`, `GET /executions/{id}/status`, `POST /executions/{id}/cancel`.

6. **Classical Benchmarking Engine (`test_classical_benchmarking.py` - 5 tests):**
   - Multi-solver simultaneous comparative execution on identical problem instances.
   - Multi-trial stochastic repetition computing statistical variance (mean, std, min, max).
   - Exact global optimum baseline calculation with optimality gap evaluation:
     $$\text{optimality\_gap} = \frac{|f_{\text{heuristic}} - f^*|}{|f^*| + 1\times 10^{-9}} \times 100\%$$
   - 100% independent feasibility verification across all benchmark trials.
   - REST endpoints: `POST /benchmark`, `GET /benchmarks`, `GET /benchmarks/{id}`.

### 3.2 Phase 3 Formulation & Mathematical Test Modules (28 Tests - Verified Passing)
1. **QUBO Foundation (`test_qubo_foundation.py` - 7 tests):**
   - Validates upper-triangular canonical indexing ($i < j$).
   - Symmetric off-diagonal normalization (routing $(u, v) \to (\min, \max)$ without doubling).
   - Squared penalty expansion $\lambda (\sum w_k x_k - C)^2$ matching analytical linear, quadratic, and constant formulas.
   - Dense upper-triangular and dense symmetric matrix generation.
   - Sparse dictionary mapping and variable ordering metadata.
   - Numerical energy calculation $E_{\text{QUBO}}(x) = x^T Q x + c$.

2. **Max-Cut QUBO Formulation (`test_max_cut_qubo.py` - 3 tests):**
   - Minimization mapping: proves $E_{\text{QUBO}}(x) = -\text{Cut}(x)$ for every binary partition.
   - Weighted and unweighted graphs; verifies on-diagonal $Q_{ii} = -\text{deg}_w(i)$ and coupling $Q_{ij} = 2 w_{ij}$.
   - Disconnected graph support with zero interaction between disjoint components.

3. **Assignment QUBO Formulation (`test_assignment_qubo.py` - 3 tests):**
   - Exact one-to-one matching formulation with row and column penalties.
   - Strict rejection of rectangular (non-square) cost matrices with explicit `ValueError`.
   - Penalty bound verification: checks that recommended bounds prevent illegal multi-assignments.

4. **TSP QUBO Formulation (`test_tsp_qubo.py` - 3 tests):**
   - $n^2$ position-based variables $x_{i, p}$.
   - Consecutive leg quadratic transitions including the cyclic loop $((p+1) \bmod n \to 0)$.
   - City and step uniqueness penalties.
   - Designated starting city penalty ($x_{\text{start}, 0} = 1$).

5. **QUBO-to-Ising Conversion (`test_ising_conversion.py` - 4 tests):**
   - Physics spin mapping: $x_i = (1 - Z_i)/2$ with $Z_i \in \{-1, +1\}$.
   - Exact derivation of local fields $h_i = -a_i/2 - \frac{1}{4}\sum_{j \ne i} b_{ij}$.
   - Pairwise couplings $J_{ij} = b_{ij}/4$.
   - Energy offset $C = c + \frac{1}{2}\sum_i a_i + \frac{1}{4}\sum_{i < j} b_{ij}$.
   - Verification across 100% of bitstrings and spins: $|E_{\text{QUBO}}(x) - H_{\text{Ising}}(Z)| < 10^{-10}$.

6. **Exhaustive Formulation Verification (`test_formulation_verification.py` - 4 tests):**
   - Truth-table verification across all $2^n$ binary states ($n \le 12$).
   - Cross-checks with Phase 2 independent objective evaluators (`MaxCutEvaluator`, `AssignmentEvaluator`, `TSPEvaluator`).
   - Rejection and error handling when state space exceeds $n = 12$.
   - Detection of insufficient penalty coefficients.

7. **Formulations API Integration (`test_formulations_api.py` - 4 tests):**
   - `POST /api/v1/formulations/generate` for stored problems and ad-hoc payloads.
   - `POST /api/v1/formulations/verify` returning structured verification results.
   - `GET /api/v1/formulations/{id}` retrieval.
   - `GET /api/v1/formulations/{id}/export` multi-format exports (`dense`, `sparse`, `ising`).

### 3.2 Phase 1 & 2 Regressions (52 Tests - Verified Passing)
- `test_health.py` (2 tests): Service health, versioning, memory fallback.
- `test_config.py` (1 test): Settings and environment variable validation.
- `test_problem_schemas.py` (10 tests): Pydantic validation for Max-Cut, Assignment, TSP, and edge cases.
- `test_problems_api.py` (3 tests): REST CRUD, validation, listing.
- `test_max_cut_evaluator.py` (8 tests): Independent Max-Cut evaluator, disconnected graphs, weights.
- `test_assignment_evaluator.py` (8 tests): Independent Assignment evaluator, rectangular matchings, greedy baseline.
- `test_tsp_evaluator.py` (8 tests): Independent TSP evaluator, tour feasibility, loop closure, start pinning.
- `test_constraints.py` (8 tests): Constraint validation engine, structured violation objects.
- `test_evaluation_api.py` (4 tests): Ad-hoc and stored problem evaluation endpoints.

### 3.3 Phase 4 Classical Engine Regressions (37 Tests - Verified Passing)
- `test_classical_infrastructure.py` (8 tests): Solver interfaces, contracts, registry, factory.
- `test_exact_solver.py` (6 tests): Deterministic exact search across Max-Cut, Assignment, TSP.
- `test_genetic_algorithm_solver.py` (6 tests): Binary and permutation chromosomes, Order Crossover (OX), elitism.
- `test_simulated_annealing_solver.py` (6 tests): Metropolis acceptance, exponential/linear cooling, 2-opt moves.
- `test_classical_pipeline.py` (6 tests): Thread-pooled background execution, polling, cancellation.
- `test_classical_benchmarking.py` (5 tests): Multi-solver statistical benchmarking and optimality gaps.

### 3.4 Phase 5 QAOA Quantum Engine Test Suites (42 Tests - Verified Passing)
- `test_quantum_infrastructure.py` (8 tests): QuantumBackendManager, AerSimulator availability, hardware transparency note enforcement, QuantumResourceLimits bounds (qubit and shot ceilings), QuantumExecutionContext cooperative cancellation and execution timeout handling.
- `test_qaoa_hamiltonians.py` (6 tests): QAOACostHamiltonian derived from Phase 3 Ising models, linear RZ(2*gamma*h_i) and coupling RZZ(2*gamma*J_ij) rotation synthesis, QAOAMixerHamiltonian RX(2*beta) transverse-field decomposition, SparsePauliOp operator conversions, exhaustive mathematical energy equivalence across all 2^n basis states against Phase 3 QUBO.
- `test_qaoa_circuit_builder.py` (6 tests): QAOACircuitBuilder with ParameterVector (gamma, beta), Hadamard uniform superposition initialization, alternating cost and mixer layers, parameter binding without graph rebuilding, measurement registration, structural circuit metadata extraction, resource limit enforcement.
- `test_qaoa_optimizer.py` (4 tests): QAOAOptimizer supporting COBYLA, SLSQP, Nelder-Mead, L-BFGS-B; initialization strategies (random, zeros, linear ramp, custom); exact statevector expectation and finite-shot expectation evaluation; convergence history tracing; cancellation handling.
- `test_qaoa_execution_engine.py` (5 tests): QuantumExecutionEngine with Aer transpilation, multi-shot measurement sampling, probability normalization, most frequent bitstring detection, optional depolarizing noise modeling, resource limits enforcement.
- `test_qaoa_solution_decoder.py` (5 tests): QAOASolutionDecoder with little-endian bit-order mapping, domain-specific reconstruction (Max-Cut partitions, Assignment matching pairs, TSP closed loops), constraint validation via Phase 2 validators, objective evaluation via Phase 2 evaluators, selection by true optimization sense, energy cross-verification.
- `test_qaoa_pipeline_and_api.py` (5 tests): QAOAExecutionPipeline with thread-pooled background dispatch, lifecycle tracking (PENDING, RUNNING, COMPLETED, CANCELLED, FAILED), MongoDB/memory persistence, cooperative cancellation, lightweight status polling endpoint (/status), recent executions listing (/executions), synchronous and asynchronous REST endpoints.
- `test_hybrid_benchmarking.py` (3 tests): HybridBenchmarkEngine comparing QAOA against ExactSolver, GeneticAlgorithmSolver, and SimulatedAnnealingSolver; computing approximation ratio (r), optimality gaps, statistical variance across trials, computational evaluations budget, and classical Aer simulator overhead; REST endpoints (/benchmark, /benchmarks, /benchmarks/{id}).

---

## 4. Frontend Test Coverage Breakdown (26 Vitest Tests)

1. **App Shell & Routing (`App.test.tsx` - 3 tests):**
   - Renders landing page hero with hybrid quantum-classical overview.
   - Navigates from landing page to workspace with sidebar and header.
   - Navigates across workspace tabs (Overview, Problem Builder, Formulation Studio, Classical Lab).

2. **Problem Builder Feature (`ProblemBuilder.test.tsx` - 4 tests):**
   - Renders Max-Cut node/edge visualizers and metrics.
   - Switches between Max-Cut, Assignment, and TSP problem families.
   - Confirmation workflow modal for canonical problem creation.
   - Independent solution evaluator modal.

3. **Formulation Studio Feature (`FormulationStudio.test.tsx` - 5 tests):**
   - Renders formulation studio shell, benchmark preset selector, and phase badge.
   - Loads and renders QUBO upper-triangular matrix heatmap with metadata cards (Variables, Linear terms, Quadratic couplings, Offset).
   - Switches between QUBO, Ising Spin Hamiltonian, and Mathematical Verification tabs.
   - Executes exhaustive mathematical verification on the verification tab and displays the `MATHEMATICALLY VERIFIED` badge.
   - Renders penalty configuration inputs (Row/Column Lagrange multipliers) when selecting constrained problem presets.

4. **Classical Optimization Lab (`ClassicalLab.test.tsx` - 7 tests):**
   - Renders Classical Lab header, problem selection controls, and benchmark presets.
   - Renders classical solver selection cards with algorithm categorization badges.
   - Switches solver selection to Genetic Algorithm and displays evolutionary hyperparameters (population size, generations, mutation rate, selection method, elitism).
   - Switches solver selection to Simulated Annealing and displays annealing hyperparameters (initial temperature, cooling rate, steps per temp, cooling schedule).
   - Executes exact classical solver and renders results panel with proven optimal status, independent evaluator verification callout, and domain solution visualizer.
   - Switches to Comparative Benchmark Suite tab, enables multi-solver selection, configures stochastic trials, executes suite, and verifies ranked results table.
   - Switches to Execution Audit History tab, renders past solver execution logs, and verifies inspection modal.

5. **Quantum Optimization Lab (`QuantumLab.test.tsx` - 7 tests):**
   - Renders Quantum Lab header, Phase 5 Active badge, and problem/backend selector.
   - Renders mandatory scientific hardware transparency notice banner.
   - Renders QAOA ansatz and optimizer configuration controls (depth p, shots, simulation mode, optimizer).
   - Renders circuit blueprint and resource bounds card (qubits, 2p parameters, gate decomposition).
   - Executes QAOA simulation and displays results with executive metrics, optimal variational parameters, and independent evaluation verification.
   - Switches to Execution Audit tab and displays persistent execution records.
   - Switches to Comparative Benchmark tab and executes hybrid quantum-classical benchmarking suite.

---

## 5. Release Criteria
Every phase release must satisfy:
1. `python -m pytest backend/tests` exits with code 0 (100% tests passing).
2. `npm run test` in `frontend/` exits with code 0 (100% tests passing).
3. `npm run build` in `frontend/` succeeds with zero TypeScript compiler errors.
4. Independent verification tests confirm that mathematical energy models strictly match ground-truth problem definitions.
5. Zero placeholder metrics or pseudo-quantum execution claims.


---

## 6. Phase 6 Adaptive QAOA Test Suite Coverage (42 Tests Across Backend & Frontend)

### 6.1 Backend Adaptive QAOA Test Modules (201 Total Tests Passing)
1. **Adaptive Architecture & Strategy Registry (`test_adaptive_architecture.py` - 7 tests):**
   - Validates `IAdaptiveStrategy` lifecycle contracts, configuration validation, strategy registry discovery, and REST endpoints (`/strategies`, `/strategies/{id}`, `/validate`).
2. **Adaptive Parameter Initializers (`test_adaptive_initializers.py` - 10 tests):**
   - Tests `LinearRampInitializer` adiabatic schedule discretization.
   - Tests `FourierInitializer` discrete cosine/sine frequency parameterization ($\vec{u}, \vec{v}$) across varying $q$ orders.
   - Tests `WarmStartInitializer` linear angle continuation and dimensional expansion.
   - Tests `RandomInitializer` seed reproducibility and `CustomInitializer` validation bounds.
3. **Warm-Start Parameter Transfer (`test_adaptive_transfer.py` - 6 tests):**
   - Tests `ParameterTransferService` inter-depth mapping (linear interpolation, layer padding, adiabatic extension).
   - Validates `TransferCompatibilityReport` confidence scoring and REST endpoints (`/transfer/check`, `/transfer/parameters`).
4. **Adaptive Optimizer Selection & Scheduling (`test_adaptive_optimizer_controller.py` - 4 tests):**
   - Tests dynamic transition logic (`COBYLA` $\to$ `Nelder-Mead` / `SLSQP`) on stagnation plateaus.
   - Verifies evaluation counting and transition history logging (`OptimizerTransitionRecord`).
5. **Dynamic Circuit Depth Management (`test_adaptive_depth_manager.py` - 4 tests):**
   - Tests layer progression protocols (`IMPROVEMENT_TRIGGERED`, `FIXED_INCREMENTAL`, `NONE`).
   - Verifies depth ceiling enforcement ($p \le 10$) and warm-start parameter injection during depth expansion.
6. **Convergence Monitoring & Multi-Objective Termination (`test_adaptive_convergence_monitor.py` - 4 tests):**
   - Tests rolling energy trajectory monitoring, stagnation windowing, and parameter shift norm calculation.
   - Validates arbitration among `CONTINUE_OPTIMIZATION`, `SWITCH_OPTIMIZER`, `EXPAND_DEPTH`, and `TERMINATE`.
7. **Adaptive Execution Pipeline Integration (`test_adaptive_pipeline.py` - 4 tests):**
   - Tests end-to-end integration of depth manager, optimizer controller, and convergence monitor on Qiskit Aer.
   - Tests cooperative cancellation token handling, thread-pooled worker dispatch, and REST endpoints (`/execute`, `/execute/async`, `/executions/{id}`, `/status`, `/cancel`).
8. **Adaptive Benchmarking & Ablation Studies (`test_adaptive_benchmarking.py` - 3 tests):**
   - Direct execution of `AdaptiveBenchmarkEngine` comparing standard fixed-depth QAOA baseline against Full Adaptive QAOA and ablation variants.
   - Tests multi-trial statistical distributions, exact ground-truth comparison, automated scientific ablation insights synthesis, and REST benchmark endpoints.

### 6.2 Frontend Adaptive Research Lab Test Suite (`AdaptiveQAOALab.test.tsx` - 7 Tests Passing)
1. Renders mode selector with "Adaptive QAOA Lab" tab button.
2. Switches to Adaptive QAOA Lab tab, displaying strategy presets, dynamic depth controls, and optimizer scheduling.
3. Tests strategy preset buttons updating configuration defaults (e.g. Fourier parameterization).
4. Executes Adaptive QAOA simulation, displaying executive metrics, dynamic parameter trajectory ($\vec{\gamma}, \vec{\beta}$), decision audit log, energy iteration trajectory, and hardware transparency notice.
5. Tests the Parameter Transfer Laboratory: executes compatibility checks and parameter transfers.
6. Switches to Execution Audit tab, toggling between standard QAOA and adaptive QAOA execution logs.
7. Executes Adaptive QAOA comparative ablation benchmark through the typed service client.

---

## 7. Phase 7 AI & Machine Learning Intelligence Layer Test Suite (58 Tests Across Backend & Frontend)

### 7.1 Backend AI/ML Test Modules (45 Tests, Total 246 Backend Tests Passing)
1. **AI Architecture & Service Registries (`test_ai_architecture.py` - 5 tests):**
   - Tests `MLModelRegistry` and `AIServiceRegistry` registration, retrieval, and active model toggling.
   - Tests `ExperimentDataAccess` layer querying and schema adaptation.
2. **Feature Engineering Engine (`test_ai_feature_extraction.py` - 6 tests):**
   - Tests 18-dimensional feature vector extraction across Max-Cut, Assignment, and TSP problem instances.
   - Tests QUBO and Ising Hamiltonian feature extraction and array serializability.
3. **Dataset Builder & Leakage-Free Training Pipeline (`test_ai_dataset_and_training.py` - 8 tests):**
   - Tests `SolverSelectionPolicy` Pareto efficiency and feasibility penalty enforcement.
   - Tests `ExperimentDatasetBuilder` aggregation and balance.
   - Tests `ModelTrainingPipeline` group-aware splitting (no instance seed overlap between train/test).
   - Tests classifier training (`RandomForestClassifier`, `GradientBoostingClassifier`).
4. **Intelligent Solver Recommendation (`test_ai_solver_recommendation.py` - 5 tests):**
   - Tests `RuleBasedSolverRecommender` deterministic algorithm bounds.
   - Tests `IntelligentSolverRecommender` ML probability inference and alternative rankings.
   - Tests hard safety filters (qubit limit $N \le 20$, exact solver size ceilings).
   - Tests REST endpoints (`/recommend`, `/models`, `/train`).
5. **Evaluation, Calibration & Explainability (`test_ai_evaluation_and_explainability.py` - 4 tests):**
   - Tests `SolverRecommendationEvaluator` multi-class metrics, Brier score calculation, and selection regret.
   - Tests `ExplainabilityEngine` feature contribution attribution and z-score OOD statistical detection.
6. **Natural Language Optimization Assistant (`test_ai_natural_language_assistant.py` - 7 tests):**
   - Tests intent classification and entity extraction across all three problem families.
   - Tests ambiguous text handling and missing information reporting.
   - Tests unsupported problem description rejection.
   - Tests canonical Phase 2 validation integration on draft proposals.
7. **Model Monitoring & Continuous Learning (`test_ai_monitoring_and_learning.py` - 6 tests):**
   - Tests `ModelMonitor` audit logging and user feedback recording.
   - Tests Kolmogorov-Smirnov (KS) two-sample feature drift detection.
   - Tests `ContinuousLearningPipeline` holdout candidate gating ($\Delta \ge 0.02$) and safe rollback.
8. **End-to-End AI System Integration (`test_ai_end_to_end_integration.py` - 4 tests):**
   - Full lifecycle Max-Cut workflow: NL description $\to$ draft $\to$ canonical Phase 2 validation $\to$ problem registration $\to$ recommendation $\to$ solver execution $\to$ independent evaluator verification $\to$ feedback logging.
   - Full lifecycle Assignment workflow: Hungarian polynomial-time guarantee validation.
   - Full lifecycle TSP workflow: Route distance verification and simulator limits.
   - Cross-capability safety consistency verification.

### 7.2 Frontend AI Interface Test Suite (13 Tests, Total 46 Frontend Tests Passing)
1. **AI-Assisted Problem Builder (`AIAssistedProblemBuilder.test.tsx` - 5 tests):**
   - Renders natural language input textarea, example prompt chips, and target family selector buttons.
   - Dispatches parsing and displays structured draft proposal cards (entities, objective, constraints, assumptions, missing information).
   - Validates draft proposals via Phase 2 validator and renders validation badge.
   - Tests inline JSON editor and requires explicit human confirmation before creating problem.
2. **Intelligent Solver Recommendation Panel (`AISolverRecommendation.test.tsx` - 8 tests):**
   - Renders recommendation spotlight with confidence percentage and driving features.
   - Displays ranked alternatives list with compatibility badges and resource notes.
   - Interacts with the "Apply Recommended Solver & Settings" action.
   - Opens the Recommendation Audit Modal to inspect feature vectors and safety filters.
   - Tests error and OOD warning states.
