"""Pydantic response schemas matching the Radarr / Sonarr custom-list contract."""

from enum import StrEnum

from pydantic import BaseModel


class MediaType(StrEnum):
    """High-level content category.

    Each value maps 1:1 to a typed provider subclass.  Extend this enum
    when new media types (Music, Books, Games, …) are added.
    """

    MOVIE = "movie"
    SERIES = "series"
    # Future: MUSIC = "music", BOOK = "book", GAME = "game", …


class RadarrItem(BaseModel):
    """Single entry in a Radarr custom list response."""

    TmdbId: int


class SonarrItem(BaseModel):
    """Single entry in a Sonarr custom list response."""

    TvdbId: int
