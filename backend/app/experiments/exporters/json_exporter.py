"""JSON exporter for experiment runs and results."""

import json
from typing import Any, Dict
from backend.app.experiments.models import Experiment


def export_experiment_json(experiment: Experiment) -> str:
    """Export complete experiment configuration, metadata, and results to a formatted JSON string."""
    data = experiment.model_dump(mode="json")
    return json.dumps(data, indent=2, sort_keys=True, default=str)
