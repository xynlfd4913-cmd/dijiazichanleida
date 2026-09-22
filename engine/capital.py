"""Capital ladder and exposure rules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from engine.money import ZERO, decimal


@dataclass(frozen=True, slots=True)
class CapitalLevel:
    code: str
    threshold: Decimal
    focus: str


CAPITAL_LEVELS: tuple[CapitalLevel, ...] = (
    CapitalLevel("L0", decimal(0), "生存保障、观察市场、收藏目标"),
    CapitalLevel("L1", decimal(3000), "小工具、小设备与生产资料"),
    CapitalLevel("L2", decimal(5000), "小型设备、清仓工具与小额库存"),
    CapitalLevel("L3", decimal(10000), "小型机器、批量库存与商用设备"),
    CapitalLevel("L4", decimal(30000), "成套设备、商用车辆与小型资产包"),
    CapitalLevel("L5", decimal(50000), "车辆、工业设备与成套资产"),
    CapitalLevel("L6", decimal(100000), "不动产、工业资产与复杂尽调资产"),
)


@dataclass(frozen=True, slots=True)
class CapitalProgress:
    current_level: str
    current_threshold: Decimal
    next_level: str | None
    next_target: Decimal | None
    gap_to_next: Decimal
    progress_percent: Decimal
    focus: str


def capital_progress(asset_capital: Decimal | int | str | float) -> CapitalProgress:
    """Map usable asset capital to the highest unlocked capital level.

    The plan names L0 as the pre-3000 observation stage.  This intentionally
    closes the 1000..2999 gap in the prose and prevents premature L1 assets.
    """

    capital = decimal(asset_capital)
    index = 0
    for candidate_index, level in enumerate(CAPITAL_LEVELS):
        if capital >= level.threshold:
            index = candidate_index
        else:
            break
    current = CAPITAL_LEVELS[index]
    if index == len(CAPITAL_LEVELS) - 1:
        return CapitalProgress(
            current.code,
            current.threshold,
            None,
            None,
            ZERO,
            Decimal("100.00"),
            current.focus,
        )
    following = CAPITAL_LEVELS[index + 1]
    gap = decimal(max(ZERO, following.threshold - capital))
    span = following.threshold - current.threshold
    progress = Decimal("100") if span == ZERO else ((capital - current.threshold) / span * 100)
    progress = min(Decimal("100"), max(ZERO, progress)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return CapitalProgress(
        current.code,
        current.threshold,
        following.code,
        following.threshold,
        gap,
        progress,
        current.focus,
    )


def usable_asset_budget(
    available_capital: Decimal | int | str | float,
    max_single_exposure: Decimal | int | str | float | None,
) -> Decimal:
    """Return the purchase budget; living reserve is intentionally not accepted."""

    capital = decimal(available_capital)
    if max_single_exposure is None:
        return capital
    return min(capital, decimal(max_single_exposure))

