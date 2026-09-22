from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from engine.capital import CAPITAL_LEVELS, capital_progress
from services.api.database import get_db
from services.api.models import Asset, CostItem, UserProfile

router = APIRouter(tags=["system"])


@router.get("/health")
def health(request: Request, db: Session = Depends(get_db)) -> dict[str, object]:
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "database": "ok",
        "mode": "offline_mock",
        "network_access": False,
        "version": request.app.version,
    }


@router.get("/api/capital-ladder")
def capital_ladder(db: Session = Depends(get_db)) -> dict[str, object]:
    profile = db.get(UserProfile, 1)
    capital = profile.available_capital if profile else 0
    progress = capital_progress(capital)
    return {
        "current": asdict(progress),
        "levels": [
            {
                "code": level.code,
                "threshold": level.threshold,
                "focus": level.focus,
                "unlocked": capital >= level.threshold,
            }
            for level in CAPITAL_LEVELS
        ],
    }


@router.get("/api/admin/status")
def admin_status(db: Session = Depends(get_db)) -> dict[str, object]:
    grouped = db.execute(
        select(Asset.source_platform, func.count(Asset.id)).group_by(Asset.source_platform)
    ).all()
    unknown_count = db.scalar(
        select(func.count(CostItem.id)).where(CostItem.status == "unknown")
    ) or 0
    return {
        "runtime_mode": "offline_mock",
        "real_network_enabled": False,
        "database": "sqlite",
        "sources": [
            {
                "name": platform,
                "mode": "mock",
                "status": "seeded",
                "asset_count": count,
                "last_scan": "2026-09-22T08:00:00+00:00",
            }
            for platform, count in grouped
        ],
        "totals": {
            "assets": sum(count for _, count in grouped),
            "unknown_cost_items": unknown_count,
            "crawler_errors": 0,
            "structure_change_alerts": 0,
        },
        "scheduler": {
            "enabled": False,
            "reason": "Phase 0 禁止连接真实网站；仅保留后续接口位置。",
        },
    }

