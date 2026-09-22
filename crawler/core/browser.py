"""Offline browser boundary used by parser fixtures during Phase 0."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .api_client import NetworkAccessDisabledError


@dataclass(frozen=True, slots=True)
class BrowserPage:
    location: str
    content: str
    captured_at: str


class OfflineBrowser:
    """Reads HTML fixtures under one root and rejects navigation to the web."""

    def __init__(self, fixture_root: str | Path) -> None:
        self.fixture_root = Path(fixture_root).resolve()

    def open(self, location: str | Path) -> BrowserPage:
        raw_location = str(location)
        scheme = urlparse(raw_location).scheme.lower()
        if scheme in {"http", "https"}:
            raise NetworkAccessDisabledError(
                "Phase 0 browser navigation is disabled; use a local fixture path"
            )
        path = Path(location)
        if not path.is_absolute():
            path = self.fixture_root / path
        resolved = path.resolve()
        try:
            resolved.relative_to(self.fixture_root)
        except ValueError as error:
            raise ValueError("fixture path must stay inside fixture_root") from error
        content = resolved.read_text(encoding="utf-8")
        return BrowserPage(
            location=str(resolved),
            content=content,
            captured_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


__all__ = ["BrowserPage", "OfflineBrowser"]
