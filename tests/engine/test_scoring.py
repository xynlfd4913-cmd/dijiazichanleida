from decimal import Decimal

import pytest

from engine.scoring.opportunity import (
    capital_fit_score,
    cost_certainty_score,
    distance_convenience_score,
    grade_for_score,
    margin_score,
    score_opportunity,
    skill_match_score,
)


def test_capital_fit_requires_both_deposit_and_total_cost() -> None:
    assert capital_fit_score(budget=5000, all_in_cost_max=4000, deposit=6000) == 0
    assert capital_fit_score(budget=5000, all_in_cost_max=5100, deposit=500) == 0
    assert capital_fit_score(budget=5000, all_in_cost_max=3000, deposit=500) == 100


def test_cost_certainty_does_not_credit_unknown_cost() -> None:
    assert cost_certainty_score(["known", "estimated", "unknown"]) == Decimal("53.33")


def test_skill_and_distance_scores_are_deterministic() -> None:
    assert skill_match_score(["木工", "电工"], ["木工", "摄影"]) == Decimal("50.00")
    assert distance_convenience_score(25, 100) == Decimal("75.00")
    assert distance_convenience_score(101, 100) == Decimal("0.00")


@pytest.mark.parametrize(
    ("value", "grade"),
    [(90, "S"), (80, "A"), (65, "B"), (50, "C"), (20, "Skip")],
)
def test_grade_boundaries(value: int, grade: str) -> None:
    assert grade_for_score(value) == grade


def test_weighted_score_uses_exact_product_weights() -> None:
    result = score_opportunity(
        capital_fit=100,
        safe_roi=Decimal("0.50"),
        liquidity=100,
        skill_fit=100,
        production=40,
        cost_certainty=100,
        distance=100,
    )
    assert result.overall_score == Decimal("100.00")
    assert result.production_score == Decimal("40.00")
    assert result.grade == "S"


def test_unknown_cost_caps_grade_b_and_marks_provisional() -> None:
    result = score_opportunity(
        capital_fit=100,
        safe_roi=Decimal("0.50"),
        liquidity=100,
        skill_fit=100,
        production=100,
        cost_certainty=100,
        distance=100,
        unknown_cost_count=1,
        preferred_strategy="production",
    )
    assert result.overall_score == Decimal("74.99")
    assert result.grade == "B"
    assert result.decision_status == "provisional_review"
    assert result.is_provisional is True


def test_missing_valuation_or_too_many_unknowns_is_skip() -> None:
    common = dict(
        capital_fit=100,
        safe_roi=Decimal("0.50"),
        liquidity=100,
        skill_fit=100,
        production=100,
        cost_certainty=100,
        distance=100,
    )
    assert score_opportunity(**common, valuation_available=False).grade == "Skip"
    assert score_opportunity(**common, unknown_cost_count=3, max_unknown_costs_for_review=2).grade == "Skip"


def test_margin_score_retains_ratio_precision() -> None:
    assert margin_score(Decimal("0.1960")) == Decimal("68.60")


def test_production_strategy_blends_production_inside_skill_weight() -> None:
    resale = score_opportunity(
        capital_fit=0,
        safe_roi=None,
        liquidity=0,
        skill_fit=100,
        production=0,
        cost_certainty=0,
        distance=0,
        preferred_strategy="resale",
    )
    production = score_opportunity(
        capital_fit=0,
        safe_roi=None,
        liquidity=0,
        skill_fit=100,
        production=0,
        cost_certainty=0,
        distance=0,
        preferred_strategy="production",
    )
    assert resale.overall_score == Decimal("15.00")
    assert production.overall_score == Decimal("7.50")


def test_margin_score_penalizes_non_positive_margin() -> None:
    assert margin_score(None) == 0
    assert margin_score("-0.1") == 0
    assert margin_score("0.2") == Decimal("70.00")
