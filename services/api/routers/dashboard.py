from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from engine.capital import capital_progress
from services.api.database import get_db
from services.api.models import Asset, Opportunity, UserProfile
from services.api.schemas import AssetRead, ProfileRead

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db)) -> dict[str, object]:
    profile = db.scalar(
        select(UserProfile).where(UserProfile.id == 1).options(selectinload(UserProfile.accounts))
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="用户画像不存在")
    progression = capital_progress(profile.available_capital)
    total = db.scalar(select(func.count(Asset.id))) or 0
    capital_fit = db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.capital_fit_score > 0)
    ) or 0
    region_fit = db.scalar(
        select(func.count(Asset.id)).where(Asset.province == profile.province)
    ) or 0
    hidden_filtered = db.scalar(
        select(func.count(Opportunity.id)).where(
            Opportunity.unknown_cost_count <= 2,
            Opportunity.safe_margin > 0,
        )
    ) or 0
    market_reference = db.scalar(
        select(func.count(Asset.id)).where(Asset.comparables.any())
    ) or 0
    positive_margin = db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.safe_margin > 0)
    ) or 0
    skill_fit = db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.skill_fit_score >= 50)
    ) or 0
    grade_a = db.scalar(
        select(func.count(Opportunity.id)).where(Opportunity.grade.in_(("S", "A")))
    ) or 0
    top_assets = db.scalars(
        select(Asset)
        .join(Asset.opportunity)
        .options(selectinload(Asset.opportunity))
        .where(Opportunity.capital_fit_score > 0)
        .order_by(Opportunity.overall_score.desc(), Asset.id)
        .limit(5)
    ).all()
    account_map = {item.account_type: item.balance for item in profile.accounts}
    return {
        "profile": ProfileRead.model_validate(profile).model_dump(mode="json"),
        "accounts": {
            "living_reserve": account_map.get("living_reserve", Decimal("0")),
            "asset_capital": account_map.get("asset_capital", Decimal("0")),
            "debt_repayment_fund": account_map.get("debt_repayment_fund", Decimal("0")),
            "living_reserve_protected": True,
        },
        "capital_progress": asdict(progression),
        "scan_stats": {
            "scanned": total,
            "capital_fit": capital_fit,
            "region_fit": region_fit,
            "hidden_cost_filtered": hidden_filtered,
            "with_market_reference": market_reference,
            "positive_safe_margin": positive_margin,
            "skill_fit": skill_fit,
            "grade_a_or_above": grade_a,
        },
        "today_opportunities": [
            AssetRead.model_validate(asset).model_dump(mode="json") for asset in top_assets
        ],
        "risk_notice": "结果只用于缩小人工核验范围，不构成购买、借款或收益承诺。",
    }

