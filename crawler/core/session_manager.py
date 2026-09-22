"""Non-secret local session metadata store for Phase 0.

Cookies, tokens, and browser storage are intentionally outside this contract.
Phase 1 may add an encrypted secret store after an explicit security review.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile


_SAFE_SOURCE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@dataclass(frozen=True, slots=True)
class SessionMetadata:
    source: str
    state: str = "not_configured"
    created_at: str | None = None
    expires_at: str | None = None
    profile_hint: str | None = None
    notes: str | None = None


class SessionManager:
    """Persist harmless session state without authentication material."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    @staticmethod
    def _validate_source(source: str) -> None:
        if not _SAFE_SOURCE.fullmatch(source):
            raise ValueError("source must be a lowercase identifier")

    def save(self, metadata: SessionMetadata) -> Path:
        self._validate_source(metadata.source)
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{metadata.source}.json"
        payload = asdict(metadata)
        if payload["created_at"] is None:
            payload["created_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.root,
            prefix=f".{metadata.source}-",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            temporary = Path(handle.name)
        temporary.replace(target)
        return target

    def load(self, source: str) -> SessionMetadata | None:
        self._validate_source(source)
        target = self.root / f"{source}.json"
        if not target.exists():
            return None
        payload = json.loads(target.read_text(encoding="utf-8"))
        return SessionMetadata(**payload)


__all__ = ["SessionManager", "SessionMetadata"]
