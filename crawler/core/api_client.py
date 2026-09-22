"""Phase 0 API seam backed exclusively by registered in-memory fixtures."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urlparse


class NetworkAccessDisabledError(RuntimeError):
    """Raised whenever Phase 0 code attempts to address a live endpoint."""


@dataclass(frozen=True, slots=True)
class ApiResponse:
    status_code: int
    data: Any
    headers: Mapping[str, str] = field(default_factory=dict)

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise RuntimeError(f"fixture API returned status {self.status_code}")


class ApiClient:
    """Local-only placeholder preserving the future HTTP-client boundary.

    Only ``fixture://`` URLs can be registered or requested.  There is no
    hidden environment switch that can enable network traffic in Phase 0.
    """

    def __init__(self, fixtures: Mapping[tuple[str, str], ApiResponse] | None = None) -> None:
        self._fixtures: dict[tuple[str, str], ApiResponse] = {}
        for (method, url), response in (fixtures or {}).items():
            self.register(method, url, response)

    @staticmethod
    def _assert_fixture_url(url: str) -> None:
        if urlparse(url).scheme != "fixture":
            raise NetworkAccessDisabledError(
                "Phase 0 API access is fixture-only; live network access is disabled"
            )

    def register(self, method: str, url: str, response: ApiResponse) -> None:
        self._assert_fixture_url(url)
        self._fixtures[(method.upper(), url)] = response

    def request(self, method: str, url: str, **_: Any) -> ApiResponse:
        self._assert_fixture_url(url)
        key = (method.upper(), url)
        if key not in self._fixtures:
            raise KeyError(f"no API fixture registered for {method.upper()} {url}")
        response = self._fixtures[key]
        return ApiResponse(
            status_code=response.status_code,
            data=deepcopy(response.data),
            headers=dict(response.headers),
        )

    def get(self, url: str, **kwargs: Any) -> ApiResponse:
        return self.request("GET", url, **kwargs)


__all__ = ["ApiClient", "ApiResponse", "NetworkAccessDisabledError"]
