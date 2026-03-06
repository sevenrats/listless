"""Tests for the FastAPI application factory and health endpoint."""

from unittest.mock import patch, AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from listless.schemas import MediaType


@pytest.fixture()
def app():
    """Create a test app with DB lifespan disabled."""
    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from listless.providers import ALL_PROVIDERS
    from collections import defaultdict

    @asynccontextmanager
    async def _noop_lifespan(app: FastAPI):
        yield

    test_app = FastAPI(lifespan=_noop_lifespan)

    by_name: dict[str, list] = defaultdict(list)
    for provider in ALL_PROVIDERS:
        by_name[provider.name].append(provider)

    for name, providers in by_name.items():
        for provider in providers:
            tag = f"{name}:{provider.media_type.value}"
            test_app.include_router(
                provider.router(),
                prefix=f"/{name}",
                tags=[tag],
            )

    @test_app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return test_app


@pytest.fixture()
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_all_providers_registered():
    """Every provider in ALL_PROVIDERS has a valid name and media type."""
    from listless.providers import ALL_PROVIDERS

    assert len(ALL_PROVIDERS) > 0
    for p in ALL_PROVIDERS:
        assert isinstance(p.name, str)
        assert len(p.name) > 0
        assert p.media_type in (MediaType.MOVIE, MediaType.SERIES)


async def test_expected_routes_exist(app):
    """Verify key routes are registered."""
    routes = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/health" in routes
    assert "/justwatch/movies" in routes
    assert "/justwatch/series" in routes
    assert "/imdb/chart/movies" in routes
    assert "/imdb/chart/series" in routes
    assert "/tmdb/discover/movies" in routes
    assert "/tmdb/discover/series" in routes
    assert "/tmdb/popular/movies" in routes
    assert "/tmdb/popular/series" in routes
