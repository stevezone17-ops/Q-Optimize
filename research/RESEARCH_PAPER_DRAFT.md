# An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection

> **Document Status:** *Research Paper Draft (Unpublished Academic Manuscript — Prepared for Final-Year Engineering Evaluation).*  
> **Simulation Notice:** *All quantum variational results reported in this manuscript were obtained using classical CPU simulation via Qiskit `AerSimulator`. No physical quantum hardware execution or quantum advantage is claimed.*

---

## Abstract

Combinatorial optimization over discrete structures—including Maximum Cut (Max-Cut), Linear Assignment, and the Travelling Salesperson Problem (TSP)—presents persistent computational trade-offs between exact optimality guarantees, classical metaheuristic scalability, and emerging variational quantum heuristics such as the Quantum Approximate Optimization Algorithm (QAOA). We present **Q-Optimize**, an open, modular hybrid quantum-classical optimization framework that enforces exhaustive $2^n$ QUBO/Ising equivalence checks, independent domain-level solution verification, multi-variant Adaptive QAOA ablation, and feature-driven solver recommendation with out-of-distribution (OOD) safeguards. Across 11 exhaustive verification instances (2,168 binary states), our formulation compiler achieves zero ($0.00$) energy discrepancy. Across 275 controlled benchmark trials ($n \in [6, 16]$ variables), Holm–Bonferroni-adjusted Wilcoxon signed-rank tests ($N=57$ paired trials) demonstrate that classical Simulated Annealing achieves $r = 1.0000$ significantly outperforming shallow-depth Standard QAOA simulation ($r = 0.9786, p_{\text{Holm}} = 0.0132$) and Adaptive QAOA ($r = 0.9551, p_{\text{Holm}} = 0.0229$), while pooled Standard vs. Adaptive QAOA approximation ratios show no statistically significant difference ($p_{\text{Holm}} = 0.3256$) under tight evaluation budgets (40–50 evaluations). Ablation experiments ($90$ trials) further show that Fourier parameterization reduces evaluation cost on Max-Cut and TSP, while warm-start transfer stabilizes constrained Adaptive QAOA relative to cold-started dynamic depth.

**Keywords:** QAOA, Adaptive QAOA, QUBO, Ising Model, Combinatorial Optimization, Algorithm Selection, Reproducible Benchmarking.

---

## 1. Introduction

Selecting and validating optimization algorithms across heterogeneous combinatorial problems requires rigorous mathematical guarantees and fair empirical comparisons. In practice, quantum variational implementations frequently suffer from silent QUBO penalty miscalibration, unverified bitstring decoding, or biased comparisons against uncalibrated classical baselines. **Q-Optimize** addresses these gaps by decoupling canonical problem specification from mathematical compilation, solver execution, and independent post-hoc verification.

## 2. Related Work

- **Variational Quantum Optimization:** Farhi et al. [1] introduced QAOA, alternating cost and mixer Hamiltonians over $p$ layers. Zhou et al. [5] analyzed parameter concentration and Fourier/linear-ramp initialization schedules to mitigate local traps.
- **Ising Formulations:** Lucas [2] formalized QUBO and Ising spin mappings for Max-Cut, Assignment, and TSP via quadratic penalty terms.
- **Classical Metaheuristics:** Simulated Annealing (Kirkpatrick et al. [3]) and Genetic Algorithms (Holland [4]) serve as standard stochastic classical baselines.
- **Algorithm Selection:** Rice [6] formulated the Algorithm Selection Problem linking instance features to solver performance.

**Distinction of Contributions:** Q-Optimize does *not* claim to invent QAOA, Simulated Annealing, Genetic Algorithms, or Ising mappings. Its original engineering and empirical contributions lie in: (1) an integrated $2^n$ QUBO/Ising/Evaluator parity verifier, (2) a modular 6-variant Adaptive QAOA ablation engine, (3) an OOD-guarded 18-feature solver recommender, and (4) a Holm–Bonferroni-validated reproducible benchmarking suite.

## 3. Research Problem

We investigate four empirical research questions:
- **RQ1:** How do QAOA simulation quality and runtime scale across Max-Cut, Assignment, and TSP?
- **RQ2:** Under a fixed evaluation budget (40–50 evaluations), do adaptive mechanisms improve QAOA approximation ratios over fixed-depth Standard QAOA?
- **RQ3:** Does an OOD-aware solver recommender achieve low decision regret compared to static solver choices?
- **RQ4:** Which statistical differences survive Holm–Bonferroni multiple-comparison correction?

## 4. Proposed Architecture

Q-Optimize is structured into five decoupled layers: (1) Canonical Problem & Independent Evaluator Layer, (2) Upper-Triangular QUBO/Ising Compiler & $2^n$ Verifier, (3) Classical (`Exact`, `SA`, `GA`) & Quantum (`Standard QAOA`, `Adaptive QAOA` on `AerSimulator`) Execution Pipelines, (4) `IntelligentSolverRecommender` with 18 structural/QUBO features and z-score OOD detection, and (5) Reproducible Experiment & Statistical Engine (`scipy`).

## 5. Mathematical Formulation

Binary variables $x_i \in \{0, 1\}$ map analytically to Ising spins $Z_i \in \{-1, +1\}$ via $x_i = (1 - Z_i)/2$, preserving exact energy equivalence:
$$E_{\text{QUBO}}(x) = x^T Q x + c = \sum_i h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + C = H_{\text{Ising}}(Z)$$
All QUBO matrices strictly enforce upper-triangular storage ($i < j$).

## 6. Adaptive QAOA Methodology

Our `AdaptiveBenchmarkEngine` evaluates six configurations: `standard_baseline`, `full_adaptive` (dynamic depth $p=1 \to 2$, warm-start interpolation, `COBYLA` $\to$ `Nelder-Mead` switching), `ablation_no_warm_start`, `ablation_no_dynamic_depth`, `ablation_no_optimizer_switching`, and `ablation_fourier`.

## 7. AI-Assisted Solver Selection

`IntelligentSolverRecommender` extracts 18 structural features (`num_variables`, `graph_density`, QUBO coefficient statistics, $\log_2$ search space), flags OOD instances ($\max z > 3.5$), and selects solvers with `1.153 ms` mean inference latency.

## 8. Experimental Setup

Nine reproducible dataset families (`23` canonical instances, SHA-256 fingerprinted) cover Max-Cut ($N=6,8,10$), Assignment ($3\times 3, 4\times 4$), and TSP ($N=3,4$). Quantum simulations run on Qiskit `AerSimulator` (`shots=512`, `trials=3`, `seeds=[42, 59, 76]`).

## 9. Benchmarking Results

- **Exhaustive Validation:** 11/11 instances (2,168 states) achieved `0.00` max $|E_{\text{QUBO}} - H_{\text{Ising}}|$ discrepancy.
- **Classical vs. Quantum (275 trials):** Exact, SA, and GA achieved `100%` feasibility and `0.00%` optimality gap across all 9 families. Standard and Adaptive QAOA achieved `0.00%` gap on `mc_er_n6_p05`, `mc_reg_n8_d3`, and `tsp_3city_euclid`; on `mc_er_n8_p05_w`, Adaptive QAOA reached `0.00%` gap ($r=1.0000$) vs. Standard QAOA `0.1085%`. On `mc_er_n10_p06_w` and `assign_3x3_uniform`, Standard QAOA outperformed Adaptive QAOA (`2.59%` vs `7.50%` and `10.75%` vs `38.25%` gap).
- **AI Recommender:** Recommended `exact` on 23/23 instances (`0.00%` regret), with OOD fallback triggered on 12/23 high-magnitude Assignment/TSP matrices.

## 10. Ablation Study

Across 90 ablation trials (`5` instances $\times$ `6` variants $\times$ `3` trials):
- Removing warm starts degraded `assign_3x3_uniform_i1` ratio from `0.9145` to `0.8763`.
- `ablation_fourier` achieved the fastest runtimes (`284–299 ms`) on Max-Cut and TSP, but trailed on `assign_3x3_uniform_i1` (`r = 0.7810`).
- One `full_adaptive` trial on `mc_er_n8_p05_w_i1` failed with an angle-vector mismatch during depth growth (`Expected 2 gamma values, got 1`), reported honestly without removal.

## 11. Statistical Evaluation

Holm–Bonferroni-adjusted tests ($\alpha = 0.05$):
- SA vs. Standard QAOA (Ratio, $N=57$): $W = 0.0, p_{\text{Holm}} = 0.0132, d = 0.43$ (Significant).
- SA vs. Adaptive QAOA (Ratio, $N=57$): $W = 0.0, p_{\text{Holm}} = 0.0229, d = 0.52$ (Significant).
- Standard vs. Adaptive QAOA (Ratio, $N=57$): $W = 49.0, p_{\text{Holm}} = 0.3256$ (Not significant).
- Standard vs. Adaptive QAOA (Runtime, $N=57$): $W = 109.0, p_{\text{Holm}} < 10^{-6}$ (Significant overhead).
- Standard QAOA Max-Cut vs. Assignment (Mann–Whitney): $U = 318.0$, raw $p = 0.0344$, $p_{\text{Holm}} = 0.0689$ (Not significant after Holm correction).

## 12. Discussion & Limitations

Results underscore that adaptive variational complexity does not automatically yield superior solutions under tight evaluation budgets, and rigorous multiple-comparison correction prevents false discoveries. Limitations include classical CPU simulation (`AerSimulator`), $n \le 10$ qubit ceilings for multi-trial QAOA, and a single dynamic-depth angle-resize defect observed during ablation.

## 13. Conclusion

Q-Optimize demonstrates how strict mathematical verification, independent evaluation, and non-parametric statistics enable transparent hybrid optimization research.

## References

1. E. Farhi, J. Goldstone, and S. Gutmann, "A Quantum Approximate Optimization Algorithm," *arXiv:1411.4028*, 2014.
2. A. Lucas, "Ising formulations of many NP problems," *Frontiers in Physics*, vol. 2, art. 5, 2014.
3. S. Kirkpatrick et al., "Optimization by simulated annealing," *Science*, vol. 220, pp. 671–680, 1983.
4. J. H. Holland, *Adaptation in Natural and Artificial Systems*, MIT Press, 1992.
5. L. Zhou et al., "Quantum Approximate Optimization Algorithm: Performance, Mechanism, and Implementation on Near-Term Devices," *PRX*, vol. 10, 021067, 2020.
6. J. R. Rice, "The Algorithm Selection Problem," *Advances in Computers*, vol. 15, pp. 65–118, 1976.
7. F. Wilcoxon, "Individual comparisons by ranking methods," *Biometrics Bulletin*, vol. 1, pp. 80–83, 1945.
8. H. B. Mann and D. R. Whitney, "On a test of whether one of two random variables is stochastically larger than the other," *Ann. Math. Stat.*, vol. 18, pp. 50–60, 1947.
9. S. Holm, "A simple sequentially rejective multiple test procedure," *Scand. J. Stat.*, vol. 6, pp. 65–70, 1979.
