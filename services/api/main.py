"""FastAPI entry point for the offline Phase 0 MVP."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.database import Base, build_engine, build_session_factory, default_database_url
from services.api.routers import assets, dashboard, profile, subscriptions, system, watchlist
from services.api.seed import seed_database


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


def _web_origins() -> list[str]:
    configured = os.getenv("WEB_ORIGIN", "")
    values = [item.strip() for item in configured.split(",") if item.strip()]
    return values or ["http://localhost:3000", "http://127.0.0.1:3000"]


def create_app(database_url: str | None = None, *, seed: bool | None = None) -> FastAPI:
    url = (
        database_url
        or os.getenv("RADAR_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or default_database_url()
    )
    should_seed = _env_bool("SEED_ON_START", True) if seed is None else seed
    engine = build_engine(url)
    session_factory = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        Base.metadata.create_all(engine)
        if should_seed:
            with session_factory() as session:
                seed_database(session)
        yield
        engine.dispose()

    application = FastAPI(
        title="负债人低价资产雷达 API",
        description="Phase 0 离线模拟 API；不访问真实拍卖网站，不执行竞价或付款。",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.state.engine = engine
    application.state.session_factory = session_factory
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_web_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for api_router in (
        system.router,
        dashboard.router,
        assets.router,
        profile.router,
        subscriptions.router,
        watchlist.router,
    ):
        application.include_router(api_router)

    @application.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "service": "debt-asset-radar",
            "docs": "/docs",
            "mode": "offline_mock",
        }

    return application


app = create_app()
