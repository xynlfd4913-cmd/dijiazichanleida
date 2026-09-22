"""Explicit boundary for persisting partially normalized discovery records."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from services.api.models import Asset


class NormalizedAssetRecord(BaseModel):
    """Minimum honest record accepted from a future adapter normalize layer.

    Identity, provenance, title, and observed price are mandatory. Missing
    optional facts remain ``None`` or an explicit "待确认" label; they are never
    invented as zero-valued fees or auction facts.
    """

    source_platform: str = Field(min_length=1, max_length=80)
    source_mode: Literal["mock", "api", "html", "browser"] = "mock"
    source_url: str = Field(min_length=1, max_length=500)
    external_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=300)
    current_price: Decimal = Field(ge=0)
    category: str = "待分类"
    subcategory: str = ""
    province: str = "待确认"
    city: str = "待确认"
    district: str = ""
    auction_stage: str = "待确认"
    status: str = "discovered"
    start_time: datetime | None = None
    end_time: datetime | None = None
    appraisal_price: Decimal | None = Field(default=None, ge=0)
    start_price: Decimal | None = Field(default=None, ge=0)
    deposit: Decimal | None = Field(default=None, ge=0)
    bid_increment: Decimal | None = Field(default=None, ge=0)
    observed_at: datetime

    @field_validator("observed_at", "start_time", "end_time")
    @classmethod
    def require_or_attach_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


def map_normalized_asset(record: NormalizedAssetRecord) -> Asset:
    return Asset(
        source_platform=record.source_platform,
        source_mode=record.source_mode,
        source_url=record.source_url,
        external_id=record.external_id,
        title=record.title,
        category=record.category,
        subcategory=record.subcategory,
        province=record.province,
        city=record.city,
        district=record.district,
        seller_or_court="待确认",
        auction_stage=record.auction_stage,
        status=record.status,
        start_time=record.start_time,
        end_time=record.end_time,
        first_seen_at=record.observed_at,
        last_seen_at=record.observed_at,
        appraisal_price=record.appraisal_price,
        start_price=record.start_price,
        current_price=record.current_price,
        deposit=record.deposit,
        bid_increment=record.bid_increment,
        required_skills=[],
        attachment_urls=[],
        notice_summary="已发现基础记录；详情、费用与市场参照尚未获取。",
    )
