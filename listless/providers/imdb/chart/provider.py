"""IMDb chart typed providers.

``ImdbChartMovieProvider``  → ``/imdb/chart/movies``  (Radarr list)
``ImdbChartSeriesProvider`` → ``/imdb/chart/series``   (Sonarr list)
"""

from fastapi import APIRouter

from listless.providers.base import MovieListProvider, SeriesListProvider
from listless.providers.imdb.chart.router import build_movie_router, build_series_router


class ImdbChartMovieProvider(MovieListProvider):
    @property
    def name(self) -> str:
        return "imdb"

    def router(self) -> APIRouter:
        return build_movie_router()


class ImdbChartSeriesProvider(SeriesListProvider):
    @property
    def name(self) -> str:
        return "imdb"

    def router(self) -> APIRouter:
        return build_series_router()
