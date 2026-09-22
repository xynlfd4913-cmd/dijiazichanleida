"""Ali Jianlou Phase 0 adapter.

This module intentionally has no HTTP, Playwright, cookie, or login imports.
It accepts caller-supplied fixtures so the complete adapter pipeline can be
developed and tested without contacting a real platform.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

from crawler.core.api_client import NetworkAccessDisabledError
from crawler.core.base_adapter import Attachment, BaseAdapter, DiscoveryQuery
from crawler.core.normalize import normalize_asset, normalize_money, normalize_text


class FixtureNotFoundError(KeyError):
    pass


class UnsupportedFixtureError(ValueError):
    pass


class AliJianlouAdapter(BaseAdapter[Mapping[str, Any]]):
    """Offline fixture implementation of the future Ali source contract."""

    source_platform = "ali_jianlou"
    source_mode = "fixture"
    phase = 0
    network_enabled = False

    def __init__(self, fixtures: Iterable[Mapping[str, Any]] = ()) -> None:
        self._fixtures: dict[str, dict[str, Any]] = {}
        for fixture in fixtures:
            identifier = normalize_text(
                fixture.get("external_id") or fixture.get("item_id") or fixture.get("id")
            )
            if not identifier:
                raise UnsupportedFixtureError("every fixture requires an external_id")
            if identifier in self._fixtures:
                raise UnsupportedFixtureError(f"duplicate fixture external_id: {identifier}")
            self._fixtures[identifier] = deepcopy(dict(fixture))

    @staticmethod
    def _price(record: Mapping[str, Any]) -> Decimal | None:
        value = (
            record.get("current_price")
            or record.get("start_price")
            or record.get("price")
        )
        normalized = normalize_money(value)
        return Decimal(normalized) if normalized is not None else None

    def discover(self, query: DiscoveryQuery) -> Sequence[Mapping[str, Any]]:
        results: list[Mapping[str, Any]] = []
        for record in self._fixtures.values():
            province = normalize_text(record.get("province"))
            city = normalize_text(record.get("city"))
            category = normalize_text(record.get("category") or record.get("asset_type"))
            price = self._price(record)
            if query.province and province != query.province:
                continue
            if query.city and city != query.city:
                continue
            if query.category and category != query.category:
                continue
            if query.min_price is not None and (price is None or price < query.min_price):
                continue
            if query.max_price is not None and (price is None or price > query.max_price):
                continue
            results.append(deepcopy(record))
            if len(results) >= query.limit:
                break
        return tuple(results)

    def fetch_detail(self, record: Mapping[str, Any] | str) -> Mapping[str, Any]:
        if isinstance(record, Mapping):
            identifier = normalize_text(
                record.get("external_id") or record.get("item_id") or record.get("id")
            )
        else:
            scheme = urlparse(record).scheme.lower()
            if scheme in {"http", "https"}:
                raise NetworkAccessDisabledError(
                    "Ali Jianlou Phase 0 is fixture-only and cannot fetch a live URL"
                )
            identifier = record.removeprefix("fixture://ali_jianlou/")
        if not identifier or identifier not in self._fixtures:
            raise FixtureNotFoundError(f"Ali Jianlou fixture not found: {identifier!r}")
        return deepcopy(self._fixtures[identifier])

    def fetch_attachments(self, detail: Any) -> Sequence[Attachment]:
        if not isinstance(detail, Mapping):
            raise UnsupportedFixtureError("attachment detail must be a mapping")
        raw_attachments = detail.get("attachments") or detail.get("attachment_urls") or []
        if isinstance(raw_attachments, (str, bytes)):
            raw_attachments = [raw_attachments]
        attachments: list[Attachment] = []
        for item in raw_attachments:
            if isinstance(item, Mapping):
                url = normalize_text(item.get("url") or item.get("href"))
                name = normalize_text(item.get("name"))
                media_type = normalize_text(item.get("media_type") or item.get("content_type"))
                raw_content = item.get("content")
            else:
                url = normalize_text(item)
                name = None
                media_type = None
                raw_content = None
            if not url:
                raise UnsupportedFixtureError("attachment fixture requires a URL")
            if urlparse(url).scheme != "fixture":
                raise NetworkAccessDisabledError(
                    "Ali Jianlou Phase 0 attachments must use fixture:// URLs"
                )
            if raw_content is None:
                content = None
            elif isinstance(raw_content, bytes):
                content = raw_content
            else:
                content = str(raw_content).encode("utf-8")
            digest = hashlib.sha256(content).hexdigest() if content is not None else None
            attachments.append(
                Attachment(
                    url=url,
                    name=name,
                    media_type=media_type,
                    sha256=digest,
                    content=content,
                )
            )
        return tuple(attachments)

    def parse(self, raw: Any) -> Mapping[str, Any]:
        if isinstance(raw, Mapping):
            return deepcopy(dict(raw))
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        if isinstance(raw, str):
            if urlparse(raw).scheme in {"http", "https"}:
                raise NetworkAccessDisabledError(
                    "parse accepts fixture content, not a live URL"
                )
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as error:
                raise UnsupportedFixtureError(
                    "Phase 0 Ali parser accepts JSON fixture content only"
                ) from error
            if not isinstance(parsed, Mapping):
                raise UnsupportedFixtureError("Ali fixture JSON must contain an object")
            return dict(parsed)
        raise UnsupportedFixtureError(
            f"unsupported Ali fixture type: {type(raw).__name__}"
        )

    def normalize(self, parsed: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_asset(
            parsed,
            source_platform=self.source_platform,
            source_mode=self.source_mode,
        )


__all__ = ["AliJianlouAdapter", "FixtureNotFoundError", "UnsupportedFixtureError"]
