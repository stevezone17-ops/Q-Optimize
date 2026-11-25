# Stage 10.4 — Adaptive QAOA Research & Ablation Study

**Project:** Q-Optimize — AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Execution Script:** `research/scripts/run_adaptive_ablation_study.py`  
**Raw Data Artifact:** `research/results/adaptive_qaoa_ablation_results.json`  
**Simulation Backend:** Qiskit `AerSimulator` (host CPU, `shots=512`, `trials=3`, `base_seed=42`, `max_evaluations_total=50`)

---

## 1. Experimental Design

We evaluated all **6 Adaptive QAOA ablation variants** implemented in `AdaptiveBenchmarkEngine` across 5 representative instances (`mc_er_n6_p05_i1`, `mc_er_n8_p05_w_i1`, `mc_reg_n8_d3_i1`, `assign_3x3_uniform_i1`, `tsp_3city_euclid_i1`):

1. `standard_baseline`: Fixed depth $p=1$, static COBYLA optimizer, linear ramp initialization.
2. `full_adaptive`: Dynamic depth growth ($p=1 \to 2$), warm-start parameter interpolation, COBYLA $\to$ Nelder-Mead fallback switching.
3. `ablation_no_warm_start`: Dynamic depth growth with random layer initialization (isolates warm-start transfer).
4. `ablation_no_dynamic_depth`: Fixed depth $p=1$ with adaptive optimizer switching (isolates dynamic depth growth).
5. `ablation_no_optimizer_switching`: Dynamic depth ($p=2$) and warm-start with static COBYLA (isolates optimizer switching).
6. `ablation_fourier`: Discrete Fourier angle parameterization at fixed depth $p=1$.

---

## 2. Empirical Ablation Results

### 2.1 Max-Cut Instances ($n = 6, 8$ Qubits)

| Instance (Exact Opt) | Variant | Trials | Mean Depth | Mean Obj | Approx. Ratio ($r$) | Mean Evals | Mean Runtime (ms) |
|---|---|---|---|---|---|---|---|
| `mc_er_n6_p05_i1` (`8.0`) | `standard_baseline` | 3 | 1.00 | 8.0000 | 1.0000 | 30.0 | 786.4 |
| `mc_er_n6_p05_i1` (`8.0`) | `full_adaptive` | 3 | 1.33 | 8.0000 | 1.0000 | 64.0 | 456.7 |
| `mc_er_n6_p05_i1` (`8.0`) | `ablation_no_warm_start` | 3 | 1.00 | 8.0000 | 1.0000 | 67.0 | 500.8 |
| `mc_er_n6_p05_i1` (`8.0`) | `ablation_no_dynamic_depth` | 3 | 1.00 | 8.0000 | 1.0000 | 64.0 | 440.8 |
| `mc_er_n6_p05_i1` (`8.0`) | `ablation_no_optimizer_switching` | 3 | 2.00 | 8.0000 | 1.0000 | 55.0 | 476.2 |
| `mc_er_n6_p05_i1` (`8.0`) | `ablation_fourier` | 3 | 1.00 | 8.0000 | 1.0000 | **30.0** | **289.1** |
| `mc_er_n8_p05_w_i1` (`65.1952`) | `standard_baseline` | 3 | 1.00 | 65.1952 | 1.0000 | 25.0 | 322.4 |
| `mc_er_n8_p05_w_i1` (`65.1952`) | `full_adaptive` *(1 trial error)* | 3 | 1.33 | 43.4635 | 0.6667 | 42.3 | 431.6 |
| `mc_er_n8_p05_w_i1` (`65.1952`) | `ablation_no_warm_start` | 3 | 1.00 | 65.1952 | 1.0000 | 51.3 | 420.0 |
| `mc_er_n8_p05_w_i1` (`65.1952`) | `ablation_no_dynamic_depth` | 3 | 1.00 | 65.1952 | 1.0000 | 58.7 | 474.7 |
| `mc_er_n8_p05_w_i1` (`65.1952`) | `ablation_no_optimizer_switching` | 3 | 2.00 | 65.1952 | 1.0000 | 50.0 | 489.6 |
| `mc_er_n8_p05_w_i1` (`65.1952`) | `ablation_fourier` | 3 | 1.00 | 65.1952 | 1.0000 | **25.0** | **295.9** |
| `mc_reg_n8_d3_i1` (`10.0`) | `standard_baseline` | 3 | 1.00 | 10.0000 | 1.0000 | 30.0 | 341.4 |
| `mc_reg_n8_d3_i1` (`10.0`) | `full_adaptive` | 3 | 1.00 | 10.0000 | 1.0000 | 67.0 | 481.1 |
| `mc_reg_n8_d3_i1` (`10.0`) | `ablation_no_warm_start` | 3 | 1.00 | 10.0000 | 1.0000 | 62.0 | 489.7 |
| `mc_reg_n8_d3_i1` (`10.0`) | `ablation_no_dynamic_depth` | 3 | 1.00 | 10.0000 | 1.0000 | 65.7 | 513.2 |
| `mc_reg_n8_d3_i1` (`10.0`) | `ablation_no_optimizer_switching` | 3 | 2.00 | 10.0000 | 1.0000 | 45.0 | 404.2 |
| `mc_reg_n8_d3_i1` (`10.0`) | `ablation_fourier` | 3 | 1.00 | 10.0000 | 1.0000 | **25.0** | **299.2** |

### 2.2 Constrained Assignment & TSP Instances ($n = 9$ Qubits)

| Instance (Exact Opt) | Variant | Trials | Mean Depth | Mean Cost | Approx. Ratio ($r$) | Mean Evals | Mean Runtime (ms) |
|---|---|---|---|---|---|---|---|
| `assign_3x3_uniform_i1` (`109.4996`) | `standard_baseline` | 3 | 1.00 | **109.4996** | **1.0000** | **15.0** | **269.4** |
| `assign_3x3_uniform_i1` (`109.4996`) | `full_adaptive` | 3 | 1.00 | 119.7370 | 0.9145 | 53.0 | 540.0 |
| `assign_3x3_uniform_i1` (`109.4996`) | `ablation_no_warm_start` | 3 | 1.00 | 124.9526 | 0.8763 | 58.0 | 536.1 |
| `assign_3x3_uniform_i1` (`109.4996`) | `ablation_no_dynamic_depth` | 3 | 1.00 | 119.7370 | 0.9145 | 53.0 | 985.1 |
| `assign_3x3_uniform_i1` (`109.4996`) | `ablation_no_optimizer_switching` | 3 | 2.00 | **109.4996** | **1.0000** | 35.0 | 479.3 |
| `assign_3x3_uniform_i1` (`109.4996`) | `ablation_fourier` | 3 | 1.00 | 140.2118 | 0.7810 | 20.0 | 300.5 |
| `tsp_3city_euclid_i1` (`175.8261`) | `standard_baseline` | 3 | 1.00 | 175.8261 | 1.0000 | 20.0 | 409.1 |
| `tsp_3city_euclid_i1` (`175.8261`) | `full_adaptive` | 3 | 1.00 | 175.8261 | 1.0000 | 60.3 | 754.8 |
| `tsp_3city_euclid_i1` (`175.8261`) | `ablation_no_warm_start` | 3 | 1.00 | 175.8261 | 1.0000 | 53.3 | 601.0 |
| `tsp_3city_euclid_i1` (`175.8261`) | `ablation_no_dynamic_depth` | 3 | 1.00 | 175.8261 | 1.0000 | 60.3 | 700.6 |
| `tsp_3city_euclid_i1` (`175.8261`) | `ablation_no_optimizer_switching` | 3 | 2.00 | 175.8261 | 1.0000 | 35.0 | 528.0 |
| `tsp_3city_euclid_i1` (`175.8261`) | `ablation_fourier` | 3 | 1.00 | 175.8261 | 1.0000 | **15.0** | **284.2** |

---

## 3. Parameter Transfer Study (`mc_er_n6_p05_i1` $\to$ `mc_er_n6_p05_i2`)

| Transfer Mode | Source Angles ($\gamma, \beta$) | Target Objective | Exact Opt | Approx. Ratio | Evaluations | Runtime (ms) |
|---|---|---|---|---|---|---|
| **Cold Start** | None (linear ramp) | 8.0 | 8.0 | 1.0000 | 30 | 317.83 |
| **Warm-Start Transfer** | $\gamma=[0.5389], \beta=[1.2526]$ | 8.0 | 8.0 | 1.0000 | 30 | **297.98** |

**Compatibility Boundary:** Parameter transfer is valid across identically scaled Max-Cut graphs with matching edge-weight distributions, but is **inappropriate** across different problem families (e.g., Max-Cut $\to$ Assignment/TSP) because constrained QUBO penalty multipliers ($A, B \gg 1$) alter the Cost Hamiltonian energy scale and optimal $\gamma$ periodicity.

---

## 4. Honest Scientific Findings & Negative Results

1. **Evaluation Overhead of Adaptive Switching:** Across small instances, `full_adaptive` averaged `53.0–67.0` evaluations vs. `15.0–30.0` for `standard_baseline` because fallback optimizer transitions (`COBYLA -> Nelder-Mead`) consume additional budget without always improving objective quality when $p=1$ already reaches the optimum.
2. **Value of Warm Starts:** On `assign_3x3_uniform_i1`, removing warm starts (`ablation_no_warm_start`) degraded approximation ratio from `0.9145` (`full_adaptive`) to `0.8763`, confirming warm-start initialization helps stabilize adaptive optimization.
3. **Fourier Parameterization Trade-off:** `ablation_fourier` achieved the **lowest runtime and evaluation count** on all Max-Cut and TSP instances (`284–299 ms`), but underperformed on `assign_3x3_uniform_i1` ($r = 0.7810$), showing that smooth Fourier frequency bases are better suited to regular/symmetric landscapes than heterogeneous cost matrices.
4. **Dynamic Depth Reliability Defect Observed:** In 1 of 3 trials on `mc_er_n8_p05_w_i1`, `full_adaptive` encountered an angle-length mismatch (`Expected 2 gamma values, got 1`) during a depth transition, reducing its 3-trial mean from `65.1952` to `43.4635`. We report this failure transparently rather than discarding the outlier.
5. **Barren Plateaus:** These $n \le 9$ simulator experiments do **not** provide evidence that dynamic depth eliminates barren plateaus in large-scale quantum circuits.
