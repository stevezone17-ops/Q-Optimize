"""Pydantic schemas and domain models for AI and Machine Learning modules."""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

from backend.app.domain.problems.models import ProblemType


class RecommendationSource(str, Enum):
    """Source of solver recommendation."""
    ML_MODEL = "ml_model"
    RULE_BASED = "rule_based"
    FALLBACK = "fallback"


class SolverCandidate(str, Enum):
    """Supported candidate solvers for recommendation."""
    EXACT = "exact"
    GENETIC_ALGORITHM = "genetic_algorithm"
    SIMULATED_ANNEALING = "simulated_annealing"
    STANDARD_QAOA = "standard_qaoa"
    ADAPTIVE_QAOA = "adaptive_qaoa"


class AIRequest(BaseModel):
    """Generic request envelope for AI operations."""
    operation: str = Field(..., description="AI operation name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional caller context")


class AIResponse(BaseModel):
    """Generic response envelope for AI operations."""
    operation: str = Field(..., description="AI operation name")
    success: bool = Field(..., description="Whether operation succeeded")
    data: Dict[str, Any] = Field(default_factory=dict, description="Operation result data")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OptimizationFeatures(BaseModel):
    """Structured feature vector characterizing an optimization problem instance."""
    schema_version: str = Field(default="v1.0.0", description="Feature schema specification version")
    problem_type: ProblemType = Field(..., description="Family of optimization problem")

    # Common dimensional features
    num_variables: int = Field(..., ge=1, description="Total decision variables in problem formulation")
    num_constraints: int = Field(default=0, ge=0, description="Formal mathematical constraints")
    constraint_density: float = Field(default=0.0, ge=0.0, description="Constraints per variable ratio")
    estimated_search_space_log2: float = Field(..., ge=0.0, description="Estimated state space size in log2")

    # Objective coefficient distribution
    coeff_min: float = Field(default=0.0, description="Minimum non-zero objective coefficient")
    coeff_max: float = Field(default=0.0, description="Maximum non-zero objective coefficient")
    coeff_mean: float = Field(default=0.0, description="Mean objective coefficient")
    coeff_std: float = Field(default=0.0, description="Standard deviation of objective coefficients")
    coeff_range: float = Field(default=0.0, description="Max minus min coefficient range")

    # Max-Cut graph features (defaults 0 when not applicable)
    num_vertices: int = Field(default=0, ge=0)
    num_edges: int = Field(default=0, ge=0)
    graph_density: float = Field(default=0.0, ge=0.0, le=1.0)
    min_degree: int = Field(default=0, ge=0)
    max_degree: int = Field(default=0, ge=0)
    avg_degree: float = Field(default=0.0, ge=0.0)
    degree_std: float = Field(default=0.0, ge=0.0)
    num_connected_components: int = Field(default=1, ge=0)

    # Assignment matrix features
    num_agents: int = Field(default=0, ge=0)
    num_tasks: int = Field(default=0, ge=0)
    is_square_matrix: bool = Field(default=True)

    # TSP features
    num_cities: int = Field(default=0, ge=0)
    is_symmetric_distance: bool = Field(default=True)
    satisfies_triangle_inequality: bool = Field(default=True)

    # QUBO and Ising features (calculated or estimated)
    qubo_num_binary_vars: int = Field(default=0, ge=0)
    qubo_nonzero_linear: int = Field(default=0, ge=0)
    qubo_nonzero_quadratic: int = Field(default=0, ge=0)
    qubo_interaction_density: float = Field(default=0.0, ge=0.0, le=1.0)
    ising_num_spins: int = Field(default=0, ge=0)
    ising_coupling_density: float = Field(default=0.0, ge=0.0, le=1.0)
    ising_max_coupling: float = Field(default=0.0)

    # Resource & Budget features
    required_qubits: int = Field(default=0, ge=0, description="Qubits required for quantum simulation")
    estimated_circuit_depth_p1: int = Field(default=0, ge=0)
    max_eval_budget: Optional[int] = Field(default=None, description="User or system evaluation budget")
    time_limit_seconds: Optional[float] = Field(default=None, description="User-specified runtime cutoff")

    model_config = ConfigDict(extra="ignore")

    def to_feature_vector(self) -> List[float]:
        """Convert scalar features to numeric vector for ML model inference."""
        return [
            float(self.num_variables),
            float(self.num_constraints),
            float(self.constraint_density),
            float(self.estimated_search_space_log2),
            float(self.coeff_min),
            float(self.coeff_max),
            float(self.coeff_mean),
            float(self.coeff_std),
            float(self.coeff_range),
            float(self.graph_density),
            float(self.avg_degree),
            float(self.degree_std),
            float(self.qubo_num_binary_vars),
            float(self.qubo_interaction_density),
            float(self.ising_num_spins),
            float(self.ising_coupling_density),
            float(self.required_qubits),
            float(self.estimated_circuit_depth_p1),
        ]


class RankedSolverAlternative(BaseModel):
    """An alternative solver with comparative score and suitability explanation."""
    solver_name: str = Field(..., description="Solver name identifier")
    score: float = Field(..., ge=0.0, le=1.0, description="Relative suitability score or calibrated confidence")
    rank: int = Field(..., ge=1, description="Rank position (1=recommended, 2=first runner-up, etc.)")
    is_compatible: bool = Field(default=True, description="Whether instance satisfies solver safety limits")
    reason: str = Field(..., description="Plain-English explanation of relative rank")
    estimated_runtime_class: str = Field(default="fast", description="Expected runtime tier (fast, moderate, heavy)")


class SolverRecommendation(BaseModel):
    """Intelligent solver recommendation response."""
    problem_id: Optional[str] = Field(default=None, description="Target problem instance ID")
    problem_type: ProblemType = Field(..., description="Identified problem type")
    recommended_solver: str = Field(..., description="Primary recommended solver name")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence or heuristic match score")
    is_confidence_calibrated: bool = Field(default=False, description="Whether confidence represents calibrated posterior")
    recommendation_source: RecommendationSource = Field(..., description="ML model, expert rule, or safe fallback")
    ranked_alternatives: List[RankedSolverAlternative] = Field(default_factory=list)
    explanation: str = Field(..., description="Detailed textual rationale for recommendation")
    key_features_summary: Dict[str, Any] = Field(default_factory=dict, description="Key features influencing decision")
    resource_considerations: Dict[str, Any] = Field(default_factory=dict, description="Resource bounds, qubit requirements, or complexity")
    is_out_of_distribution: bool = Field(default=False, description="Flagged if instance diverges from training distribution")
    known_limitations: List[str] = Field(default_factory=list, description="Caveats and boundaries")
    model_version: Optional[str] = Field(default=None, description="ML model version if ML-generated")
    dataset_version: Optional[str] = Field(default=None, description="Training dataset version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModelMetadata(BaseModel):
    """Metadata describing a serialized or registered machine learning model."""
    model_id: str = Field(..., description="Unique model identifier")
    model_version: str = Field(..., description="Semantic version string, e.g. v1.0.0")
    algorithm_name: str = Field(..., description="Underlying algorithm (e.g. RandomForestClassifier)")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)
    feature_schema_version: str = Field(default="v1.0.0")
    features_list: List[str] = Field(default_factory=list)
    target_classes: List[str] = Field(default_factory=list)
    trained_at: Optional[datetime] = None
    training_sample_count: int = Field(default=0, ge=0)
    is_trained: bool = Field(default=False)
    is_active: bool = Field(default=False)
    accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    notes: Optional[str] = None


class TrainingDatasetMetadata(BaseModel):
    """Metadata describing an experiment training dataset."""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    dataset_version: str = Field(..., description="Semantic version of dataset")
    total_samples: int = Field(..., ge=0)
    class_distribution: Dict[str, int] = Field(default_factory=dict)
    problem_type_counts: Dict[str, int] = Field(default_factory=dict)
    source_experiment_types: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_summary: str = Field(default="Aggregated from Q-Optimize execution and benchmark records")


class ModelEvaluationResult(BaseModel):
    """Comprehensive performance and regret metrics for a recommendation model."""
    model_id: str
    model_version: str
    dataset_version: str
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sample_count: int = Field(..., ge=0)

    # Classification metrics
    accuracy: float = Field(..., ge=0.0, le=1.0)
    macro_precision: float = Field(..., ge=0.0, le=1.0)
    macro_recall: float = Field(..., ge=0.0, le=1.0)
    macro_f1: float = Field(..., ge=0.0, le=1.0)
    top_2_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    confusion_matrix: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    # Recommendation regret metrics
    mean_runtime_regret_ms: float = Field(default=0.0, ge=0.0)
    mean_objective_regret_percent: float = Field(default=0.0, ge=0.0)
    feasibility_violation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    resource_budget_violation_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    recommendation_coverage: float = Field(default=1.0, ge=0.0, le=1.0)


class ExperimentRecord(BaseModel):
    """Normalized experiment execution record used for dataset assembly."""
    record_id: str = Field(..., description="Unique experiment or execution identifier")
    provenance_collection: str = Field(..., description="Origin collection (executions, quantum_executions, adaptive_executions, benchmarks)")
    problem_id: Optional[str] = None
    problem_type: ProblemType
    instance_data: Dict[str, Any] = Field(default_factory=dict)
    features: Optional[OptimizationFeatures] = None
    solver_name: str
    solver_category: str = Field(default="classical", description="classical or quantum_simulator")
    solver_config: Dict[str, Any] = Field(default_factory=dict)
    status: str
    is_feasible: bool = Field(default=True)
    objective_value: Optional[float] = None
    runtime_seconds: float = Field(default=0.0, ge=0.0)
    evaluation_count: int = Field(default=0, ge=0)
    circuit_metadata: Optional[Dict[str, Any]] = None
    random_seed: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_valid_for_training: bool = Field(default=True)
    exclusion_reason: Optional[str] = None


class TrainingSample(BaseModel):
    """A prepared training example for solver recommendation."""
    instance_id: str = Field(..., description="Group ID representing unique problem instance")
    problem_type: ProblemType
    features: OptimizationFeatures
    feature_vector: List[float] = Field(default_factory=list)
    best_solver_label: str = Field(..., description="Ground-truth preferred solver according to selection policy")
    solver_evaluations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class RecommendationFeedback(BaseModel):
    """User and runtime feedback on a solver recommendation."""
    feedback_id: str = Field(..., description="Unique feedback record ID")
    problem_id: Optional[str] = None
    problem_type: ProblemType
    recommended_solver: str
    user_selected_solver: str
    was_accepted: bool = Field(..., description="Whether user accepted recommended solver")
    model_version: Optional[str] = None
    recommendation_source: RecommendationSource
    realized_objective_value: Optional[float] = None
    realized_runtime_seconds: Optional[float] = None
    realized_is_feasible: Optional[bool] = None
    user_comments: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
