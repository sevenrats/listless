"""JustWatch typed providers – one per media type.

``JustWatchMovieProvider``  → ``/justwatch/movies``  (Radarr list)
``JustWatchSeriesProvider`` → ``/justwatch/series``   (Sonarr list)
"""

from fastapi import APIRouter

from listless.providers.base import MovieListProvider, SeriesListProvider
from listless.providers.justwatch.router import build_movie_router, build_series_router


class JustWatchMovieProvider(MovieListProvider):
    @property
    def name(self) -> str:
        return "justwatch"

    def router(self) -> APIRouter:
        return build_movie_router()


class JustWatchSeriesProvider(SeriesListProvider):
    @property
    def name(self) -> str:
        return "justwatch"

    def router(self) -> APIRouter:
        return build_series_router()
