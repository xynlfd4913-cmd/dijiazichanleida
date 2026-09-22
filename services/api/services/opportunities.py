"""Recalculate persisted opportunities after a profile or asset change."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from engine.hidden_cost.calculator import minimum_cash_required, summarize_costs
from engine.scoring.opportunity import (
    capital_fit_score,
    cost_certainty_score,
    distance_convenience_score,
    score_opportunity,
    skill_match_score,
)
from engine.types import ComparableInput, CostInput
from engine.valuation.calculator import calculate_valuation
from services.api.models import Asset, Opportunity, UserProfile


def refresh_asset_opportunity(asset: Asset, profile: UserProfile) -> Opportunity:
    costs = [
        CostInput(item.fee_name, item.status, item.min_amount, item.max_amount)
        for item in asset.cost_items
    ]
    comparables = [ComparableInput(item.price, item.listing_or_sold) for item in asset.comparables]
    summary = summarize_costs(asset.current_price, costs)
    conservative_hint = max(
        (item.price for item in comparables),
        default=asset.appraisal_price or asset.current_price,
    )
    valuation = calculate_valuation(
        comparables=comparables,
        all_in_cost_max=summary.all_in_cost_max,
        non_bid_costs_max=summary.all_in_cost_max - asset.current_price,
        target_profit=max(Decimal("300"), conservative_hint * Decimal("0.20")),
    )
    existing = asset.opportunity
    liquidity = existing.liquidity_score if existing else Decimal("50")
    production = existing.production_score if existing else Decimal("50")
    capital = capital_fit_score(
        budget=min(profile.available_capital, profile.max_single_exposure),
        all_in_cost_max=summary.all_in_cost_max,
        deposit=asset.deposit,
    )
    skill = skill_match_score(asset.required_skills, profile.skills)
    has_cost_evidence = bool(costs)
    certainty = cost_certainty_score(item.status for item in asset.cost_items)
    effective_unknown_count = summary.unknown_cost_count if has_cost_evidence else 1
    estimate_complete = summary.estimate_complete and has_cost_evidence
    distance = distance_convenience_score(asset.distance_km, profile.search_radius)
    scores = score_opportunity(
        capital_fit=capital,
        safe_roi=valuation.safe_roi,
        liquidity=liquidity,
        skill_fit=skill,
        production=production,
        cost_certainty=certainty,
        distance=distance,
        unknown_cost_count=effective_unknown_count,
        valuation_available=valuation.is_available,
        preferred_strategy=profile.preferred_strategy,
    )
    monthly_income = asset.estimated_monthly_income or Decimal("0")
    payback = (
        (summary.all_in_cost_max / monthly_income).quantize(Decimal("0.01"))
        if monthly_income > 0
        else None
    )
    opportunity = existing or Opportunity(asset=asset)
    opportunity.conservative_resale_value = valuation.conservative_resale_value
    opportunity.all_in_cost_min = summary.all_in_cost_min
    opportunity.all_in_cost_max = summary.all_in_cost_max
    opportunity.safe_margin = valuation.safe_margin
    opportunity.safe_roi = valuation.safe_roi
    opportunity.max_recommended_bid = valuation.max_recommended_bid
    opportunity.minimum_cash_required = minimum_cash_required(asset.deposit, summary.all_in_cost_max)
    opportunity.capital_fit_score = scores.capital_fit_score
    opportunity.liquidity_score = scores.liquidity_score
    opportunity.skill_fit_score = scores.skill_fit_score
    opportunity.production_score = scores.production_score
    opportunity.cost_certainty_score = scores.cost_certainty_score
    opportunity.distance_score = scores.distance_score
    opportunity.overall_score = scores.overall_score
    opportunity.grade = scores.grade
    opportunity.valuation_basis = valuation.valuation_basis
    opportunity.decision_status = scores.decision_status
    opportunity.margin_is_provisional = scores.is_provisional or not estimate_complete
    opportunity.unknown_cost_count = effective_unknown_count
    opportunity.cost_estimate_complete = estimate_complete
    opportunity.recommendation_reason = "；".join(
        (
            "本金范围内" if capital > 0 else "超过当前单笔本金上限",
            (
                "缺少可用市场参照"
                if valuation.safe_margin is None
                else "存在正安全价差"
                if valuation.safe_margin > 0
                else "安全价差不足"
            ),
            f"{effective_unknown_count} 项未知费用待核验",
        )
    ) + ("；安全价差与 ROI 为暂估值。" if opportunity.margin_is_provisional else "。")
    opportunity.recommended_use = "自用生产优先" if production >= Decimal("75") else "转卖前先询价"
    opportunity.payback_months = payback
    return opportunity


def refresh_all_opportunities(session: Session, profile: UserProfile) -> None:
    assets = session.scalars(
        select(Asset).options(
            selectinload(Asset.cost_items),
            selectinload(Asset.comparables),
            selectinload(Asset.opportunity),
        )
    ).all()
    for asset in assets:
        session.add(refresh_asset_opportunity(asset, profile))
    session.flush()
