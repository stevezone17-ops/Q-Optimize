# Testing Strategy & Quality Assurance

## 1. Testing Philosophy
Mathematical correctness is an absolute release blocker. A beautiful, dark-first scientific UI cannot compensate for an incorrect objective sign, inverted Ising spin mapping, double-counted quadratic coefficient, or violated constraint. Every layer of the platform is validated against independent analytical benchmarks and small-instance ground truths.

---

## 2. Test Suites Overview (Phases 1, 2, & 3 Active)

| Suite | Runner | Test Files | Total Tests | Status |
|---|---|---|---|---|
| Backend Domain & Formulas | Pytest (Python 3.12) | 16 test modules | 80 tests | **100% Passing** |
| Frontend Component & UI | Vitest + RTL | 3 test suites | 12 tests | **100% Passing** |
| Production Build Check | Vite + TypeScript | `tsc && vite build` | 0 errors | **Clean Build** |

---

## 3. Backend Test Coverage Breakdown (80 Pytest Tests)

### 3.1 Phase 3 Formulation & Mathematical Test Modules (28 New Tests)
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

## 4. Frontend Test Coverage Breakdown (12 Vitest Tests)

1. **App Shell & Routing (`App.test.tsx` - 3 tests):**
   - Renders landing page hero with hybrid quantum-classical overview.
   - Navigates from landing page to workspace with sidebar and header.
   - Navigates across workspace tabs (Overview, Problem Builder, Formulation Studio).

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

---

## 5. Release Criteria
Every phase release must satisfy:
1. `python -m pytest backend/tests` exits with code 0 (100% tests passing).
2. `npm run test` in `frontend/` exits with code 0 (100% tests passing).
3. `npm run build` in `frontend/` succeeds with zero TypeScript compiler errors.
4. Independent verification tests confirm that mathematical energy models strictly match ground-truth problem definitions.
5. Zero placeholder metrics or pseudo-quantum execution claims.
