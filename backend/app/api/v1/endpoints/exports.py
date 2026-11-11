"""Experiment export endpoints — CSV, JSON, XLSX, PDF, and Research Report."""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.experiment_exceptions import ExperimentNotFoundError
from backend.app.experiments.exporters.csv_exporter import export_experiment_csv
from backend.app.experiments.exporters.json_exporter import export_experiment_json
from backend.app.experiments.exporters.xlsx_exporter import export_experiment_xlsx
from backend.app.experiments.exporters.pdf_reporter import generate_experiment_pdf_report
from backend.app.experiments.exporters.report_generator import generate_research_report, ResearchReport

router = APIRouter(prefix="/exports", tags=["Exports & Reports"])


@router.get("/experiments/{experiment_id}/csv", response_class=PlainTextResponse)
async def get_experiment_csv(experiment_id: str) -> PlainTextResponse:
    """Export experiment results as CSV."""
    try:
        exp = experiment_registry.get(experiment_id)
        csv_data = export_experiment_csv(exp)
        return PlainTextResponse(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="experiment_{experiment_id}.csv"'},
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/experiments/{experiment_id}/json")
async def get_experiment_json(experiment_id: str) -> Response:
    """Export complete experiment record as JSON."""
    try:
        exp = experiment_registry.get(experiment_id)
        json_data = export_experiment_json(exp)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="experiment_{experiment_id}.json"'},
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/experiments/{experiment_id}/xlsx")
async def get_experiment_xlsx(experiment_id: str) -> Response:
    """Export experiment results as an Excel (.xlsx) workbook."""
    try:
        exp = experiment_registry.get(experiment_id)
        xlsx_bytes = export_experiment_xlsx(exp)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="experiment_{experiment_id}.xlsx"'},
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/experiments/{experiment_id}/pdf")
async def get_experiment_pdf(experiment_id: str) -> Response:
    """Generate and download a PDF scientific research summary report."""
    try:
        exp = experiment_registry.get(experiment_id)
        pdf_bytes = generate_experiment_pdf_report(exp)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="experiment_{experiment_id}_report.pdf"'},
        )
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/experiments/{experiment_id}/report", response_model=ResearchReport)
async def get_experiment_research_report(experiment_id: str) -> ResearchReport:
    """Get structured scientific research report as JSON."""
    try:
        exp = experiment_registry.get(experiment_id)
        return generate_research_report(exp)
    except ExperimentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
