"""Filesystem snapshot storage for normalized, non-secret asset records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping

from .base_adapter import AdapterDiff, BaseAdapter


_SAFE_SEGMENT = re.compile(r"[^a-zA-Z0-9._-]+")


def _segment(value: str) -> str:
    result = _SAFE_SEGMENT.sub("_", value).strip("._")
    if not result:
        raise ValueError("snapshot identifier is empty after sanitization")
    return result[:120]


def _json_default(value: Any) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"cannot serialize {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class Snapshot:
    source_platform: str
    external_id: str
    captured_at: str
    fingerprint: str
    payload: Mapping[str, Any]


class SnapshotStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def capture(
        self,
        adapter: BaseAdapter[Any],
        payload: Mapping[str, Any],
        *,
        captured_at: datetime | None = None,
    ) -> tuple[Snapshot, Path]:
        source = str(payload.get("source_platform") or adapter.source_platform)
        external_id = str(payload.get("external_id") or "")
        if not external_id:
            raise ValueError("external_id is required for a snapshot")
        point = captured_at or datetime.now(timezone.utc)
        if point.tzinfo is None:
            raise ValueError("captured_at must be timezone-aware")
        point = point.astimezone(timezone.utc)
        snapshot = Snapshot(
            source_platform=source,
            external_id=external_id,
            captured_at=point.isoformat(timespec="seconds"),
            fingerprint=adapter.fingerprint(payload),
            payload=dict(payload),
        )
        directory = (self.root / _segment(source) / _segment(external_id)).resolve()
        try:
            directory.relative_to(self.root)
        except ValueError as error:
            raise ValueError("snapshot directory must stay inside snapshot root") from error
        directory.mkdir(parents=True, exist_ok=True)
        stamp = point.strftime("%Y%m%dT%H%M%S%fZ")
        target = directory / f"{stamp}-{snapshot.fingerprint[:12]}.json"
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            prefix=".snapshot-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(asdict(snapshot), handle, ensure_ascii=False, indent=2, default=_json_default)
            temporary = Path(handle.name)
        temporary.replace(target)
        return snapshot, target

    def list_paths(self, source_platform: str, external_id: str) -> tuple[Path, ...]:
        directory = self.root / _segment(source_platform) / _segment(external_id)
        if not directory.exists():
            return ()
        return tuple(sorted(directory.glob("*.json")))

    def load(self, path: str | Path) -> Snapshot:
        resolved = Path(path).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as error:
            raise ValueError("snapshot path must stay inside snapshot root") from error
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        return Snapshot(**payload)

    def latest(self, source_platform: str, external_id: str) -> Snapshot | None:
        paths = self.list_paths(source_platform, external_id)
        return self.load(paths[-1]) if paths else None

    def diff_latest(
        self,
        adapter: BaseAdapter[Any],
        current: Mapping[str, Any],
    ) -> AdapterDiff | None:
        source = str(current.get("source_platform") or adapter.source_platform)
        external_id = str(current.get("external_id") or "")
        latest = self.latest(source, external_id) if external_id else None
        return adapter.diff(latest.payload, current) if latest else None


__all__ = ["Snapshot", "SnapshotStore"]
