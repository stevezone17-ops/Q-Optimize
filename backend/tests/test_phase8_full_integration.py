"""Stage 8.10 — Full Integration and End-to-End Workflow Validation."""

import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.experiments.dataset_manager import dataset_manager
from backend.app.experiments.models import ExperimentAlgorithm, ExperimentStatus
from backend.app.experiments.schemas import ExperimentCreateRequest
from backend.app.experiments.experiment_manager import experiment_manager
from backend.app.experiments.experiment_runner import experiment_runner
from backend.app.experiments.analytics import comparison_engine
from backend.app.experiments.exporters.csv_exporter import export_experiment_csv
from backend.app.experiments.exporters.json_exporter import export_experiment_json
from backend.app.experiments.exporters.xlsx_exporter import export_experiment_xlsx
from backend.app.experiments.exporters.pdf_reporter import generate_experiment_pdf_report
from backend.app.experiments.exporters.report_generator import generate_research_report
from backend.app.experiments.validators import benchmark_validator


@pytest.fixture
def client():
    return TestClient(app)


class TestPhase8FullIntegration:
    def test_complete_end_to_end_research_pipeline(self, client: TestClient):
        """
        Full scientific workflow:
        1. Generate synthetic reproducible dataset (Max-Cut Erdős–Rényi).
        2. Create multi-algorithm experiment on instance.
        3. Execute experiment across algorithms synchronously.
        4. Run statistical comparison analytics (Mann-Whitney U, Cohen's d).
        5. Validate experimental integrity (check missing trials, outliers).
        6. Export artifacts to CSV, JSON, XLSX, and PDF.
        """
        # Step 1: Generate dataset
        dataset = dataset_manager.generate_max_cut_erdos_renyi(
            num_nodes=4,
            edge_probability=0.8,
            num_instances=1,
            base_seed=101,
            name="E2E Pipeline Dataset",
        )
        assert len(dataset.instances) == 1
        instance_data = dataset.instances[0].instance_data
        # Ensure node and edge keys for exact solver compatibility
        instance_data["nodes"] = [str(i) for i in range(instance_data["num_nodes"])]
        instance_data["edges"] = [[str(e[0]), str(e[1]), 1.0] for e in instance_data["edge_list"]]

        # Step 2: Create experiment
        create_req = ExperimentCreateRequest(
            name="E2E Max-Cut Benchmark",
            problem_type="max_cut",
            problem_instance=instance_data,
            algorithms=[ExperimentAlgorithm.EXACT, ExperimentAlgorithm.SIMULATED_ANNEALING],
            num_trials=2,
            seeds=[42, 43],
        )
        exp = experiment_manager.create_experiment(create_req)
        assert exp.status == ExperimentStatus.DRAFT

        # Step 3: Execute experiment
        executed = experiment_runner.run_experiment(exp)
        assert executed.status in {ExperimentStatus.COMPLETED, ExperimentStatus.PARTIALLY_COMPLETED}
        assert len(executed.results) == 4  # 2 algos * 2 trials

        # Step 4: Run comparison analytics
        analysis = comparison_engine.analyze_results(
            results=executed.results,
            problem_type="max_cut",
            problem_instance=instance_data,
            experiment_id=executed.experiment_id,
        )
        assert len(analysis.algorithm_summaries) == 2
        exact_sum = next(s for s in analysis.algorithm_summaries if s.algorithm == "exact")
        sa_sum = next(s for s in analysis.algorithm_summaries if s.algorithm == "simulated_annealing")
        assert exact_sum.best_objective is not None
        assert sa_sum.best_objective is not None

        # Step 5: Validate integrity
        val_report = benchmark_validator.validate_experiment(executed)
        assert val_report.is_valid is True

        # Step 6: Test exports
        csv_out = export_experiment_csv(executed)
        assert "experiment_id" in csv_out
        assert "simulated_annealing" in csv_out

        json_out = export_experiment_json(executed)
        parsed_json = json.loads(json_out)
        assert parsed_json["experiment_id"] == executed.experiment_id

        xlsx_out = export_experiment_xlsx(executed)
        assert len(xlsx_out) > 500

        pdf_out = generate_experiment_pdf_report(executed)
        assert len(pdf_out) > 500

        research_rep = generate_research_report(executed)
        assert research_rep.experiment_id == executed.experiment_id

    def test_api_endpoints_health_and_exports(self, client: TestClient):
        """Verify REST API routes for experiments and exports."""
        # Create experiment via REST
        res = client.post(
            "/api/v1/experiments",
            json={
                "name": "REST API Test Benchmark",
                "problem_type": "max_cut",
                "problem_instance": {"num_nodes": 4, "edge_list": [[0, 1]]},
                "algorithms": ["simulated_annealing"],
                "num_trials": 1,
            },
        )
        assert res.status_code == 201
        exp_id = res.json()["experiment_id"]

        # List experiments
        list_res = client.get("/api/v1/experiments")
        assert list_res.status_code == 200

        # Get experiment status
        status_res = client.get(f"/api/v1/experiments/{exp_id}/status")
        assert status_res.status_code == 200

        # Download CSV export
        csv_res = client.get(f"/api/v1/exports/experiments/{exp_id}/csv")
        assert csv_res.status_code == 200
        assert "text/csv" in csv_res.headers.get("content-type", "")

        # Download JSON export
        json_res = client.get(f"/api/v1/exports/experiments/{exp_id}/json")
        assert json_res.status_code == 200
        assert "application/json" in json_res.headers.get("content-type", "")

        # Download XLSX export
        xlsx_res = client.get(f"/api/v1/exports/experiments/{exp_id}/xlsx")
        assert xlsx_res.status_code == 200

        # Download PDF export
        pdf_res = client.get(f"/api/v1/exports/experiments/{exp_id}/pdf")
        assert pdf_res.status_code == 200
        assert "application/pdf" in pdf_res.headers.get("content-type", "")

        # Research report JSON
        rep_res = client.get(f"/api/v1/exports/experiments/{exp_id}/report")
        assert rep_res.status_code == 200
        assert rep_res.json()["experiment_id"] == exp_id
