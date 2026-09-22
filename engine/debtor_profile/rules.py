"""Rules that keep protected living money outside acquisition decisions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from engine.capital import usable_asset_budget
from engine.money import decimal


@dataclass(frozen=True, slots=True)
class BudgetDecision:
    budget: Decimal
    deposit_affordable: bool
    all_in_cost_affordable: bool
    eligible: bool
    reason: str


def evaluate_budget(
    *,
    available_capital: Decimal | int | str | float,
    max_single_exposure: Decimal | int | str | float | None,
    deposit: Decimal | int | str | float,
    all_in_cost_max: Decimal | int | str | float,
) -> BudgetDecision:
    budget = usable_asset_budget(available_capital, max_single_exposure)
    deposit_ok = decimal(deposit) <= budget
    total_ok = decimal(all_in_cost_max) <= budget
    eligible = deposit_ok and total_ok
    if not deposit_ok:
        reason = "保证金超过当前资产本金预算"
    elif not total_ok:
        reason = "全口径最高成本超过当前资产本金预算"
    else:
        reason = "本金门槛符合，仍需人工核验未知费用与资产状况"
    return BudgetDecision(budget, deposit_ok, total_ok, eligible, reason)

