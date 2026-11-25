"""Stage 10.9 — Build 20-Slide Final Project Presentation (.pptx) using python-pptx."""

from __future__ import annotations

from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PPTX = REPO_ROOT / "research" / "FINAL_PROJECT_PRESENTATION.pptx"
FIG_DIR = REPO_ROOT / "research" / "figures"

BG_DARK = RGBColor(15, 23, 42)
ACCENT_BLUE = RGBColor(56, 189, 248)
TEXT_WHITE = RGBColor(248, 250, 252)
TEXT_MUTED = RGBColor(203, 213, 225)


def _style_slide_bg(slide) -> None:
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_DARK


def add_bullet_slide(prs: Presentation, title: str, bullets: list[str], fig_name: str | None = None) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _style_slide_bg(slide)

    tb_title = slide.shapes.add_textbox(Inches(0.6), Inches(0.35), Inches(12.1), Inches(0.8))
    tf_t = tb_title.text_frame
    tf_t.word_wrap = True
    p_t = tf_t.paragraphs[0]
    p_t.text = title
    p_t.font.size = Pt(26)
    p_t.font.bold = True
    p_t.font.color.rgb = ACCENT_BLUE

    text_width = Inches(5.8) if fig_name else Inches(12.0)
    tb_body = slide.shapes.add_textbox(Inches(0.6), Inches(1.3), text_width, Inches(5.6))
    tf_b = tb_body.text_frame
    tf_b.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf_b.paragraphs[0] if i == 0 else tf_b.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(16 if fig_name else 18)
        p.font.color.rgb = TEXT_WHITE
        p.space_after = Pt(10)

    if fig_name:
        fpath = FIG_DIR / fig_name
        if fpath.exists():
            slide.shapes.add_picture(str(fpath), Inches(6.6), Inches(1.4), width=Inches(6.2))


def main() -> None:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Slide 1: Title Slide
    s1 = prs.slides.add_slide(prs.slide_layouts[6])
    _style_slide_bg(s1)
    tb = s1.shapes.add_textbox(Inches(0.9), Inches(1.8), Inches(11.5), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = "Q-OPTIMIZE"
    p0.font.size = Pt(44)
    p0.font.bold = True
    p0.font.color.rgb = ACCENT_BLUE
    p1 = tf.add_paragraph()
    p1.text = "An AI-Assisted Hybrid Quantum-Classical Optimization Framework with Adaptive QAOA and Intelligent Solver Selection"
    p1.font.size = Pt(24)
    p1.font.color.rgb = TEXT_WHITE
    p1.space_before = Pt(16)
    p2 = tf.add_paragraph()
    p2.text = "Final-Year B.Tech CSE Project Defense  |  November 2026  |  443 Automated Tests Passing"
    p2.font.size = Pt(16)
    p2.font.color.rgb = TEXT_MUTED
    p2.space_before = Pt(28)

    slides_spec = [
        ("2. Problem Statement", [
            "Combinatorial optimization (Max-Cut, Assignment, TSP) is NP-hard and underpins routing, scheduling, and network design.",
            "Existing quantum/classical toolkits lack unified formulation verification, independent evaluation, and fair cross-paradigm benchmarking.",
            "Researchers need an end-to-end platform enforcing mathematical correctness and honest statistical comparison."
        ], None),
        ("3. Motivation", [
            "Prevent silent QUBO penalty errors and unverified bitstring decoding.",
            "Compare Exact, Simulated Annealing, Genetic Algorithm, and QAOA under explicit computational budgets.",
            "Provide AI-assisted solver guidance with out-of-distribution (OOD) safeguards.",
            "Maintain strict scientific transparency: AerSimulator CPU emulation vs. physical quantum hardware."
        ], None),
        ("4. Existing System Limitations", [
            "Fragmented scripts without canonical schemas or SHA-256 dataset provenance.",
            "Trusting solver self-reported scores instead of independent constraint evaluators.",
            "Lack of multiple-comparison statistical correction (Holm-Bonferroni).",
            "Missing production hardening (RBAC, rate limiting, bounded job queues, Docker/CI)."
        ], None),
        ("5. Proposed Solution: Q-Optimize", [
            "Full-stack web platform: React 18 + TypeScript UI and FastAPI + MongoDB 7.0 backend.",
            "Canonical problem modeling with independent Phase 2 evaluators.",
            "Upper-triangular QUBO & analytical Ising compiler with 2^n exhaustive verification.",
            "Classical, Standard QAOA, Adaptive QAOA (6 ablation variants), and 18-feature AI recommender."
        ], None),
        ("6. Project Objectives", [
            "Model Max-Cut, Linear Assignment, and TSP with strict constraint validation.",
            "Verify QUBO/Ising mathematical equivalence across 2^n states (n <= 12).",
            "Benchmark 5 solver paradigms across reproducible SHA-256 fingerprinted datasets.",
            "Evaluate Adaptive QAOA ablations, statistical validity, and production readiness."
        ], None),
        ("7. System Architecture", [
            "Presentation Layer: React 18, TypeScript, Tailwind CSS, SVG visualizers, ErrorBoundaries.",
            "Security & API Layer: JWT/bcrypt RBAC, token-bucket rate limiter, 10MB limit, HSTS/CSP.",
            "Compute Layer: ClassicalSolverFactory, QAOA & Adaptive QAOA (AerSimulator), IntelligentSolverRecommender.",
            "Reliability Layer: JobQueueManager (DLQ, timeouts), MongoDB pooling + in-memory fallback, Docker Compose."
        ], None),
        ("8. Mathematical Foundation (Stage 10.1)", [
            "11 exhaustive verification instances (2,168 binary states): 0.00 max |E_QUBO - H_Ising|.",
            "Verified zero-weight, negative-weight, disconnected graphs, and non-square matrix rejection.",
            "12/12 end-to-end solver parity checks matched independent domain evaluators."
        ], "fig12_problem_solution_visualization.png"),
        ("9. QUBO & Ising Formulation", [
            "Upper-triangular QUBO invariant (i < j) eliminates off-diagonal double counting.",
            "Analytical spin mapping: x_i = (1 - Z_i) / 2 preserves exact energy spectrum.",
            "Penalty sufficiency checks guarantee infeasible states exceed optimal feasible energy."
        ], None),
        ("10. Classical Optimization Algorithms", [
            "Exact Solver: Branch-and-bound / enumeration (0.00% gap in < 0.004s for n <= 16).",
            "Simulated Annealing: 250 iterations, geometric cooling -> 100% feasibility, 0.00% gap.",
            "Genetic Algorithm: Population 30, 80 generations -> 100% feasibility, 0.00% gap (slower than SA)."
        ], "fig02_execution_time_comparison.png"),
        ("11. Quantum Approximate Optimization Algorithm (QAOA)", [
            "Alternates p layers of cost U(H_C, gamma) and mixer U(H_M, beta) unitaries.",
            "Simulated classically via Qiskit AerSimulator (512 shots, COBYLA, 40 evals).",
            "Reached 0.00% gap on unweighted Max-Cut (n=6, 8) and 3-city TSP (n=9)."
        ], "fig05_qaoa_convergence_curve.png"),
        ("12. Adaptive QAOA", [
            "Integrates linear-ramp/Fourier/warm-start initializers, dynamic depth (p=1->2), and COBYLA->Nelder-Mead switching.",
            "Achieved 0.00% gap on weighted N=8 Max-Cut (vs 0.11% Standard QAOA).",
            "Parameter transfer (i1 -> i2) preserved r=1.0000 with faster runtime (297.98 ms vs 317.83 ms)."
        ], "fig06_adaptive_qaoa_convergence_curve.png"),
        ("13. AI-Assisted Solver Recommendation", [
            "Extracts 18 structural and QUBO features in 1.153 ms mean latency.",
            "Out-of-distribution (OOD) z-score check (> 3.5) triggers safe rule-based fallback.",
            "Selected Exact Solver on 23/23 tractable instances (0.00% decision regret)."
        ], None),
        ("14. Experiments & Reproducible Datasets", [
            "9 dataset families (23 canonical instances) with deterministic seeds and SHA-256 fingerprints.",
            "275 controlled benchmark trials + 90 Adaptive QAOA ablation trials executed.",
            "Fixed per-trial seed offsets (42, 59, 76) and paired instance evaluation."
        ], "fig10_scalability_analysis.png"),
        ("15. Experimental Results: Classical vs. Quantum", [
            "SA & GA achieved r = 1.0000 across all 9 families (including 16-qubit Assignment/TSP).",
            "Standard QAOA achieved r = 0.9950 on Max-Cut and r = 0.9296 on 3x3 Assignment.",
            "Under 50-eval budget, Standard QAOA beat Adaptive QAOA on N=10 Max-Cut & 3x3 uniform Assignment."
        ], "fig01_objective_comparison.png"),
        ("16. Adaptive QAOA Ablation Study", [
            "Removing warm starts degraded 3x3 Assignment ratio from 0.9145 to 0.8763.",
            "Fourier parameterization achieved lowest eval counts & runtimes (284-299 ms) on Max-Cut/TSP.",
            "1/90 trial failure (angle mismatch on depth transition) transparently reported."
        ], "fig09_ablation_study_comparison.png"),
        ("17. Statistical Analysis (Holm-Bonferroni)", [
            "SA significantly outperformed Standard QAOA (p_Holm=0.0132) & Adaptive QAOA (p_Holm=0.0229).",
            "Pooled Standard vs Adaptive QAOA ratio difference is not significant (p_Holm=0.3256).",
            "Max-Cut vs Assignment QAOA raw p=0.0344 did not survive Holm correction (p_Holm=0.0689)."
        ], "fig11_statistical_distribution_plots.png"),
        ("18. Live Application Demonstration & Production Readiness", [
            "443 passing automated tests (382 Pytest + 61 Vitest) and clean Vite build (119 kB gzip JS).",
            "Load test verified 364.0 req/s throughput with 0% error rate; probes < 5 ms.",
            "Full Docker Compose stack + GitHub Actions CI + CSV/JSON/XLSX/PDF exports."
        ], None),
        ("19. Limitations & Honest Disclosure", [
            "All quantum results use classical Qiskit AerSimulator (no physical QPU speedup claimed).",
            "Multi-trial QAOA capped at n <= 10 qubits due to 2^n classical simulation scaling.",
            "In-memory rate limiter requires Redis for multi-replica horizontal scaling."
        ], None),
        ("20. Conclusion & Future Scope", [
            "Delivered a mathematically verified, secure, containerized, and statistically rigorous framework.",
            "Future: Fix dynamic-depth angle resize edge case, add IBM/Braket hardware connectors, and scale via Celery/Redis.",
            "Thank you! Ready for Live Demonstration & Viva Questions."
        ], None),
    ]

    for title, bullets, fig_name in slides_spec:
        add_bullet_slide(prs, title, bullets, fig_name)

    prs.save(str(OUT_PPTX))
    print(f"Generated 20-slide presentation -> {OUT_PPTX}")


if __name__ == "__main__":
    main()
