"""Transparent weighted opportunity scoring (100 points total)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from engine.money import ZERO, decimal, percentage, scalar


@dataclass(frozen=True, slots=True)
class OpportunityScores:
    capital_fit_score: Decimal
    margin_score: Decimal
    liquidity_score: Decimal
    skill_fit_score: Decimal
    production_score: Decimal
    strategy_fit_score: Decimal
    cost_certainty_score: Decimal
    distance_score: Decimal
    ungated_score: Decimal
    overall_score: Decimal
    grade: str
    decision_status: str
    is_provisional: bool


def capital_fit_score(
    *,
    budget: Decimal | int | str | float,
    all_in_cost_max: Decimal | int | str | float,
    deposit: Decimal | int | str | float | None,
) -> Decimal:
    usable = decimal(budget)
    total = decimal(all_in_cost_max)
    if deposit is None:
        return ZERO
    cash_gate = decimal(deposit)
    if usable == ZERO or cash_gate > usable or total > usable:
        return ZERO
    utilisation = total / usable
    if utilisation <= Decimal("0.65"):
        return Decimal("100.00")
    if utilisation <= Decimal("0.80"):
        return Decimal("90.00")
    if utilisation <= Decimal("0.90"):
        return Decimal("75.00")
    return Decimal("60.00")


def margin_score(safe_roi: Decimal | int | str | float | None) -> Decimal:
    if safe_roi is None:
        return ZERO
    roi = scalar(safe_roi, allow_negative=True)
    if roi <= ZERO:
        return ZERO
    if roi >= Decimal("0.50"):
        return Decimal("100.00")
    # 20% ROI maps to 70 and 30% to 85; linear interpolation is auditable.
    if roi <= Decimal("0.20"):
        return decimal(roi / Decimal("0.20") * Decimal("70"))
    return decimal(Decimal("70") + (roi - Decimal("0.20")) / Decimal("0.30") * Decimal("30"))


def cost_certainty_score(statuses: Iterable[str]) -> Decimal:
    values = {"known": Decimal("100"), "estimated": Decimal("60"), "unknown": ZERO}
    normalized = [values[str(status)] for status in statuses]
    if not normalized:
        return ZERO
    return decimal(sum(normalized, ZERO) / len(normalized))


def skill_match_score(required_skills: Iterable[str], user_skills: Iterable[str]) -> Decimal:
    required = {item.strip().casefold() for item in required_skills if item.strip()}
    possessed = {item.strip().casefold() for item in user_skills if item.strip()}
    if not required:
        return Decimal("50.00")
    return decimal(Decimal(len(required & possessed)) / Decimal(len(required)) * Decimal("100"))


def distance_convenience_score(distance_km: float | int | Decimal, radius_km: float | int | Decimal) -> Decimal:
    distance = Decimal(str(distance_km))
    radius = Decimal(str(radius_km))
    if distance < 0 or radius < 0:
        raise ValueError("distance and radius cannot be negative")
    if radius == 0:
        return Decimal("100.00") if distance == 0 else ZERO
    if distance > radius:
        return ZERO
    return percentage((Decimal("1") - distance / radius) * Decimal("100"))


def grade_for_score(score: Decimal | int | str | float) -> str:
    value = percentage(score)
    if value >= Decimal("85"):
        return "S"
    if value >= Decimal("75"):
        return "A"
    if value >= Decimal("60"):
        return "B"
    if value >= Decimal("45"):
        return "C"
    return "Skip"


def score_opportunity(
    *,
    capital_fit: Decimal | int | str | float,
    safe_roi: Decimal | int | str | float | None,
    liquidity: Decimal | int | str | float,
    skill_fit: Decimal | int | str | float,
    production: Decimal | int | str | float,
    cost_certainty: Decimal | int | str | float,
    distance: Decimal | int | str | float,
    unknown_cost_count: int = 0,
    valuation_available: bool = True,
    max_unknown_costs_for_review: int = 2,
    preferred_strategy: str = "resale",
) -> OpportunityScores:
    """Score against the product's explicit 25/25/20/15/10/5 weighting.

    Production value is blended inside the existing 15-point skill component
    for production/hybrid profiles, never added as a hidden seventh weight.
    """

    capital = percentage(capital_fit)
    margin = margin_score(safe_roi)
    liquid = percentage(liquidity)
    skill = percentage(skill_fit)
    prod = percentage(production)
    if preferred_strategy == "production":
        strategy_fit = decimal(skill * Decimal("0.50") + prod * Decimal("0.50"))
    elif preferred_strategy == "hybrid":
        strategy_fit = decimal(skill * Decimal("0.75") + prod * Decimal("0.25"))
    elif preferred_strategy == "resale":
        strategy_fit = skill
    else:
        raise ValueError("preferred_strategy must be production, resale, or hybrid")
    certainty = percentage(cost_certainty)
    travel = percentage(distance)
    if unknown_cost_count < 0 or max_unknown_costs_for_review < 0:
        raise ValueError("unknown cost counts cannot be negative")
    ungated = (
        capital * Decimal("0.25")
        + margin * Decimal("0.25")
        + liquid * Decimal("0.20")
        + strategy_fit * Decimal("0.15")
        + certainty * Decimal("0.10")
        + travel * Decimal("0.05")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    is_provisional = unknown_cost_count > 0 or not valuation_available
    if not valuation_available:
        overall = min(ungated, Decimal("44.99"))
        grade = "Skip"
        decision_status = "insufficient_market_data"
    elif unknown_cost_count > max_unknown_costs_for_review:
        overall = min(ungated, Decimal("44.99"))
        grade = "Skip"
        decision_status = "too_many_unknown_costs"
    elif unknown_cost_count > 0:
        overall = min(ungated, Decimal("74.99"))
        grade = grade_for_score(overall)
        decision_status = "provisional_review"
    else:
        overall = ungated
        grade = grade_for_score(overall)
        decision_status = "review_ready"
    return OpportunityScores(
        capital_fit_score=capital,
        margin_score=margin,
        liquidity_score=liquid,
        skill_fit_score=skill,
        production_score=prod,
        strategy_fit_score=strategy_fit,
        cost_certainty_score=certainty,
        distance_score=travel,
        ungated_score=ungated,
        overall_score=overall,
        grade=grade,
        decision_status=decision_status,
        is_provisional=is_provisional,
    )
