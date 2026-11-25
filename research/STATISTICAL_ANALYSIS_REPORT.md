# Stage 10.5 — Statistical Analysis & Research Validity Report

**Project:** Q-Optimize — AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Execution Script:** `research/scripts/run_statistical_analysis.py`  
**Raw Data Artifact:** `research/results/statistical_analysis_results.json`  
**Input Dataset:** 275 benchmark trial records from Stage 10.3 (`classical_vs_quantum_benchmark.json`)  
**Date:** 2026-11-25

---

## 1. Statistical Methodology & Validity Controls

1. **Distribution-Free Non-Parametric Testing:** Variational quantum simulation outcomes are bounded and non-Gaussian; therefore, we apply **Wilcoxon signed-rank tests** for paired `(instance_id, trial)` comparisons and **Mann–Whitney U tests** for independent problem-family comparisons (`scipy 1.16.0` via `backend/app/experiments/statistics.py`).
2. **Effect Sizes:** Reported via **Cohen's $d$** for standardized mean differences and **rank-biserial correlation ($r$)** for Mann–Whitney comparisons.
3. **Multiple-Comparison Correction:** All 6 hypothesis tests are adjusted using **Holm–Bonferroni step-down correction** ($\alpha = 0.05$) to control family-wise Type I error rate.
4. **Honest Limitations:** Exact, SA, and GA achieve zero-variance $r = 1.0000$ across all tested instances, producing heavy ties in signed-rank tests; additionally, classical CPU runtimes and `AerSimulator` runtimes reflect fundamentally different computational models and are not evidence of physical quantum advantage.

---

## 2. Descriptive Statistics & 95% Confidence Intervals

| Problem Type | Solver | $N$ Trials | Mean Approx. Ratio ($r$) | 95% CI ($r$) | Mean Gap (%) | Mean Runtime (s) | 95% CI Runtime (s) |
|---|---|---|---|---|---|---|---|
| `max_cut` | `exact` | 11 | 1.0000 | [1.0000, 1.0000] | 0.0000% | 0.0013 | [0.0006, 0.0021] |
| `max_cut` | `simulated_annealing` | 33 | 1.0000 | [1.0000, 1.0000] | 0.0000% | 0.0514 | [0.0292, 0.0735] |
| `max_cut` | `genetic_algorithm` | 33 | 1.0000 | [1.0000, 1.0000] | 0.0000% | 0.3512 | [0.2599, 0.4426] |
| `max_cut` | `standard_qaoa` (Aer) | 33 | 0.9950 | [0.9883, 1.0017] | 0.5006% | 1.0537 | [0.5230, 1.5845] |
| `max_cut` | `adaptive_qaoa` (Aer) | 33 | 0.9864 | [0.9708, 1.0019] | 1.3642% | 1.1710 | [0.9011, 1.4410] |
| `assignment` | `exact` | 7 | 1.0000 | [1.0000, 1.0000] | 0.0000% | 0.0002 | [0.0002, 0.0002] |
| `assignment` | `simulated_annealing` | 21 | 1.0000 | [1.0000, 1.0000] | 0.0000% | 0.0381 | — |
| `assignment` | `standard_qaoa` (Aer) | 15 | 0.9296 | — | — | — | — |
| `tsp` | `adaptive_qaoa` (Aer) | 9 | 1.0000 | [1.0000, 1.0000] | 0.0000% | 0.8933 | [0.8075, 0.9792] |

*(Full per-family rows are archived in `research/results/statistical_analysis_results.json`.)*

---

## 3. Hypothesis Testing & Holm–Bonferroni Adjusted Results

| Comparison | Design & Test | $N$ | Mean A vs Mean B | Test Stat | Raw $p$-value | Holm Adj. $p$ | Cohen's $d$ | Significant ($\alpha=0.05$) |
|---|---|---|---|---|---|---|---|---|
| **SA vs Standard QAOA (Approx. Ratio)** | Paired Wilcoxon | 57 pairs | 1.0000 vs 0.9786 | $W = 0.0$ | `0.003299` | **`0.013196`** | `0.4277` (small–med) | ✅ **Yes** |
| **SA vs Adaptive QAOA (Approx. Ratio)** | Paired Wilcoxon | 57 pairs | 1.0000 vs 0.9551 | $W = 0.0$ | `0.007632` | **`0.022897`** | `0.5152` (medium) | ✅ **Yes** |
| **Standard QAOA vs Adaptive QAOA (Approx. Ratio)** | Paired Wilcoxon | 57 pairs | 0.9786 vs 0.9551 | $W = 49.0$ | `0.325627` | **`0.325627`** | `0.2334` (small) | ❌ **No** |
| **Standard QAOA vs Adaptive QAOA (Runtime s)** | Paired Wilcoxon | 57 pairs | 0.8338 s vs 1.0161 s | $W = 109.0$ | `1.19e-08` | **`< 0.000001`** | `-0.1965` (small) | ✅ **Yes** |
| **SA vs Genetic Algorithm (Runtime s)** | Paired Wilcoxon | 57 pairs | 0.0443 s vs 0.3030 s | $W = 0.0$ | `5.14e-11` | **`< 0.000001`** | `-1.7457` (large) | ✅ **Yes** |
| **Standard QAOA Ratio: Max-Cut vs Assignment** | Independent Mann–Whitney U | 33 vs 15 | 0.9950 vs 0.9296 | $U = 318.0$ | `0.034432` | **`0.068864`** | `0.9208` ($r=-0.2848$) | ❌ **No** *(after Holm)* |

---

## 4. Scientific Interpretation & Limitations

1. **Classical Heuristic Superiority at Small Scale:** Simulated Annealing significantly outperforms both Standard QAOA ($p_{\text{Holm}} = 0.0132, d = 0.43$) and Adaptive QAOA ($p_{\text{Holm}} = 0.0229, d = 0.52$) in approximation ratio across the 57 paired quantum-compatible trials, while also running significantly faster than Genetic Algorithm ($p_{\text{Holm}} < 10^{-6}, d = -1.75$).
2. **Standard vs. Adaptive QAOA Parity Under Tight Budgets:** Across all 57 paired trials, the difference in approximation ratio between Standard QAOA ($0.9786$) and Adaptive QAOA ($0.9551$) is **not statistically significant** ($p_{\text{Holm}} = 0.3256$), whereas Adaptive QAOA incurs statistically significantly higher simulation runtime ($1.0161\text{ s}$ vs. $0.8338\text{ s}$, $p_{\text{Holm}} < 10^{-6}$).
3. **Importance of Multiple-Comparison Control:** Comparing Standard QAOA approximation ratios on Max-Cut ($0.9950$) vs. Assignment ($0.9296$) yields a raw Mann–Whitney $p = 0.0344$, which **fails to remain significant after Holm–Bonferroni correction** ($p_{\text{Holm}} = 0.0689$), preventing an overstated family-level claim given $n_{\text{assign}} = 15$.
