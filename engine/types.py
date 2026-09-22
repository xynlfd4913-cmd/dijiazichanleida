"""Transport-neutral value objects shared by engine modules."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from engine.money import decimal


class CostStatus(StrEnum):
    KNOWN = "known"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CostInput:
    fee_name: str
    status: CostStatus | str
    min_amount: Decimal | int | str | float | None = None
    max_amount: Decimal | int | str | float | None = None

    def __post_init__(self) -> None:
        normalized_status = CostStatus(self.status)
        object.__setattr__(self, "status", normalized_status)
        if not self.fee_name.strip():
            raise ValueError("fee_name cannot be empty")
        if normalized_status is CostStatus.UNKNOWN:
            if self.min_amount is not None or self.max_amount is not None:
                raise ValueError("unknown costs must not be represented as zero or a guessed range")
            return
        if self.min_amount is None:
            raise ValueError(f"{normalized_status.value} cost requires min_amount")
        low = decimal(self.min_amount)
        high = decimal(self.max_amount if self.max_amount is not None else low)
        if high < low:
            raise ValueError("max_amount cannot be less than min_amount")
        object.__setattr__(self, "min_amount", low)
        object.__setattr__(self, "max_amount", high)


@dataclass(frozen=True, slots=True)
class ComparableInput:
    price: Decimal | int | str | float
    listing_or_sold: str = "listing"

    def __post_init__(self) -> None:
        if self.listing_or_sold not in {"listing", "sold"}:
            raise ValueError("listing_or_sold must be 'listing' or 'sold'")
        object.__setattr__(self, "price", decimal(self.price))

