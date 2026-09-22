from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any, Mapping, Sequence

from crawler.core.base_adapter import Attachment, BaseAdapter, DiscoveryQuery


class SyncAdapter(BaseAdapter[Mapping[str, Any]]):
    source_platform = "test"

    def discover(self, query: DiscoveryQuery) -> Sequence[Mapping[str, Any]]:
        return ({"external_id": "one", "limit": query.limit},)

    def fetch_detail(self, record: Mapping[str, Any] | str) -> Any:
        return record

    def fetch_attachments(self, detail: Any) -> Sequence[Attachment]:
        return ()

    def parse(self, raw: Any) -> Mapping[str, Any]:
        return dict(raw)

    def normalize(self, parsed: Mapping[str, Any]) -> dict[str, Any]:
        return dict(parsed)


class AsyncAdapter(SyncAdapter):
    async def discover(self, query: DiscoveryQuery) -> Sequence[Mapping[str, Any]]:
        return ({"external_id": "async", "limit": query.limit},)


def test_fingerprint_is_stable_and_ignores_observation_timestamps() -> None:
    adapter = SyncAdapter()
    first = {
        "external_id": "A-1",
        "price": Decimal("5000.00"),
        "nested": {"b": 2, "a": 1},
        "last_seen_at": "2026-09-22T08:00:00+08:00",
    }
    second = {
        "nested": {"a": 1, "b": 2},
        "last_seen_at": "2026-09-22T09:00:00+08:00",
        "price": Decimal("5000.00"),
        "external_id": "A-1",
    }

    assert adapter.fingerprint(first) == adapter.fingerprint(second)


def test_diff_reports_nested_added_removed_and_changed_paths() -> None:
    adapter = SyncAdapter()
    result = adapter.diff(
        {
            "external_id": "A-1",
            "price": "5000.00",
            "fees": {"transport": None, "legacy": "remove"},
            "tags": ["machine"],
        },
        {
            "external_id": "A-1",
            "price": "4800.00",
            "fees": {"transport": "300.00", "repair": None},
            "tags": ["machine", "woodworking"],
        },
    )

    assert result.changed is True
    assert result.before_fingerprint != result.after_fingerprint
    assert {(change.path, change.kind.value) for change in result.changes} == {
        ("/price", "changed"),
        ("/fees/legacy", "removed"),
        ("/fees/repair", "added"),
        ("/fees/transport", "changed"),
        ("/tags/1", "added"),
    }


def test_async_facade_accepts_sync_and_async_implementations() -> None:
    query = DiscoveryQuery(limit=3)
    sync_result = asyncio.run(SyncAdapter().adiscover(query))
    async_result = asyncio.run(AsyncAdapter().adiscover(query))

    assert sync_result[0]["external_id"] == "one"
    assert async_result[0]["external_id"] == "async"


def test_discovery_query_rejects_an_inverted_price_range() -> None:
    try:
        DiscoveryQuery(min_price=Decimal("5000"), max_price=Decimal("3000"))
    except ValueError as error:
        assert "min_price" in str(error)
    else:
        raise AssertionError("expected an invalid price range to fail")
