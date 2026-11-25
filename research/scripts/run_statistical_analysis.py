"""Stage 10.5 — Statistical Validation of Research Findings.

Reads Stage 10.3 raw trial records (classical_vs_quantum_benchmark.json),
computes descriptive metrics + 95% confidence intervals, runs paired Wilcoxon
signed-rank tests, independent Mann-Whitney U tests, Cohen's d, rank-biserial r,
and applies Holm-Bonferroni multiple-comparison correction.

Saves results to: research/results/statistical_analysis_results.json
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.experiments.statistics import (
    _mean,
    _median,
    _std,
    _t_confidence_interval,
    cohens_d,
    mann_whitney_u,
    wilcoxon_signed_rank,
)


def _holm_bonferroni(tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply Holm-Bonferroni step-down adjustment to valid p-values."""
    valid_indices = [
        i for i, t in enumerate(tests)
        if t.get("p_value") is not None and not math.isnan(t["p_value"])
    ]
    sorted_idx = sorted(valid_indices, key=lambda i: tests[i]["p_value"])
    m = len(sorted_idx)
    running_max = 0.0
    for rank_0, idx in enumerate(sorted_idx):
        adj = min(1.0, tests[idx]["p_value"] * (m - rank_0))
        running_max = max(running_max, adj)
        tests[idx]["p_adjusted_holm"] = round(running_max, 6)
        tests[idx]["significant_alpha_05"] = running_max < 0.05
    for i, t in enumerate(tests):
        if i not in valid_indices:
            t["p_adjusted_holm"] = None
            t["significant_alpha_05"] = False
    return tests


def _clean_num(val: float, digits: int = 6) -> Any:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    return round(float(val), digits)


def main() -> None:
    bm_path = REPO_ROOT / "research" / "results" / "classical_vs_quantum_benchmark.json"
    bm = json.loads(bm_path.read_text(encoding="utf-8"))
    trials = bm["trial_records"]

    # 1. Descriptive statistics & 95% CIs by (problem_type, solver)
    descriptive: List[Dict[str, Any]] = []
    ptypes = ["max_cut", "assignment", "tsp"]
    solvers = ["exact", "simulated_annealing", "genetic_algorithm", "standard_qaoa", "adaptive_qaoa"]

    for pt in ptypes:
        for sol in solvers:
            sub = [r for r in trials if r["problem_type"] == pt and r["solver"] == sol]
            if not sub:
                continue
            ratios = [r["approximation_ratio"] for r in sub if r["approximation_ratio"] is not None]
            gaps = [r["optimality_gap_pct"] for r in sub if r["optimality_gap_pct"] is not None]
            rts = [r["runtime_seconds"] for r in sub]
            ci_r = _t_confidence_interval(ratios) if len(ratios) >= 2 else (float("nan"), float("nan"))
            ci_rt = _t_confidence_interval(rts) if len(rts) >= 2 else (float("nan"), float("nan"))

            descriptive.append({
                "problem_type": pt,
                "solver": sol,
                "n_trials": len(sub),
                "approx_ratio_mean": _clean_num(_mean(ratios), 4),
                "approx_ratio_median": _clean_num(_median(ratios), 4),
                "approx_ratio_std": _clean_num(_std(ratios), 4),
                "approx_ratio_ci95": [_clean_num(ci_r[0], 4), _clean_num(ci_r[1], 4)],
                "gap_pct_mean": _clean_num(_mean(gaps), 4),
                "runtime_mean_s": _clean_num(_mean(rts), 4),
                "runtime_std_s": _clean_num(_std(rts), 4),
                "runtime_ci95_s": [_clean_num(ci_rt[0], 4), _clean_num(ci_rt[1], 4)],
            })

    # Index paired trials by (instance_id, trial, solver)
    by_key: Dict[Tuple[str, int, str], Dict[str, Any]] = {
        (r["instance_id"], r["trial"], r["solver"]): r for r in trials
    }
    paired_keys = sorted({(r["instance_id"], r["trial"]) for r in trials if r["qubo_variables"] <= 10 and r["solver"] != "exact"})

    def get_paired_vectors(sol_a: str, sol_b: str, metric: str) -> Tuple[List[float], List[float]]:
        va, vb = [], []
        for inst_id, tr in paired_keys:
            ra = by_key.get((inst_id, tr, sol_a))
            rb = by_key.get((inst_id, tr, sol_b))
            if ra and rb and ra.get(metric) is not None and rb.get(metric) is not None:
                va.append(float(ra[metric]))
                vb.append(float(rb[metric]))
        return va, vb

    hypothesis_tests: List[Dict[str, Any]] = []

    # Paired tests
    paired_specs = [
        ("SA vs Standard QAOA (Approx. Ratio)", "simulated_annealing", "standard_qaoa", "approximation_ratio"),
        ("SA vs Adaptive QAOA (Approx. Ratio)", "simulated_annealing", "adaptive_qaoa", "approximation_ratio"),
        ("Standard QAOA vs Adaptive QAOA (Approx. Ratio)", "standard_qaoa", "adaptive_qaoa", "approximation_ratio"),
        ("Standard QAOA vs Adaptive QAOA (Runtime s)", "standard_qaoa", "adaptive_qaoa", "runtime_seconds"),
        ("SA vs Genetic Algorithm (Runtime s)", "simulated_annealing", "genetic_algorithm", "runtime_seconds"),
    ]
    for label, sa, sb, metric in paired_specs:
        va, vb = get_paired_vectors(sa, sb, metric)
        w_res = wilcoxon_signed_rank(va, vb)
        d_val = cohens_d(va, vb)
        hypothesis_tests.append({
            "comparison": label,
            "design": "paired",
            "test": "wilcoxon_signed_rank",
            "n_pairs": len(va),
            "mean_a": _clean_num(_mean(va), 4),
            "mean_b": _clean_num(_mean(vb), 4),
            "statistic": _clean_num(w_res.get("statistic"), 4),
            "p_value": w_res.get("p_value") if w_res.get("p_value") == w_res.get("p_value") else None,
            "cohens_d": _clean_num(d_val, 4),
            "error": w_res.get("error"),
        })

    # Independent-sample Mann-Whitney U tests across problem families
    qaoa_mc_r = [
        r["approximation_ratio"] for r in trials
        if r["problem_type"] == "max_cut" and r["solver"] == "standard_qaoa" and r["approximation_ratio"] is not None
    ]
    qaoa_asg_r = [
        r["approximation_ratio"] for r in trials
        if r["problem_type"] == "assignment" and r["solver"] == "standard_qaoa" and r["approximation_ratio"] is not None
    ]
    mw1 = mann_whitney_u(qaoa_mc_r, qaoa_asg_r)
    hypothesis_tests.append({
        "comparison": "Standard QAOA Approx. Ratio: Max-Cut vs Assignment",
        "design": "independent",
        "test": "mann_whitney_u",
        "n_a": len(qaoa_mc_r),
        "n_b": len(qaoa_asg_r),
        "mean_a": _clean_num(_mean(qaoa_mc_r), 4),
        "mean_b": _clean_num(_mean(qaoa_asg_r), 4),
        "statistic": _clean_num(mw1.get("statistic"), 4),
        "p_value": mw1.get("p_value") if mw1.get("p_value") == mw1.get("p_value") else None,
        "effect_size_r": _clean_num(mw1.get("effect_size_r"), 4),
        "cohens_d": _clean_num(cohens_d(qaoa_mc_r, qaoa_asg_r), 4),
        "error": mw1.get("error"),
    })

    hypothesis_tests = _holm_bonferroni(hypothesis_tests)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "descriptive_statistics": descriptive,
        "hypothesis_tests": hypothesis_tests,
    }
    out_path = REPO_ROOT / "research" / "results" / "statistical_analysis_results.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Saved Stage 10.5 statistical analysis ->", out_path)
    for ht in hypothesis_tests:
        print(
            f"  {ht['comparison']} | stat={ht['statistic']} | p={ht['p_value']} | "
            f"p_holm={ht['p_adjusted_holm']} | sig={ht['significant_alpha_05']}"
        )


if __name__ == "__main__":
    main()
