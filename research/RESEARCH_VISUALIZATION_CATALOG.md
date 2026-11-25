# Stage 10.6 — Research Visualization Catalog

**Generator Script:** `research/scripts/generate_research_figures.py`  
**Output Directory:** `research/figures/` (300 DPI PNG)  
**Data Sources:** `qoptimize_research_datasets.json`, `classical_vs_quantum_benchmark.json`, `adaptive_qaoa_ablation_results.json`, `statistical_analysis_results.json`, and live `AerSimulator` traces.

---

## Figure Inventory (12 Publication-Quality Figures)

| # | Filename | Title / Description | Data Source |
|---|---|---|---|
| **1** | `fig01_objective_comparison.png` | Classical vs. Quantum (`AerSimulator`) Mean Approximation Ratio ($r$) across 7 quantum-compatible families ($n=19$ instances, 3 trials/solver) | `classical_vs_quantum_benchmark.json` |
| **2** | `fig02_execution_time_comparison.png` | Mean Execution Time Comparison (log-scale seconds) across Exact, SA, GA, Standard QAOA, and Adaptive QAOA | `classical_vs_quantum_benchmark.json` |
| **3** | `fig03_optimality_gap_comparison.png` | Mean Optimality Gap (%) Relative to Exact Optimum across heuristic and variational solvers | `classical_vs_quantum_benchmark.json` |
| **4** | `fig04_approximation_ratio_comparison.png` | Pooled Approximation Ratio by Problem Family (Max-Cut, Assignment, TSP) with 95% $t$-Confidence Intervals | `statistical_analysis_results.json` |
| **5** | `fig05_qaoa_convergence_curve.png` | Standard QAOA ($p=1$, shots=512, COBYLA) expectation value $\langle H_C \rangle$ convergence trajectory on `mc_er_n8_p05_w_i1` | Live `QAOAExecutionPipeline` (`AerSimulator`) |
| **6** | `fig06_adaptive_qaoa_convergence_curve.png` | Adaptive QAOA instantaneous and best-so-far $\langle H_C \rangle$ convergence trajectory on `mc_er_n8_p05_w_i1` | Live `AdaptiveQAOAExecutionPipeline` (`AerSimulator`) |
| **7** | `fig07_adaptive_depth_progression.png` | Mean Final Circuit Depth ($p$) and Mean Optimizer Evaluation Cost across all 6 ablation variants | `adaptive_qaoa_ablation_results.json` |
| **8** | `fig08_parameter_transfer_analysis.png` | Parameter Transfer (`mc_er_n6_p05_i1` $\to$ `mc_er_n6_p05_i2`): Cold Start vs. Warm-Start Transfer runtime & optimality | `adaptive_qaoa_ablation_results.json` |
| **9** | `fig09_ablation_study_comparison.png` | 6-Variant Adaptive QAOA Ablation Comparison across 5 representative instances ($3$ trials/variant) | `adaptive_qaoa_ablation_results.json` |
| **10** | `fig10_scalability_analysis.png` | Runtime Scalability (log-scale seconds) vs. QUBO Variable / Qubit Count ($n = 6$ to $16$) | `classical_vs_quantum_benchmark.json` |
| **11** | `fig11_statistical_distribution_plots.png` | Paired Boxplot Distributions of Approximation Ratio and Runtime ($N = 57$ paired trials per solver) | `classical_vs_quantum_benchmark.json` |
| **12** | `fig12_problem_solution_visualization.png` | Problem-Specific Verified Optimal Solutions: (a) Max-Cut Partition Graph, (b) $3\times 3$ Assignment Matrix, (c) 3-City Euclidean TSP Cycle | `qoptimize_research_datasets.json` + `ExactSolver` |
