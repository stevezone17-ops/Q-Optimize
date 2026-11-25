# Stage 10.9 — Viva Questions & Answers (105 Technical Q&A)

**Project:** Q-Optimize — An AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Target Audience:** B.Tech CSE Final-Year Project Viva / External Examination

---

## Section A: Basic Quantum Computing, Qubits, Superposition & Entanglement (Q1–Q18)

1. **Q1: What is a qubit and how does it differ from a classical bit?**  
   **A:** A classical bit is strictly `0` or `1`. A qubit is a two-level quantum mechanical system whose state $|\psi\rangle = \alpha|0\rangle + \beta|1\rangle$ can exist in a linear superposition of basis states $|0\rangle$ and $|1\rangle$ with complex amplitudes satisfying $|\alpha|^2 + |\beta|^2 = 1$.
2. **Q2: What is superposition?**  
   **A:** Superposition is the ability of a quantum system to exist in a coherent linear combination of computational basis states simultaneously until measured.
3. **Q3: What happens when a qubit in superposition is measured?**  
   **A:** Measurement projects the state onto $|0\rangle$ with probability $|\alpha|^2$ or $|1\rangle$ with probability $|\beta|^2$, collapsing the superposition into a classical bitstring.
4. **Q4: What is quantum entanglement?**  
   **A:** Entanglement is a non-classical correlation between multiple qubits where the joint quantum state cannot be factored into independent single-qubit states (e.g., Bell state $\frac{|00\rangle + |11\rangle}{\sqrt{2}}$).
5. **Q5: Why is entanglement important in QAOA?**  
   **A:** Two-qubit $ZZ$ interaction gates ($e^{-i\gamma J_{ij} Z_i Z_j}$) entangle qubits corresponding to coupled decision variables, allowing interference across correlated variable assignments.
6. **Q6: What is the dimension of an $n$-qubit Hilbert space?**  
   **A:** $2^n$ complex dimensions. Adding one qubit doubles the statevector dimension, which is why classical simulation (`AerSimulator`) scales exponentially in RAM/CPU.
7. **Q7: What is a quantum gate?**  
   **A:** A reversible, unitary linear operator $U$ ($U^\dagger U = I$) acting on one or more qubits to evolve their quantum state.
8. **Q8: What does the Hadamard gate ($H$) do?**  
   **A:** It maps $|0\rangle \to |+\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$, creating an equal superposition of all $2^n$ states when applied to $n$ qubits at the start of QAOA.
9. **Q9: What are Pauli-$X$, Pauli-$Y$, and Pauli-$Z$ gates?**  
   **A:** Single-qubit $\pi$ rotations around the $X$, $Y$, and $Z$ axes of the Bloch sphere. In QAOA, $Z$ encodes problem eigenvalues ($\pm 1$) and $X$ drives mixer transitions.
10. **Q10: What is the $R_X(\theta)$ rotation gate used for in QAOA?**  
    **A:** $R_X(2\beta) = e^{-i\beta X}$ implements the transverse-field mixer unitary $U(H_M, \beta)$ on each qubit.
11. **Q11: How is a two-qubit $e^{-i\gamma J_{ij} Z_i Z_j}$ gate decomposed?**  
    **A:** Using a `CNOT`–`RZ(2 * gamma * J_ij)`–`CNOT` sequence (or native `RZZ` gate).
12. **Q12: What is a Hermitian operator / observable?**  
    **A:** An operator $H = H^\dagger$ with real eigenvalues, representing measurable physical quantities such as energy.
13. **Q13: What is an expectation value $\langle \psi | H_C | \psi \rangle$?**  
    **A:** The average cost Hamiltonian energy obtained over repeated measurements (shots) of the trial state $|\psi\rangle$.
14. **Q14: What is shot noise in quantum measurement?**  
    **A:** Statistical sampling variance ($\propto 1/\sqrt{S}$ for $S$ shots) when estimating $\langle H_C \rangle$ from finite bitstring samples.
15. **Q15: What is a quantum simulator vs. real quantum hardware?**  
    **A:** A simulator (like Qiskit `AerSimulator`) computes linear algebra on a classical CPU/GPU; physical hardware manipulates real qubits subject to decoherence and gate errors.
16. **Q16: Does Q-Optimize run on physical quantum hardware?**  
    **A:** No. All quantum executions in Q-Optimize run on Qiskit `AerSimulator` on classical CPU, and this is explicitly disclosed in all reports and UI outputs.
17. **Q17: What is a barren plateau?**  
    **A:** A phenomenon in deep parameterized quantum circuits where cost-function gradients vanish exponentially with qubit count, stalling gradient-based optimizers.
18. **Q18: What is the No-Cloning Theorem?**  
    **A:** An arbitrary unknown quantum state cannot be copied identically, which is why each QAOA evaluation prepares and measures a fresh circuit.

---

## Section B: Hamiltonians, QUBO & Ising Formulations (Q19–Q36)

19. **Q19: What is QUBO?**  
    **A:** Quadratic Unconstrained Binary Optimization: minimizing $E(x) = x^T Q x + c$ over binary variables $x \in \{0, 1\}^n$.
20. **Q20: Why convert constrained problems to QUBO?**  
    **A:** Quantum annealers and QAOA natively minimize unconstrained quadratic objectives; constraints are enforced by adding squared penalty terms.
21. **Q21: What is the upper-triangular QUBO convention in Q-Optimize?**  
    **A:** Quadratic coefficients $Q_{ij}$ are strictly stored for $i < j$ in `variable_order`, preventing double-counting of symmetric off-diagonal terms.
22. **Q22: What is the Ising model?**  
    **A:** A spin Hamiltonian $H_{\text{Ising}}(Z) = \sum_i h_i Z_i + \sum_{i<j} J_{ij} Z_i Z_j + C$ with spin variables $Z_i \in \{-1, +1\}$.
23. **Q23: Write the exact binary-to-spin mapping used in Q-Optimize.**  
    **A:** $x_i = \frac{1 - Z_i}{2}$ (equivalently $Z_i = 1 - 2x_i$), mapping $x_i=0 \mapsto Z_i=+1$ and $x_i=1 \mapsto Z_i=-1$.
24. **Q24: How is Max-Cut formulated as a QUBO?**  
    **A:** Each cut edge $(u,v)$ contributes $w_{uv}(x_u + x_v - 2x_u x_v)$; because QUBO minimizes, we negate this objective so $E_{\text{QUBO}}(x) = -C_{\text{cut}}(x)$.
25. **Q25: How is the Linear Assignment Problem formulated as a QUBO?**  
    **A:** $n^2$ binary variables $x_{i,j}$ (agent $i$ assigned to task $j$), minimizing $\sum c_{ij}x_{ij}$ plus row-sum and column-sum penalties $A\sum_i(\sum_j x_{ij}-1)^2 + B\sum_j(\sum_i x_{ij}-1)^2$.
26. **Q26: Why does Q-Optimize reject non-square Assignment cost matrices?**  
    **A:** Exact 1-to-1 permutation equality constraints require $|A| = |T|$; rectangular matrices require slack variables not implied by standard square matching.
27. **Q27: How is TSP encoded as a QUBO?**  
    **A:** $N^2$ binary variables $x_{u,p}$ (city $u$ visited at tour position $p$), minimizing $\sum d_{uv} x_{u,p} x_{v,p+1}$ plus uniqueness penalties ensuring each city and position appears once.
28. **Q28: How should penalty multipliers $A$ and $B$ be chosen?**  
    **A:** Large enough that any infeasible state has strictly higher QUBO energy than the optimal feasible state, without causing excessive numerical dynamic range.
29. **Q29: How does `FormulationVerifier` verify mathematical correctness?**  
    **A:** For $n \le 12$ ($2^n \le 4,096$ states), it exhaustively enumerates all bitstrings and checks $|E_{\text{QUBO}}(x) - H_{\text{Ising}}(Z)| < 10^{-6}$ and parity with Phase 2 evaluators.
30. **Q30: What maximum energy discrepancy was observed in Stage 10.1?**  
    **A:** `0.0` across all 11 tested instances (2,168 enumerated states).
31. **Q31: Why does Q-Optimize keep an independent Phase 2 evaluator?**  
    **A:** To prevent solver self-reporting bias; every candidate bitstring is decoded and re-evaluated directly against the canonical problem definition.
32. **Q32: What happens if a QAOA bitstring violates TSP city uniqueness?**  
    **A:** The decoder and independent evaluator flag `is_feasible = False` and record `DUPLICATE_CITY_VISIT` / `OMITTED_CITIES` violations.
33. **Q33: How does Q-Optimize handle zero-weight or negative-weight Max-Cut graphs?**  
    **A:** Validated in Stage 10.1 (`maxcut_zero_weights`, `maxcut_negative_weights`): $E_{\text{QUBO}} = -C_{\text{cut}}$ holds identically for all edge signs.
34. **Q34: What happens with disconnected graphs in Max-Cut?**  
    **A:** Each connected component cuts independently, and the total cut equals the sum of component cuts (`maxcut_disconnected` verified 16/16 states).
35. **Q35: What is the QUBO variable count for an $N$-city TSP?**  
    **A:** $N^2$ qubits (e.g., 3 cities = 9 qubits, 4 cities = 16 qubits).
36. **Q36: Why limit exhaustive truth-table verification to $n \le 12$?**  
    **A:** $2^{12} = 4,096$ states run in milliseconds; $2^{20} > 10^6$ states would stall interactive API requests.

---

## Section C: QAOA, Parameter Optimization & Adaptive QAOA (Q37–Q56)

37. **Q37: Explain the QAOA ansatz in one sentence.**  
    **A:** Starting from $|+\rangle^{\otimes n}$, QAOA alternates $p$ layers of cost unitaries $e^{-i\gamma_l H_C}$ and mixer unitaries $e^{-i\beta_l H_M}$ parameterized by $2p$ angles $(\vec{\gamma}, \vec{\beta})$.
38. **Q38: What happens as circuit depth $p \to \infty$ in QAOA?**  
    **A:** By Trotterized adiabatic evolution, the ground-state approximation ratio approaches $1$ for optimal angles.
39. **Q39: Why is QAOA called a *hybrid* quantum-classical algorithm?**  
    **A:** A quantum circuit prepares and samples states, while a classical optimizer (`COBYLA`, `Nelder-Mead`, `SLSQP`) updates $(\vec{\gamma}, \vec{\beta})$ to minimize $\langle H_C \rangle$.
40. **Q40: Why use derivative-free optimizers like COBYLA in QAOA?**  
    **A:** Finite-shot sampling introduces stochastic noise that destabilizes finite-difference gradient estimates; COBYLA handles noisy objectives more robustly.
41. **Q41: What is Adaptive QAOA in Q-Optimize?**  
    **A:** An enhanced variational pipeline supporting dynamic depth expansion ($p \to p+1$), warm-start parameter transfer, Fourier angle parameterization, and adaptive optimizer switching.
42. **Q42: How does warm-start parameter transfer work?**  
    **A:** Optimal angles from depth $p$ (or from a similar source graph) initialize depth $p+1$ (or a target instance) instead of cold random angles.
43. **Q43: What did our Stage 10.4 Parameter Transfer experiment show?**  
    **A:** Transferring optimal angles from `mc_er_n6_p05_i1` to `mc_er_n6_p05_i2` preserved $r = 1.0000$ while reducing runtime from `317.83 ms` (cold) to `297.98 ms`.
44. **Q44: When is parameter transfer *inappropriate*?**  
    **A:** Across incompatible problem families (e.g., Max-Cut $\to$ Assignment) where penalty terms rescale the Cost Hamiltonian by orders of magnitude.
45. **Q45: What is Fourier parameterization in QAOA?**  
    **A:** Representing $(\vec{\gamma}, \vec{\beta})$ via smooth discrete sine/cosine frequency coefficients $(\vec{u}, \vec{v})$ to reduce search-space ruggedness.
46. **Q46: What trade-off did `ablation_fourier` show in Stage 10.4?**  
    **A:** It achieved the lowest evaluation counts and fastest runtimes (`284–299 ms`) on Max-Cut and TSP, but underperformed on `assign_3x3_uniform_i1` ($r = 0.7810$).
47. **Q47: Did Adaptive QAOA always beat Standard QAOA in our benchmarks?**  
    **A:** No—honestly reported in Stages 10.3–10.5. Under a 40–50 evaluation budget, pooled approximation ratios had no significant difference ($p_{\text{Holm}} = 0.3256$), and Adaptive QAOA took longer due to depth/optimizer switching.
48. **Q48: What defect was discovered during Stage 10.4 ablation?**  
    **A:** One `full_adaptive` trial on `mc_er_n8_p05_w_i1` raised `Expected 2 gamma values, got 1` during dynamic depth transition; it was transparently logged and included in the mean (`r = 0.6667`).
49. **Q49: Did removing warm starts hurt Adaptive QAOA?**  
    **A:** Yes, on `assign_3x3_uniform_i1`, `ablation_no_warm_start` dropped approximation ratio from `0.9145` (`full_adaptive`) to `0.8763`.
50. **Q50: Can we claim Adaptive QAOA eliminates barren plateaus?**  
    **A:** No. Our experiments ($n \le 10$ qubits) do not provide evidence regarding asymptotic barren-plateau elimination.
51. **Q51: How is the best solution extracted from QAOA sampling?**  
    **A:** `QAOASolutionDecoder` maps measured bitstrings to domain candidates, evaluates feasibility, and selects the best feasible solution (or most frequent if none feasible).
52. **Q52: What is the approximation ratio $r$ for maximization vs. minimization?**  
    **A:** Maximization (Max-Cut): $r = C_{\text{best}} / C_{\text{exact}}$. Minimization (Assignment, TSP): $r = C_{\text{exact}} / C_{\text{best}}$. Both satisfy $r \in (0, 1]$ for feasible sub-optimal solutions.
53. **Q53: How is optimality gap (%) defined?**  
    **A:** $\text{Gap}(\%) = \frac{|C_{\text{best}} - C_{\text{exact}}|}{|C_{\text{exact}}|} \times 100\%$.
54. **Q54: What shot count did Q-Optimize use in Phase 10 benchmarks?**  
    **A:** `512` shots per circuit evaluation.
55. **Q55: Why does QAOA runtime increase steeply from $n=6$ to $n=10$ on AerSimulator?**  
    **A:** Classical statevector simulation scales as $O(2^n)$ in memory and gate matrix multiplications.
56. **Q56: What is adaptive optimizer switching?**  
    **A:** Starting with global exploration (`COBYLA`) and switching to local simplex refinement (`Nelder-Mead`) when energy improvement stagnates.

---

## Section D: Classical Optimization & AI/ML Solver Selection (Q57–Q72)

57. **Q57: How does the Exact Solver work?**  
    **A:** Uses branch-and-bound / exhaustive enumeration over feasible configurations to guarantee the global optimum within safety size limits ($n \le 18$ Max-Cut, $n \le 10$ TSP).
58. **Q58: Explain Simulated Annealing (SA).**  
    **A:** A single-trajectory stochastic local search that always accepts improving moves and probabilistically accepts worsening moves with $P = e^{-\Delta E / T}$ as temperature $T$ cools geometrically.
59. **Q59: Explain Genetic Algorithms (GA).**  
    **A:** A population-based evolutionary metaheuristic evolving candidate solutions via tournament selection, crossover, and random mutation.
60. **Q60: How did SA compare to GA in Stage 10.5?**  
    **A:** Both achieved $r = 1.0000$ across all 9 families, while SA ran significantly faster (`0.0443 s` vs. `0.3030 s`, Wilcoxon $p_{\text{Holm}} < 10^{-6}$, Cohen's $d = -1.75$).
61. **Q61: How did SA compare to QAOA simulation?**  
    **A:** SA significantly outperformed both Standard QAOA ($p_{\text{Holm}} = 0.0132$) and Adaptive QAOA ($p_{\text{Holm}} = 0.0229$) in approximation ratio across 57 paired trials.
62. **Q62: What is the Algorithm Selection Problem (Rice, 1976)?**  
    **A:** Learning a mapping from structural instance features $\mathcal{X}$ to the best-performing solver $s^* \in \mathcal{S}$.
63. **Q63: How many features does `IntelligentSolverRecommender` extract?**  
    **A:** `18` structural and QUBO features (variable count, graph density, degree stats, QUBO coefficient min/max/mean/std, $\log_2$ search space).
64. **Q64: What is Out-of-Distribution (OOD) detection in the recommender?**  
    **A:** Computing z-scores against reference feature distributions; if $\max z > 3.5$, the recommender flags OOD and falls back safely to `RuleBasedSolverRecommender`.
65. **Q65: What happened when we evaluated the recommender in Stage 10.3?**  
    **A:** It achieved `1.153 ms` mean latency, selected `exact` on all 23 tractable instances (`0.0%` decision regret), and triggered OOD fallback on 12 high-magnitude Assignment/TSP matrices.
66. **Q66: Why is Group-Aware Splitting important when training the ML recommender?**  
    **A:** Random splits leak multiple trials of the same graph across train/test sets; grouping by instance ID ensures generalization to unseen topologies.
67. **Q67: What is Decision Regret?**  
    **A:** Relative objective loss incurred by picking the recommended solver instead of the oracle best solver.
68. **Q68: Why does Q-Optimize never treat the recommender as a solver?**  
    **A:** The recommender only suggests *which* solver to run; the selected solver must still execute and pass independent verification.
69. **Q69: What is Brier calibration score?**  
    **A:** Mean squared error between predicted solver-selection probabilities and actual one-hot optimality outcomes.
70. **Q70: What happens if the active ML model is untrained?**  
    **A:** `IntelligentSolverRecommender` logs the state and delegates cleanly to `RuleBasedSolverRecommender`.
71. **Q71: Explain Natural Language Problem Creation in Q-Optimize.**  
    **A:** Uses Gemini (or a deterministic fallback parser) to produce a *reviewable draft* that requires explicit human confirmation before canonical problem creation.
72. **Q72: Why require human confirmation on NL drafts?**  
    **A:** To prevent LLM hallucinations from silently entering mathematical formulations or benchmark datasets.

---

## Section E: Statistical Testing & Experimental Methodology (Q73–Q84)

73. **Q73: Why use non-parametric tests (Wilcoxon, Mann–Whitney) instead of $t$-tests?**  
    **A:** Bounded approximation ratios ($r \le 1.0$) and runtimes are heavily skewed and non-Gaussian.
74. **Q74: When do you use Wilcoxon signed-rank vs. Mann–Whitney U?**  
    **A:** Wilcoxon signed-rank for *paired* observations (two solvers on the same instance & seed); Mann–Whitney U for *independent* groups (e.g., Max-Cut vs. Assignment).
75. **Q75: What is Holm–Bonferroni correction and why use it?**  
    **A:** A step-down adjustment that controls family-wise Type I error rate when testing multiple hypotheses simultaneously.
76. **Q76: Give an example where Holm–Bonferroni changed a conclusion in Stage 10.5.**  
    **A:** Standard QAOA Max-Cut vs. Assignment had raw Mann–Whitney $p = 0.0344 < 0.05$, which became $p_{\text{Holm}} = 0.0689$ (non-significant) after correction.
77. **Q77: What is Cohen's $d$?**  
    **A:** Standardized mean difference divided by pooled standard deviation, measuring practical effect size alongside $p$-values.
78. **Q78: What is rank-biserial correlation $r$?**  
    **A:** The non-parametric effect size paired with the Mann–Whitney U test.
79. **Q79: How is dataset integrity guaranteed in Stage 10.2?**  
    **A:** Every canonical instance carries a deterministic generator seed and a SHA-256 fingerprint over sorted JSON.
80. **Q80: What is Tukey's IQR outlier fence in Q-Optimize?**  
    **A:** Flagging trials outside $[Q_1 - 1.5\cdot\text{IQR}, Q_3 + 1.5\cdot\text{IQR}]$ for audit without silently deleting data.
81. **Q81: What seed schedule is used for multi-trial reproducibility?**  
    **A:** `seed_k = 42 + 17 * k` for $k \in \{0, 1, 2\}$.
82. **Q82: Why separate formulation time from solver execution time?**  
    **A:** So QUBO compilation overhead is not misattributed to the optimization algorithm itself.
83. **Q83: What happens if a trial fails during a benchmark?**  
    **A:** The failure is logged in `TrialRecord.error` and reported transparently, never silently omitted.
84. **Q84: How many total benchmark trials and ablation trials were executed in Phase 10?**  
    **A:** `275` benchmark trials (Stage 10.3) and `90` ablation trials (Stage 10.4), plus `26` validation checks (Stage 10.1).

---

## Section F: System Architecture, Security, Deployment & Limitations (Q85–Q105)

85. **Q85: What tech stack powers Q-Optimize?**  
    **A:** FastAPI + Python 3.12 + MongoDB 7.0 + Qiskit Aer + Scikit-Learn + SciPy on backend; React 18 + TypeScript + Vite + Tailwind CSS on frontend.
86. **Q86: How are passwords stored?**  
    **A:** Salted `bcrypt` hashes (cost factor 12); plaintext passwords are never persisted or logged.
87. **Q87: How does authentication work?**  
    **A:** HS256-signed JWT Access Tokens (30 min) and Refresh Tokens (7 days) validated via FastAPI `Depends(get_current_user)`.
88. **Q88: What RBAC roles exist?**  
    **A:** `admin`, `researcher`, and `user`, enforced on backend endpoints via `require_role` and `verify_resource_ownership`.
89. **Q89: How does Q-Optimize prevent horizontal privilege escalation (IDOR)?**  
    **A:** Every private problem/experiment/job checks `owner_id == current_user.id` (unless `admin`), returning `403 Forbidden` otherwise.
90. **Q90: What API protections are active in middleware?**  
    **A:** Token-bucket rate limiting (`20/min` auth, `120/min` general), `10 MB` payload limit (`413`), CORS restrictions, NoSQL `$`-operator sanitization (`400`), and HSTS/CSP/X-Frame-Options headers.
91. **Q91: How are secrets protected in production?**  
    **A:** Pydantic `model_validator` in `config.py` rejects `APP_ENV=production` startup if `DEBUG=True` or `JWT_SECRET_KEY` is weak/default.
92. **Q92: How does `SensitiveDataRedactor` protect logs?**  
    **A:** A custom logging filter scrubs Bearer tokens, passwords, and API keys before log emission.
93. **Q93: How does MongoDB connection reliability work?**  
    **A:** PyMongo pooling (`minPoolSize=5, maxPoolSize=50`), startup unique/composite indexing, health pings, and automatic in-memory fallback when MongoDB is unavailable.
94. **Q94: How does `JobQueueManager` handle heavy compute jobs?**  
    **A:** Bounded `ThreadPoolExecutor` (max 4 workers), per-user quotas, 120s watchdog timeouts, cooperative cancellation tokens, host RAM checks (`psutil` > 90% guard), and a Dead-Letter Queue.
95. **Q95: What Kubernetes health probes are exposed?**  
    **A:** `/health/live` (`3.44 ms` mean), `/health/ready` (`3.38 ms` mean verifying DB readiness), and `/health` (full telemetry).
96. **Q96: What frontend accessibility features were added in Phase 9?**  
    **A:** Per-tab `ErrorBoundary`, responsive mobile drawer, skip-to-main-content link, `:focus-visible` outlines, and `prefers-reduced-motion` CSS support.
97. **Q97: How is Q-Optimize containerized?**  
    **A:** Multi-stage `backend/Dockerfile` (`python:3.12-slim`), multi-stage `frontend/Dockerfile` (`node:20-alpine` $\to$ `nginx:alpine`), and `docker-compose.yml` with `mongo:7.0`.
98. **Q98: What does the GitHub Actions CI workflow run?**  
    **A:** Automated Python 3.12 Pytest (`382` tests), Node 20 Vitest (`61` tests), `tsc --noEmit`, and `vite build` on every push/PR to `main`.
99. **Q99: What load throughput was measured in Stage 9.9?**  
    **A:** `364.0 req/s` across 5 concurrent workers (`13.28 ms` mean latency, `0.0%` error rate).
100. **Q100: What are the total automated tests passing in Q-Optimize?**  
     **A:** **443 passing tests** (`382` backend Pytest + `61` frontend Vitest) with 0 failures and a clean TypeScript build.
101. **Q101: What export formats does Q-Optimize support?**  
     **A:** CSV, JSON, styled Excel (`.xlsx` via `openpyxl`), and publication-grade PDF (`reportlab`).
102. **Q102: Why use in-memory rate limiting vs. Redis?**  
     **A:** Zero external dependency for single-node deployment; Redis is documented as the scaling upgrade path for multi-replica clusters.
103. **Q103: What are the main limitations of Q-Optimize?**  
     **A:** Classical `AerSimulator` only (no physical QPU), small qubit simulation ceiling ($n \le 10$ for multi-trial studies), and tight-budget under-convergence in dynamic depth expansion.
104. **Q104: What is the single biggest engineering lesson from Phase 10?**  
     **A:** Running full end-to-end experiments exposed real integration bugs (e.g., `AdaptiveQAOAResult.best_solution` rejecting Assignment/TSP lists) that isolated unit mocks missed.
105. **Q105: What is the main scientific takeaway of Q-Optimize?**  
     **A:** Mathematical formulation verification, independent evaluators, and Holm–Bonferroni statistical discipline are essential to keep hybrid quantum-classical research honest and reproducible.
