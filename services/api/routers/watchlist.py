from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from services.api.database import get_db
from services.api.models import Asset, Watchlist
from services.api.schemas import WatchlistCreate, WatchlistRead

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


def _options():
    return selectinload(Watchlist.asset).options(
        selectinload(Asset.cost_items),
        selectinload(Asset.comparables),
        selectinload(Asset.opportunity),
    )


@router.get("", response_model=list[WatchlistRead])
def list_watchlist(db: Session = Depends(get_db)) -> list[Watchlist]:
    return list(db.scalars(select(Watchlist).options(_options()).order_by(Watchlist.id)).all())


@router.post("", response_model=WatchlistRead, status_code=status.HTTP_201_CREATED)
def add_watchlist(payload: WatchlistCreate, db: Session = Depends(get_db)) -> Watchlist:
    if db.get(Asset, payload.asset_id) is None:
        raise HTTPException(status_code=404, detail="资产不存在")
    existing = db.scalar(
        select(Watchlist).where(Watchlist.profile_id == 1, Watchlist.asset_id == payload.asset_id)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="资产已在关注列表")
    item = Watchlist(profile_id=1, **payload.model_dump())
    db.add(item)
    db.commit()
    return db.scalar(select(Watchlist).where(Watchlist.id == item.id).options(_options()))


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_watchlist(asset_id: int, db: Session = Depends(get_db)) -> Response:
    item = db.scalar(
        select(Watchlist).where(Watchlist.profile_id == 1, Watchlist.asset_id == asset_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="关注记录不存在")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

