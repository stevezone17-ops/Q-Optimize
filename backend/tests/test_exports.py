"""Tests for Stage 8.8 — Experiment Exports and Research Reports."""

import json
import pytest
from backend.app.experiments.models import (
    Experiment,
    ExperimentAlgorithm,
    ExperimentConfiguration,
    ExperimentResult,
    ExperimentStatus,
)
from backend.app.experiments.registry import experiment_registry
from backend.app.experiments.exporters.csv_exporter import export_experiment_csv
from backend.app.experiments.exporters.json_exporter import export_experiment_json
from backend.app.experiments.exporters.xlsx_exporter import export_experiment_xlsx
from backend.app.experiments.exporters.pdf_reporter import generate_experiment_pdf_report
from backend.app.experiments.exporters.report_generator import generate_research_report


@pytest.fixture
def sample_experiment():
    exp = Experiment(
        experiment_id="exp-export-test-1",
        name="Export Test Benchmark",
        configuration=ExperimentConfiguration(
            problem_type="max_cut",
            problem_instance={"num_nodes": 4, "edge_list": [[0, 1], [1, 2], [2, 3]]},
            algorithms=[ExperimentAlgorithm.SIMULATED_ANNEALING, ExperimentAlgorithm.EXACT],
            num_trials=2,
        ),
        status=ExperimentStatus.COMPLETED,
        results=[
            ExperimentResult(
                algorithm="simulated_annealing",
                trial_index=0,
                seed=42,
                objective_value=3.0,
                runtime_seconds=0.045,
                is_feasible=True,
                num_evaluations=100,
                status="completed",
            ),
            ExperimentResult(
                algorithm="simulated_annealing",
                trial_index=1,
                seed=43,
                objective_value=3.0,
                runtime_seconds=0.041,
                is_feasible=True,
                num_evaluations=95,
                status="completed",
            ),
            ExperimentResult(
                algorithm="exact",
                trial_index=0,
                seed=None,
                objective_value=3.0,
                runtime_seconds=0.005,
                is_feasible=True,
                num_evaluations=16,
                status="completed",
            ),
        ],
    )
    experiment_registry.save(exp)
    return exp


class TestExperimentExports:
    def test_export_csv_valid_headers_and_rows(self, sample_experiment):
        csv_str = export_experiment_csv(sample_experiment)
        lines = csv_str.strip().split("\r\n" if "\r\n" in csv_str else "\n")
        assert len(lines) == 4  # header + 3 rows
        header = lines[0]
        assert "experiment_id" in header
        assert "objective_value" in header
        assert "runtime_seconds" in header
        assert "simulated_annealing" in lines[1]

    def test_export_json_valid_and_parseable(self, sample_experiment):
        json_str = export_experiment_json(sample_experiment)
        parsed = json.loads(json_str)
        assert parsed["experiment_id"] == sample_experiment.experiment_id
        assert len(parsed["results"]) == 3
        assert parsed["status"] == "completed"

    def test_export_xlsx_produces_valid_bytes(self, sample_experiment):
        xlsx_bytes = export_experiment_xlsx(sample_experiment)
        assert isinstance(xlsx_bytes, bytes)
        assert len(xlsx_bytes) > 1000  # zip/xlsx signature
        assert xlsx_bytes[:2] == b"PK"  # standard zip magic bytes

    def test_export_pdf_report_generates_valid_pdf(self, sample_experiment):
        pdf_bytes = generate_experiment_pdf_report(sample_experiment)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes[:4] == b"%PDF"  # PDF header magic bytes

    def test_generate_research_report_structure(self, sample_experiment):
        report = generate_research_report(sample_experiment)
        assert report.experiment_id == sample_experiment.experiment_id
        assert report.problem_type == "max_cut"
        assert "simulated_annealing" in report.performance_metrics
        assert "exact" in report.performance_metrics
        assert len(report.limitations) > 0
        assert "reproducibility_hash" in report.hardware_provenance
