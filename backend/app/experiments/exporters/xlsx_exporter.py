"""Excel (.xlsx) exporter for experiment runs and results."""

import io
from typing import BinaryIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from backend.app.experiments.models import Experiment


def export_experiment_xlsx(experiment: Experiment) -> bytes:
    """Generate a multi-sheet styled Excel workbook for the experiment."""
    wb = openpyxl.Workbook()

    # Sheet 1: Summary & Metadata
    ws_meta = wb.active
    ws_meta.title = "Summary"

    header_font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")

    ws_meta.append(["Attribute", "Value"])
    for cell in ws_meta[1]:
        cell.font = header_font
        cell.fill = header_fill

    meta_rows = [
        ["Experiment ID", experiment.experiment_id],
        ["Experiment Name", experiment.name],
        ["Status", experiment.status.value],
        ["Problem Class", experiment.configuration.problem_type],
        ["Number of Trials", experiment.configuration.num_trials],
        ["Algorithms Evaluated", ", ".join(a.value for a in experiment.configuration.algorithms)],
        ["Reproducibility Hash", experiment.metadata.reproducibility_hash],
        ["Python Version", experiment.metadata.python_version],
        ["Created At", experiment.metadata.created_at.isoformat()],
        ["Completed At", experiment.metadata.completed_at.isoformat() if experiment.metadata.completed_at else ""],
    ]
    for row in meta_rows:
        ws_meta.append(row)

    ws_meta.column_dimensions["A"].width = 25
    ws_meta.column_dimensions["B"].width = 50

    # Sheet 2: Trial Results
    ws_results = wb.create_sheet(title="Trial Results")
    res_headers = [
        "Algorithm",
        "Trial",
        "Seed",
        "Status",
        "Objective Value",
        "Runtime (s)",
        "Feasible",
        "Evaluations",
        "Error",
    ]
    ws_results.append(res_headers)
    for cell in ws_results[1]:
        cell.font = header_font
        cell.fill = header_fill

    for r in experiment.results:
        ws_results.append([
            r.algorithm,
            r.trial_index,
            r.seed if r.seed is not None else "",
            r.status,
            r.objective_value if r.objective_value is not None else "",
            round(r.runtime_seconds, 6),
            "Yes" if r.is_feasible else "No",
            r.num_evaluations,
            r.error or "",
        ])

    for col in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]:
        ws_results.column_dimensions[col].width = 18

    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()
