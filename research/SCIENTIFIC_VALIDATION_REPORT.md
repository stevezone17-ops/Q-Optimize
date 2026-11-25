# Stage 10.1 — Final Scientific Validation Report

**Project:** Q-Optimize — AI-Assisted Hybrid Quantum-Classical Optimization Framework  
**Date:** 2026-11-25  
**Validation Script:** `research/scripts/validate_models.py`  
**Raw Evidence Artifact:** `research/results/scientific_validation_results.json`  
**Status:** **PASSED (26 / 26 Checks Verified, 0 Discrepancies)**

---

## 1. Executive Summary

This report documents the independent mathematical and algorithmic validation of all three canonical combinatorial optimization problem families implemented in Q-Optimize:
1. **Max-Cut** (Unweighted, Weighted, Zero-Weight, Negative-Weight, Disconnected)
2. **Linear Assignment Problem** ($2 \times 2$ and $3 \times 3$, Zero-Cost, Negative-Cost, Non-Square Rejection)
3. **Travelling Salesperson Problem (TSP)** (3-City Symmetric & Asymmetric Hamiltonian Cycles)

Exhaustive $2^n$ state-space enumeration via `FormulationVerifier` confirmed exact mathematical equivalence between the canonical problem objective $C(x)$, the upper-triangular QUBO energy $E_{\text{QUBO}}(x)$, and the transformed Ising Hamiltonian energy $H_{\text{Ising}}(Z)$ across **2,168 enumerated binary states**, with a maximum energy discrepancy of **$0.00 \times 10^0$**.

---

## 2. Exhaustive $2^n$ Formulation Verification Results

All QUBO matrices strictly satisfied the upper-triangular storage invariant ($i < j$ in `variable_order`).

| Instance ID | Problem Type | $n$ Vars | States Tested | Feasible States | Max $|E_{\text{QUBO}} - H_{\text{Ising}}|$ | Min $E_{\text{QUBO}}$ | Min $H_{\text{Ising}}$ | Upper-Triangular | Status |
|---|---|---|---|---|---|---|---|---|---|
| `maxcut_k4_unweighted` | `max_cut` | 4 | 16 | 16 | `0.0` | -4.0 | -4.0 | ✅ Valid | ✅ PASS |
| `maxcut_weighted_5node` | `max_cut` | 5 | 32 | 32 | `0.0` | -12.5 | -12.5 | ✅ Valid | ✅ PASS |
| `maxcut_zero_weights` | `max_cut` | 3 | 8 | 8 | `0.0` | 0.0 | 0.0 | ✅ Valid | ✅ PASS |
| `maxcut_negative_weights` | `max_cut` | 4 | 16 | 16 | `0.0` | -7.5 | -7.5 | ✅ Valid | ✅ PASS |
| `maxcut_disconnected` | `max_cut` | 4 | 16 | 16 | `0.0` | -5.0 | -5.0 | ✅ Valid | ✅ PASS |
| `assignment_2x2_standard` | `assignment` | 4 | 16 | 2 | `0.0` | 5.0 | 5.0 | ✅ Valid | ✅ PASS |
| `assignment_3x3_standard` | `assignment` | 9 | 512 | 6 | `0.0` | 9.0 | 9.0 | ✅ Valid | ✅ PASS |
| `assignment_3x3_zero_cost` | `assignment` | 9 | 512 | 6 | `0.0` | 0.0 | 0.0 | ✅ Valid | ✅ PASS |
| `assignment_2x2_negative_cost` | `assignment` | 4 | 16 | 2 | `0.0` | -13.0 | -13.0 | ✅ Valid | ✅ PASS |
| `tsp_3city_symmetric` | `tsp` | 9 | 512 | 6 | `0.0` | 45.0 | 45.0 | ✅ Valid | ✅ PASS |
| `tsp_3city_asymmetric` | `tsp` | 9 | 512 | 6 | `0.0` | 20.0 | 20.0 | ✅ Valid | ✅ PASS |

### Key Mathematical Findings
1. **Max-Cut Sign Convention:** For all Max-Cut instances (including zero-weight, mixed-sign negative weights, and disconnected components), $E_{\text{QUBO}}(x) = -C_{\text{cut}}(x)$ holds exactly across every binary partition.
2. **Constraint Penalty Sufficiency:** For all constrained Assignment and TSP instances, every infeasible bitstring incurs strictly positive penalty energy, ensuring $\min_{x \in \mathcal{S}_{\text{infeasible}}} E_{\text{QUBO}}(x) > \min_{x \in \mathcal{S}_{\text{feasible}}} E_{\text{QUBO}}(x)$, while feasible permutations incur zero penalty ($E_{\text{QUBO}}(x) = C_{\text{orig}}(x)$).

---

## 3. Negative & Infeasible Edge-Case Validation

| Edge Case | Expected Behavior | Observed Result | Status |
|---|---|---|---|
| **Non-Square Assignment ($2 \times 3$)** | Reject rectangular matrix with explicit `ValueError` | Raised `ValueError`: *"Standard 1-to-1 matching equality constraints require square dimensions..."* | ✅ PASS |
| **Infeasible Assignment (Duplicate Task)** | Flag `is_feasible = False` with structured violations | Detected `TASK_DUPLICATE_ASSIGNMENT` and `UNASSIGNED_TASK` | ✅ PASS |
| **Infeasible TSP (Duplicate City)** | Flag `is_feasible = False` with structured violations | Detected `DUPLICATE_CITY_VISIT` and `OMITTED_CITIES` | ✅ PASS |

---

## 4. End-to-End Solver & Independent Evaluator Parity

Each solver (`exact`, `simulated_annealing`, `genetic_algorithm`, and `qaoa_aer_p1` executed on Qiskit `AerSimulator` with `shots=512, p=1, max_evaluations=30, seed=42`) was evaluated against the independent Phase 2 domain evaluators (`EvaluatorFactory`).

| Instance | Solver | Reported Obj | Independent Evaluator Obj | QUBO Energy | Ising Energy | Feasible | Parity |
|---|---|---|---|---|---|---|---|
| `maxcut_4node` | `exact` | 10.0 | 10.0 | — | — | ✅ | ✅ Exact Match |
| `maxcut_4node` | `simulated_annealing` | 10.0 | 10.0 | — | — | ✅ | ✅ Exact Match |
| `maxcut_4node` | `genetic_algorithm` | 10.0 | 10.0 | — | — | ✅ | ✅ Exact Match |
| `maxcut_4node` | `qaoa_aer_p1` (Aer) | 10.0 | 10.0 | -10.0 | -10.0 | ✅ | ✅ Exact Match |
| `assignment_3x3` | `exact` | 9.0 | 9.0 | — | — | ✅ | ✅ Exact Match |
| `assignment_3x3` | `simulated_annealing` | 9.0 | 9.0 | — | — | ✅ | ✅ Exact Match |
| `assignment_3x3` | `genetic_algorithm` | 9.0 | 9.0 | — | — | ✅ | ✅ Exact Match |
| `assignment_3x3` | `qaoa_aer_p1` (Aer) | 10.0 | 10.0 | 10.0 | 10.0 | ✅ | ✅ Exact Match |
| `tsp_3city` | `exact` | 45.0 | 45.0 | — | — | ✅ | ✅ Exact Match |
| `tsp_3city` | `simulated_annealing` | 45.0 | 45.0 | — | — | ✅ | ✅ Exact Match |
| `tsp_3city` | `genetic_algorithm` | 45.0 | 45.0 | — | — | ✅ | ✅ Exact Match |
| `tsp_3city` | `qaoa_aer_p1` (Aer) | 45.0 | 45.0 | 45.0 | 45.0 | ✅ | ✅ Exact Match |

*Note: On `assignment_3x3` ($n=9$ qubits), shallow `qaoa_aer_p1` ($p=1$, 30 evaluations) converged to a feasible assignment of cost `10.0` (vs. exact optimum `9.0`), demonstrating honest simulator behavior while maintaining exact QUBO/Ising/evaluator parity (`10.0 == 10.0 == 10.0`).*

---

## 5. Conclusion

All mathematical models, QUBO/Ising mappings, constraint penalties, edge-case guards, and independent solution evaluators are verified mathematically sound with zero discrepancies.
