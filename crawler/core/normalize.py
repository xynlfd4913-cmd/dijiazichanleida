"""Pure, deterministic normalization helpers for source adapters."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from typing import Any, Iterable, Mapping
CHINA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")
UNKNOWN_TEXT = frozenset(
    {
        "",
        "-",
        "--",
        "—",
        "未知",
        "不详",
        "暂无",
        "待核验",
        "null",
        "none",
        "unknown",
        "n/a",
        "na",
    }
)
MONEY_FIELDS = (
    "appraisal_price",
    "start_price",
    "current_price",
    "deposit",
    "bid_increment",
    "previous_round_price",
)


class NormalizationError(ValueError):
    """Raised when a record cannot satisfy the minimum canonical contract."""


def _first(raw: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in raw and raw[key] is not None:
            return raw[key]
    return default


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    if text.lower() in UNKNOWN_TEXT:
        return None
    return text


def normalize_money(value: Any) -> str | None:
    """Return a JSON-safe, two-decimal amount string; unknown never becomes 0."""

    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        amount = value
    elif isinstance(value, (int, float)):
        amount = Decimal(str(value))
    else:
        text = normalize_text(value)
        if text is None:
            return None
        multiplier = Decimal("10000") if "万" in text else Decimal("1")
        cleaned = (
            text.replace(",", "")
            .replace("，", "")
            .replace("人民币", "")
            .replace("RMB", "")
            .replace("rmb", "")
            .replace("CNY", "")
            .replace("¥", "")
            .replace("￥", "")
            .replace("万元", "")
            .replace("万", "")
            .replace("元", "")
            .strip()
        )
        match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
        if not match:
            return None
        try:
            amount = Decimal(match.group(0)) * multiplier
        except InvalidOperation:
            return None
    if not amount.is_finite():
        return None
    return format(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def normalize_timestamp(value: Any) -> str | None:
    """Normalize common source timestamps to ISO-8601 with an explicit zone."""

    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = normalize_text(value)
        if text is None:
            return None
        candidate = text.replace("年", "-").replace("月", "-").replace("日", " ")
        candidate = candidate.replace("/", "-").strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            parsed = None
            for date_format in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d",
            ):
                try:
                    parsed = datetime.strptime(candidate, date_format)
                    break
                except ValueError:
                    continue
            if parsed is None:
                raise NormalizationError(f"unsupported timestamp: {value!r}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=CHINA_TZ)
    return parsed.isoformat(timespec="seconds")


def normalize_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "是", "有", "支持"}:
        return True
    if text in {"0", "false", "no", "n", "否", "无", "不支持"}:
        return False
    return None


def _normalize_choice(value: Any, aliases: Mapping[str, str]) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    compact = text.lower().replace(" ", "")
    return aliases.get(compact, compact)


def _normalize_urls(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        values: Iterable[Any] = [value]
    elif isinstance(value, Iterable):
        values = value
    else:
        values = [value]
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        if isinstance(item, Mapping):
            item = _first(item, "url", "href", "source_url")
        url = normalize_text(item)
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result


def normalize_asset(
    raw: Mapping[str, Any],
    *,
    source_platform: str | None = None,
    source_mode: str | None = None,
) -> dict[str, Any]:
    """Normalize source aliases into the Phase 0 canonical asset mapping.

    Monetary values are decimal strings.  This keeps the adapter boundary JSON
    compatible and avoids binary floating-point changes before persistence.
    """

    external_id = normalize_text(_first(raw, "external_id", "item_id", "id", "auction_id"))
    title = normalize_text(_first(raw, "title", "name", "subject"))
    if not external_id:
        raise NormalizationError("external_id is required")
    if not title:
        raise NormalizationError("title is required")

    platform = normalize_text(source_platform or _first(raw, "source_platform", "platform"))
    if not platform:
        raise NormalizationError("source_platform is required")

    stage_aliases = {
        "一拍": "first",
        "第一次拍卖": "first",
        "first": "first",
        "二拍": "second",
        "第二次拍卖": "second",
        "second": "second",
        "变卖": "liquidation",
        "liquidation": "liquidation",
    }
    status_aliases = {
        "即将开始": "upcoming",
        "进行中": "active",
        "竞价中": "active",
        "已结束": "ended",
        "已成交": "sold",
        "成交": "sold",
        "流拍": "failed",
        "撤回": "withdrawn",
    }

    normalized: dict[str, Any] = {
        "source_platform": platform,
        "source_mode": normalize_text(source_mode or _first(raw, "source_mode", default="fixture")),
        "source_url": normalize_text(_first(raw, "source_url", "url", "detail_url")),
        "external_id": external_id,
        "title": title,
        "category": normalize_text(_first(raw, "category", "asset_type")),
        "subcategory": normalize_text(_first(raw, "subcategory", "asset_subtype")),
        "province": normalize_text(_first(raw, "province")),
        "city": normalize_text(_first(raw, "city")),
        "district": normalize_text(_first(raw, "district", "county")),
        "seller_or_court": normalize_text(_first(raw, "seller_or_court", "seller", "court")),
        "auction_stage": _normalize_choice(
            _first(raw, "auction_stage", "stage", "round"), stage_aliases
        ),
        "status": _normalize_choice(_first(raw, "status", "auction_status"), status_aliases),
        "start_time": normalize_timestamp(_first(raw, "start_time", "starts_at")),
        "end_time": normalize_timestamp(_first(raw, "end_time", "ends_at")),
        "payment_deadline": normalize_timestamp(
            _first(raw, "payment_deadline", "pay_before")
        ),
        "first_seen_at": normalize_timestamp(_first(raw, "first_seen_at")),
        "last_seen_at": normalize_timestamp(_first(raw, "last_seen_at", "fetched_at")),
        "previous_round_result": normalize_text(
            _first(raw, "previous_round_result", "last_round_result")
        ),
        "brand": normalize_text(_first(raw, "brand")),
        "model": normalize_text(_first(raw, "model")),
        "year": normalize_text(_first(raw, "year", "manufacture_year")),
        "quantity": normalize_text(_first(raw, "quantity", "qty")),
        "condition": normalize_text(_first(raw, "condition", "asset_condition")),
        "ownership_status": normalize_text(_first(raw, "ownership_status", "ownership")),
        "occupancy_status": normalize_text(_first(raw, "occupancy_status", "occupancy")),
        "inspection_available": normalize_bool(
            _first(raw, "inspection_available", "can_inspect")
        ),
        "attachment_urls": _normalize_urls(
            _first(raw, "attachment_urls", "attachments", "files")
        ),
        "announcement_text": normalize_text(
            _first(raw, "announcement_text", "announcement", "notice")
        ),
        "defect_description": normalize_text(
            _first(raw, "defect_description", "defects", "瑕疵说明")
        ),
        "tax_description": normalize_text(
            _first(raw, "tax_description", "taxes", "税费说明")
        ),
        "fee_description": normalize_text(
            _first(raw, "fee_description", "fees", "费用说明")
        ),
    }
    for field_name in MONEY_FIELDS:
        aliases = {
            "appraisal_price": ("appraisal_price", "assessed_price", "evaluation_price"),
            "start_price": ("start_price", "starting_price", "reserve_price"),
            "current_price": ("current_price", "latest_price", "price"),
            "deposit": ("deposit", "security_deposit"),
            "bid_increment": ("bid_increment", "increment"),
            "previous_round_price": ("previous_round_price", "last_round_price"),
        }[field_name]
        normalized[field_name] = normalize_money(_first(raw, *aliases))
    return normalized


__all__ = [
    "MONEY_FIELDS",
    "NormalizationError",
    "normalize_asset",
    "normalize_bool",
    "normalize_money",
    "normalize_text",
    "normalize_timestamp",
]
