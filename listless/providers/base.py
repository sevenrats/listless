"""Abstract provider hierarchy.

The class tree encodes *media type* so that every concrete provider is
statically bound to one content category:

    ListProvider            (ABC – name, media_type, router)
    ├─ MovieListProvider    (media_type = MOVIE)
    ├─ SeriesListProvider   (media_type = SERIES)
    └─ …future…             (MUSIC, BOOK, GAME, …)

Concrete providers (e.g. ``JustWatchMovieProvider``) inherit from one of
the typed bases and implement ``name`` + ``router()``.
"""

from abc import ABC, abstractmethod

from fastapi import APIRouter

from listless.schemas import MediaType


class ListProvider(ABC):
    """Root contract every Listless provider must satisfy.

    *name*
        Lower-case slug used as the URL prefix (``/justwatch``).
        Multiple typed providers may share the same *name* — their
        routers are merged under a single prefix by the app factory.

    *media_type*
        The :class:`MediaType` this provider produces.

    *router()*
        Returns a ready-to-mount :class:`APIRouter` whose paths are
        **relative** to the provider's prefix.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def media_type(self) -> MediaType: ...

    @abstractmethod
    def router(self) -> APIRouter: ...


# ── Typed bases ──────────────────────────────────────────────────────────


class MovieListProvider(ListProvider):
    """Provider that yields Radarr-compatible movie lists (``TmdbId``)."""

    @property
    def media_type(self) -> MediaType:
        return MediaType.MOVIE


class SeriesListProvider(ListProvider):
    """Provider that yields Sonarr-compatible series lists (``TvdbId``)."""

    @property
    def media_type(self) -> MediaType:
        return MediaType.SERIES
