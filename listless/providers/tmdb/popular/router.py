"""FastAPI routers for the TMDB Popular subprovider.

Endpoints
---------
GET /tmdb/popular/movies  → ``[{"TmdbId": …}, …]``  (Radarr list)
GET /tmdb/popular/series  → ``[{"TvdbId": …}, …]``   (Sonarr list)
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from listless.db import get_db
from listless.providers.tmdb.popular.client import TmdbPopularClient
from listless.schemas import RadarrItem, SonarrItem
from listless.services.id_mapping import IdMappingService

log = logging.getLogger(__name__)

_client = TmdbPopularClient()

# ── Query-parameter types ────────────────────────────────────────────────

Language = Annotated[str, Query(description="TMDB language tag (e.g. en-US)")]
Region = Annotated[str | None, Query(description="ISO 3166-1 region code")]
N = Annotated[int, Query(ge=1, le=200, description="Maximum results to return")]
Page = Annotated[int, Query(ge=1, description="Starting page number")]


# ── Movie router ─────────────────────────────────────────────────────────


def build_movie_router() -> APIRouter:
    router = APIRouter()

    @router.get("/popular/movies", response_model=list[RadarrItem])
    def popular_movies(
        language: Language = "en-US",
        region: Region = None,
        n: N = 20,
        page: Page = 1,
    ) -> list[dict]:
        """Currently popular movies from TMDB."""
        tmdb_ids = _client.popular(
            "movie", language=language, region=region, n=n, page=page,
        )
        return [{"TmdbId": i} for i in tmdb_ids]

    return router


# ── Series router ────────────────────────────────────────────────────────


def build_series_router() -> APIRouter:
    router = APIRouter()

    @router.get("/popular/series", response_model=list[SonarrItem])
    async def popular_series(
        language: Language = "en-US",
        n: N = 20,
        page: Page = 1,
        db: AsyncSession = Depends(get_db),
    ) -> list[dict]:
        """Currently popular TV series from TMDB."""
        mapping = IdMappingService(db)
        tmdb_ids = _client.popular("tv", language=language, n=n, page=page)

        tvdb_ids: list[int] = []
        for tid in tmdb_ids:
            tvdb = await mapping.tmdb_to_tvdb(tid)
            if tvdb is not None:
                tvdb_ids.append(tvdb)

        return [{"TvdbId": i} for i in tvdb_ids]

    return router
