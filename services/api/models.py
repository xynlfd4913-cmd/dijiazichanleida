"""SQLAlchemy persistence model for the local MVP."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from services.api.database import Base

MONEY = Numeric(14, 2)
SCORE = Numeric(6, 2)
RATIO = Numeric(9, 4)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    available_capital: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    monthly_new_capital: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    living_reserve: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    debt_repayment_fund: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    city: Mapped[str] = mapped_column(String(80), default="武汉")
    province: Mapped[str] = mapped_column(String(80), default="湖北")
    search_radius: Mapped[int] = mapped_column(Integer, default=100)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    storage_available: Mapped[bool] = mapped_column(Boolean, default=False)
    vehicle_available: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_asset_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_strategy: Mapped[str] = mapped_column(String(20), default="hybrid")
    max_single_exposure: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    accounts: Mapped[list["Account"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("profile_id", "account_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    account_type: Mapped[str] = mapped_column(String(40), index=True)
    balance: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    protected: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    profile: Mapped[UserProfile] = relationship(back_populates="accounts")


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("source_platform", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_platform: Mapped[str] = mapped_column(String(80), index=True)
    source_mode: Mapped[str] = mapped_column(String(20), default="mock")
    source_url: Mapped[str] = mapped_column(String(500))
    external_id: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    subcategory: Mapped[str] = mapped_column(String(80), default="")
    province: Mapped[str] = mapped_column(String(80), index=True)
    city: Mapped[str] = mapped_column(String(80), index=True)
    district: Mapped[str] = mapped_column(String(80), default="")
    seller_or_court: Mapped[str] = mapped_column(String(200), default="模拟处置方")
    auction_stage: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    appraisal_price: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    start_price: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    current_price: Mapped[Decimal] = mapped_column(MONEY)
    deposit: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    bid_increment: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    payment_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    previous_round_price: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    previous_round_result: Mapped[str | None] = mapped_column(String(40), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    condition: Mapped[str] = mapped_column(String(100), default="现状交付")
    ownership_status: Mapped[str] = mapped_column(String(100), default="待核验")
    occupancy_status: Mapped[str] = mapped_column(String(100), default="不适用")
    inspection_available: Mapped[bool] = mapped_column(Boolean, default=True)
    attachment_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    distance_km: Mapped[int] = mapped_column(Integer, default=0)
    estimated_monthly_income: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    notice_summary: Mapped[str] = mapped_column(Text, default="离线模拟公告，仅用于 Phase 0 测试。")

    cost_items: Mapped[list["CostItem"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )
    comparables: Mapped[list["Comparable"]] = relationship(
        back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )
    opportunity: Mapped["Opportunity | None"] = relationship(
        back_populates="asset", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )


class CostItem(Base):
    __tablename__ = "cost_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    fee_name: Mapped[str] = mapped_column(String(100))
    min_amount: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    max_amount: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    evidence_text: Mapped[str] = mapped_column(Text, default="")
    evidence_source: Mapped[str] = mapped_column(String(300), default="模拟公告")
    confidence: Mapped[Decimal] = mapped_column(SCORE, default=Decimal("0"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset: Mapped[Asset] = relationship(back_populates="cost_items")


class Comparable(Base):
    __tablename__ = "comparables"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    source_url: Mapped[str] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(MONEY)
    region: Mapped[str] = mapped_column(String(100))
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    condition: Mapped[str] = mapped_column(String(100), default="二手可用")
    listing_or_sold: Mapped[str] = mapped_column(String(20), default="listing")
    notes: Mapped[str] = mapped_column(Text, default="人工模拟市场参照")

    asset: Mapped[Asset] = relationship(back_populates="comparables")


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), unique=True)
    conservative_resale_value: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    all_in_cost_min: Mapped[Decimal] = mapped_column(MONEY)
    all_in_cost_max: Mapped[Decimal] = mapped_column(MONEY)
    safe_margin: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    safe_roi: Mapped[Decimal | None] = mapped_column(RATIO, nullable=True)
    max_recommended_bid: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    minimum_cash_required: Mapped[Decimal | None] = mapped_column(MONEY, nullable=True)
    capital_fit_score: Mapped[Decimal] = mapped_column(SCORE)
    liquidity_score: Mapped[Decimal] = mapped_column(SCORE)
    skill_fit_score: Mapped[Decimal] = mapped_column(SCORE)
    production_score: Mapped[Decimal] = mapped_column(SCORE)
    cost_certainty_score: Mapped[Decimal] = mapped_column(SCORE)
    distance_score: Mapped[Decimal] = mapped_column(SCORE)
    overall_score: Mapped[Decimal] = mapped_column(SCORE)
    grade: Mapped[str] = mapped_column(String(10), index=True)
    valuation_basis: Mapped[str] = mapped_column(String(20), default="unavailable")
    decision_status: Mapped[str] = mapped_column(String(40), default="insufficient_market_data")
    margin_is_provisional: Mapped[bool] = mapped_column(Boolean, default=True)
    unknown_cost_count: Mapped[int] = mapped_column(Integer, default=0)
    cost_estimate_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    recommendation_reason: Mapped[str] = mapped_column(Text)
    recommended_use: Mapped[str] = mapped_column(String(40), default="人工核验")
    payback_months: Mapped[Decimal | None] = mapped_column(RATIO, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="opportunity")

    @property
    def valuation_status(self) -> str:
        if self.conservative_resale_value is None:
            return "unavailable"
        if self.margin_is_provisional:
            return "provisional"
        return "bounded"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    platform: Mapped[str | None] = mapped_column(String(80), nullable=True)
    province: Mapped[str | None] = mapped_column(String(80), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    max_all_in_cost: Mapped[Decimal] = mapped_column(MONEY)
    min_safe_margin: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    min_safe_roi: Mapped[Decimal] = mapped_column(RATIO, default=Decimal("0"))
    max_unknown_costs: Mapped[int] = mapped_column(Integer, default=2)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    auction_stages: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_use: Mapped[str] = mapped_column(String(40), default="production")
    alert_frequency: Mapped[str] = mapped_column(String(40), default="daily")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    profile: Mapped[UserProfile] = relationship(back_populates="subscriptions")


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("profile_id", "asset_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id", ondelete="CASCADE"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    asset: Mapped[Asset] = relationship(lazy="selectin")
