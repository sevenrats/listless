"""FastAPI routers for the JustWatch provider.

Builders
--------
``build_movie_router()``  → GET /movies  → ``[{"TmdbId": …}, …]``
``build_series_router()`` → GET /series  → ``[{"TvdbId": …}, …]``
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from listless.db import get_db
from listless.providers.justwatch.client import JustWatchClient
from listless.schemas import RadarrItem, SonarrItem
from listless.services.id_mapping import IdMappingService

log = logging.getLogger(__name__)

# Shared client instance (stateless, so safe to share)
_client = JustWatchClient()


# ── Shared query‑parameter dependency ────────────────────────────────────

Country = Annotated[str, Query(description="ISO 3166-1 alpha-2 country code")]
Language = Annotated[str, Query(description="ISO 639-1 language code")]
Providers = Annotated[
    str | None,
    Query(description="Comma-separated JustWatch package short names (e.g. nfx,dnp)"),
]
Genres = Annotated[str | None, Query(description="Comma-separated genre slugs")]
MonetizationTypes = Annotated[
    str | None,
    Query(description="Comma-separated monetization types (e.g. flatrate,free,ads)"),
]
MinYear = Annotated[int | None, Query(description="Minimum release year")]
MaxYear = Annotated[int | None, Query(description="Maximum release year")]
SortBy = Annotated[str, Query(description="JustWatch sort order")]
Limit = Annotated[int, Query(ge=1, le=500, description="Maximum results")]


def _split(val: str | None) -> list[str] | None:
    """Comma-separated string → list, or *None*."""
    if not val:
        return None
    return [s.strip() for s in val.split(",") if s.strip()]


# ── Movie router ─────────────────────────────────────────────────────────


def build_movie_router() -> APIRouter:
    router = APIRouter()

    @router.get("/movies", response_model=list[RadarrItem])
    async def list_movies(
        country: Country = "US",
        language: Language = "en",
        providers: Providers = None,
        genres: Genres = None,
        monetization_types: MonetizationTypes = None,
        min_year: MinYear = None,
        max_year: MaxYear = None,
        sort_by: SortBy = "POPULAR",
        limit: Limit = 40,
        db: AsyncSession = Depends(get_db),
    ) -> list[dict]:
        mapping = IdMappingService(db)

        titles = _client.get_popular(
            country=country,
            language=language,
            content_types=["MOVIE"],
            providers=_split(providers),
            genres=_split(genres),
            monetization_types=_split(monetization_types),
            min_year=min_year,
            max_year=max_year,
            sort_by=sort_by,
            limit=limit,
        )

        tmdb_ids: set[int] = set()
        for t in titles:
            tid = t.tmdb_id
            if tid is None and t.imdb_id:
                tid = await mapping.imdb_to_tmdb(t.imdb_id, "movie")
            if tid is not None:
                tmdb_ids.add(tid)

        return [{"TmdbId": i} for i in sorted(tmdb_ids)]

    return router


# ── Series router ────────────────────────────────────────────────────────


def build_series_router() -> APIRouter:
    router = APIRouter()

    @router.get("/series", response_model=list[SonarrItem])
    async def list_series(
        country: Country = "US",
        language: Language = "en",
        providers: Providers = None,
        genres: Genres = None,
        monetization_types: MonetizationTypes = None,
        min_year: MinYear = None,
        max_year: MaxYear = None,
        sort_by: SortBy = "POPULAR",
        limit: Limit = 40,
        db: AsyncSession = Depends(get_db),
    ) -> list[dict]:
        mapping = IdMappingService(db)

        titles = _client.get_popular(
            country=country,
            language=language,
            content_types=["SHOW"],
            providers=_split(providers),
            genres=_split(genres),
            monetization_types=_split(monetization_types),
            min_year=min_year,
            max_year=max_year,
            sort_by=sort_by,
            limit=limit,
        )

        tvdb_ids: set[int] = set()
        for t in titles:
            tvdb_id: int | None = None
            if t.tmdb_id is not None:
                tvdb_id = await mapping.tmdb_to_tvdb(t.tmdb_id)
            elif t.imdb_id:
                tvdb_id = await mapping.imdb_to_tvdb(t.imdb_id)
            if tvdb_id is not None and tvdb_id > 0:
                tvdb_ids.add(tvdb_id)

        return [{"TvdbId": i} for i in sorted(tvdb_ids)]

    return router
