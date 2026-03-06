"""Tests for Pydantic response schemas."""

from listless.schemas import MediaType, RadarrItem, SonarrItem


def test_media_type_values():
    assert MediaType.MOVIE == "movie"
    assert MediaType.SERIES == "series"


def test_radarr_item():
    item = RadarrItem(TmdbId=12345)
    assert item.TmdbId == 12345
    assert item.model_dump() == {"TmdbId": 12345}


def test_sonarr_item():
    item = SonarrItem(TvdbId=67890)
    assert item.TvdbId == 67890
    assert item.model_dump() == {"TvdbId": 67890}
