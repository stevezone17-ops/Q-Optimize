"""Mathematical formulation package for QUBO and Ising models."""

from backend.app.formulations.interface import IFormulationEngine
from backend.app.formulations.qubo_builder import QuboBuilder
from backend.app.formulations.penalties import PenaltyManager, PenaltyRecommendation
from backend.app.formulations.max_cut_qubo import MaxCutQuboGenerator
from backend.app.formulations.assignment_qubo import AssignmentQuboGenerator
from backend.app.formulations.tsp_qubo import TSPQuboGenerator
from backend.app.formulations.ising_converter import IsingConverter
from backend.app.formulations.verification import FormulationVerifier
from backend.app.formulations.engine import FormulationEngine

__all__ = [
    "IFormulationEngine",
    "QuboBuilder",
    "PenaltyManager",
    "PenaltyRecommendation",
    "MaxCutQuboGenerator",
    "AssignmentQuboGenerator",
    "TSPQuboGenerator",
    "IsingConverter",
    "FormulationVerifier",
    "FormulationEngine",
]
