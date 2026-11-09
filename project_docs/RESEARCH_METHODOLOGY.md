# Research Methodology

## 1. Proposed Research Scope
Investigate adaptive QAOA parameter strategies, formulation robustness, and ML-assisted solver recommendation for canonical combinatorial optimization problems (Max-Cut, Linear Assignment, and Travelling Salesperson Problem).

---

## 2. Research Questions
- **RQ1:** How does QAOA solution quality vary with problem size, graph density, and constraint density?
- **RQ2:** Do defined adaptive parameter strategies improve solution quality or convergence under a fixed evaluation budget compared to standard heuristics?
- **RQ3:** Can structural problem features support useful solver recommendations compared with a rule-based baseline?
- **RQ4:** How do selected simulated noise settings affect QAOA quality and variability?
- **RQ5:** Under which tested conditions do classical heuristic methods (Simulated Annealing, Genetic Algorithms) outperform or match QAOA simulation?

---

## 3. Hypotheses
Treat as hypotheses, not promised outcomes:
- **H1:** Some adaptive strategies may improve QAOA quality or convergence on selected instance families.
- **H2:** A recommender may reduce recommendation regret on held-out instances compared to random or static baselines.
- **H3:** Increasing depolarizing/thermal noise under the chosen simulator model may degrade solution quality or increase bitstring variance.

Negative or inconclusive results are scientifically valid and will be reported with equal rigor.

---

## 4. Problem Instance Families
- **Max-Cut:** Erdős-Rényi random graphs, cycle graphs, complete graphs, and regular graphs with varied density and edge weights.
- **Linear Assignment:** Square assignment instances with uniform, clustered, and metric cost matrices.
- **TSP:** Small geometric and asymmetric Euclidean instances with 3 to 10 cities.
- All instances record generator seeds and reproducible JSON representations.

---

## 5. Baselines & Experimental Controls
- **Solvers:** Exact brute-force solver (small $N$), Genetic Algorithm, Simulated Annealing, greedy heuristics, standard QAOA ($p=1, 2, 3$), and adaptive QAOA.
- **Controls:** Identical problem instance across compared solvers; fixed random seeds; equivalent evaluation budgets (shots $\times$ iterations); separation of formulation generation time from solver execution time; machine/library version provenance.

---

## 6. Evaluation Metrics & Independent Truth
1. **Objective Value:** Evaluated strictly by an independent domain evaluator directly against the original problem definition, not the internal solver score.
2. **Feasibility Rate:** Fraction of measured bitstrings that satisfy 100% of problem constraints.
3. **Approximation Ratio:** $\alpha = \frac{\text{Computed Value}}{\text{Optimal Value}}$ when exact optimum is known.
4. **Energy Discrepancy:** $|E_{\text{QUBO}}(x) - H_{\text{Ising}}(Z)|$ to confirm formulation precision.

---

## 7. Formulation Verification & Penalty Sufficiency Methodology (Phase 3)

### 7.1 Exhaustive Truth-Table State Space Verification
To guarantee that QUBO and Ising models accurately reflect the intended combinatorial problem:
- For small benchmark instances ($n \le 12$ binary variables, corresponding to $2^{12} = 4,096$ states), the platform performs exhaustive state-space enumeration.
- For each state $x \in \{0, 1\}^n$:
  1. Evaluate classical QUBO energy $E_{\text{QUBO}}(x) = x^T Q x + c$.
  2. Map bitstring to spin configuration $Z_i = 1 - 2x_i$ and compute $H_{\text{Ising}}(Z) = \sum h_i Z_i + \sum J_{ij} Z_i Z_j + C$.
  3. Verify $|E_{\text{QUBO}}(x) - H_{\text{Ising}}(Z)| < 10^{-6}$.
  4. For all feasible states, compare $E_{\text{QUBO}}(x)$ to the Phase 2 independent objective evaluator output to ensure objective direction and offsets match.

### 7.2 Penalty Multiplier Sufficiency Testing
For constrained problems (Assignment and TSP), penalty multipliers $A$ and $B$ must exceed the maximum possible objective decrease achievable by violating a constraint. 
The platform tests:
\[
\min_{x \in \mathcal{S}_{\text{infeasible}}} E_{\text{QUBO}}(x) > \min_{x \in \mathcal{S}_{\text{feasible}}} E_{\text{QUBO}}(x)
\]
If an infeasible state achieves an energy lower than the optimal feasible state, the penalty coefficients are marked as insufficient, and the researcher is provided with mathematically grounded lower bounds.

---

## 8. Reproducibility & Research Integrity
- Every experiment record preserves the exact QUBO upper-triangular matrix, variable ordering array, penalty parameters, random seeds, and raw bitstring count distribution.
- **Strict Prohibition:** Simulator-based experiments do not establish physical quantum advantage and will never be presented as physical quantum speedup.

---

## 9. QAOA Experimental Protocols & Benchmarking Standards (Phase 5)

### 9.1 Variational Angle Search & Convergence Protocols
- Parameter search is initialized using standardized strategies (`linear_ramp`, `random`, `zeros`).
- Multi-trial stochastic restarts ($k \in [1, 10]$) are executed with deterministic seed schedules ($seed_k = base\_seed + k \times 17$).
- Classical optimizer iterations track expectation value trajectories $\langle H_C \rangle_k$ and parameter distances $\Delta \vec{\gamma}, \Delta \vec{\beta}$.

### 9.2 Fair Multi-Paradigm Comparison Protocol
When comparing QAOA against classical heuristics (GA, SA) and exact methods:
1. **Identical Canonical Instances:** All solvers consume the exact same problem graph or cost matrix.
2. **Computational Work Accounting:** Total function evaluations are recorded alongside wall-clock time:
   - Classical: Objective function evaluations.
   - Quantum Simulation: Classical optimizer function evaluations $\times$ shots per evaluation.
3. **Approximation Ratio Standardization:**
   - Maximization (Max-Cut): $r = \frac{C_{\text{best}}}{C_{\text{exact}}}$.
   - Minimization (Assignment, TSP): $r = \frac{C_{\text{exact}}}{C_{\text{best}}}$.
   - Optimality Gap: $\text{gap} = \frac{|C_{\text{best}} - C_{\text{exact}}|}{|C_{\text{exact}}| + 10^{-9}} \times 100\%$.
4. **Hardware Transparency:**
   All QAOA experiments are conducted via Qiskit Aer numerical simulation on host CPU. Wall-clock runtimes include simulation matrix multiplication overhead and are reported as classical simulation latencies, never as physical quantum coherence time.


---

## 10. Adaptive QAOA Research Methodology & Ablation Protocols (Phase 6)

### 10.1 Core Research Questions & Hypotheses
- **RQ6.1 (Dynamic Layer Growth):** Does progressive circuit depth expansion ($p \to p+1$) triggered by energy stagnation achieve higher approximation ratios ($r$) or lower evaluation counts than starting from a fixed high depth ($p=3$)?
- **RQ6.2 (Warm-Start Parameter Transfer):** Does smooth angle interpolation across depths prevent barren plateau stagnation compared to cold/random re-initialization at higher depths?
- **RQ6.3 (Adaptive Optimizer Scheduling):** Does dynamically switching from a derivative-free exploration optimizer (`COBYLA`) to a gradient or simplex local refinement optimizer (`Nelder-Mead`, `SLSQP`) on plateaus improve final objective accuracy?
- **RQ6.4 (Fourier Parameterization):** Does parameterizing $2p$ angles through $q$ frequency components ($\vec{u}, \vec{v}$) accelerate convergence on structured graphs?

### 10.2 Empirical Ablation Study Protocol
To isolate the exact causal contribution of each architectural innovation, experiments execute systematic ablation variants on identical problem topologies:
1. `standard_baseline`: Fixed depth $p$, static optimizer, linear ramp initialization.
2. `full_adaptive`: Dynamic depth growth + warm-start angle transfer + adaptive optimizer fallback.
3. `ablation_no_warm_start`: Dynamic depth growth with random layer initialization (isolates value of angle transfer).
4. `ablation_no_dynamic_depth`: Adaptive optimizer schedule with fixed depth (isolates value of layer growth).
5. `ablation_no_optimizer_switching`: Dynamic depth and warm-start with static optimizer (isolates value of optimizer switching).
6. `ablation_fourier`: Direct evaluation of discrete cosine/sine parameterization against raw angle parameters.

### 10.3 Statistical Significance & Evaluation Budgeting
- Each variant is executed across multiple randomized trials ($k \ge 3$) with seed offsets ($seed_k = base\_seed + 7k$).
- Metrics reported: Sample mean $\mu$, sample standard deviation $\sigma$, min, max, approximation ratio $r$, optimality gap $\%$, and evaluation efficiency ratio.
- Evaluation budget is strictly held invariant across compared variants to ensure fair benchmarking.

### 10.4 Scientific Hardware Transparency Notice
All Adaptive QAOA algorithms are simulated using Qiskit Aer on classical CPU infrastructure. In accordance with platform integrity policies, no simulated experiment is ever reported as demonstrating quantum supremacy or physical quantum hardware advantage.

---

## 11. Machine Learning Methodology & Algorithm Selection (Phase 7)

### 11.1 Problem Formulation as Algorithm Selection
The algorithm selection problem is formalized as finding a mapping $\mathcal{F}: \mathcal{X} \to \mathcal{S}$ where $\mathcal{X} \subset \mathbb{R}^{18}$ represents the continuous-discrete optimization feature space and $\mathcal{S} = \{s_1, \dots, s_K\}$ denotes the catalog of supported classical and quantum solvers:
$$\mathcal{S} = \{\text{exact}, \text{genetic\_algorithm}, \text{simulated\_annealing}, \text{standard\_qaoa}, \text{adaptive\_qaoa}\}$$

### 11.2 Supervised Label Assignment via Pareto Optimality
Ground-truth solver labels $y^* \in \mathcal{S}$ are derived from empirical experiment records using a multi-criteria Pareto dominance policy:
1. **Feasibility Gate:** Infeasible executions are strictly penalized ($f(s) = \infty$).
2. **Objective Quality:** For instance $i$, the primary criterion is achieving the best verified objective value $f^*(i) = \min_{s} f(s, i)$ (or $\max$ for Max-Cut).
3. **Runtime Efficiency Tie-Breaker:** For solvers achieving identical objective values within numerical tolerance $|f(s_1) - f(s_2)| \le 10^{-4}$, the solver with lower execution latency is selected:
   $$y^*(i) = \arg\min_{s \in \mathcal{S}_{\text{opt}}(i)} t_{\text{exec}}(s, i)$$

### 11.3 Group-Aware Leakage-Free Validation Protocol
Random k-fold partitioning across execution logs causes severe data leakage when multiple runs of the same problem instance appear in both training and test splits. Q-Optimize strictly enforces **Group-Aware Splitting**:
- Group identifier: Problem instance ID or graph generation seed.
- Invariant: $\text{Groups}(\mathcal{D}_{\text{train}}) \cap \text{Groups}(\mathcal{D}_{\text{test}}) = \emptyset$.
- This ensures models generalize to novel unseen problem topologies rather than memorizing graph instances.

### 11.4 Recommendation Performance Metrics
Beyond traditional classification accuracy and macro F1, recommender evaluation incorporates domain-specific regret metrics:
- **Decision Regret:**
  $$\text{Regret}(i) = \frac{|f(s_{\text{rec}}, i) - f(s^*, i)|}{|f(s^*, i)| + 10^{-9}}$$
- **Brier Probability Calibration Score:**
  $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (p_{ik} - y_{ik})^2$$
  where $p_{ik}$ is the model's predicted probability for solver $k$ and $y_{ik} \in \{0, 1\}$ is the one-hot ground-truth label.
- **Feasibility Assurance Rate:** Percentage of recommended solvers that yield 100% constraint-satisfying feasible solutions.

### 11.5 Out-of-Distribution (OOD) Detection & Continuous Monitoring
- **Z-Score Distance Metric:** For feature vector $\vec{x}$, distance from training distribution mean $\vec{\mu}$ and variance $\vec{\sigma}$ is evaluated:
  $$z_{\text{max}}(\vec{x}) = \max_{j \in [1, 18]} \frac{|x_j - \mu_j|}{\sigma_j}$$
  Instances with $z_{\text{max}} > 3.5$ trigger automated fallback to deterministic rule-based algorithms.
- **Two-Sample Kolmogorov-Smirnov (KS) Drift Test:**
  The continuous learning monitor tests null hypothesis $H_0: F_{\text{recent}}(x_j) = F_{\text{reference}}(x_j)$. Features exhibiting $p < 0.05$ trigger drift alerts and retrain recommendations.

### 11.6 Scientific Transparency & Model Integrity
1. **Zero Hallucination Tolerance:** Natural language extraction never fabricates costs or constraints. Incomplete inputs produce explicit `missing_information` warnings.
2. **Deterministic Mathematical Verification:** All AI-proposed models undergo canonical Phase 2 validation before entering the problem registry.
3. **Hardware Transparency:** Recommender explanations explicitly differentiate between CPU-simulated quantum algorithms and classical heuristics, never implying physical quantum superiority.
