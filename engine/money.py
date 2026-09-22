"""Strict Decimal helpers used by all monetary rules."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import TypeAlias

MoneyLike: TypeAlias = Decimal | int | str | float

CENT = Decimal("0.01")
ZERO = Decimal("0.00")
ONE_HUNDRED = Decimal("100")


def decimal(value: MoneyLike, *, allow_negative: bool = False) -> Decimal:
    """Convert a scalar to a two-decimal Decimal without binary-float leakage."""

    if isinstance(value, bool):
        raise TypeError("boolean is not a monetary value")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid monetary value: {value!r}") from exc
    if not result.is_finite():
        raise ValueError("monetary value must be finite")
    result = result.quantize(CENT, rounding=ROUND_HALF_UP)
    if result < ZERO and not allow_negative:
        raise ValueError("monetary value cannot be negative")
    return result


def percentage(value: MoneyLike) -> Decimal:
    """Clamp a percentage-like score to the inclusive 0..100 range."""

    result = decimal(value)
    return min(ONE_HUNDRED, max(ZERO, result))


def scalar(
    value: MoneyLike,
    *,
    places: Decimal = Decimal("0.0001"),
    allow_negative: bool = False,
) -> Decimal:
    """Convert a non-money scalar without rounding it to cents.

    Ratios and thresholds must retain at least four decimal places so boundary
    comparisons are not silently changed by monetary rounding.
    """

    if isinstance(value, bool):
        raise TypeError("boolean is not a numeric scalar")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid numeric scalar: {value!r}") from exc
    if not result.is_finite():
        raise ValueError("numeric scalar must be finite")
    result = result.quantize(places, rounding=ROUND_HALF_UP)
    if result < 0 and not allow_negative:
        raise ValueError("numeric scalar cannot be negative")
    return result


def ratio(numerator: MoneyLike, denominator: MoneyLike) -> Decimal | None:
    """Return a four-decimal ratio, or ``None`` for a zero denominator."""

    top = decimal(numerator, allow_negative=True)
    bottom = decimal(denominator)
    if bottom == ZERO:
        return None
    return scalar(top / bottom, allow_negative=True)


def money_sum(values: list[MoneyLike] | tuple[MoneyLike, ...]) -> Decimal:
    return decimal(sum((decimal(value) for value in values), ZERO), allow_negative=True)
