# Testing Strategy & Quality Assurance

## 1. Testing Philosophy
Mathematical correctness is an absolute release blocker. A beautiful, dark-first scientific UI cannot compensate for an incorrect objective sign, inverted Ising spin mapping, double-counted quadratic coefficient, or violated constraint. Every layer of the platform is validated against independent analytical benchmarks and small-instance ground truths.

---

## 2. Test Suites Overview (Phases 1, 2, 3, & 4 Active)

| Suite | Runner | Test Files | Total Tests | Status |
|---|---|---|---|---|
| Backend Domain, Formulas & Classical Solvers | Pytest (Python 3.12) | 22 test modules | 117 tests | **100% Passing** |
| Frontend Component & UI Suite | Vitest + RTL | 4 test suites | 19 tests | **100% Passing** |
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

---

## 4. Frontend Test Coverage Breakdown (19 Vitest Tests)

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

---

## 5. Release Criteria
Every phase release must satisfy:
1. `python -m pytest backend/tests` exits with code 0 (100% tests passing).
2. `npm run test` in `frontend/` exits with code 0 (100% tests passing).
3. `npm run build` in `frontend/` succeeds with zero TypeScript compiler errors.
4. Independent verification tests confirm that mathematical energy models strictly match ground-truth problem definitions.
5. Zero placeholder metrics or pseudo-quantum execution claims.
