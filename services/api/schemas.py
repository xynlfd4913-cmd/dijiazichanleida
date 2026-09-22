"""Public API contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @field_validator("*", mode="before", check_fields=False)
    @classmethod
    def attach_utc_to_sqlite_datetimes(cls, value: object) -> object:
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class AccountRead(ORMModel):
    id: int
    account_type: str
    balance: Decimal
    protected: bool
    updated_at: datetime


class ProfileRead(ORMModel):
    id: int
    available_capital: Decimal
    monthly_new_capital: Decimal
    living_reserve: Decimal
    debt_repayment_fund: Decimal
    city: str
    province: str
    search_radius: int
    skills: list[str]
    storage_available: bool
    vehicle_available: bool
    preferred_asset_types: list[str]
    preferred_strategy: Literal["production", "resale", "hybrid"]
    max_single_exposure: Decimal
    accounts: list[AccountRead] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    available_capital: Decimal | None = Field(default=None, ge=0)
    monthly_new_capital: Decimal | None = Field(default=None, ge=0)
    living_reserve: Decimal | None = Field(default=None, ge=0)
    debt_repayment_fund: Decimal | None = Field(default=None, ge=0)
    city: str | None = Field(default=None, min_length=1, max_length=80)
    province: str | None = Field(default=None, min_length=1, max_length=80)
    search_radius: int | None = Field(default=None, ge=0, le=2000)
    skills: list[str] | None = None
    storage_available: bool | None = None
    vehicle_available: bool | None = None
    preferred_asset_types: list[str] | None = None
    preferred_strategy: Literal["production", "resale", "hybrid"] | None = None
    max_single_exposure: Decimal | None = Field(default=None, ge=0)

    @model_validator(mode="before")
    @classmethod
    def reject_explicit_nulls(cls, value: object) -> object:
        if isinstance(value, dict):
            null_fields = sorted(key for key in cls.model_fields if key in value and value[key] is None)
            if null_fields:
                raise ValueError(f"fields may be omitted but cannot be null: {', '.join(null_fields)}")
        return value

    @field_validator("skills", "preferred_asset_types")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        return list(dict.fromkeys(tag.strip() for tag in value if tag.strip()))


class CostItemRead(ORMModel):
    id: int
    fee_name: str
    min_amount: Decimal | None
    max_amount: Decimal | None
    status: Literal["known", "estimated", "unknown"]
    evidence_text: str
    evidence_source: str
    confidence: Decimal
    updated_at: datetime


class ComparableRead(ORMModel):
    id: int
    source_url: str
    price: Decimal
    region: str
    brand: str | None
    model: str | None
    condition: str
    listing_or_sold: Literal["listing", "sold"]
    notes: str


class OpportunityRead(ORMModel):
    conservative_resale_value: Decimal | None
    all_in_cost_min: Decimal
    all_in_cost_max: Decimal
    safe_margin: Decimal | None
    safe_roi: Decimal | None
    max_recommended_bid: Decimal | None
    minimum_cash_required: Decimal | None
    capital_fit_score: Decimal
    liquidity_score: Decimal
    skill_fit_score: Decimal
    production_score: Decimal
    cost_certainty_score: Decimal
    distance_score: Decimal
    overall_score: Decimal
    grade: Literal["S", "A", "B", "C", "Skip"]
    valuation_basis: Literal["sold", "listing", "unavailable"]
    valuation_status: Literal["bounded", "provisional", "unavailable"]
    decision_status: Literal[
        "review_ready", "provisional_review", "too_many_unknown_costs", "insufficient_market_data"
    ]
    margin_is_provisional: bool
    unknown_cost_count: int
    cost_estimate_complete: bool
    recommendation_reason: str
    recommended_use: str
    payback_months: Decimal | None


class AssetRead(ORMModel):
    id: int
    source_platform: str
    source_mode: str
    source_url: str
    external_id: str
    title: str
    category: str
    subcategory: str
    province: str
    city: str
    district: str
    seller_or_court: str
    auction_stage: str
    status: str
    start_time: datetime | None
    end_time: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    appraisal_price: Decimal | None
    start_price: Decimal | None
    current_price: Decimal
    deposit: Decimal | None
    bid_increment: Decimal | None
    payment_deadline: datetime | None
    previous_round_price: Decimal | None
    previous_round_result: str | None
    brand: str | None
    model: str | None
    year: int | None
    quantity: int
    condition: str
    ownership_status: str
    occupancy_status: str
    inspection_available: bool
    attachment_urls: list[str]
    required_skills: list[str]
    distance_km: int
    estimated_monthly_income: Decimal | None
    notice_summary: str
    opportunity: OpportunityRead | None


class AssetDetail(AssetRead):
    costs: list[CostItemRead] = Field(default_factory=list, validation_alias="cost_items")
    comparables: list[ComparableRead] = Field(default_factory=list)
    risk_notice: str = "模拟数据仅用于筛选与人工核验，不构成购买、投资或收益承诺。"


class AssetPage(BaseModel):
    items: list[AssetRead]
    total: int
    page: int
    page_size: int


class SubscriptionBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    platform: str | None = None
    province: str | None = None
    city: str | None = None
    max_all_in_cost: Decimal = Field(ge=0)
    min_safe_margin: Decimal = Field(default=Decimal("0"), ge=0)
    min_safe_roi: Decimal = Field(default=Decimal("0"), ge=0)
    max_unknown_costs: int = Field(default=2, ge=0, le=50)
    categories: list[str] = Field(default_factory=list)
    auction_stages: list[str] = Field(default_factory=list)
    preferred_use: Literal["production", "resale", "hybrid"] = "production"
    alert_frequency: Literal["instant", "daily", "disabled"] = "daily"
    enabled: bool = True


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    platform: str | None = None
    province: str | None = None
    city: str | None = None
    max_all_in_cost: Decimal | None = Field(default=None, ge=0)
    min_safe_margin: Decimal | None = Field(default=None, ge=0)
    min_safe_roi: Decimal | None = Field(default=None, ge=0)
    max_unknown_costs: int | None = Field(default=None, ge=0, le=50)
    categories: list[str] | None = None
    auction_stages: list[str] | None = None
    preferred_use: Literal["production", "resale", "hybrid"] | None = None
    alert_frequency: Literal["instant", "daily", "disabled"] | None = None
    enabled: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_required_field_nulls(cls, value: object) -> object:
        required_in_storage = {
            "name",
            "max_all_in_cost",
            "min_safe_margin",
            "min_safe_roi",
            "max_unknown_costs",
            "categories",
            "auction_stages",
            "preferred_use",
            "alert_frequency",
            "enabled",
        }
        if isinstance(value, dict):
            null_fields = sorted(key for key in required_in_storage if key in value and value[key] is None)
            if null_fields:
                raise ValueError(f"fields may be omitted but cannot be null: {', '.join(null_fields)}")
        return value


class SubscriptionRead(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    created_at: datetime


class WatchlistCreate(BaseModel):
    asset_id: int
    note: str = Field(default="", max_length=1000)


class WatchlistRead(ORMModel):
    id: int
    profile_id: int
    asset_id: int
    note: str
    created_at: datetime
    asset: AssetRead


class MessageResponse(BaseModel):
    message: str
