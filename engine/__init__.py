"""Deterministic business rules for the debt asset radar.

The engine deliberately has no database, HTTP, crawler, or AI dependency.  Every
financial result is therefore reproducible and independently testable.
"""

from engine.capital import CAPITAL_LEVELS, CapitalProgress, capital_progress
from engine.hidden_cost.calculator import CostSummary, summarize_costs
from engine.scoring.opportunity import OpportunityScores, score_opportunity
from engine.valuation.calculator import ValuationResult, calculate_valuation

__all__ = [
    "CAPITAL_LEVELS",
    "CapitalProgress",
    "CostSummary",
    "OpportunityScores",
    "ValuationResult",
    "calculate_valuation",
    "capital_progress",
    "score_opportunity",
    "summarize_costs",
]

