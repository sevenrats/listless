"""Tests for the IdMappingService."""

from unittest.mock import AsyncMock, patch

import pytest

from listless.db.models import IdMapping, MappingType
from listless.services.id_mapping import IdMappingService


async def test_seed_mapping_types(async_db):
    """seed_mapping_types should create 'tv' and 'movie' rows."""
    from sqlalchemy import select

    result = await async_db.execute(select(MappingType.type))
    types = sorted(row[0] for row in result.all())
    assert types == ["movie", "tv"]


async def test_imdb_to_tmdb_cache_hit(async_db):
    """When a mapping exists in the DB, return it without calling the API."""
    import time

    now = int(time.time())
    async_db.add(IdMapping(imdb="tt1234567", tmdb="42", type="movie", created_at=now, updated_at=now))
    await async_db.commit()

    svc = IdMappingService(async_db)
    result = await svc.imdb_to_tmdb("tt1234567", "movie")
    assert result == 42


async def test_imdb_to_tmdb_cache_miss_no_api_key(async_db):
    """Without an API key, a cache miss returns None."""
    svc = IdMappingService(async_db)
    with patch.object(svc, "_tmdb_key", ""):
        result = await svc.imdb_to_tmdb("tt0000001", "movie")
    assert result is None


async def test_imdb_to_tmdb_cache_miss_api_call(async_db):
    """On cache miss with an API key, the service fetches from TMDb and caches."""
    from unittest.mock import MagicMock

    svc = IdMappingService(async_db)
    svc._tmdb_key = "fake-key"

    mock_response = MagicMock()
    mock_response.json.return_value = {"movie_results": [{"id": 99}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch("listless.services.id_mapping.httpx.AsyncClient") as MockClient:
        MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await svc.imdb_to_tmdb("tt9999999", "movie")

    assert result == 99

    # Verify it was cached
    result2 = await svc.imdb_to_tmdb("tt9999999", "movie")
    assert result2 == 99


async def test_imdb_to_tmdb_invalid_type(async_db):
    """Invalid type raises ValueError."""
    svc = IdMappingService(async_db)
    with pytest.raises(ValueError, match="Invalid type"):
        await svc.imdb_to_tmdb("tt1234567", "podcast")


async def test_imdb_to_tmdb_empty_id(async_db):
    """Empty IMDb ID returns None."""
    svc = IdMappingService(async_db)
    result = await svc.imdb_to_tmdb("", "movie")
    assert result is None


async def test_tmdb_to_tvdb_cache_hit(async_db):
    """Cached TMDb → TVDb mapping is returned directly."""
    import time

    now = int(time.time())
    async_db.add(IdMapping(tmdb="100", tvdb="200", type="tv", created_at=now, updated_at=now))
    await async_db.commit()

    svc = IdMappingService(async_db)
    result = await svc.tmdb_to_tvdb(100)
    assert result == 200


async def test_normalize_tvdb():
    """_normalize_tvdb handles various edge cases."""
    norm = IdMappingService._normalize_tvdb
    assert norm(None) is None
    assert norm(0) is None
    assert norm(42) == 42
    assert norm("0") is None
    assert norm("none") is None
    assert norm("123") == 123
    assert norm("") is None
    assert norm("abc") is None


async def test_imdb_to_tvdb_chains(async_db):
    """imdb_to_tvdb chains imdb→tmdb→tvdb."""
    import time

    now = int(time.time())
    async_db.add(IdMapping(imdb="tt5555555", tmdb="300", tvdb="400", type="tv", created_at=now, updated_at=now))
    await async_db.commit()

    svc = IdMappingService(async_db)
    result = await svc.imdb_to_tvdb("tt5555555")
    assert result == 400
