# Stage 10.9 — Final Demonstration Guide

**Project:** Q-Optimize — AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Target Duration:** 12–15 minutes (Live University Evaluation)

---

## Pre-Demo Verification (5 Minutes Prior)

1. Ensure backend (`uvicorn backend.app.main:app --port 8000`) and frontend (`npm run dev --prefix frontend`) are running, or launch via `docker-compose up -d`.
2. Verify health probes: `GET http://localhost:8000/health/live` and `GET http://localhost:8000/health/ready` return `200 OK`.
3. Use small, deterministic instances (`4-node Max-Cut` or `3x3 Assignment`) so every solver completes in **< 2 seconds**.

---

## 12-Step Live Demonstration Script

| Step | Feature Area | Action to Perform | Expected Outcome |
|---|---|---|---|
| **1** | **Application Login** | Open `http://localhost:5173`, register/login as Researcher via `AuthModal` | JWT Access/Refresh tokens issued; user badge appears in Header |
| **2** | **Dashboard Overview** | Inspect Overview metrics & system health indicator | Green API health status; 9 workspace navigation tabs visible |
| **3** | **Problem Creation** | Open **Problem Builder** → Select **Max-Cut** → Create 4-node graph (`A-B: 2, B-C: 3, C-D: 1, D-A: 4, A-C: 1.5`) | Problem saved and listed; canonical validation passes |
| **4** | **QUBO Generation** | Open **Formulation Studio** → Select the 4-node Max-Cut → Click **Generate QUBO** | Upper-triangular QUBO heatmap ($4\times 4$) rendered ($E = -C$) |
| **5** | **Ising Conversion** | Switch to **Ising Inspector** & **Verification** tabs → Run exhaustive verification | `h_i`, `J_ij`, offset $C$ displayed; 16/16 states verified (`0.00` discrepancy) |
| **6** | **Classical Optimization** | Open **Classical Lab** → Run **Exact Solver**, then **Simulated Annealing** (`seed=42`) | Optimal cut `10.0` returned in `< 0.05s` with feasibility verified |
| **7** | **Standard QAOA** | Open **Quantum Lab** → Select `p=1`, `shots=512`, `COBYLA`, `max_evals=30` → Run | `AerSimulator` executes circuit; returns cut `10.0` + bitstring distribution |
| **8** | **Adaptive QAOA** | Switch to **Adaptive QAOA Lab** → Run `FULL_ADAPTIVE` ($p=1\to 2$) | Convergence curve & decision log displayed; hardware note shown |
| **9** | **AI Solver Recommendation** | Click **Recommend Solver** on the 4-node problem | `IntelligentSolverRecommender` explains 18 features & recommends `exact` (~1 ms) |
| **10** | **Experiment Benchmarking** | Open **Experiments Dashboard** → Launch multi-algorithm benchmark (SA, GA, QAOA) | Parallel trials complete with live progress & trial table |
| **11** | **Statistical Comparison** | View **Statistical BoxPlot** & comparison charts | Mean, std, 95% CI, and non-parametric comparison rendered |
| **12** | **Research Report Export** | Click **Export PDF / CSV / XLSX** on the completed experiment | Publication-grade PDF / styled Excel workbook downloads cleanly |
