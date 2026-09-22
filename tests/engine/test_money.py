from decimal import Decimal

import pytest

from engine.money import decimal, ratio


def test_decimal_avoids_float_artifacts() -> None:
    assert decimal(0.1) == Decimal("0.10")
    assert decimal("1.005") == Decimal("1.01")


@pytest.mark.parametrize("bad", [True, "NaN", "Infinity", "-0.01"])
def test_decimal_rejects_invalid_or_negative_values(bad: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        decimal(bad)  # type: ignore[arg-type]


def test_ratio_handles_zero_and_negative_numerator() -> None:
    assert ratio(1, 0) is None
    assert ratio(-25, 100) == Decimal("-0.2500")

