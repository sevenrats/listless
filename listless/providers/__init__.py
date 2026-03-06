from listless.providers.base import (
    ListProvider,
    MovieListProvider,
    SeriesListProvider,
)
from listless.providers.imdb.chart.provider import (
    ImdbChartMovieProvider,
    ImdbChartSeriesProvider,
)
from listless.providers.justwatch.provider import (
    JustWatchMovieProvider,
    JustWatchSeriesProvider,
)
from listless.providers.tmdb.discover.provider import (
    TmdbDiscoverMovieProvider,
    TmdbDiscoverSeriesProvider,
)
from listless.providers.tmdb.popular.provider import (
    TmdbPopularMovieProvider,
    TmdbPopularSeriesProvider,
)

ALL_PROVIDERS: list[ListProvider] = [
    JustWatchMovieProvider(),
    JustWatchSeriesProvider(),
    ImdbChartMovieProvider(),
    ImdbChartSeriesProvider(),
    TmdbDiscoverMovieProvider(),
    TmdbDiscoverSeriesProvider(),
    TmdbPopularMovieProvider(),
    TmdbPopularSeriesProvider(),
]

__all__ = [
    "ALL_PROVIDERS",
    "ListProvider",
    "MovieListProvider",
    "SeriesListProvider",
]
