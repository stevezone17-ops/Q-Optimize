"""CSV exporter for experiment runs and results."""

import csv
import io
from typing import List
from backend.app.experiments.models import Experiment


def export_experiment_csv(experiment: Experiment) -> str:
    """Export all trial results of an experiment to a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "experiment_id",
        "experiment_name",
        "problem_type",
        "algorithm",
        "trial_index",
        "seed",
        "status",
        "objective_value",
        "runtime_seconds",
        "is_feasible",
        "num_evaluations",
        "error",
    ])

    for res in experiment.results:
        writer.writerow([
            experiment.experiment_id,
            experiment.name,
            experiment.configuration.problem_type,
            res.algorithm,
            res.trial_index,
            res.seed if res.seed is not None else "",
            res.status,
            res.objective_value if res.objective_value is not None else "",
            round(res.runtime_seconds, 6),
            res.is_feasible,
            res.num_evaluations,
            res.error or "",
        ])

    return output.getvalue()
