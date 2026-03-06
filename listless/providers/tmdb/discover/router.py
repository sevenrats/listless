"""FastAPI routers for the TMDB Discover subprovider.

Endpoints
---------
GET /tmdb/discover/movies  → ``[{"TmdbId": …}, …]``  (Radarr list)
GET /tmdb/discover/series  → ``[{"TvdbId": …}, …]``   (Sonarr list)

All query parameters **except** ``n`` and ``recent_days`` are forwarded
verbatim to the TMDB ``/discover/movie`` or ``/discover/tv`` endpoint.
Consult the `TMDB Discover docs <https://developer.themoviedb.org/reference/discover-movie>`_
for supported filters (``with_genres``, ``with_watch_providers``, etc.).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from listless.db import get_db
from listless.providers.tmdb.discover.client import TmdbDiscoverClient
from listless.schemas import RadarrItem, SonarrItem
from listless.services.id_mapping import IdMappingService

log = logging.getLogger(__name__)

_client = TmdbDiscoverClient()


# ── Movie router ─────────────────────────────────────────────────────────


def build_movie_router() -> APIRouter:
    router = APIRouter()

    @router.get("/discover/movies", response_model=list[RadarrItem])
    def discover_movies(
        request: Request,
    ) -> list[dict]:
        """Proxy TMDB ``/discover/movie``.

        Pass any TMDB discover filter as a query parameter.
        Local extras: ``n`` (max results, 1-200) and ``recent_days``
        (rolling date window, 1-365).
        """
        raw = dict(request.query_params)
        tmdb_ids = _client.discover("movie", raw_params=raw)
        return [{"TmdbId": i} for i in tmdb_ids]

    return router


# ── Series router ────────────────────────────────────────────────────────


def build_series_router() -> APIRouter:
    router = APIRouter()

    @router.get("/discover/series", response_model=list[SonarrItem])
    async def discover_series(
        request: Request,
        db: AsyncSession = Depends(get_db),
    ) -> list[dict]:
        """Proxy TMDB ``/discover/tv``.

        Pass any TMDB discover filter as a query parameter.
        Local extras: ``n`` (max results, 1-200) and ``recent_days``
        (rolling date window, 1-365).
        """
        mapping = IdMappingService(db)
        raw = dict(request.query_params)
        tmdb_ids = _client.discover("tv", raw_params=raw)

        tvdb_ids: list[int] = []
        for tid in tmdb_ids:
            tvdb = await mapping.tmdb_to_tvdb(tid)
            if tvdb is not None:
                tvdb_ids.append(tvdb)

        return [{"TvdbId": i} for i in tvdb_ids]

    return router
