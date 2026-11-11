"""Default configuration constants for experiments."""

# Experiment lifecycle defaults
DEFAULT_MAX_RUNTIME_SECONDS = 300.0
DEFAULT_NUM_TRIALS = 1
DEFAULT_MAX_SHOTS = 1024
DEFAULT_QAOA_LAYERS = 3
DEFAULT_MAX_WORKERS = 4

# Allowed status transitions
EXPERIMENT_STATUS_TRANSITIONS = {
    "draft": {"validating", "cancelled"},
    "validating": {"queued", "failed", "cancelled"},
    "queued": {"running", "cancelled"},
    "running": {"completed", "failed", "cancelled", "partially_completed"},
    "completed": set(),
    "failed": {"queued"},  # allow retry
    "cancelled": set(),
    "partially_completed": {"queued"},  # allow retry
}

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
