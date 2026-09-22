from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from services.api.database import get_db
from services.api.models import Asset, Opportunity
from services.api.schemas import AssetDetail, AssetPage

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _asset_options():
    return (
        selectinload(Asset.cost_items),
        selectinload(Asset.comparables),
        selectinload(Asset.opportunity),
    )


@router.get("", response_model=AssetPage)
@router.get("/list", response_model=AssetPage, include_in_schema=False)
def list_assets(
    db: Session = Depends(get_db),
    q: str | None = None,
    platform: str | None = None,
    category: str | None = None,
    province: str | None = None,
    city: str | None = None,
    auction_stage: str | None = None,
    status: str | None = None,
    grade: str | None = None,
    max_price: Decimal | None = Query(default=None, ge=0),
    max_all_in_cost: Decimal | None = Query(default=None, ge=0),
    min_safe_roi: Decimal | None = None,
    max_unknown_costs: int | None = Query(default=None, ge=0),
    production_only: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AssetPage:
    filters = []
    if q:
        search = f"%{q.strip()}%"
        filters.append(or_(Asset.title.ilike(search), Asset.subcategory.ilike(search)))
    if platform:
        filters.append(Asset.source_platform == platform)
    if category:
        filters.append(Asset.category == category)
    if province:
        filters.append(Asset.province == province)
    if city:
        filters.append(Asset.city == city)
    if auction_stage:
        filters.append(Asset.auction_stage == auction_stage)
    if status:
        filters.append(Asset.status == status)
    if max_price is not None:
        filters.append(Asset.current_price <= max_price)
    requires_opportunity = any(
        value is not None for value in (grade, max_all_in_cost, min_safe_roi, max_unknown_costs)
    ) or production_only
    statement = select(Asset)
    count_statement = select(func.count(Asset.id))
    if requires_opportunity:
        statement = statement.join(Asset.opportunity)
        count_statement = count_statement.join(Asset.opportunity)
        if grade:
            filters.append(Opportunity.grade == grade)
        if max_all_in_cost is not None:
            filters.append(Opportunity.all_in_cost_max <= max_all_in_cost)
        if min_safe_roi is not None:
            filters.append(Opportunity.safe_roi >= min_safe_roi)
        if max_unknown_costs is not None:
            filters.append(Opportunity.unknown_cost_count <= max_unknown_costs)
        if production_only:
            filters.append(Opportunity.production_score >= 75)
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    total = db.scalar(count_statement) or 0
    items = db.scalars(
        statement.options(*_asset_options())
        .outerjoin(Asset.opportunity)
        .order_by(Opportunity.overall_score.desc(), Asset.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).unique().all()
    return AssetPage(items=list(items), total=total, page=page, page_size=page_size)


@router.get("/{asset_id}", response_model=AssetDetail)
def get_asset(asset_id: int, db: Session = Depends(get_db)) -> Asset:
    asset = db.scalar(
        select(Asset).where(Asset.id == asset_id).options(*_asset_options())
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    return asset
