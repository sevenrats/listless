"""Async HTTP client for the TMDB ``/movie/popular`` and ``/tv/popular`` endpoints.

Provides a simple paginated fetch that returns raw TMDB IDs.
"""

from __future__ import annotations

import logging

import httpx

from listless.config import settings

log = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en-US"


class TmdbPopularClient:
    """Paginated client for TMDB Popular lists."""

    def __init__(self, timeout: float | None = None) -> None:
        self._timeout = timeout or settings.default_http_timeout
        self._base = settings.tmdb_api_base
        self._key = settings.tmdb_api_key

    # ------------------------------------------------------------------ public

    def popular(
        self,
        media_type: str,
        *,
        language: str = DEFAULT_LANGUAGE,
        region: str | None = None,
        n: int = 20,
        page: int = 1,
    ) -> list[int]:
        """Return up to *n* TMDB IDs from ``/{media_type}/popular``.

        Parameters
        ----------
        media_type:
            ``"movie"`` or ``"tv"``.
        language:
            TMDB language tag, e.g. ``en-US``.
        region:
            ISO 3166-1 code to filter by release region (movies only).
        n:
            Maximum results to return (1-200).
        page:
            Starting page number (≥ 1).
        """
        n = max(1, min(n, 200))
        page = max(1, page)

        params: dict[str, str] = {
            "api_key": self._key,
            "language": language,
        }
        if region:
            params["region"] = region

        collected: list[int] = []

        with httpx.Client(timeout=self._timeout) as client:
            while len(collected) < n:
                params["page"] = str(page)
                url = f"{self._base}/{media_type}/popular"
                resp = client.get(url, params=params)
                resp.raise_for_status()

                payload = resp.json()
                results = payload.get("results", [])
                if not results:
                    break

                collected.extend(r["id"] for r in results)

                if page >= payload.get("total_pages", page):
                    break
                page += 1

        return collected[:n]
