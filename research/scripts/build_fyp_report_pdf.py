"""Stage 10.7 — Generate PDF version of the Final-Year Project Report using ReportLab."""

from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_PDF = REPO_ROOT / "research" / "FINAL_YEAR_PROJECT_REPORT.pdf"
FIG_DIR = REPO_ROOT / "research" / "figures"


def build_pdf() -> None:
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="Q-Optimize Final Year Project Report",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=18, spaceAfter=14, textColor=colors.HexColor("#0f172a"))
    h1 = ParagraphStyle("H1Custom", parent=styles["Heading1"], fontSize=14, spaceBefore=14, spaceAfter=8, textColor=colors.HexColor("#1e3a8a"))
    body = ParagraphStyle("BodyCustom", parent=styles["Normal"], fontSize=10, leading=14, spaceAfter=8)

    story = []
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("Q-OPTIMIZE: AN AI-ASSISTED HYBRID QUANTUM-CLASSICAL OPTIMIZATION FRAMEWORK WITH ADAPTIVE QAOA AND INTELLIGENT SOLVER SELECTION", title_style))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("<b>Final-Year Engineering Project Report</b><br/>Bachelor of Technology in Computer Science and Engineering<br/>Repository: https://github.com/stevezone17-ops/Q-Optimize<br/>November 2026", body))
    story.append(PageBreak())

    sections = [
        ("Abstract", "Q-Optimize is a production-hardened hybrid quantum-classical optimization platform unifying Max-Cut, Linear Assignment, and TSP modeling, upper-triangular QUBO/Ising compilers, Classical (Exact, SA, GA) and Quantum (Standard & Adaptive QAOA on Qiskit AerSimulator) solvers, an 18-feature AI recommender, and Holm-Bonferroni statistical evaluation. Exhaustive 2^n verification across 2,168 binary states confirmed 0.00 energy discrepancy, while 275 controlled benchmark trials and 443 automated software tests validated system integrity."),
        ("1. System Architecture & Mathematical Foundations", "The platform integrates a React 18 + TypeScript SPA with a FastAPI + MongoDB 7.0 backend protected by JWT/bcrypt RBAC, rate limiting, and bounded background job queues. Binary variables map to Pauli-Z spins via x_i = (1 - Z_i)/2, with independent Phase 2 domain evaluators verifying every solver output."),
        ("2. Experimental & Statistical Findings", "Simulated Annealing achieved 100% feasibility and 0.00% optimality gap across all 9 dataset families (mean runtime 0.0443s on paired trials), significantly outperforming shallow QAOA simulation in approximation ratio (p_Holm = 0.0132). Standard QAOA vs. Adaptive QAOA showed no significant pooled ratio difference (p_Holm = 0.3256) under a 40-50 evaluation budget, while Fourier parameterization consistently minimized evaluation counts. All QAOA runs were executed on classical Qiskit AerSimulator."),
    ]
    for heading, text in sections:
        story.append(Paragraph(heading, h1))
        story.append(Paragraph(text, body))

    # Summary Table
    story.append(Paragraph("3. Key Empirical Summary Table", h1))
    table_data = [
        ["Comparison / Metric", "Sample / Scope", "Key Verified Result"],
        ["Exhaustive QUBO-Ising Equivalence", "11 instances (2,168 states)", "0.00 max energy discrepancy (11/11 PASS)"],
        ["SA vs. Standard QAOA (Approx. Ratio)", "57 paired trials (Wilcoxon)", "1.0000 vs 0.9786 (p_Holm = 0.0132, sig)"],
        ["Standard vs. Adaptive QAOA (Ratio)", "57 paired trials (Wilcoxon)", "0.9786 vs 0.9551 (p_Holm = 0.3256, n.s.)"],
        ["AI Solver Recommender", "23 canonical instances", "100% optimal choice (1.153 ms mean latency)"],
        ["Automated Software Test Suite", "Backend + Frontend", "382 Pytest + 61 Vitest = 443 Passing"],
    ]
    tbl = Table(table_data, colWidths=[2.3 * inch, 1.8 * inch, 2.5 * inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.25 * inch))

    # Embed key figures
    for fig_name, caption in [
        ("fig01_objective_comparison.png", "Figure 1: Classical vs. Quantum (AerSimulator) Objective Quality Comparison."),
        ("fig09_ablation_study_comparison.png", "Figure 9: 6-Variant Adaptive QAOA Ablation Comparison Across 5 Instances."),
        ("fig12_problem_solution_visualization.png", "Figure 12: Problem-Specific Optimal Solution Visualizations."),
    ]:
        fpath = FIG_DIR / fig_name
        if fpath.exists():
            story.append(Image(str(fpath), width=6.4 * inch, height=2.9 * inch))
            story.append(Paragraph(f"<i>{caption}</i>", body))
            story.append(Spacer(1, 0.15 * inch))

    doc.build(story)
    print(f"Generated PDF report -> {OUT_PDF}")


if __name__ == "__main__":
    build_pdf()
