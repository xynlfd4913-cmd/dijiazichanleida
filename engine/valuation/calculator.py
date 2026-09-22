"""Comparable-based deterministic valuation rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from typing import Iterable

from engine.money import ZERO, decimal, ratio
from engine.types import ComparableInput

LISTING_HAIRCUT = Decimal("0.90")


@dataclass(frozen=True, slots=True)
class ValuationResult:
    conservative_resale_value: Decimal | None
    safe_margin: Decimal | None
    safe_roi: Decimal | None
    max_recommended_bid: Decimal | None
    valuation_basis: str

    @property
    def is_available(self) -> bool:
        return self.conservative_resale_value is not None


def conservative_resale_value(comparables: Iterable[ComparableInput]) -> Decimal | None:
    """Prefer sold evidence; use haircutted listings only as a fallback."""

    items = tuple(comparables)
    sold = sorted(decimal(item.price) for item in items if item.listing_or_sold == "sold" and item.price > ZERO)
    listings = sorted(
        decimal(item.price * LISTING_HAIRCUT)
        for item in items
        if item.listing_or_sold == "listing" and item.price > ZERO
    )
    adjusted = sold or listings
    if not adjusted:
        return None
    # Nearest-rank lower quartile.  It remains conservative for small samples.
    rank = max(1, int((Decimal(len(adjusted)) * Decimal("0.25")).to_integral_value(rounding=ROUND_CEILING)))
    return adjusted[rank - 1]


def calculate_max_recommended_bid(
    conservative_value: Decimal | int | str | float | None,
    non_bid_costs_max: Decimal | int | str | float,
    target_profit: Decimal | int | str | float,
    risk_reserve: Decimal | int | str | float = ZERO,
) -> Decimal | None:
    if conservative_value is None:
        return None
    result = (
        decimal(conservative_value)
        - decimal(non_bid_costs_max)
        - decimal(target_profit)
        - decimal(risk_reserve)
    )
    return decimal(max(ZERO, result))


def calculate_valuation(
    *,
    comparables: Iterable[ComparableInput],
    all_in_cost_max: Decimal | int | str | float,
    non_bid_costs_max: Decimal | int | str | float,
    target_profit: Decimal | int | str | float,
    risk_reserve: Decimal | int | str | float = ZERO,
) -> ValuationResult:
    comparable_items = tuple(comparables)
    conservative = conservative_resale_value(comparable_items)
    if conservative is None:
        return ValuationResult(
            conservative_resale_value=None,
            safe_margin=None,
            safe_roi=None,
            max_recommended_bid=None,
            valuation_basis="unavailable",
        )
    basis = "sold" if any(item.listing_or_sold == "sold" and item.price > ZERO for item in comparable_items) else "listing"
    maximum_cost = decimal(all_in_cost_max)
    margin = decimal(conservative - maximum_cost, allow_negative=True)
    return ValuationResult(
        conservative_resale_value=conservative,
        safe_margin=margin,
        safe_roi=ratio(margin, maximum_cost),
        max_recommended_bid=calculate_max_recommended_bid(
            conservative, non_bid_costs_max, target_profit, risk_reserve
        ),
        valuation_basis=basis,
    )
