"""All-in cost calculation with explicit uncertainty."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from engine.money import ZERO, decimal
from engine.types import CostInput, CostStatus


@dataclass(frozen=True, slots=True)
class CostSummary:
    acquisition_price: Decimal
    known_cost_min: Decimal
    known_cost_max: Decimal
    estimated_cost_min: Decimal
    estimated_cost_max: Decimal
    all_in_cost_min: Decimal
    all_in_cost_max: Decimal
    unknown_fee_names: tuple[str, ...]
    duplicate_fee_names: tuple[str, ...]
    estimate_complete: bool

    @property
    def unknown_cost_count(self) -> int:
        return len(self.unknown_fee_names)

    @property
    def known_costs(self) -> Decimal:
        """Backward-compatible exact-known total when callers need one scalar.

        The maximum is returned deliberately; new code should use the explicit
        ``known_cost_min`` and ``known_cost_max`` bounds.
        """

        return self.known_cost_max


def _deduplicate_costs(costs: Iterable[CostInput]) -> tuple[list[CostInput], tuple[str, ...]]:
    """Merge repeated fee evidence without charging the same fee twice.

    Grouping is whitespace/case insensitive. Unknown evidence dominates,
    followed by estimated evidence; otherwise the widest known range is kept.
    Sorting by the normalized name makes the result independent of input order.
    """

    grouped: dict[str, list[CostInput]] = {}
    for item in costs:
        key = " ".join(item.fee_name.split()).casefold()
        grouped.setdefault(key, []).append(item)

    merged: list[CostInput] = []
    duplicates: list[str] = []
    for key in sorted(grouped):
        entries = grouped[key]
        label = sorted((" ".join(item.fee_name.split()) for item in entries), key=str.casefold)[0]
        if len(entries) > 1:
            duplicates.append(label)
        statuses = {item.status for item in entries}
        if CostStatus.UNKNOWN in statuses:
            merged.append(CostInput(label, CostStatus.UNKNOWN))
            continue
        lows = [item.min_amount for item in entries if item.min_amount is not None]
        highs = [item.max_amount for item in entries if item.max_amount is not None]
        status = CostStatus.ESTIMATED if CostStatus.ESTIMATED in statuses else CostStatus.KNOWN
        merged.append(CostInput(label, status, min(lows), max(highs)))
    return merged, tuple(duplicates)


def summarize_costs(
    acquisition_price: Decimal | int | str | float,
    costs: Iterable[CostInput],
) -> CostSummary:
    """Compute bounded known/estimated totals while preserving unknown fees.

    ``all_in_cost_*`` are documented bounds over known and estimated items, not
    a claim that unknown items cost zero.  Consumers must inspect
    ``estimate_complete`` and ``unknown_fee_names`` before recommending review.
    """

    price = decimal(acquisition_price)
    normalized_costs, duplicate_names = _deduplicate_costs(costs)
    known_min = ZERO
    known_max = ZERO
    estimated_min = ZERO
    estimated_max = ZERO
    unknown: list[str] = []
    for item in normalized_costs:
        if item.status is CostStatus.UNKNOWN:
            unknown.append(item.fee_name)
        elif item.status is CostStatus.KNOWN:
            assert item.min_amount is not None and item.max_amount is not None
            known_min += item.min_amount
            known_max += item.max_amount
        else:
            assert item.min_amount is not None and item.max_amount is not None
            estimated_min += item.min_amount
            estimated_max += item.max_amount
    known_min = decimal(known_min)
    known_max = decimal(known_max)
    estimated_min = decimal(estimated_min)
    estimated_max = decimal(estimated_max)
    return CostSummary(
        acquisition_price=price,
        known_cost_min=known_min,
        known_cost_max=known_max,
        estimated_cost_min=estimated_min,
        estimated_cost_max=estimated_max,
        all_in_cost_min=decimal(price + known_min + estimated_min),
        all_in_cost_max=decimal(price + known_max + estimated_max),
        unknown_fee_names=tuple(unknown),
        duplicate_fee_names=duplicate_names,
        estimate_complete=not unknown,
    )


def minimum_cash_required(
    deposit: Decimal | int | str | float | None,
    all_in_cost_max: Decimal | int | str | float,
) -> Decimal | None:
    """Cash needed to complete acquisition; deposit remains a separate gate."""

    if deposit is None:
        return None
    return max(decimal(deposit), decimal(all_in_cost_max))
