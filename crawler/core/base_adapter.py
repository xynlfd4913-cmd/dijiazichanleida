"""Stable contract shared by every asset source.

Adapters may implement their source operations as ordinary functions or as
coroutines.  Callers that do not know which style an adapter uses should call
the ``a*`` facade methods (``adiscover``, ``afetch_detail`` and so on).

Fingerprinting and structural diffing are deliberately source-independent and
deterministic.  They operate on normalized JSON-like values only and ignore
observation timestamps by default.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import hashlib
import inspect
import json
from typing import Any, Awaitable, Generic, Mapping, Sequence, TypeVar


JsonMapping = Mapping[str, Any]
T = TypeVar("T")
MaybeAwaitable = T | Awaitable[T]


@dataclass(frozen=True, slots=True)
class DiscoveryQuery:
    """Source-neutral filters used during discovery.

    ``extras`` is the escape hatch for a source-specific filter.  Business
    logic must not rely on fields placed there until they are promoted into the
    common contract.
    """

    province: str | None = None
    city: str | None = None
    category: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    limit: int = 100
    extras: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.limit <= 0:
            raise ValueError("limit must be greater than zero")
        if (
            self.min_price is not None
            and self.max_price is not None
            and self.min_price > self.max_price
        ):
            raise ValueError("min_price cannot exceed max_price")


@dataclass(frozen=True, slots=True)
class Attachment:
    """Attachment metadata; fetching bytes is a separate source concern."""

    url: str
    name: str | None = None
    media_type: str | None = None
    sha256: str | None = None
    content: bytes | None = field(default=None, repr=False, compare=False)


class ChangeKind(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True, slots=True)
class AdapterChange:
    """One JSON-pointer-addressed change between two normalized documents."""

    path: str
    kind: ChangeKind
    before: Any = None
    after: Any = None


@dataclass(frozen=True, slots=True)
class AdapterDiff:
    before_fingerprint: str
    after_fingerprint: str
    changes: tuple[AdapterChange, ...]

    @property
    def changed(self) -> bool:
        return bool(self.changes)


async def maybe_await(value: MaybeAwaitable[T]) -> T:
    """Resolve a synchronous value or awaitable without guessing its origin."""

    if inspect.isawaitable(value):
        return await value
    return value


def _json_pointer_part(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def _canonicalize(value: Any, ignored_fields: frozenset[str]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _canonicalize(item, ignored_fields)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
            if str(key) not in ignored_fields
        }
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item, ignored_fields) for item in value]
    if isinstance(value, (set, frozenset)):
        canonical_items = [_canonicalize(item, ignored_fields) for item in value]
        return sorted(
            canonical_items,
            key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True),
        )
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, bytes):
        return {"$bytes_sha256": hashlib.sha256(value).hexdigest()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported fingerprint value: {type(value).__name__}")


def _diff_values(before: Any, after: Any, path: str = "") -> list[AdapterChange]:
    if isinstance(before, Mapping) and isinstance(after, Mapping):
        changes: list[AdapterChange] = []
        before_keys = set(before)
        after_keys = set(after)
        for key in sorted(before_keys - after_keys, key=str):
            child_path = f"{path}/{_json_pointer_part(key)}"
            changes.append(
                AdapterChange(child_path, ChangeKind.REMOVED, before=before[key])
            )
        for key in sorted(after_keys - before_keys, key=str):
            child_path = f"{path}/{_json_pointer_part(key)}"
            changes.append(
                AdapterChange(child_path, ChangeKind.ADDED, after=after[key])
            )
        for key in sorted(before_keys & after_keys, key=str):
            child_path = f"{path}/{_json_pointer_part(key)}"
            changes.extend(_diff_values(before[key], after[key], child_path))
        return changes

    if isinstance(before, list) and isinstance(after, list):
        changes = []
        shared_length = min(len(before), len(after))
        for index in range(shared_length):
            changes.extend(_diff_values(before[index], after[index], f"{path}/{index}"))
        for index in range(shared_length, len(before)):
            changes.append(
                AdapterChange(f"{path}/{index}", ChangeKind.REMOVED, before=before[index])
            )
        for index in range(shared_length, len(after)):
            changes.append(
                AdapterChange(f"{path}/{index}", ChangeKind.ADDED, after=after[index])
            )
        return changes

    if before != after:
        return [AdapterChange(path or "/", ChangeKind.CHANGED, before, after)]
    return []


class BaseAdapter(ABC, Generic[T]):
    """Adapter interface for API, HTML, browser, or fixture-backed sources."""

    source_platform: str
    source_mode: str = "fixture"
    volatile_fields: frozenset[str] = frozenset(
        {"first_seen_at", "last_seen_at", "fetched_at", "captured_at"}
    )

    @abstractmethod
    def discover(self, query: DiscoveryQuery) -> MaybeAwaitable[Sequence[T]]:
        """Return lightweight source records matching ``query``."""

    @abstractmethod
    def fetch_detail(self, record: T | str) -> MaybeAwaitable[Any]:
        """Load the source detail representation for a record or external id."""

    @abstractmethod
    def fetch_attachments(self, detail: Any) -> MaybeAwaitable[Sequence[Attachment]]:
        """Return attachment descriptors/content allowed by the active source mode."""

    @abstractmethod
    def parse(self, raw: Any) -> MaybeAwaitable[JsonMapping]:
        """Parse a raw response or fixture into a source-shaped mapping."""

    @abstractmethod
    def normalize(self, parsed: JsonMapping) -> MaybeAwaitable[dict[str, Any]]:
        """Map source-shaped data into the canonical asset contract."""

    def fingerprint(self, normalized: JsonMapping) -> str:
        canonical = _canonicalize(normalized, self.volatile_fields)
        encoded = json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def diff(self, before: JsonMapping, after: JsonMapping) -> AdapterDiff:
        canonical_before = _canonicalize(before, self.volatile_fields)
        canonical_after = _canonicalize(after, self.volatile_fields)
        return AdapterDiff(
            before_fingerprint=self.fingerprint(before),
            after_fingerprint=self.fingerprint(after),
            changes=tuple(_diff_values(canonical_before, canonical_after)),
        )

    async def adiscover(self, query: DiscoveryQuery) -> Sequence[T]:
        return await maybe_await(self.discover(query))

    async def afetch_detail(self, record: T | str) -> Any:
        return await maybe_await(self.fetch_detail(record))

    async def afetch_attachments(self, detail: Any) -> Sequence[Attachment]:
        return await maybe_await(self.fetch_attachments(detail))

    async def aparse(self, raw: Any) -> JsonMapping:
        return await maybe_await(self.parse(raw))

    async def anormalize(self, parsed: JsonMapping) -> dict[str, Any]:
        return await maybe_await(self.normalize(parsed))
