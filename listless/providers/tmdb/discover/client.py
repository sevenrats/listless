"""Async HTTP client for the TMDB ``/discover`` endpoint.

Wraps ``/discover/movie`` and ``/discover/tv`` with transparent pagination
and local-only meta-parameters (``n``, ``recent_days``).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

import httpx

from listless.config import settings

log = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "en-US"


class TmdbDiscoverClient:
    """Paginated client for TMDB Discover queries."""

    def __init__(self, timeout: float | None = None) -> None:
        self._timeout = timeout or settings.default_http_timeout
        self._base = settings.tmdb_api_base
        self._key = settings.tmdb_api_key

    # ------------------------------------------------------------------ public

    def discover(
        self,
        media_type: str,
        *,
        raw_params: dict[str, Any] | None = None,
    ) -> list[int]:
        """Return up to *n* TMDB IDs from ``/discover/{media_type}``.

        Parameters
        ----------
        media_type:
            ``"movie"`` or ``"tv"``.
        raw_params:
            Arbitrary query-string parameters forwarded verbatim to
            TMDB, **plus** the local meta-params ``n`` and
            ``recent_days`` which are consumed here.
        """
        params = dict(raw_params or {})

        # ── Local-only params ────────────────────────────────────────
        n = int(params.pop("n", 20))
        n = max(1, min(n, 200))

        recent_days = int(params.pop("recent_days", 60))
        recent_days = max(1, min(recent_days, 365))

        # ── Defaults ─────────────────────────────────────────────────
        params.setdefault("sort_by", "popularity.desc")
        params.setdefault("language", DEFAULT_LANGUAGE)

        # ── Rolling date window (only if the caller didn't specify) ──
        today = date.today()
        start_date = today - timedelta(days=recent_days)

        if media_type == "tv":
            if not any(
                k.startswith("air_date.") or k.startswith("first_air_date.")
                for k in params
            ):
                params.setdefault("air_date.gte", start_date.isoformat())
                params.setdefault("air_date.lte", today.isoformat())
        else:  # movie
            if not any(k.startswith("primary_release_date.") for k in params):
                params.setdefault(
                    "primary_release_date.gte", start_date.isoformat()
                )
                params.setdefault(
                    "primary_release_date.lte", today.isoformat()
                )

        # ── Auth ─────────────────────────────────────────────────────
        params["api_key"] = self._key

        # ── Paginated fetch ──────────────────────────────────────────
        collected: list[int] = []
        page = int(params.pop("page", 1))
        page = max(1, page)

        with httpx.Client(timeout=self._timeout) as client:
            while len(collected) < n:
                params["page"] = str(page)
                url = f"{self._base}/discover/{media_type}"
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
