# Q-OPTIMIZE: AN AI-ASSISTED HYBRID QUANTUM-CLASSICAL OPTIMIZATION FRAMEWORK WITH ADAPTIVE QAOA AND INTELLIGENT SOLVER SELECTION

**A Final-Year Engineering Project Report**  
Submitted in partial fulfillment of the requirements for the degree of  
**Bachelor of Technology in Computer Science and Engineering**

**Repository:** `https://github.com/stevezone17-ops/Q-Optimize`  
**Date:** November 2026

---

## Certificate *(Placeholder)*

> This is to certify that the project report entitled **"Q-Optimize: An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection"** is a bonafide record of the final-year engineering project work carried out during the academic year 2026.
>
> *Project Guide:* ___________________________  
> *Head of Department:* ___________________________  
> *External Examiner:* ___________________________

---

## Declaration

I hereby declare that the work presented in this project report is an authentic record of software engineering, mathematical validation, and empirical simulation research conducted on the Q-Optimize platform. All experimental data, statistical tests, and performance benchmarks reported herein were generated directly from the implemented codebase without fabrication. All quantum circuit executions were performed on the classical Qiskit `AerSimulator`, and no physical quantum hardware speedup is claimed.

---

## Acknowledgement

We express our sincere gratitude to our project guide, faculty reviewers, and the open-source scientific computing communities behind Python, FastAPI, React, TypeScript, SciPy, Scikit-Learn, and Qiskit for providing the foundational tooling that enabled this work.

---

## Abstract

Combinatorial optimization problems—such as Maximum Cut (Max-Cut), Linear Assignment, and the Travelling Salesperson Problem (TSP)—are NP-hard in general and arise across logistics, scheduling, network design, and circuit layout. While classical exact solvers guarantee global optimality only for small problem dimensions and classical metaheuristics (Simulated Annealing, Genetic Algorithms) scale polynomially per iteration without optimality proofs, variational quantum algorithms such as the Quantum Approximate Optimization Algorithm (QAOA) offer a complementary paradigm when mapped onto Quadratic Unconstrained Binary Optimization (QUBO) and Ising Hamiltonians.

This project presents **Q-Optimize**, a full-stack, production-hardened, AI-assisted hybrid quantum-classical optimization platform built with FastAPI, React/TypeScript, MongoDB, Scikit-Learn, and Qiskit Aer. Across ten development phases, Q-Optimize integrates: (1) canonical problem modeling with independent domain evaluators, (2) upper-triangular QUBO and analytical Ising formulation verified across exhaustive $2^n$ state spaces, (3) Exact, Simulated Annealing, and Genetic Algorithm classical baselines, (4) Standard QAOA and Adaptive QAOA engines featuring warm-start transfer, Fourier parameterization, dynamic depth expansion, and adaptive optimizer switching, (5) an 18-dimensional AI/ML solver recommender with out-of-distribution (OOD) safeguards, and (6) a reproducible experimentation, statistical analysis, and containerized deployment stack.

Empirical validation across **2,168 exhaustive state-space checks** ($0.00$ energy discrepancy), **275 controlled benchmark trials**, **90 adaptive ablation trials**, and **443 automated software tests** (`382` backend Pytest + `61` frontend Vitest) confirms complete mathematical fidelity. Statistical testing with Holm–Bonferroni correction demonstrates that classical Simulated Annealing remains significantly stronger in approximation ratio ($r = 1.0000$) than shallow-depth QAOA simulation ($r = 0.9786$, $p_{\text{Holm}} = 0.0132$) at small scales ($n \le 10$ qubits), while Adaptive QAOA matches or improves select Max-Cut instances ($r = 1.0000$ on `mc_er_n8_p05_w`) and Fourier parameterization reduces variational evaluation cost.

---

## Table of Contents

1. Introduction  
2. Problem Statement  
3. Motivation  
4. Objectives  
5. Literature Review  
6. Research Gap  
7. Proposed System  
8. System Architecture  
9. Mathematical Foundations  
10. QUBO and Ising Formulation  
11. Classical Optimization Algorithms  
12. Quantum Approximate Optimization Algorithm (QAOA)  
13. Adaptive QAOA  
14. AI/ML Solver Recommendation  
15. Experiment Management & Reproducibility  
16. Research Methodology  
17. Implementation Details  
18. Experimental Results  
19. Comparative Analysis  
20. Statistical Analysis  
21. Ablation Study  
22. Discussion  
23. Limitations  
24. Conclusion  
25. Future Scope  
26. References  
27. Appendices

---

## List of Figures

- **Figure 1:** Classical vs. Quantum (`AerSimulator`) Objective Quality Comparison (`research/figures/fig01_objective_comparison.png`)
- **Figure 2:** Solver Execution Time Comparison (`research/figures/fig02_execution_time_comparison.png`)
- **Figure 3:** Mean Optimality Gap (%) Relative to Exact Optimum (`research/figures/fig03_optimality_gap_comparison.png`)
- **Figure 4:** Pooled Approximation Ratio with 95% Confidence Intervals (`research/figures/fig04_approximation_ratio_comparison.png`)
- **Figure 5:** Standard QAOA Convergence Trajectory (`research/figures/fig05_qaoa_convergence_curve.png`)
- **Figure 6:** Adaptive QAOA Convergence Trajectory (`research/figures/fig06_adaptive_qaoa_convergence_curve.png`)
- **Figure 7:** Adaptive Depth Progression and Evaluation Cost (`research/figures/fig07_adaptive_depth_progression.png`)
- **Figure 8:** Parameter Transfer Analysis (`research/figures/fig08_parameter_transfer_analysis.png`)
- **Figure 9:** 6-Variant Adaptive QAOA Ablation Comparison (`research/figures/fig09_ablation_study_comparison.png`)
- **Figure 10:** Runtime Scalability Across Problem Dimensions (`research/figures/fig10_scalability_analysis.png`)
- **Figure 11:** Statistical Distribution Boxplots (`research/figures/fig11_statistical_distribution_plots.png`)
- **Figure 12:** Problem-Specific Optimal Solution Visualizations (`research/figures/fig12_problem_solution_visualization.png`)

---

## List of Tables

- **Table 1:** Exhaustive $2^n$ Formulation Verification Summary (Stage 10.1)
- **Table 2:** Reproducible Research Dataset Catalog (Stage 10.2)
- **Table 3:** Multi-Algorithm Benchmark Results Across Max-Cut, Assignment, and TSP (Stage 10.3)
- **Table 4:** Adaptive QAOA 6-Variant Ablation Results (Stage 10.4)
- **Table 5:** Holm–Bonferroni Adjusted Non-Parametric Hypothesis Tests (Stage 10.5)
- **Table 6:** Phase 9–10 Software Engineering & Security Test Baseline

---

## 1. Introduction

Combinatorial optimization seeks an optimal configuration $x^*$ from a finite discrete search space $\mathcal{S}$ that minimizes or maximizes an objective function $C(x)$ subject to structural constraints. As problem size $N$ grows, $|\mathcal{S}|$ expands exponentially ($2^N$ or $N!$), motivating hybrid architectures that unify exact solvers, classical metaheuristics, variational quantum simulation, and automated algorithm selection. **Q-Optimize** provides an end-to-end research and engineering environment for formulating, solving, independently verifying, and statistically benchmarking such hybrid workflows.

## 2. Problem Statement

Existing optimization and quantum-simulation tools are fragmented: mathematical modeling libraries rarely enforce independent solution verification against original domain constraints, variational quantum scripts often lack fair computational-budget accounting against classical heuristics, and end users lack interpretable guidance on which solver paradigm suits a given problem instance.

## 3. Motivation

A rigorous academic platform must bridge mathematical formulation correctness, multi-paradigm solver execution, statistical validation, and production-grade web engineering while upholding strict scientific honesty—explicitly distinguishing classical CPU quantum simulation from physical quantum hardware execution.

## 4. Objectives

1. Model **Max-Cut**, **Linear Assignment**, and **TSP** canonically with independent constraint evaluators.
2. Generate upper-triangular **QUBO** and analytical **Ising** Hamiltonians verified exhaustively for $n \le 12$.
3. Implement **Exact**, **Simulated Annealing**, **Genetic Algorithm**, **Standard QAOA**, and **Adaptive QAOA** solvers.
4. Build an **18-feature AI/ML solver recommender** with OOD fallback and decision-regret evaluation.
5. Harden the full-stack platform with RBAC, rate limiting, MongoDB pooling, bounded job queues, Docker, and CI/CD.
6. Validate all claims empirically via reproducible datasets, ablation studies, and Holm–Bonferroni statistical tests.

## 5. Literature Review

- **QAOA:** Farhi, Goldstone, and Gutmann [1] introduced QAOA as a variational quantum-classical algorithm alternating cost $U(H_C, \gamma)$ and mixer $U(H_M, \beta)$ unitaries over $p$ layers.
- **QUBO & Ising Mappings:** Lucas [2] established canonical Ising formulations for NP-complete and NP-hard problems including Max-Cut, Assignment, and TSP via quadratic penalty terms.
- **Classical Metaheuristics:** Kirkpatrick et al. [3] formalized Simulated Annealing via Metropolis acceptance schedules; Holland [4] established Genetic Algorithms using selection, crossover, and mutation.
- **Parameter Concentration & Schedules:** Zhou et al. [5] analyzed QAOA parameter landscapes, motivating linear-ramp, Fourier, and warm-start interpolation strategies.
- **Algorithm Selection:** Rice [6] defined the Algorithm Selection Problem mapping structural instance features to optimal solver selection.
- **Non-Parametric Statistics:** Wilcoxon [7], Mann and Whitney [8], and Holm [9] provide distribution-free hypothesis testing and step-down family-wise error control.

## 6. Research Gap

Few unified platforms combine exhaustive $2^n$ QUBO/Ising equivalence checking, independent post-hoc feasibility verification, multi-variant Adaptive QAOA ablation, OOD-aware solver recommendation, and Holm–Bonferroni statistical evaluation inside one reproducible, production-hardened application.

## 7. Proposed System

Q-Optimize implements a decoupled, layered architecture separating canonical problem definitions, mathematical QUBO/Ising compilers, independent evaluators, classical/quantum solver pipelines, AI feature extractors, experiment orchestrators, and a dark-first React scientific UI.

## 8. System Architecture

The system comprises: (a) **Frontend SPA** (React 18, TypeScript, Vite, Tailwind CSS, ErrorBoundary, responsive drawer), (b) **FastAPI Security Layer** (JWT/bcrypt RBAC, token-bucket rate limiter, 10MB payload limit, security headers), (c) **Optimization & AI Core** (FormulationEngine, EvaluatorFactory, ClassicalSolverFactory, QAOA/Adaptive QAOA on `AerSimulator`, IntelligentSolverRecommender), (d) **Async JobQueueManager** (bounded ThreadPoolExecutor, cancellation tokens, dead-letter queue), and (e) **MongoDB 7.0 Persistence** with connection pooling and automatic in-memory fallback.

## 9. Mathematical Foundations

For binary vector $x \in \{0, 1\}^n$ and spin vector $Z \in \{-1, +1\}^n$ under $x_i = \frac{1 - Z_i}{2}$:
$$E_{\text{QUBO}}(x) = \sum_{i} Q_{ii} x_i + \sum_{i < j} Q_{ij} x_i x_j + c$$
$$H_{\text{Ising}}(Z) = \sum_{i} h_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + C$$

## 10. QUBO and Ising Formulation

- **Max-Cut:** $\max \sum_{(u,v)\in E} w_{uv}(x_u + x_v - 2x_u x_v)$, minimized via $E_{\text{QUBO}}(x) = -C_{\text{cut}}(x)$.
- **Assignment:** $\min \sum_{i,j} c_{ij} x_{ij} + A \sum_i (\sum_j x_{ij} - 1)^2 + B \sum_j (\sum_i x_{ij} - 1)^2$.
- **TSP:** $\min \sum_{u,v,p} d_{uv} x_{u,p} x_{v,p+1} + A\sum_u (\sum_p x_{u,p} - 1)^2 + B\sum_p (\sum_u x_{u,p} - 1)^2$.

## 11. Classical Optimization Algorithms

- **Exact Solver:** Branch-and-bound / exhaustive enumeration (tractability bounds: $n \le 18$ Max-Cut, $n \le 10$ TSP).
- **Simulated Annealing:** Geometric cooling ($T_0 = 100.0, \alpha = 0.95$, 250 iterations).
- **Genetic Algorithm:** Population size 30, 80 generations, mutation rate $0.1$, tournament selection.

## 12. Quantum Approximate Optimization Algorithm (QAOA)

Parameterized quantum circuit $|\psi(\vec{\gamma}, \vec{\beta})\rangle = \prod_{l=1}^{p} e^{-i\beta_l H_M} e^{-i\gamma_l H_C} |+\rangle^{\otimes n}$ simulated on Qiskit `AerSimulator` (512 shots, COBYLA optimizer, 40 evaluations), followed by bitstring decoding and independent evaluation.

## 13. Adaptive QAOA

Extends QAOA with: (a) **Linear-Ramp / Fourier / Warm-Start Initializers**, (b) **Dynamic Depth Expansion** ($p = 1 \to 2$) triggered on energy stagnation, (c) **Adaptive Optimizer Switching** (`COBYLA` $\to$ `Nelder-Mead`), and (d) **Parameter Transfer** across topologically compatible instances.

## 14. AI/ML Solver Recommendation

Extracts 18 structural and QUBO features (`num_variables`, `graph_density`, coefficient statistics, search space $\log_2$), checks OOD z-scores ($z > 3.5$), and routes through `MLSolverRecommenderModel` or `RuleBasedSolverRecommender` (`1.153 ms` mean latency).

## 15. Experiment Management & Reproducibility

Every experiment dataset is fingerprinted with SHA-256 (`qoptimize_research_datasets.json`), paired across identical instances, and seeded deterministically (`seed_k = 42 + 17k`).

## 16. Research Methodology

Detailed in `research/EXPERIMENTAL_METHODOLOGY.md` and `research/experiment_configs/benchmark_protocol.json`: 9 dataset families, 23 canonical instances, 3 trials per stochastic solver, independent evaluation, and Holm–Bonferroni correction.

## 17. Implementation Details

- Backend: Python 3.12, FastAPI, Pydantic v2, PyMongo, Qiskit + Qiskit Aer, SciPy 1.16.0, Scikit-Learn 1.7.2, ReportLab 4.2.0.
- Frontend: React 18, TypeScript, Vite 5.4.21, Tailwind CSS, Lucide Icons.
- Deployment: Multi-stage Dockerfiles, `docker-compose.yml` (MongoDB 7.0 + Backend + Nginx), GitHub Actions CI.

## 18. Experimental Results

- **Stage 10.1 Scientific Validation:** 11/11 exhaustive instances (2,168 binary states, `0.0` max $|E_{\text{QUBO}} - H_{\text{Ising}}|$), 3/3 edge cases, and 12/12 solver parity checks passed (`research/SCIENTIFIC_VALIDATION_REPORT.md`).
- **Stage 10.3 Benchmarking (275 trials):**
  - Classical Exact, SA, and GA achieved **100% feasibility and 0.00% optimality gap** across all 9 families.
  - Standard QAOA and Adaptive QAOA achieved `0.00%` gap on `mc_er_n6_p05`, `mc_reg_n8_d3`, and `tsp_3city_euclid`; on `mc_er_n8_p05_w`, Adaptive QAOA achieved `0.00%` gap ($r = 1.0000$) vs. Standard QAOA `0.1085%` gap ($r = 0.9989$).
  - On `mc_er_n10_p06_w` and `assign_3x3_uniform`, Standard QAOA outperformed Adaptive QAOA under the tight 50-evaluation budget (`2.59%` vs `7.50%` and `10.75%` vs `38.25%` gap).

## 19. Comparative Analysis

See Figures 1–4 and `research/CLASSICAL_VS_QUANTUM_BENCHMARK_REPORT.md`. Classical SA executes ~10–50× faster than `AerSimulator` QAOA on CPU (`0.0443 s` vs `0.8338 s` mean across paired trials) while guaranteeing $r = 1.0000$ on $n \le 16$.

## 20. Statistical Analysis

Across $N = 57$ paired trials (Holm–Bonferroni adjusted $\alpha = 0.05$):
- **SA vs. Standard QAOA (Ratio):** $W = 0.0, p_{\text{Holm}} = 0.0132, d = 0.43$ (Significant).
- **SA vs. Adaptive QAOA (Ratio):** $W = 0.0, p_{\text{Holm}} = 0.0229, d = 0.52$ (Significant).
- **Standard vs. Adaptive QAOA (Ratio):** $W = 49.0, p_{\text{Holm}} = 0.3256, d = 0.23$ (Not significant).
- **Standard vs. Adaptive QAOA (Runtime):** $W = 109.0, p_{\text{Holm}} < 10^{-6}$ (Significant runtime overhead for Adaptive).
- **SA vs. GA (Runtime):** $W = 0.0, p_{\text{Holm}} < 10^{-6}, d = -1.75$ (SA significantly faster).
- **Standard QAOA Max-Cut vs. Assignment (Mann–Whitney):** $U = 318.0$, raw $p = 0.0344$, $p_{\text{Holm}} = 0.0689$ (Not significant after Holm correction).

## 21. Ablation Study

Across 90 ablation trials (`research/ADAPTIVE_QAOA_ABLATION_STUDY.md`):
- Removing warm starts (`ablation_no_warm_start`) degraded `assign_3x3_uniform_i1` ratio from `0.9145` to `0.8763`.
- `ablation_fourier` achieved the fastest runtimes and fewest evaluations on all Max-Cut and TSP instances (`284–299 ms`), though it trailed on heterogeneous Assignment (`0.7810`).
- One `full_adaptive` trial on `mc_er_n8_p05_w_i1` failed with an angle-dimension mismatch during depth expansion (`Expected 2 gamma values, got 1`), honestly reported in the aggregate (`r = 0.6667`).
- Same-family parameter transfer (`mc_er_n6_p05_i1 -> i2`) preserved $r = 1.0000$ with slightly lower runtime (`297.98 ms` vs `317.83 ms`).

## 22. Discussion

Empirical evidence confirms that mathematical verification and independent evaluation prevent silent formulation bugs, while honest statistical testing prevents overclaiming variational quantum gains under small evaluation budgets.

## 23. Limitations

1. All quantum runs use classical CPU simulation (`AerSimulator`), not physical QPUs.
2. Small qubit ceilings ($n \le 10$ for multi-trial QAOA benchmarks) restrict asymptotic scaling observations.
3. Dynamic depth expansion can under-converge if the evaluation budget is not scaled proportionally with $p$.
4. In-memory rate limiting requires Redis backing for multi-replica horizontal scaling.

## 24. Conclusion

**Q-Optimize** successfully delivers a mathematically verified, security-hardened, containerized, and statistically validated hybrid optimization research platform. All 443 automated software tests pass, and all experimental findings are reproducible from version-controlled scripts.

## 25. Future Scope

1. Fix the dynamic-depth angle-vector resize race condition observed in 1/90 ablation trials.
2. Integrate cloud quantum hardware providers (IBM Quantum, AWS Braket) with shot-noise mitigation.
3. Scale background job execution to distributed Celery/Redis worker clusters.

## 26. References (IEEE Format)

1. E. Farhi, J. Goldstone, and S. Gutmann, "A Quantum Approximate Optimization Algorithm," *arXiv preprint arXiv:1411.4028*, 2014.
2. A. Lucas, "Ising formulations of many NP problems," *Frontiers in Physics*, vol. 2, art. 5, 2014.
3. S. Kirkpatrick, C. D. Gelatt Jr., and M. P. Vecchi, "Optimization by simulated annealing," *Science*, vol. 220, no. 4598, pp. 671–680, 1983.
4. J. H. Holland, *Adaptation in Natural and Artificial Systems*, MIT Press, 1992.
5. L. Zhou, S.-T. Wang, S. Choi, H. Pichler, and M. D. Lukin, "Quantum Approximate Optimization Algorithm: Performance, Mechanism, and Implementation on Near-Term Devices," *Physical Review X*, vol. 10, no. 2, 021067, 2020.
6. J. R. Rice, "The Algorithm Selection Problem," *Advances in Computers*, vol. 15, pp. 65–118, 1976.
7. F. Wilcoxon, "Individual comparisons by ranking methods," *Biometrics Bulletin*, vol. 1, no. 6, pp. 80–83, 1945.
8. H. B. Mann and D. R. Whitney, "On a test of whether one of two random variables is stochastically larger than the other," *The Annals of Mathematical Statistics*, vol. 18, no. 1, pp. 50–60, 1947.
9. S. Holm, "A simple sequentially rejective multiple test procedure," *Scandinavian Journal of Statistics*, vol. 6, no. 2, pp. 65–70, 1979.

## 27. Appendices

- **Appendix A:** Reproducible Scripts (`research/scripts/validate_models.py`, `generate_research_datasets.py`, `run_classical_vs_quantum_benchmark.py`, `run_adaptive_ablation_study.py`, `run_statistical_analysis.py`, `generate_research_figures.py`).
- **Appendix B:** Raw Experimental JSON Artifacts (`research/results/*.json`, `research/datasets/qoptimize_research_datasets.json`).
