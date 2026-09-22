from __future__ import annotations

from decimal import Decimal
import hashlib

import pytest

from crawler.adapters.ali_jianlou import AliJianlouAdapter, FixtureNotFoundError
from crawler.core.api_client import ApiClient, NetworkAccessDisabledError
from crawler.core.base_adapter import DiscoveryQuery


@pytest.fixture()
def adapter() -> AliJianlouAdapter:
    return AliJianlouAdapter(
        [
            {
                "external_id": "ALI-001",
                "title": "木工设备一批",
                "category": "机器设备",
                "province": "湖北",
                "city": "武汉",
                "current_price": "4,800元",
                "deposit": "500元",
                "source_url": "https://example.invalid/original/ALI-001",
                "attachments": [
                    {
                        "url": "fixture://ali_jianlou/ALI-001/notice.txt",
                        "name": "公告.txt",
                        "media_type": "text/plain",
                        "content": "现状交付，运输费用由买受人承担",
                    }
                ],
            },
            {
                "external_id": "ALI-002",
                "title": "外省车辆",
                "category": "车辆",
                "province": "湖南",
                "city": "长沙",
                "current_price": "8,000元",
            },
        ]
    )


def test_discover_uses_only_local_fixtures_and_applies_common_filters(
    adapter: AliJianlouAdapter,
) -> None:
    matches = adapter.discover(
        DiscoveryQuery(
            province="湖北",
            category="机器设备",
            max_price=Decimal("5000"),
        )
    )

    assert [record["external_id"] for record in matches] == ["ALI-001"]
    assert adapter.network_enabled is False


def test_fixture_detail_parse_normalize_and_attachment_pipeline(
    adapter: AliJianlouAdapter,
) -> None:
    detail = adapter.fetch_detail("ALI-001")
    parsed = adapter.parse(detail)
    normalized = adapter.normalize(parsed)
    attachments = adapter.fetch_attachments(detail)

    assert normalized["source_platform"] == "ali_jianlou"
    assert normalized["source_mode"] == "fixture"
    assert normalized["current_price"] == "4800.00"
    assert normalized["deposit"] == "500.00"
    assert attachments[0].sha256 == hashlib.sha256(
        "现状交付，运输费用由买受人承担".encode("utf-8")
    ).hexdigest()


def test_live_urls_are_rejected_in_phase_zero(adapter: AliJianlouAdapter) -> None:
    with pytest.raises(NetworkAccessDisabledError):
        adapter.fetch_detail("https://sf-item.example.invalid/ALI-001")
    with pytest.raises(NetworkAccessDisabledError):
        adapter.parse("https://sf-item.example.invalid/ALI-001")
    with pytest.raises(NetworkAccessDisabledError):
        adapter.fetch_attachments(
            {"attachments": ["https://files.example.invalid/notice.pdf"]}
        )
    with pytest.raises(NetworkAccessDisabledError):
        ApiClient().get("https://api.example.invalid/items")


def test_unknown_fixture_does_not_fall_back_to_network(adapter: AliJianlouAdapter) -> None:
    with pytest.raises(FixtureNotFoundError):
        adapter.fetch_detail("ALI-NOT-FOUND")
