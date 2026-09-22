"""Pure budget-subscription matching rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from engine.money import decimal, scalar


@dataclass(frozen=True, slots=True)
class SubscriptionCriteria:
    max_all_in_cost: Decimal
    min_safe_margin: Decimal = Decimal("0")
    min_safe_roi: Decimal = Decimal("0")
    max_unknown_costs: int = 2
    province: str | None = None
    city: str | None = None
    categories: tuple[str, ...] = ()
    auction_stages: tuple[str, ...] = ()


def matches_subscription(
    criteria: SubscriptionCriteria,
    *,
    all_in_cost_max: Decimal | int | str | float,
    safe_margin: Decimal | int | str | float,
    safe_roi: Decimal | int | str | float | None,
    unknown_cost_count: int,
    province: str,
    city: str,
    category: str,
    auction_stage: str,
) -> bool:
    roi = scalar(safe_roi, allow_negative=True) if safe_roi is not None else None
    return all(
        (
            decimal(all_in_cost_max) <= decimal(criteria.max_all_in_cost),
            decimal(safe_margin, allow_negative=True) >= decimal(criteria.min_safe_margin, allow_negative=True),
            roi is not None and roi >= scalar(criteria.min_safe_roi, allow_negative=True),
            unknown_cost_count <= criteria.max_unknown_costs,
            not criteria.province or criteria.province == province,
            not criteria.city or criteria.city == city,
            not criteria.categories or category in criteria.categories,
            not criteria.auction_stages or auction_stage in criteria.auction_stages,
        )
    )
