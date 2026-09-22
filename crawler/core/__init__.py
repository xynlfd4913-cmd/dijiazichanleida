"""Shared crawler primitives.

Phase 0 intentionally contains no live HTTP or browser implementation.
"""

from .base_adapter import (
    AdapterChange,
    AdapterDiff,
    Attachment,
    BaseAdapter,
    DiscoveryQuery,
    maybe_await,
)

__all__ = [
    "AdapterChange",
    "AdapterDiff",
    "Attachment",
    "BaseAdapter",
    "DiscoveryQuery",
    "maybe_await",
]
