from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import pytest

from crawler.core.api_client import ApiClient, ApiResponse, NetworkAccessDisabledError
from crawler.core.base_adapter import Attachment, BaseAdapter, DiscoveryQuery
from crawler.core.browser import OfflineBrowser
from crawler.core.scheduler import LocalScheduler, ScheduledJob
from crawler.core.session_manager import SessionManager, SessionMetadata
from crawler.core.snapshot import SnapshotStore


class FixtureAdapter(BaseAdapter[Mapping[str, Any]]):
    source_platform = "fixture_source"

    def discover(self, query: DiscoveryQuery) -> Sequence[Mapping[str, Any]]:
        return ()

    def fetch_detail(self, record: Mapping[str, Any] | str) -> Any:
        return record

    def fetch_attachments(self, detail: Any) -> Sequence[Attachment]:
        return ()

    def parse(self, raw: Any) -> Mapping[str, Any]:
        return dict(raw)

    def normalize(self, parsed: Mapping[str, Any]) -> dict[str, Any]:
        return dict(parsed)


def test_api_client_only_serves_registered_fixture_urls() -> None:
    client = ApiClient(
        {
            ("GET", "fixture://source/items"): ApiResponse(
                status_code=200, data={"items": [1]}
            )
        }
    )

    response = client.get("fixture://source/items")
    response.data["items"].append(2)
    assert client.get("fixture://source/items").data == {"items": [1]}
    with pytest.raises(NetworkAccessDisabledError):
        client.get("http://127.0.0.1:8000/items")


def test_offline_browser_stays_inside_fixture_root(tmp_path: Path) -> None:
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    page_path = fixture_root / "detail.html"
    page_path.write_text("<h1>本地标的</h1>", encoding="utf-8")
    browser = OfflineBrowser(fixture_root)

    assert "本地标的" in browser.open("detail.html").content
    with pytest.raises(ValueError, match="inside"):
        browser.open("../outside.html")
    with pytest.raises(NetworkAccessDisabledError):
        browser.open("https://example.invalid")


def test_session_manager_persists_metadata_without_secret_fields(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path / "sessions")
    path = manager.save(
        SessionMetadata(source="ali_jianlou", state="not_configured", notes="Phase 0")
    )

    assert path.exists()
    assert manager.load("ali_jianlou") is not None
    assert "cookie" not in path.read_text(encoding="utf-8").lower()
    with pytest.raises(ValueError):
        manager.load("../escape")


def test_scheduler_is_explicit_and_supports_async_callbacks() -> None:
    now = datetime(2026, 9, 22, 0, 0, tzinfo=timezone.utc)
    scheduler = LocalScheduler()

    async def callback() -> str:
        return "ran"

    job = ScheduledJob(
        name="fixture_scan",
        interval=timedelta(hours=2),
        callback=callback,
        next_run_at=now,
    )
    scheduler.add_job(job)

    assert asyncio.run(scheduler.run_due(now)) == {"fixture_scan": "ran"}
    assert scheduler.due(now) == ()
    assert job.next_run_at == now + timedelta(hours=2)


def test_snapshot_store_round_trip_and_diff(tmp_path: Path) -> None:
    adapter = FixtureAdapter()
    store = SnapshotStore(tmp_path / "snapshots")
    initial = {
        "source_platform": "fixture_source",
        "external_id": "A-1",
        "current_price": "5000.00",
    }
    snapshot, path = store.capture(
        adapter,
        initial,
        captured_at=datetime(2026, 9, 22, tzinfo=timezone.utc),
    )

    assert path.exists()
    assert store.latest("fixture_source", "A-1") == snapshot
    difference = store.diff_latest(adapter, {**initial, "current_price": "4800.00"})
    assert difference is not None
    assert [change.path for change in difference.changes] == ["/current_price"]
