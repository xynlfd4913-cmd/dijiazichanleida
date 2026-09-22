"""Deterministic, in-process scheduling seam for Phase 0 tests and demos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from .base_adapter import MaybeAwaitable, maybe_await


JobCallback = Callable[[], MaybeAwaitable[Any]]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ScheduledJob:
    name: str
    interval: timedelta
    callback: JobCallback
    next_run_at: datetime
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.interval.total_seconds() <= 0:
            raise ValueError("job interval must be positive")
        if self.next_run_at.tzinfo is None:
            raise ValueError("next_run_at must be timezone-aware")


class LocalScheduler:
    """Runs only when ``run_due`` is explicitly called; starts no threads."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}

    def add_job(self, job: ScheduledJob) -> None:
        if job.name in self._jobs:
            raise ValueError(f"job already exists: {job.name}")
        self._jobs[job.name] = job

    def list_jobs(self) -> tuple[ScheduledJob, ...]:
        return tuple(sorted(self._jobs.values(), key=lambda job: job.name))

    def due(self, now: datetime | None = None) -> tuple[ScheduledJob, ...]:
        point = now or _utc_now()
        if point.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return tuple(
            job
            for job in sorted(self._jobs.values(), key=lambda item: item.next_run_at)
            if job.enabled and job.next_run_at <= point
        )

    async def run_due(self, now: datetime | None = None) -> dict[str, Any]:
        point = now or _utc_now()
        results: dict[str, Any] = {}
        for job in self.due(point):
            results[job.name] = await maybe_await(job.callback())
            while job.next_run_at <= point:
                job.next_run_at += job.interval
        return results


__all__ = ["LocalScheduler", "ScheduledJob"]
