"""Explicit placeholders for sources that are outside Phase 0."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from crawler.core.base_adapter import Attachment, BaseAdapter, DiscoveryQuery


class SourceNotImplementedError(RuntimeError):
    pass


class PlannedSourceAdapter(BaseAdapter[Mapping[str, Any]]):
    source_platform = "planned"

    def _unavailable(self) -> SourceNotImplementedError:
        return SourceNotImplementedError(
            f"{self.source_platform} is a planned source and is not implemented in Phase 0"
        )

    def discover(self, query: DiscoveryQuery) -> Sequence[Mapping[str, Any]]:
        raise self._unavailable()

    def fetch_detail(self, record: Mapping[str, Any] | str) -> Any:
        raise self._unavailable()

    def fetch_attachments(self, detail: Any) -> Sequence[Attachment]:
        raise self._unavailable()

    def parse(self, raw: Any) -> Mapping[str, Any]:
        raise self._unavailable()

    def normalize(self, parsed: Mapping[str, Any]) -> dict[str, Any]:
        raise self._unavailable()


__all__ = ["PlannedSourceAdapter", "SourceNotImplementedError"]
