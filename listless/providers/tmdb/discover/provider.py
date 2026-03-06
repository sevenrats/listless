"""TMDB Discover typed providers.

``TmdbDiscoverMovieProvider``  → ``/tmdb/discover/movies``  (Radarr list)
``TmdbDiscoverSeriesProvider`` → ``/tmdb/discover/series``   (Sonarr list)
"""

from fastapi import APIRouter

from listless.providers.base import MovieListProvider, SeriesListProvider
from listless.providers.tmdb.discover.router import build_movie_router, build_series_router


class TmdbDiscoverMovieProvider(MovieListProvider):
    @property
    def name(self) -> str:
        return "tmdb"

    def router(self) -> APIRouter:
        return build_movie_router()


class TmdbDiscoverSeriesProvider(SeriesListProvider):
    @property
    def name(self) -> str:
        return "tmdb"

    def router(self) -> APIRouter:
        return build_series_router()
