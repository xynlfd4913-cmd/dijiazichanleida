from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from services.api.database import get_db
from services.api.models import Account, UserProfile
from services.api.schemas import ProfileRead, ProfileUpdate
from services.api.services.opportunities import refresh_all_opportunities

router = APIRouter(prefix="/api", tags=["profile"])


def _load_profile(db: Session) -> UserProfile:
    profile = db.scalar(
        select(UserProfile).where(UserProfile.id == 1).options(selectinload(UserProfile.accounts))
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="用户画像不存在")
    return profile


def _update_profile(payload: ProfileUpdate, db: Session) -> UserProfile:
    profile = _load_profile(db)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(profile, key, value)
    account_values = {
        "living_reserve": profile.living_reserve,
        "asset_capital": profile.available_capital,
        "debt_repayment_fund": profile.debt_repayment_fund,
    }
    accounts = {account.account_type: account for account in profile.accounts}
    for account_type, balance in account_values.items():
        account = accounts.get(account_type)
        if account is None:
            account = Account(
                profile=profile,
                account_type=account_type,
                protected=account_type != "asset_capital",
            )
            db.add(account)
        account.balance = balance
    refresh_all_opportunities(db, profile)
    db.commit()
    db.refresh(profile)
    return _load_profile(db)


@router.get("/profile", response_model=ProfileRead)
def get_profile(db: Session = Depends(get_db)) -> UserProfile:
    return _load_profile(db)


@router.put("/profile", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)) -> UserProfile:
    return _update_profile(payload, db)


@router.get("/settings", response_model=ProfileRead)
@router.get("/profile/settings", response_model=ProfileRead, include_in_schema=False)
def get_settings(db: Session = Depends(get_db)) -> UserProfile:
    return _load_profile(db)


@router.put("/settings", response_model=ProfileRead)
@router.put("/profile/settings", response_model=ProfileRead, include_in_schema=False)
def update_settings(payload: ProfileUpdate, db: Session = Depends(get_db)) -> UserProfile:
    return _update_profile(payload, db)
