from __future__ import annotations

import pytest

from crawler.core.normalize import (
    NormalizationError,
    normalize_asset,
    normalize_money,
    normalize_timestamp,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("￥5,000元", "5000.00"),
        ("1.25万元", "12500.00"),
        (3000, "3000.00"),
        ("未知", None),
        (None, None),
    ],
)
def test_normalize_money_preserves_unknown_and_decimal_precision(raw: object, expected: str | None) -> None:
    assert normalize_money(raw) == expected


def test_normalize_asset_maps_aliases_without_inventing_unknown_costs() -> None:
    normalized = normalize_asset(
        {
            "item_id": 123,
            "name": "  木工设备   一批 ",
            "asset_type": "机器设备",
            "province": "湖北",
            "city": "武汉",
            "starting_price": "3,200元",
            "price": "未知",
            "security_deposit": "500",
            "stage": "第二次拍卖",
            "auction_status": "竞价中",
            "starts_at": "2026-09-22 07:30",
            "attachments": [
                {"url": "fixture://ali_jianlou/123/notice.pdf"},
                "fixture://ali_jianlou/123/notice.pdf",
            ],
        },
        source_platform="ali_jianlou",
        source_mode="fixture",
    )

    assert normalized["external_id"] == "123"
    assert normalized["title"] == "木工设备 一批"
    assert normalized["start_price"] == "3200.00"
    assert normalized["current_price"] is None
    assert normalized["deposit"] == "500.00"
    assert normalized["auction_stage"] == "second"
    assert normalized["status"] == "active"
    assert normalized["start_time"] == "2026-09-22T07:30:00+08:00"
    assert normalized["attachment_urls"] == [
        "fixture://ali_jianlou/123/notice.pdf"
    ]


def test_normalize_asset_requires_identity_and_title() -> None:
    with pytest.raises(NormalizationError, match="external_id"):
        normalize_asset({"title": "无编号"}, source_platform="test")
    with pytest.raises(NormalizationError, match="title"):
        normalize_asset({"external_id": "A-1"}, source_platform="test")


def test_normalize_timestamp_rejects_ambiguous_text() -> None:
    with pytest.raises(NormalizationError):
        normalize_timestamp("下周某天")
