"""Source adapters and Phase 0 placeholders."""

from .ali_jianlou import AliJianlouAdapter

PLANNED_SOURCES = (
    "ovupre",
    "gpai",
    "pccz",
    "jd_asset",
    "rmfysszc",
    "caa123",
)

__all__ = ["AliJianlouAdapter", "PLANNED_SOURCES"]
