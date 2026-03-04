"""Feature modules for advanced loan contract analysis."""

from .hidden_cost_revealer import HiddenCostRevealer, CostAnalysis, Fee
from .clause_simplifier import ClauseSimplifier, SimplifiedClause
from .obligation_timeline import ObligationTimeline, LoanTimeline, TimelineEvent
from .contradiction_detector import ContradictionDetector, ContradictionReport, Contradiction

__all__ = [
    "HiddenCostRevealer",
    "CostAnalysis",
    "Fee",
    "ClauseSimplifier",
    "SimplifiedClause",
    "ObligationTimeline",
    "LoanTimeline",
    "TimelineEvent",
    "ContradictionDetector",
    "ContradictionReport",
    "Contradiction",
]
