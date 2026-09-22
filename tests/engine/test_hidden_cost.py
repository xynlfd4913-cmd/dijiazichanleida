from decimal import Decimal

import pytest

from engine.hidden_cost.calculator import minimum_cash_required, summarize_costs
from engine.types import CostInput


def test_all_in_cost_keeps_deposit_out_and_unknown_explicit() -> None:
    summary = summarize_costs(
        3200,
        [
            CostInput("服务费", "known", 48),
            CostInput("拆装", "estimated", 200, 500),
            CostInput("缺件", "unknown"),
        ],
    )
    assert summary.all_in_cost_min == Decimal("3448.00")
    assert summary.all_in_cost_max == Decimal("3748.00")
    assert summary.unknown_fee_names == ("缺件",)
    assert summary.estimate_complete is False
    assert minimum_cash_required(500, summary.all_in_cost_max) == Decimal("3748.00")


def test_unknown_cost_cannot_be_silently_stored_as_zero() -> None:
    with pytest.raises(ValueError, match="must not"):
        CostInput("未知维修", "unknown", 0, 0)


def test_estimated_range_must_be_ordered() -> None:
    with pytest.raises(ValueError, match="max_amount"):
        CostInput("运输", "estimated", 500, 200)


def test_known_cost_defaults_to_exact_range() -> None:
    item = CostInput("佣金", "known", "120")
    assert item.min_amount == item.max_amount == Decimal("120.00")


def test_known_ranges_preserve_both_bounds() -> None:
    summary = summarize_costs(100, [CostInput("过户费", "known", 10, 20)])
    assert summary.known_cost_min == Decimal("10.00")
    assert summary.known_cost_max == Decimal("20.00")
    assert summary.all_in_cost_min == Decimal("110.00")
    assert summary.all_in_cost_max == Decimal("120.00")


def test_duplicate_fee_evidence_is_not_double_counted() -> None:
    summary = summarize_costs(
        100,
        [CostInput("运输费", "estimated", 10, 20), CostInput(" 运输费 ", "estimated", 15, 30)],
    )
    assert summary.estimated_cost_min == Decimal("10.00")
    assert summary.estimated_cost_max == Decimal("30.00")
    assert summary.duplicate_fee_names == ("运输费",)
