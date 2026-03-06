"""FastAPI routers for the IMDb chart subprovider.

Endpoints
---------
GET /imdb/chart/movies  → ``[{"TmdbId": …}, …]``  (Radarr – most popular movies)
GET /imdb/chart/series  → ``[{"TvdbId": …}, …]``   (Sonarr – most popular TV)
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from listless.db import get_db
from listless.providers.imdb.chart.client import ChartKind, ImdbChartClient
from listless.schemas import RadarrItem, SonarrItem
from listless.services.id_mapping import IdMappingService

log = logging.getLogger(__name__)

_client = ImdbChartClient()

Limit = Annotated[
    int | None,
    Query(ge=1, le=500, description="Return only the *limit* most-popular items"),
]


# ── Movie router ─────────────────────────────────────────────────────────


def build_movie_router() -> APIRouter:
    router = APIRouter()

    @router.get("/chart/movies", response_model=list[RadarrItem])
    async def chart_movies(
        limit: Limit = None,
        db: AsyncSession = Depends(get_db),
    ) -> list[dict]:
        """Most-popular movies from IMDb's *moviemeter* chart."""
        mapping = IdMappingService(db)
        titles = _client.get_chart(ChartKind.MOVIE_METER)
        if limit is not None:
            titles = titles[:limit]

        tmdb_ids: set[int] = set()
        for t in titles:
            tid = await mapping.imdb_to_tmdb(t.imdb_id, "movie")
            if tid is not None:
                tmdb_ids.add(tid)

        return [{"TmdbId": i} for i in sorted(tmdb_ids)]

    return router


# ── Series router ────────────────────────────────────────────────────────


def build_series_router() -> APIRouter:
    router = APIRouter()

    @router.get("/chart/series", response_model=list[SonarrItem])
    async def chart_series(
        limit: Limit = None,
        db: AsyncSession = Depends(get_db),
    ) -> list[dict]:
        """Most-popular TV series from IMDb's *tvmeter* chart."""
        mapping = IdMappingService(db)
        titles = _client.get_chart(ChartKind.TV_METER)
        if limit is not None:
            titles = titles[:limit]

        tvdb_ids: set[int] = set()
        for t in titles:
            tvdb_id = await mapping.imdb_to_tvdb(t.imdb_id)
            if tvdb_id is not None and tvdb_id > 0:
                tvdb_ids.add(tvdb_id)

        return [{"TvdbId": i} for i in sorted(tvdb_ids)]

    return router
