from decimal import Decimal

from engine.types import ComparableInput
from engine.valuation.calculator import (
    calculate_max_recommended_bid,
    calculate_valuation,
    conservative_resale_value,
)


def test_sold_prices_take_precedence_over_listing_prices() -> None:
    value = conservative_resale_value(
        [
            ComparableInput(6000, "listing"),
            ComparableInput(5500, "sold"),
            ComparableInput(5800, "sold"),
            ComparableInput(7000, "listing"),
        ]
    )
    assert value == Decimal("5500.00")


def test_listing_prices_are_haircut_when_no_sold_evidence_exists() -> None:
    value = conservative_resale_value(
        [ComparableInput(6000, "listing"), ComparableInput(7000, "listing")]
    )
    assert value == Decimal("5400.00")


def test_missing_comparables_produce_unavailable_valuation() -> None:
    result = calculate_valuation(
        comparables=[],
        all_in_cost_max=4200,
        non_bid_costs_max=800,
        target_profit=1000,
    )
    assert result.conservative_resale_value is None
    assert result.safe_margin is None
    assert result.safe_roi is None
    assert result.max_recommended_bid is None
    assert result.valuation_basis == "unavailable"


def test_safe_margin_roi_and_max_bid() -> None:
    result = calculate_valuation(
        comparables=[ComparableInput(5500, "sold")],
        all_in_cost_max=4200,
        non_bid_costs_max=800,
        target_profit=1000,
        risk_reserve=200,
    )
    assert result.safe_margin == Decimal("1300.00")
    assert result.safe_roi == Decimal("0.3095")
    assert result.max_recommended_bid == Decimal("3500.00")


def test_max_bid_is_never_negative() -> None:
    assert calculate_max_recommended_bid(1000, 700, 400) == Decimal("0.00")
