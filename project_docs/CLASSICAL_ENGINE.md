# Classical Optimization Engine

## 1. Architectural Purpose and Core Mandate
The **Classical Optimization Engine** of Q-Optimize provides mathematically transparent, reproducible, and independently verified classical baselines across canonical optimization problem families (Max-Cut, Assignment, and TSP). These baselines serve as the definitive ground truth for benchmarking heuristic quality, runtime scalability, and evaluating prospective quantum advantage without fabrication.

All classical solvers implement a unified contract, decouple algorithmic internals from problem definitions, utilize Phase 2 independent evaluators (`MaxCutEvaluator`, `AssignmentEvaluator`, `TSPEvaluator`) for solution truth verification, and feed into a persistent execution and benchmarking pipeline.

---

## 2. Solver Architecture and Interfaces

### 2.1 The `IClassicalSolver` Interface
All solvers inherit from the abstract base class `IClassicalSolver`:

```python
class IClassicalSolver(ABC):
    @property
    @abstractmethod
    def solver_id(self) -> str: ...
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def description(self) -> str: ...
    @property
    @abstractmethod
    def supported_problem_types(self) -> List[ProblemType]: ...
    @property
    @abstractmethod
    def is_implemented(self) -> bool: ...
    @property
    @abstractmethod
    def stage_introduced(self) -> str: ...
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]: ...
    @abstractmethod
    def solve(
        self,
        problem_type: ProblemType,
        instance: Dict[str, Any],
        config: Optional[SolverConfiguration] = None,
        seed: Optional[int] = 42,
    ) -> SolverResult: ...
```

### 2.2 Standardized Output Contract (`SolverResult`)
Every solver execution emits a typed `SolverResult` containing:
- `execution_id`: Unique tracking identifier (`exec-<uuid>`).
- `solver_id`, `solver_name`: Solver identity.
- `problem_type`: Canonical problem family.
- `status`: Lifecycle termination state (`COMPLETED`, `TIMED_OUT`, `FAILED`, `CANCELLED`).
- `candidate_solution`: Domain-specific solution representation (node dictionary, assignment map, tour list).
- `objective_value`: Verified objective value computed by Phase 2 independent ground truth evaluator.
- `is_feasible`: Boolean constraint satisfaction indicator.
- `constraint_violations`: Array of violation explanations if infeasible.
- `runtime_seconds`: Pure algorithmic execution time.
- `iterations`, `evaluations`: Iteration counts and candidate evaluation metrics.
- `optimality_status`: Mathematical classification (`proven_optimal`, `heuristic_feasible`, `heuristic_infeasible`).
- `termination_reason`: Deterministic reason for stopping.
- `convergence_history`: Checkpoint list of `ConvergencePoint` tracking trajectory over iterations.
- `metadata`: Algorithm-specific internal parameters and diagnostics.

---

## 3. Implemented Algorithms

### 3.1 Exact Classical Solver (`ExactSolver`, Stage 4.2)
- **ID:** `exact`
- **Max-Cut:** Exhaustive enumeration over all $2^{n-1}$ non-isomorphic bipartitions by symmetry reduction (fixing vertex 0 to Partition 0). Enforces a hard safety cutoff ($n \le 18$) to prevent exponential memory/CPU exhaustion.
- **Assignment:** Deterministic polynomial-time global optimum via the Hungarian algorithm ($O(n^3)$) through `scipy.optimize.linear_sum_assignment`. Formats candidate as `{agent_i: task_j}`.
- **TSP:** Full permutation enumeration over $(n-1)!$ tours by fixing the designated starting vertex (or vertex 0). Enforces safety cutoff ($n \le 10$).
- **Optimality Status:** Always `proven_optimal` upon normal completion.

### 3.2 Genetic Algorithm Engine (`GeneticAlgorithmSolver`, Stage 4.3)
- **ID:** `genetic_algorithm`
- **Max-Cut Encoding:** Binary string chromosomes of length $n$. Uniform two-point crossover, bit-flip mutation ($p_m$), tournament/roulette selection, and elitism.
- **Assignment Encoding:** Permutation representations of task indices `0..n-1`. Order Crossover (OX) and pairwise transposition swap mutations preserve 1-to-1 matching validity strictly by construction (100% feasibility guaranteed).
- **TSP Encoding:** Permutation tour chromosomes with starting city pinning. Order Crossover (OX) preserves Hamiltonian cycle properties; 2-opt inversion and swap mutations drive neighborhood exploration.
- **Features:** Configurable population size, generations, mutation/crossover rates, elitism count, tournament size, deterministic seeding, and convergence logging.

### 3.3 Simulated Annealing Engine (`SimulatedAnnealingSolver`, Stage 4.4)
- **ID:** `simulated_annealing`
- **Metropolis Acceptance:** For minimization ($\Delta E = E_{\text{cand}} - E_{\text{curr}}$), accept unconditionally if $\Delta E \le 0$; accept with probability $P = \exp(-\Delta E / T)$ if $\Delta E > 0$. For maximization (Max-Cut), energy is $E = -\text{cut\_weight}$.
- **Cooling Schedules:**
  - *Exponential:* $T_{k+1} = \max(T_f, T_k \cdot \alpha)$ with decay rate $\alpha \in (0, 1)$.
  - *Linear:* $T_k = \max(T_f, T_0 - k \cdot \Delta T)$ where $\Delta T = \frac{T_0 - T_f}{K}$.
- **Neighborhood Operators:**
  - *Max-Cut:* 1-flip neighborhood transitions.
  - *Assignment:* Pairwise task swap between two distinct agents.
  - *TSP:* 2-opt edge inversion (subsegment reversal) and vertex swap moves.
- **State Tracking:** Maintains separate best-so-far solution from current perturbed state; logs temperature and objective at every temperature step.

---

## 4. Execution Pipeline (`ClassicalExecutionPipeline`, Stage 4.5)
The engine provides a thread-pooled, non-blocking execution manager:
- Decouples compute-heavy solver execution from the FastAPI asynchronous event loop using `concurrent.futures.ThreadPoolExecutor`.
- Tracks full lifecycle states: `PENDING` $\to$ `RUNNING` $\to$ `COMPLETED` / `CANCELLED` / `FAILED` / `TIMED_OUT`.
- Supports cooperative cancellation via `threading.Event` tokens.
- Dual-tier persistence: in-memory fast cache (`db_manager.memory_store["executions"]`) and persistent MongoDB collection (`executions`).
- Endpoints:
  - `POST /api/v1/solvers/classical/execute` (synchronous or background mode)
  - `POST /api/v1/solvers/classical/execute/async` (immediate 202 Accepted)
  - `GET /api/v1/solvers/classical/executions/{id}` (full record)
  - `GET /api/v1/solvers/classical/executions/{id}/status` (lightweight polling)
  - `POST /api/v1/solvers/classical/executions/{id}/cancel` (cancellation)
  - `GET /api/v1/solvers/classical/executions` (recent audit history)

---

## 5. Benchmarking & Performance Evaluation Engine (`ClassicalBenchmarkEngine`, Stage 4.6)
The benchmarking engine executes multiple solvers simultaneously against a problem instance across multiple stochastic trials:
- **Statistical Metrics:**
  - Best Objective ($f_{\text{best}}$), Mean Objective ($\bar{f}$), Worst Objective ($f_{\text{worst}}$), Standard Deviation ($\sigma_f$).
  - Feasibility Rate: Percentage of trials satisfying 100% of canonical problem constraints.
  - Runtime Latency: Mean, Min, Max runtime in milliseconds.
  - Mean Evaluations: Total objective function evaluations per solver.
- **True Optimality Gap Metric:**
  When an exact solver is included (or exact global optimum $f^*$ is known), the true optimality gap is computed as:
  $$\text{optimality\_gap} = \frac{|f_{\text{heuristic}} - f^*|}{|f^*| + 1\times 10^{-9}} \times 100\%$$
- **Fair Comparison Standards:**
  - Identical problem instances across all competitors.
  - Deterministic pseudo-random seed sequences ($seed_k = base\_seed + k \times 17$).
  - Independent objective evaluator truth verification without trusting solver self-reporting.
  - Persistent benchmark storage in `db_manager` and MongoDB collection `benchmarks`.

---

## 6. Classical Lab Frontend (Stage 4.7)
The React/TypeScript frontend (`ClassicalLabPage.tsx`) offers three integrated modes:
1. **Single Solver Lab:** Interactive algorithm selection, hyperparameter tuning, live execution dispatch, ground truth evaluator verification, and domain visualizers (Partition $S$ vs $V \setminus S$, Assignment matching grid, TSP route chip loops).
2. **Comparative Benchmark Suite:** Multi-solver selection, trials configuration, and side-by-side comparison tables featuring rank badges (🥇, 🥈, 🥉), feasibility rates, mean runtimes, and optimality gap badges.
3. **Execution Audit History:** Tabular audit log of previous runs with one-click result inspection into the main viewer.

---

## 7. Hybrid Quantum-Classical Integration (Stage 5.9)
The Classical Optimization Engine directly powers the baseline comparison suite of the Phase 5 Quantum Engine (`HybridBenchmarkEngine`):
- `ExactSolver` establishes the verified global optimum $f^*$ to compute the quantum **Approximation Ratio** ($r = C_{\text{QAOA}} / C^*$ for Max-Cut, $r = C^* / C_{\text{QAOA}}$ for Assignment/TSP).
- `GeneticAlgorithmSolver` and `SimulatedAnnealingSolver` provide realistic classical heuristic competitors with equivalent function evaluation budgets and runtime baselines.
- The hybrid benchmark suite persists in `hybrid_benchmarks` and is accessible in both the Classical Lab and Quantum Lab.

---

## 8. ML-Recommended Solver Selection (Phase 7 Integration)

The Phase 7 AI and Machine Learning Intelligence Layer (`backend/app/ai/`) integrates directly with the Classical Optimization Engine to provide automated, data-driven algorithm selection:

### 8.1 Complexity-Aware Recommendations
- **Assignment Problems:** For all valid linear sum assignment instances, the recommendation engine recommends `exact` (Hungarian algorithm) with $\ge 90\%$ confidence, recognizing its polynomial runtime complexity $O(n^3)$ that guarantees global optimality without heuristic approximations.
- **Max-Cut Problems:**
  - $n \le 18$: Recommends `exact` solver (exhaustive enumeration with bitwise symmetry reduction to $2^{n-1}$).
  - $n > 20$: Exact solver is automatically disabled by safety filters. For dense graphs with high variance, `genetic_algorithm` or `simulated_annealing` is recommended depending on graph density and degree variance.
- **TSP Problems:**
  - $n \le 10$: `exact` (lexicographic permutation search $O(n!)$).
  - $n > 10$: Exact solver disabled. `simulated_annealing` with 2-opt neighborhood operator is recommended for rapid convergence.

### 8.2 Frontend Lab Integration
- Both `ClassicalLabPage.tsx` and `ProblemBuilderPage.tsx` include the unified `SolverRecommendationPanel`:
  - Instant recommendation badge with confidence percentage and top 3 influential features.
  - One-click "Apply Recommended Solver & Settings" button that pre-configures the lab controls.
  - Detailed audit modal disclosing feature values, safety filter determinations, and full alternative rankings.
- User feedback and solver selections are recorded via `POST /api/v1/ai/feedback` to train future recommender iterations.
