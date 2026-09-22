from decimal import Decimal

import pytest

from engine.capital import capital_progress, usable_asset_budget
from engine.debtor_profile.rules import evaluate_budget
from engine.subscriptions.matcher import SubscriptionCriteria, matches_subscription


@pytest.mark.parametrize(
    ("capital", "level", "next_level"),
    [(0, "L0", "L1"), (2999, "L0", "L1"), (3000, "L1", "L2"), (5000, "L2", "L3"), (100000, "L6", None)],
)
def test_capital_ladder(capital: int, level: str, next_level: str | None) -> None:
    progress = capital_progress(capital)
    assert progress.current_level == level
    assert progress.next_level == next_level


def test_living_reserve_is_not_an_input_to_budget() -> None:
    assert usable_asset_budget(5000, 4000) == Decimal("4000.00")
    decision = evaluate_budget(
        available_capital=5000,
        max_single_exposure=4000,
        deposit=1000,
        all_in_cost_max=4200,
    )
    assert decision.eligible is False
    assert "全口径" in decision.reason


def test_subscription_matches_all_safety_constraints() -> None:
    criteria = SubscriptionCriteria(
        max_all_in_cost=Decimal("5000"),
        min_safe_margin=Decimal("1000"),
        min_safe_roi=Decimal("0.20"),
        max_unknown_costs=2,
        province="湖北",
        categories=("工具",),
    )
    kwargs = dict(
        all_in_cost_max=4500,
        safe_margin=1200,
        safe_roi=Decimal("0.2667"),
        unknown_cost_count=1,
        province="湖北",
        city="武汉",
        category="工具",
        auction_stage="二拍",
    )
    assert matches_subscription(criteria, **kwargs) is True
    assert matches_subscription(criteria, **{**kwargs, "unknown_cost_count": 3}) is False


def test_subscription_roi_boundary_keeps_four_decimal_precision() -> None:
    criteria = SubscriptionCriteria(
        max_all_in_cost=Decimal("5000"),
        min_safe_roi=Decimal("0.2044"),
    )
    kwargs = dict(
        all_in_cost_max=4000,
        safe_margin=1000,
        unknown_cost_count=0,
        province="湖北",
        city="武汉",
        category="工具",
        auction_stage="一拍",
    )
    assert matches_subscription(criteria, safe_roi=Decimal("0.2041"), **kwargs) is False
    assert matches_subscription(criteria, safe_roi=Decimal("0.2044"), **kwargs) is True
