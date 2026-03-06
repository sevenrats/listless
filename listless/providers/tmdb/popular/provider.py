"""TMDB Popular typed providers.

``TmdbPopularMovieProvider``  → ``/tmdb/popular/movies``  (Radarr list)
``TmdbPopularSeriesProvider`` → ``/tmdb/popular/series``   (Sonarr list)
"""

from fastapi import APIRouter

from listless.providers.base import MovieListProvider, SeriesListProvider
from listless.providers.tmdb.popular.router import build_movie_router, build_series_router


class TmdbPopularMovieProvider(MovieListProvider):
    @property
    def name(self) -> str:
        return "tmdb"

    def router(self) -> APIRouter:
        return build_movie_router()


class TmdbPopularSeriesProvider(SeriesListProvider):
    @property
    def name(self) -> str:
        return "tmdb"

    def router(self) -> APIRouter:
        return build_series_router()
