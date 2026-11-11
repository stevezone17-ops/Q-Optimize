"""PDF research report generator using reportlab."""

import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.app.experiments.models import Experiment
from backend.app.experiments.statistics import statistical_analyzer


def generate_experiment_pdf_report(experiment: Experiment) -> bytes:
    """Generate a publication-grade PDF research summary report for an experiment."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#3b82f6"),
        spaceBefore=14,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    caption_style = ParagraphStyle(
        "ReportCaption",
        parent=styles["Italic"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=8,
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Q-Optimize Scientific Research Report", title_style))
    story.append(
        Paragraph(
            f"<b>Experiment:</b> {experiment.name} &bull; <b>Problem:</b> {experiment.configuration.problem_type.upper()} &bull; <b>Status:</b> {experiment.status.value.upper()}",
            body_style,
        )
    )
    story.append(
        Paragraph(
            f"<b>SHA-256 Reproducibility Fingerprint:</b> {experiment.metadata.reproducibility_hash}",
            caption_style,
        )
    )
    story.append(Spacer(1, 10))

    # Executive Summary
    story.append(Paragraph("1. Executive Summary", h2_style))
    summary_text = (
        f"This report presents empirical benchmark performance evaluation for '{experiment.name}' across "
        f"{len(experiment.configuration.algorithms)} algorithm(s) and {experiment.configuration.num_trials} trial(s) per configuration. "
        "Evaluations include classical heuristics and quantum variational algorithms executed on Qiskit Aer statevector simulators."
    )
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 8))

    # Performance Table
    story.append(Paragraph("2. Algorithm Comparative Performance Table", h2_style))

    table_data = [
        ["Algorithm", "Trials", "Best Obj", "Mean Obj", "Std", "Mean Time (s)", "Feasibility"],
    ]

    by_algo = {}
    for r in experiment.results:
        by_algo.setdefault(r.algorithm, []).append(r)

    for algo, runs in by_algo.items():
        objs = [r.objective_value for r in runs if r.objective_value is not None]
        rts = [r.runtime_seconds for r in runs]
        feas = [r.is_feasible for r in runs]
        evals = [r.num_evaluations for r in runs]

        if objs:
            m = statistical_analyzer.compute_metrics(objs, rts, feas, evals)
            table_data.append([
                algo.replace("_", " ").title(),
                str(m.get("n_trials", 0)),
                f"{m.get('best_objective', 0.0):.2f}",
                f"{m.get('mean_objective', 0.0):.2f}",
                f"{m.get('std_objective', 0.0):.2f}",
                f"{m.get('mean_runtime_seconds', 0.0):.4f}",
                f"{m.get('feasibility_rate', 0.0) * 100:.0f}%",
            ])
        else:
            table_data.append([algo, str(len(runs)), "N/A", "N/A", "N/A", "N/A", "0%"])

    t = Table(table_data, colWidths=[120, 45, 60, 60, 50, 75, 65])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(t)
    story.append(Spacer(1, 10))

    # Reproducibility & Environment Note
    story.append(Paragraph("3. Provenance & Execution Integrity", h2_style))
    story.append(
        Paragraph(
            f"<b>Platform:</b> {experiment.metadata.platform or 'Windows/Linux x86_64'} &bull; "
            f"<b>Python Version:</b> {experiment.metadata.python_version.split()[0] if experiment.metadata.python_version else '3.12'} &bull; "
            f"<b>Quantum Target:</b> Qiskit Aer Statevector Simulation (CPU). No quantum supremacy or advantage claimed.",
            body_style,
        )
    )

    doc.build(story)
    return buffer.getvalue()
