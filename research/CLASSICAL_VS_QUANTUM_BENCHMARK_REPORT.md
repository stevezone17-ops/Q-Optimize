# Stage 10.3 — Classical vs Quantum Algorithm Benchmarking Report

**Project:** Q-Optimize — AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Execution Script:** `research/scripts/run_classical_vs_quantum_benchmark.py`  
**Raw Data Artifact:** `research/results/classical_vs_quantum_benchmark.json`  
**Total Executed Trials:** 275 trials across 9 dataset families (23 canonical instances)  
**Simulation Disclosure:** *All Standard QAOA and Adaptive QAOA experiments were executed classically on Qiskit `AerSimulator` (host CPU). No physical quantum hardware speedup is claimed.*

---

## 1. Executive Summary

We executed controlled, paired multi-trial benchmarks comparing **Exact Solver**, **Simulated Annealing (SA)**, **Genetic Algorithm (GA)**, **Standard QAOA** ($p=1$, 512 shots, 40 evals), and **Adaptive QAOA** ($p=1 \to 2$, 512 shots, 50 evals) across Max-Cut, Linear Assignment, and TSP. Separately, the **AI-Assisted Solver Recommender** (`IntelligentSolverRecommender`) was evaluated on all 23 instances for selection quality, OOD safety handling, and inference latency.

### Key Empirical Findings
1. **Classical Baselines Dominate Small-to-Medium Instances:** Exact Solver, SA, and GA achieved **100% feasibility and 0.00% optimality gap** across all 9 families (including $n=16$ Assignment/TSP) in under **0.65 seconds** per trial.
2. **QAOA Simulator Performance Varies by Topology & Budget:**
   - On unweighted $N=6$ and 3-regular $N=8$ Max-Cut, plus 3-city TSP ($n=9$), both Standard and Adaptive QAOA reached **0.00% optimality gap** ($r = 1.000$).
   - On weighted Erdős–Rényi $N=8$ Max-Cut (`mc_er_n8_p05_w`), **Adaptive QAOA achieved 0.00% gap ($r = 1.000$)**, slightly outperforming Standard QAOA (`0.11%` gap, $r = 0.9989$).
   - On larger $N=10$ weighted Max-Cut and $3\times 3$ uniform Assignment under a tight 50-evaluation budget, Standard QAOA outperformed Adaptive QAOA (`2.59%` vs `7.50%` gap on $N=10$ Max-Cut; `10.75%` vs `38.25%` on `assign_3x3_uniform`), demonstrating that dynamic depth expansion without an expanded evaluation budget can leave $p=2$ parameters under-converged.
3. **AI Recommender:** Selected `exact` on 23/23 instances (100% optimal choice with 0.0% decision regret, mean latency **1.153 ms**), with OOD safety fallback cleanly catching 12 high-magnitude Assignment/TSP cost matrices.

---

## 2. Multi-Algorithm Benchmark Results by Dataset Family

All objectives are independently verified via Phase 2 domain evaluators (`EvaluatorFactory`).

### 2.1 Max-Cut Families ($N=6, 8, 10$ Qubits, Maximization)

| Family | Solver | Feasibility | Mean Obj | Std Obj | Mean Gap (%) | Mean Approx. Ratio ($r$) | Mean Runtime (s) |
|---|---|---|---|---|---|---|---|
| `mc_er_n6_p05` | `exact` | 1.00 | 7.0000 | 1.7321 | 0.0000% | 1.0000 | 0.0008 |
| `mc_er_n6_p05` | `simulated_annealing` | 1.00 | 7.0000 | 1.5000 | 0.0000% | 1.0000 | 0.1183 |
| `mc_er_n6_p05` | `genetic_algorithm` | 1.00 | 7.0000 | 1.5000 | 0.0000% | 1.0000 | 0.6477 |
| `mc_er_n6_p05` | `standard_qaoa` (Aer) | 1.00 | 7.0000 | 1.5000 | 0.0000% | 1.0000 | 2.2952 |
| `mc_er_n6_p05` | `adaptive_qaoa` (Aer) | 1.00 | 7.0000 | 1.5000 | 0.0000% | 1.0000 | 2.1262 |
| `mc_er_n8_p05_w` | `exact` | 1.00 | 65.6079 | 1.4476 | 0.0000% | 1.0000 | 0.0011 |
| `mc_er_n8_p05_w` | `simulated_annealing` | 1.00 | 65.6079 | 1.2536 | 0.0000% | 1.0000 | 0.0377 |
| `mc_er_n8_p05_w` | `genetic_algorithm` | 1.00 | 65.6079 | 1.2536 | 0.0000% | 1.0000 | 0.3279 |
| `mc_er_n8_p05_w` | `standard_qaoa` (Aer) | 1.00 | 65.5372 | 1.2872 | 0.1085% | 0.9989 | 0.7833 |
| `mc_er_n8_p05_w` | `adaptive_qaoa` (Aer) | 1.00 | 65.6079 | 1.2536 | **0.0000%** | **1.0000** | 0.9693 |
| `mc_reg_n8_d3` | `exact` | 1.00 | 10.0000 | 0.0000 | 0.0000% | 1.0000 | 0.0006 |
| `mc_reg_n8_d3` | `simulated_annealing` | 1.00 | 10.0000 | 0.0000 | 0.0000% | 1.0000 | 0.0171 |
| `mc_reg_n8_d3` | `genetic_algorithm` | 1.00 | 10.0000 | 0.0000 | 0.0000% | 1.0000 | 0.1627 |
| `mc_reg_n8_d3` | `standard_qaoa` (Aer) | 1.00 | 10.0000 | 0.0000 | 0.0000% | 1.0000 | 0.4082 |
| `mc_reg_n8_d3` | `adaptive_qaoa` (Aer) | 1.00 | 10.0000 | 0.0000 | 0.0000% | 1.0000 | 0.6252 |
| `mc_er_n10_p06_w` | `exact` | 1.00 | 105.1358 | 4.5274 | 0.0000% | 1.0000 | 0.0034 |
| `mc_er_n10_p06_w` | `simulated_annealing` | 1.00 | 105.1357 | 3.5069 | 0.0000% | 1.0000 | 0.0229 |
| `mc_er_n10_p06_w` | `genetic_algorithm` | 1.00 | 105.1357 | 3.5069 | 0.0000% | 1.0000 | 0.2244 |
| `mc_er_n10_p06_w` | `standard_qaoa` (Aer) | 1.00 | 102.4795 | 6.7697 | 2.5905% | 0.9741 | 0.5655 |
| `mc_er_n10_p06_w` | `adaptive_qaoa` (Aer) | 1.00 | 97.4878 | 11.9076 | 7.5028% | 0.9250 | 0.8596 |

### 2.2 Linear Assignment Families ($3 \times 3$ [$n=9$], $4 \times 4$ [$n=16$], Minimization)

| Family | Solver | Feasibility | Mean Cost | Std Cost | Mean Gap (%) | Mean Approx. Ratio ($r$) | Mean Runtime (s) |
|---|---|---|---|---|---|---|---|
| `assign_3x3_uniform` | `exact` | 1.00 | 93.1432 | 20.7431 | 0.0000% | 1.0000 | 0.0002 |
| `assign_3x3_uniform` | `simulated_annealing` | 1.00 | 93.1432 | 17.9641 | 0.0000% | 1.0000 | 0.0343 |
| `assign_3x3_uniform` | `genetic_algorithm` | 1.00 | 93.1432 | 17.9641 | 0.0000% | 1.0000 | 0.2316 |
| `assign_3x3_uniform` | `standard_qaoa` (Aer) | 1.00 | 104.1998 | 33.7679 | 10.7515% | 0.9304 | 0.5044 |
| `assign_3x3_uniform` | `adaptive_qaoa` (Aer) | 1.00 | 120.6199 | 25.9249 | 38.2541% | 0.8126 | 0.7711 |
| `assign_3x3_normal` | `exact` | 1.00 | 137.5846 | 6.7071 | 0.0000% | 1.0000 | 0.0002 |
| `assign_3x3_normal` | `simulated_annealing` | 1.00 | 137.5846 | 5.1953 | 0.0000% | 1.0000 | 0.0352 |
| `assign_3x3_normal` | `genetic_algorithm` | 1.00 | 137.5846 | 5.1953 | 0.0000% | 1.0000 | 0.2372 |
| `assign_3x3_normal` | `standard_qaoa` (Aer) | 1.00 | 150.1282 | 21.8666 | 8.8452% | 0.9284 | 0.5160 |
| `assign_3x3_normal` | `adaptive_qaoa` (Aer) | 1.00 | 150.2110 | 23.5627 | 8.8713% | 0.9300 | 0.7152 |
| `assign_4x4_uniform` | `exact` | 1.00 | 136.0735 | 26.8078 | 0.0000% | 1.0000 | 0.0002 |
| `assign_4x4_uniform` | `simulated_annealing` | 1.00 | 136.0735 | 20.7652 | 0.0000% | 1.0000 | 0.0466 |
| `assign_4x4_uniform` | `genetic_algorithm` | 1.00 | 136.0735 | 20.7652 | 0.0000% | 1.0000 | 0.2588 |

### 2.3 Travelling Salesperson Problem ($N=3$ [$n=9$], $N=4$ [$n=16$], Minimization)

| Family | Solver | Feasibility | Mean Tour | Std Tour | Mean Gap (%) | Mean Approx. Ratio ($r$) | Mean Runtime (s) |
|---|---|---|---|---|---|---|---|
| `tsp_3city_euclid` | `exact` | 1.00 | 147.8392 | 29.9487 | 0.0000% | 1.0000 | 0.0003 |
| `tsp_3city_euclid` | `simulated_annealing` | 1.00 | 147.8392 | 25.9363 | 0.0000% | 1.0000 | 0.0342 |
| `tsp_3city_euclid` | `genetic_algorithm` | 1.00 | 147.8392 | 25.9363 | 0.0000% | 1.0000 | 0.2412 |
| `tsp_3city_euclid` | `standard_qaoa` (Aer) | 1.00 | 147.8392 | 25.9363 | 0.0000% | 1.0000 | 0.5687 |
| `tsp_3city_euclid` | `adaptive_qaoa` (Aer) | 1.00 | 147.8392 | 25.9363 | 0.0000% | 1.0000 | 0.8933 |
| `tsp_4city_euclid` | `exact` | 1.00 | 219.3012 | 52.3977 | 0.0000% | 1.0000 | 0.0002 |
| `tsp_4city_euclid` | `simulated_annealing` | 1.00 | 219.3012 | 40.5871 | 0.0000% | 1.0000 | 0.0527 |
| `tsp_4city_euclid` | `genetic_algorithm` | 1.00 | 219.3012 | 40.5871 | 0.0000% | 1.0000 | 0.2660 |

---

## 3. AI-Assisted Solver Recommendation Evaluation (Separate Analysis)

`IntelligentSolverRecommender` was evaluated across all 23 canonical instances:
- **Mean Inference Latency:** `1.153 ms` per instance (18-dimensional feature extraction + OOD check + selection).
- **Selection Outcome:** Recommended `exact` for `23 / 23` instances, yielding **0.00% decision regret** against the empirical ground-truth best solver (since all 23 instances satisfy Exact Solver's tractability thresholds $n_{\text{maxcut}} \le 18$, $n_{\text{tsp}} \le 10$, and solve in `< 0.004 s`).
- **OOD Safeguard Behavior:** Triggered Out-of-Distribution alerts (`max_z > 3.5`) on **12 / 23** instances (high-magnitude Assignment/TSP cost matrices in `[1, 100]`), cleanly delegating to `RuleBasedSolverRecommender` (`fallback` source) while Max-Cut instances used `rule_based` directly (untrained default ML registry).
- **Comparison vs. Static Baseline:** Compared to a static `standard_qaoa` selection baseline, the recommender avoids suboptimal variational gaps (up to `38.25%` on `assign_3x3_uniform`) and reduces runtime by $>100\times$ on these small-to-medium instances.

---

## 4. Technical Defect Discovered & Fixed During Benchmarking

During real execution of `AdaptiveQAOAExecutionPipeline.execute_sync` on Assignment (`List[Tuple[str, str]]`) and TSP (`List[str]`), Pydantic validation failed because `AdaptiveQAOAResult.best_solution` was typed as `Dict[str, Any]`.
- **Fix Applied:** Updated `AdaptiveQAOAResult.best_solution` in `backend/app/solvers/quantum/adaptive/adaptive_models.py` to `Any` and added an `"adhoc"` default for `AdaptiveExecutionRecord.problem_id` in `backend/app/solvers/quantum/adaptive/pipeline.py`.
