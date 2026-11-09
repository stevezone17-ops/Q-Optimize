# Q-Optimize

> **An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection**

[![Status: Phase 7 Complete](https://img.shields.io/badge/Status-Phase%207%20AI%20%26%20ML-10B981.svg)](#)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](#)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](#)
[![React: 18](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TypeScript-61DAFB.svg)](#)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](#)
[![Tests: 246 Pytest | 46 Vitest](https://img.shields.io/badge/Tests-292%20Passing-emerald.svg)](#)

---

## 1. Overview

**Q-Optimize** is a scientific research and computing platform designed to assist researchers, educators, and developers in describing combinatorial optimization problems, generating verified QUBO and Ising mathematical formulations, executing quantum simulation algorithms (QAOA) alongside exact and heuristic classical baselines, and evaluating solutions with independent mathematical verification.

### Core Principles
- **Mathematical Correctness Before Polish:** Formulations, constraint penalties, and variable orders are verified against exhaustive small-instance truth tables.
- **Upper-Triangular Storage Standard:** All QUBO quadratic terms strictly enforce $i < j$ storage, eliminating double-counting and off-diagonal ambiguity.
- **Analytical Spin Mapping:** Transformations from binary variables $x_i \in \{0, 1\}$ to Pauli-$Z$ spins $Z_i \in \{-1, +1\}$ are exact and mathematically verified across all $2^n$ states.
- **Independent Evaluator Truth:** Solution candidates from any solver are re-evaluated by an independent evaluator directly against the canonical problem definition.
- **Scientific Reproducibility:** Every experiment preserves problem instances, random seeds, optimizer iterations, library versions, and raw bitstring traces.
- **Zero Fabricated Metrics:** No simulated advantage or pseudo-quantum execution is presented as real physical quantum hardware advantage.

---

## 2. Platform Architecture

```text
Q-Optimize/
├── backend/                  # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/           # Versioned REST endpoints (health, problems, formulations, solvers)
│   │   ├── core/             # Configuration, logging, CORS middleware
│   │   ├── domain/           # Canonical problem schemas & formulation domain models
│   │   ├── db/               # MongoDB manager with in-memory local fallback
│   │   ├── services/         # Problem & formulation lifecycle services
│   │   ├── evaluation/       # Independent objective evaluator & constraint validation engine
│   │   ├── formulations/     # QUBO builders, penalty managers, Ising converters, verification engine
│   │   ├── solvers/          # Classical, QAOA (Phase 5), & Adaptive QAOA (Phase 6)
│   │   │   ├── classical/    # IClassicalSolver, ExactSolver, GA, SA, Pipeline, BenchmarkEngine
│   │   │   └── quantum/      # QAOA Hamiltonians, CircuitBuilder, Optimizer, Sampling, Pipeline
│   │   │       └── adaptive/ # Adaptive Strategies, Initializers, Transfer, Scheduling, Depth, Monitor, Pipeline, Benchmarking
│   │   ├── ai/               # AI & ML Intelligence Layer (Phase 7)
│   │   │   ├── natural_language/ # Gemini & Deterministic NL Assistant
│   │   │   ├── feature_extraction.py # 18-dim optimization feature engineering
│   │   │   ├── recommender.py    # MLSolverRecommenderModel & RuleBasedSolverRecommender
│   │   │   ├── explainability.py # Feature attribution, calibration & OOD checks
│   │   │   ├── monitoring.py     # Feedback logging & KS-test feature drift detection
│   │   │   └── continuous_learning.py # Retraining pipeline & safe model rollback
│   │   └── workers/          # Background task queue interfaces (Phase 8)
│   └── tests/                # Pytest unit, constraint, formulation, solver, & AI test suite (246 tests)
├── frontend/                 # React 18 + TypeScript + Vite frontend
│   └── src/
│       ├── app/              # App root and view management
│       ├── components/ui/    # Accessible dark-first scientific UI component library
│       ├── components/layout/# AppLayout, Sidebar (9 workspace tabs), Header
│       ├── features/         # Problem editors, SolutionEvaluatorModal, Formulation Studio components
│       │   ├── problem-builder/     # MaxCutEditor, AssignmentEditor, TSPEditor
│       │   └── formulation-studio/  # QuboHeatmap, IsingInspector, VerificationPanel
│       ├── pages/            # Overview, ProblemBuilder, FormulationStudio, ClassicalLabPage, Learn, Settings
│       ├── services/         # Centralized API service (problemService, formulationService, classicalService)
│       ├── hooks/            # useBackendHealth polling and diagnostic hook
│       └── tests/            # Vitest and Testing Library test suite (46 tests)
├── research/                 # Reproducible research datasets, configs, and notebooks
├── docs/                     # Supplemental documentation
└── project_docs/             # Canonical project requirements and specifications
```

---

## 3. Implemented Capabilities (Phases 1, 2, 3, 4, 5, 6 & 7)

### Phase 7: AI and Machine Learning Intelligence Layer
1. **Natural Language Optimization Assistant (Capability A):**
   - Natural language parsing engine translating human descriptions into formal optimization problems.
   - Dual-provider architecture: Google Gemini API integration (`GeminiLLMProvider`) and robust regex/heuristic parser (`DeterministicFallbackParser`).
   - Domain-specific entity extraction, objective direction determination, and constraint formulation for Max-Cut, Assignment, and TSP.
   - Ambiguity and omission detection returning explicit `missing_information` warnings without hallucinating missing data.
   - Mandatory Phase 2 canonical mathematical validation gate rejecting invalid instances.
   - Human confirmation gate requiring explicit review before problem creation.

2. **Intelligent Solver Recommendation Engine (Capability B):**
   - Supervised ML recommender (`RandomForestClassifier`, `GradientBoostingClassifier`) trained on empirical execution data.
   - Expert `RuleBasedSolverRecommender` enforcing theoretical complexity limits and algorithm suitability.
   - 18-dimensional optimization feature extraction pipeline covering graph structure, degree statistics, constraint densities, QUBO/Ising properties, and resource limits.
   - Strict physical and simulation safety filters (disabling exact solvers for $N > 20$ Max-Cut and $N > 10$ TSP; gating quantum simulators at $N \le 20$ CPU qubits).
   - Group-aware cross-validation splitting by instance ID to eliminate test leakage.
   - Pareto-optimal solver selection policy trading off solution quality and execution latency.

3. **Explainability, Calibration & Out-of-Distribution Safeguards:**
   - Decision rationale synthesis with top-3 feature contribution importance values.
   - Brier score probability calibration evaluation.
   - Out-of-Distribution (OOD) detection via feature z-score divergence ($z_{\text{max}} > 3.5$) with automated fallback to rule-based recommendations.

4. **Continuous Learning & Model Lifecycle Monitoring:**
   - Continuous audit logging of recommendations and user acceptance feedback.
   - Two-sample Kolmogorov-Smirnov (KS) test for feature distribution drift detection.
   - Retraining pipeline with holdout candidate evaluation and safe version rollback.

5. **Integrated Frontend UI & AI Advisor:**
   - Problem Builder: Interactive natural language drafting with suggestion chips and validation badge.
   - Classical & Quantum Labs: Embedded `SolverRecommendationPanel` with one-click preset configuration and full `RecommendationAuditModal`.

### Phase 6: Adaptive QAOA Research & Dynamic Parameter Strategies
1. **Adaptive QAOA Architecture & Extensible Framework:**
   - Standardized `IAdaptiveStrategy` interface with lifecycle methods (`initialize`, `execute_step`, `evaluate_depth_growth`, `on_convergence`, `get_state`).
   - Strategy registry and factory (`AdaptiveStrategyRegistry`, `AdaptiveStrategyFactory`) supporting preset archetypes:
     - `FullAdaptiveStrategy`: Simultaneous depth growth, Fourier/ramp initialization, multi-stage optimizer transitions, and warm starts.
     - `DynamicDepthStrategy`: Layer progression from $p_{\text{init}}$ up to $p_{\text{max}} \le 10$ triggered by stagnation or fixed increments.
     - `FourierStrategy`: Sine/cosine frequency parametrization $(u, v)$ for continuous parameter curves.
     - `WarmStartStrategy`: Interpolates or extends optimal angles from previous runs or depths.
     - `AdaptiveOptimizerStrategy`: Coarse-to-fine or fallback optimizer switching based on plateau detection.
   - Pydantic v2 domain schemas (`AdaptiveQAOARequest`, `AdaptiveQAOAResult`, `AdaptiveStrategyConfiguration`, `AdaptiveIteration`).

2. **Parameter Initialization Strategies:**
   - `LinearRampInitializer`: Physics-grounded Trotterized adiabatic schedule ($\gamma_i = \frac{i}{p}\Delta t$, $\beta_i = (1 - \frac{i}{p})\Delta t$).
   - `FourierInitializer`: Discrete cosine transform / frequency representation reducing $2p$ parameters to $2q$ coefficients ($q \ll p$).
   - `WarmStartInitializer`: Layer-wise interpolation mapping optimal angles $(\vec{\gamma}^*, \vec{\beta}^*)_{p_{\text{old}}} \to (\vec{\gamma}, \vec{\beta})_{p_{\text{new}}}$.
   - `RandomInitializer` with explicit seed reproducibility and `CustomInitializer` with validation.

3. **Parameter Transfer & Warm-Start Engine:**
   - `ParameterTransferService` performing mathematical interpolation and adiabatic extension between differing circuit depths.
   - Compatibility validation (`check_transfer_compatibility`) verifying Hamiltonian overlap, qubit counts, and layer ratios.
   - Extraction of historical parameter trajectories from completed executions.

4. **Dynamic Classical Optimizer Scheduling:**
   - `AdaptiveOptimizerController` supporting `STATIC`, `ADAPTIVE_FALLBACK`, and `MULTI_STAGE` scheduling modes.
   - Automatic heuristic recommendation: COBYLA for small/noisy depths, Nelder-Mead for plateaus, L-BFGS-B / SLSQP for smooth fine-tuning.
   - Comprehensive transition auditing logging optimizer switches, trigger causes, and iteration boundaries.

5. **Dynamic Circuit Depth Management:**
   - `AdaptiveDepthManager` implementing progressive depth growth protocols (`FIXED_INCREMENTAL`, `IMPROVEMENT_TRIGGERED`, `NONE`).
   - Safety ceiling enforcement ($p_{\text{init}} \le p \le 10$) preventing exponential circuit explosion.
   - Warm-start parameter interpolation automatically projecting optimized angles into expanded layer spaces.

6. **Convergence Monitoring & Stopping Conditions:**
   - `AdaptiveConvergenceMonitor` tracking rolling energy histories, moving average gradients, and parameter shift norms.
   - Stagnation windowing evaluating plateau thresholds over configurable patience windows.
   - Multi-objective stopping conditions: `CONVERGED`, `STAGNATED`, `MAX_EVALUATIONS_REACHED`, `TIMEOUT`, `TARGET_ENERGY_REACHED`, `CANCELLED`.
   - Tactical action arbitration: `CONTINUE_OPTIMIZATION`, `SWITCH_OPTIMIZER`, `EXPAND_DEPTH`, `TERMINATE`.

7. **Adaptive QAOA Execution Pipeline:**
   - `AdaptiveQAOAExecutionPipeline` dispatching asynchronous tasks to thread pool (`qopt-aqaoa-`).
   - Cooperative cancellation tokens and full execution persistence in MongoDB with memory fallback.
   - Independent solution decoding: bitstrings decoded and re-evaluated by Phase 2 canonical evaluators (`MaxCutEvaluator`, `AssignmentEvaluator`, `TSPEvaluator`).

8. **Adaptive QAOA Research Lab (Frontend UI):**
   - Interactive Research Lab tab in `frontend/src/pages/QuantumLabPage.tsx`.
   - Strategy architecture presets, dynamic depth controls, classical optimizer scheduling, and parameter transfer tools.
   - Executive metrics grid, parameter trajectory graphs, decision audit logs, energy convergence traces, and domain visualizers.
   - History audit toggle seamlessly switching between standard QAOA and Adaptive QAOA records.

9. **Adaptive Benchmarking & Ablation Study Engine:**
   - `AdaptiveBenchmarkEngine` comparing Standard QAOA baseline against Full Adaptive QAOA and 4 ablation variants (`ablation_no_warm_start`, `ablation_no_dynamic_depth`, `ablation_no_optimizer_switching`, `ablation_fourier`).
   - Multi-trial stochastic repetition, computing statistical distributions (mean, std dev, min, max).
   - Exact ground-truth comparison against `ExactSolver`, reporting Approximation Ratio ($r$), optimality gaps, and evaluation efficiency speedups.
   - Automated synthesis of scientific ablation findings and insights.

10. **Scientific Hardware Transparency Guarantee:**
    - Zero simulated quantum advantage claims: all quantum state evolutions and sampling are explicitly executed on classical CPU emulation via Qiskit Aer.
    - Verified against Phase 2 independent ground-truth evaluators.

### Phase 5: QAOA Quantum Optimization Engine & Hybrid Benchmarking
1. **Quantum Infrastructure & Qiskit Integration:**
   - Qiskit 2.6.1 and Qiskit Aer 0.17.2 classical simulation infrastructure.
   - `QuantumBackendManager` discovering Aer simulation backends (`AerSimulator`) and enforcing hardware transparency disclaimers across all outputs.
   - `QuantumResourceLimits` enforcing strict safety ceilings ($n \le 20$ qubits, $p \le 10$ layers, $\text{shots} \le 50,000$).
   - `QuantumExecutionContext` supporting cooperative cancellation and wall-clock execution timeouts.

2. **Cost and Mixer Hamiltonians:**
   - `QAOACostHamiltonian` constructed analytically from Phase 3 Ising models.
   - Synthesizes exact rotation unitaries: single-qubit $R_Z(2\gamma h_i)$, two-qubit $R_{ZZ}(2\gamma J_{ij})$, and global scalar phase $e^{-i\gamma C}$.
   - `QAOAMixerHamiltonian` generating transverse-field mixer layers via single-qubit $R_X(2\beta)$ gates.
   - Exact mathematical energy equivalence proven across all $2^n$ basis states against Phase 3 QUBO.

3. **Parameterized QAOA Circuit Builder:**
   - Parameterized Qiskit `QuantumCircuit` using `ParameterVector("gamma", p)` and `ParameterVector("beta", p)`.
   - Initial equal superposition state via Hadamard gates $H^{\otimes n}$.
   - Alternating application of cost $U(H_C, \gamma_l)$ and mixer $U(H_M, \beta_l)$ layers for $l = 1, \dots, p$.
   - Fast parameter binding without rebuilding circuit DAGs; measurement registration onto classical registers.

4. **Classical Parameter Optimization Loop:**
   - `QAOAOptimizer` implementing derivative-free (`COBYLA`, `Nelder-Mead`) and gradient-based (`SLSQP`, `L-BFGS-B`) algorithms.
   - Parameter initialization strategies: adiabatic linear ramp, uniform random sampling, or zeros.
   - Evaluates expectation values via exact statevectors or finite-shot sampling distributions.
   - Monotonically recorded expectation convergence curves $\langle H_C \rangle_k$ and optimal angles $(\vec{\gamma}^*, \vec{\beta}^*)$.

5. **Circuit Execution & Finite-Shot Sampling Engine:**
   - Multi-shot execution via `AerSimulator` yielding empirical bitstring frequency counts.
   - Normalized probability distributions and most frequent bitstring detection.
   - Optional depolarizing noise simulation for realistic NISQ device modeling.

6. **Solution Decoding & Independent Evaluation:**
   - Reverses Qiskit little-endian bit-ordering ($x_k = \text{int}(\text{bitstring}[n-1-k])$).
   - Problem-specific reconstruction (Max-Cut partition sets, Assignment matching pairs, TSP closed loops).
   - Re-evaluates each unique measured bitstring using Phase 2 independent objective evaluators and constraint validators.
   - Selects the true best feasible candidate by optimization sense, rather than relying on measurement frequency.

7. **Execution Pipeline & Lifecycle Persistence:**
   - Thread-pooled asynchronous background dispatch via `ThreadPoolExecutor(max_workers=8)` avoiding event-loop blocking.
   - Cooperative cancellation tokens and lifecycle persistence across in-memory storage and MongoDB.
   - REST endpoints (`/solvers/quantum`, `/backends`, `/validate`, `/qaoa/execute`, `/qaoa/execute/async`, `/qaoa/executions`, `/status`, `/cancel`).

8. **Quantum Optimization Lab (Frontend UI):**
   - Interactive QAOA simulator with depth $p$ sliders, shot controls, optimizer selectors, and noise rate toggles.
   - Circuit blueprint card displaying estimated qubits, $2p$ parameters, and gate counts ($H, R_Z, R_{ZZ}, R_X$).
   - Live background execution polling with cooperative cancellation.
   - Executive metrics grid, energy convergence curve, and quantum bitstring measurement distribution histogram.
   - Domain-specific solution visualizers (Partition $S$ vs $V \setminus S$, matching grid, TSP route loop).
   - Execution audit history table with one-click past result inspection.

9. **Hybrid Quantum-Classical Benchmarking Suite:**
   - `HybridBenchmarkEngine` evaluating QAOA alongside `ExactSolver`, `GeneticAlgorithmSolver`, and `SimulatedAnnealingSolver`.
   - Computes quantum **Approximation Ratio** ($r = C_{\text{QAOA}} / C^*$), optimality gaps, and statistical distributions across stochastic trials.
   - Reports computational evaluation budgets and classical simulation latencies.
   - Interactive Comparative Benchmark UI in the Quantum Lab.

10. **Scientific Hardware Transparency Guarantee:**
    - Zero simulated quantum advantage claims: all outputs explicitly report execution on classical CPU Qiskit Aer simulation.

### Phase 4: Classical Optimization Engine & Benchmarking Suite
1. **Classical Solver Architecture & Pydantic Contracts:**
   - Standardized `IClassicalSolver` interface with abstract `solve(problem, config, cancellation_token)` and `get_metadata()`.
   - Dynamic schema validation using typed `SolverRequest`, `SolverResult`, `SolverStatus`, and parameter specifications.
   - Decoupled `ClassicalSolverRegistry` and `ClassicalSolverFactory` with discovery REST endpoint `GET /api/v1/solvers/classical`.

2. **Deterministic Exact Solver (`ExactSolver`):**
   - **Max-Cut:** Symmetry-reduced binary enumeration ($2^{n-1}$ states with fixed $x_0 = 0$) guaranteeing global optimum.
   - **Assignment Problem:** $O(n^3)$ polynomial-time Hungarian algorithm using SciPy's `linear_sum_assignment`.
   - **Travelling Salesperson Problem:** Permutation enumeration fixing start city ($x_0 = 0$) evaluating $(n-1)!$ Hamiltonian cycles.
   - Enforces strict safety cutoffs ($n \le 18$ for Max-Cut, $n \le 10$ for TSP) with immediate actionable feedback.
   - Solution marked with `is_optimal=True` serving as ground truth baseline for heuristic comparison.

3. **Genetic Algorithm Engine (`GeneticAlgorithmSolver`):**
   - Problem-specific representations ensuring 100% validity by construction:
     - **Max-Cut:** Binary chromosomes with uniform / single-point crossover and bit-flip mutation.
     - **Assignment & TSP:** Permutation chromosomes with **Order Crossover (OX)** and swap/inversion mutations preserving bijection constraints.
   - Roulette wheel and tournament selection strategies with elitism preservation.
   - Monotonically tracking convergence history across generations with reproducible random seeding.

4. **Simulated Annealing Engine (`SimulatedAnnealingSolver`):**
   - Metropolis acceptance probability for uphill moves: $P(\Delta E, T) = \exp(-\Delta E / T)$ where $\Delta E = E_{\text{new}} - E_{\text{current}}$.
   - Configurable exponential ($T_{k+1} = \alpha T_k$) and linear ($T_{k+1} = T_k - \beta$) cooling schedules.
   - Domain-specific neighborhood moves: 1-flip for Max-Cut, pairwise swap for Assignment, and 2-opt edge inversion / vertex swap for TSP.
   - Step-by-step temperature decay tracking and convergence curves.

5. **Classical Execution Pipeline:**
   - Thread-pooled asynchronous execution engine using `ThreadPoolExecutor(max_workers=8)` avoiding event-loop blocking.
   - Lifecycle tracking: `PENDING` $\to$ `RUNNING` $\to$ `COMPLETED` / `CANCELLED` / `FAILED`.
   - Thread-safe cooperative cancellation tokens (`threading.Event`) for early termination.
   - Execution persistence across in-memory cache and MongoDB.

6. **Classical Benchmark Engine:**
   - Multi-solver comparative evaluation executing multiple solvers against identical problem instances.
   - Multi-trial stochastic repetition calculating statistical distributions (mean, std dev, min, max, runtime).
   - Exact optimality gap calculation against proven global optimum:
     $$\text{optimality\_gap} = \frac{|f_{\text{heuristic}} - f^*|}{|f^*| + 1\times 10^{-9}} \times 100\%$$
   - 100% independent feasibility verification across all generated solutions.

7. **Classical Optimization Lab (Frontend UI):**
   - **Single Solver Lab:** Interactive solver selector, hyperparameter sliders, synchronous/asynchronous execution, independent evaluator verification callout, and convergence charts.
   - **Domain Visualizers:** Partition split cards ($S$ vs $V \setminus S$) for Max-Cut, agent-to-task assignment tables, and route sequence loops for TSP.
   - **Comparative Benchmark Suite:** Multi-solver comparison with stochastic trials, ranked leaderboards (🥇, 🥈, 🥉), feasibility rates, and optimality gaps.
   - **Execution Audit History:** Tabular execution log with status badges and full result inspection modal.

### Phase 3: QUBO Generation, Constraint Penalties & Ising Hamiltonian Modeling
1. **Canonical QUBO Builder & Representation:**
   - Universal energy function:
     $$E_{\text{QUBO}}(x) = \sum_i Q_{ii} x_i + \sum_{i < j} Q_{ij} x_i x_j + c$$
   - Enforces upper-triangular indexing ($i \le j$) with automatic normalization of symmetric off-diagonal additions ($Q_{ji} \to Q_{ij}$).
   - Reusable squared constraint expansion: converts expressions of form $P = \lambda (\sum_k w_k x_k - C)^2$ into exact linear, quadratic, and constant contributions without numerical drift.
   - Dual export capabilities: dense 2D matrices (upper-triangular or symmetric) and sparse dictionary mappings with variable ordering metadata.

2. **Problem-Specific QUBO Generators:**
   - **Max-Cut:**
     Minimization mapping $E_{\text{QUBO}}(x) = - \text{Cut}(x)$, yielding $Q_{ii} = -\text{deg}_w(i)$, $Q_{ij} = 2 w_{ij}$ for $(i, j) \in E$, offset $c = 0.0$.
   - **Square Assignment Problem:**
     Enforces one-to-one matching via row penalties $A \sum_i (\sum_j x_{ij} - 1)^2$ and column penalties $B \sum_j (\sum_i x_{ij} - 1)^2$. Non-square matrices are strictly rejected with actionable diagnostic errors.
   - **Travelling Salesperson Problem (TSP):**
     $n^2$ position variables $x_{i, p}$ indicating city $i$ at step $p$. Objective encodes distance along cyclic transition $((p+1) \bmod n)$. Penalties enforce exactly one city per step and one step per city, plus optional designated start pinning ($x_{\text{start}, 0} = 1$).

3. **Penalty Management Module:**
   - Reusable `PenaltyManager` calculating mathematically proven sufficiency lower bounds:
     $$A_{\text{min}}^{\text{Assignment}} > \max_{(i,j)} c_{ij} - \min_{(i,j)} c_{ij}$$
     $$A_{\text{min}}^{\text{TSP}} > \max_{(i,j)} D_{ij} - \min_{(i,j)} D_{ij}$$
   - Provides default recommendations, warning thresholds, and validation of user-specified penalty multipliers.

4. **Analytical QUBO-to-Ising Conversion Engine:**
   - Applies the standard physics convention $x_i = \frac{1 - Z_i}{2}$ where Pauli-$Z$ eigenvalues $Z_i \in \{-1, +1\}$ correspond to classical binary states $x_i \in \{0, 1\}$.
   - Exact mathematical derivation for on-site magnetic fields $h_i$, spin couplings $J_{ij}$, and energy offset $C$:
     $$h_i = -\frac{a_i}{2} - \frac{1}{4} \sum_{j \ne i} b_{ij}$$
     $$J_{ij} = \frac{b_{ij}}{4}$$
     $$C = c + \frac{1}{2} \sum_i a_i + \frac{1}{4} \sum_{i < j} b_{ij}$$
   - Generates formatted LaTeX Hamiltonian expressions and spin mapping lookup tables.

5. **Exhaustive Truth-Table Verification Module:**
   - For instances with $n \le 12$ variables (up to $4,096$ states), the backend enumerates all $2^n$ binary bitstrings.
   - Verifies numerical equivalence between $E_{\text{QUBO}}(x)$ and $H_{\text{Ising}}(Z)$ to within tolerance $10^{-6}$.
   - Cross-checks feasible state energies against the Phase 2 independent objective evaluators to prove formulation fidelity.

6. **Interactive Formulation Studio (Frontend):**
   - High-contrast interactive QUBO heatmap displaying linear on-diagonal terms and quadratic off-diagonal couplings with coordinate tooltips.
   - Ising Spin Inspector rendering LaTeX Hamiltonians, local fields $h_i$, and pairwise couplings $J_{ij}$.
   - Live penalty parameter sliders with dynamic bounds checking.
   - One-click exhaustive mathematical verification panel displaying state counts, minimum energies, and proof summaries.
   - Multi-format formulation export: JSON dense matrix, sparse terms dictionary, and LaTeX equation.

---

## 4. API Endpoints (Phase 3 Active)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health and MongoDB/memory status |
| `GET` | `/api/v1/problems/types` | List supported problem families with formulas and constraints |
| `POST` | `/api/v1/problems/validate` | Validate an ad-hoc problem definition without saving |
| `POST` | `/api/v1/problems/evaluate-direct` | Evaluate a candidate solution against an ad-hoc instance |
| `POST` | `/api/v1/problems` | Create and validate a canonical problem |
| `GET` | `/api/v1/problems` | List registered problems |
| `GET` | `/api/v1/problems/{id}` | Retrieve problem definition by ID |
| `GET` | `/api/v1/problems/{id}/metadata` | Retrieve structural statistics and canonical metadata |
| `POST` | `/api/v1/problems/{id}/validate` | Validate stored problem against domain constraints |
| `POST` | `/api/v1/problems/{id}/evaluate` | Evaluate candidate solution against stored problem |
| `POST` | `/api/v1/problems/parse-draft` | Natural language problem drafting (draft-only, human-confirmed) |
| `POST` | `/api/v1/formulations/generate` | Generate QUBO and Ising formulation for stored problem or ad-hoc instance |
| `POST` | `/api/v1/formulations/qubo` | Generate standalone QUBO model with custom penalty multipliers |
| `POST` | `/api/v1/formulations/ising` | Generate standalone Ising Hamiltonian from QUBO model |
| `POST` | `/api/v1/formulations/verify` | Exhaustively verify formulation energy against Ising and original objective ($n \le 12$) |
| `GET` | `/api/v1/formulations/{id}` | Retrieve saved formulation by ID |
| `GET` | `/api/v1/formulations/{id}/metadata`| Retrieve formulation metadata, variable counts, and assumptions |
| `GET` | `/api/v1/formulations/{id}/export` | Export formulation in `dense`, `sparse`, `ising`, or `full` format |
| `GET` | `/api/v1/solvers/classical` | List all registered classical solvers and their parameter schemas |
| `POST` | `/api/v1/solvers/classical/execute` | Execute classical solver synchronously on stored or ad-hoc problem |
| `POST` | `/api/v1/solvers/classical/execute/async` | Dispatch solver execution to background worker queue |
| `GET` | `/api/v1/solvers/classical/executions` | List recent classical solver executions |
| `GET` | `/api/v1/solvers/classical/executions/{id}` | Retrieve execution details, candidate solution, and metrics |
| `GET` | `/api/v1/solvers/classical/executions/{id}/status` | Lightweight status polling for execution progress |
| `POST` | `/api/v1/solvers/classical/executions/{id}/cancel` | Cooperatively cancel active solver run |
| `POST` | `/api/v1/solvers/classical/benchmark` | Run comparative multi-solver benchmark with stochastic trials |
| `GET` | `/api/v1/solvers/classical/benchmarks` | List past benchmark comparison runs |
| `GET` | `/api/v1/solvers/classical/benchmarks/{id}` | Retrieve detailed benchmark trial breakdown and statistics |
| `GET` | `/api/v1/solvers/quantum/backends` | List available quantum backends and hardware transparency notice |
| `POST` | `/api/v1/solvers/quantum/qaoa/execute` | Execute standard fixed-depth QAOA synchronously |
| `POST` | `/api/v1/solvers/quantum/qaoa/execute/async` | Dispatch standard QAOA to background worker queue |
| `GET` | `/api/v1/solvers/quantum/qaoa/executions` | List past standard QAOA executions |
| `GET` | `/api/v1/solvers/quantum/qaoa/executions/{id}` | Retrieve execution details, circuit metadata, and decoded solution |
| `GET` | `/api/v1/solvers/quantum/qaoa/executions/{id}/status` | Lightweight status polling for standard QAOA execution |
| `POST` | `/api/v1/solvers/quantum/qaoa/executions/{id}/cancel` | Cooperatively cancel active standard QAOA execution |
| `POST` | `/api/v1/solvers/quantum/hybrid/benchmark` | Run comparative hybrid quantum-classical benchmark |
| `GET` | `/api/v1/solvers/quantum/adaptive/strategies` | List registered adaptive QAOA strategies and parameters |
| `GET` | `/api/v1/solvers/quantum/adaptive/strategies/{strategy_id}` | Retrieve specific adaptive QAOA strategy metadata |
| `POST` | `/api/v1/solvers/quantum/adaptive/validate` | Validate adaptive QAOA configuration parameters |
| `POST` | `/api/v1/solvers/quantum/adaptive/transfer/check` | Check compatibility of parameter transfer between depths/problems |
| `POST` | `/api/v1/solvers/quantum/adaptive/transfer/parameters` | Compute interpolated or padded parameter transfer vector |
| `POST` | `/api/v1/solvers/quantum/adaptive/execute` | Execute adaptive QAOA synchronously |
| `POST` | `/api/v1/solvers/quantum/adaptive/execute/async` | Dispatch adaptive QAOA to background worker queue |
| `GET` | `/api/v1/solvers/quantum/adaptive/executions` | List past adaptive QAOA executions |
| `GET` | `/api/v1/solvers/quantum/adaptive/executions/{id}` | Retrieve adaptive execution details, audit log, and trajectories |
| `GET` | `/api/v1/solvers/quantum/adaptive/executions/{id}/status` | Lightweight status polling for adaptive execution |
| `POST` | `/api/v1/solvers/quantum/adaptive/executions/{id}/cancel` | Cooperatively cancel active adaptive QAOA execution |
| `POST` | `/api/v1/solvers/quantum/adaptive/benchmarks` | Run multi-trial adaptive ablation benchmark study |
| `GET` | `/api/v1/solvers/quantum/adaptive/benchmarks` | List past adaptive benchmark runs |
| `GET` | `/api/v1/solvers/quantum/adaptive/benchmarks/{id}` | Retrieve detailed adaptive benchmark trial results and ablation insights |

---

## 5. Getting Started

### Prerequisites
- **Python:** 3.12+
- **Node.js:** v20+ / v22+
- **npm:** 10+

### Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Running Test Suites

```bash
# Backend test suite (201 tests across schemas, evaluators, constraints, QUBO, Ising, classical solvers, QAOA, adaptive QAOA, benchmarks)
python -m pytest backend/tests -v

# Frontend test suite (33 tests across App shell, Problem Builder, Formulation Studio, Classical Lab, and Adaptive QAOA Lab)
npm test --prefix frontend

# Production build check
npm run build --prefix frontend
```

---

## 6. Known Limitations & Research Boundaries
- **Exact Solver Instance Limits:** `ExactSolver` enforces safety thresholds ($n \le 18$ for Max-Cut, $n \le 10$ for TSP) to prevent factorial/exponential computational explosions.
- **Classical Simulation Ceilings:** Quantum state evolutions and sampling are conducted classically via Qiskit Aer ($n \le 20$ qubits, $p \le 10$ layers, $\text{shots} \le 50,000$). No physical quantum hardware execution or physical quantum supremacy is claimed.
- **Natural Language Parsing:** Remains strictly draft-only; human confirmation is mandatory before canonical creation.

---

## 7. License

Licensed under the MIT License. Developed for research and educational purposes.
