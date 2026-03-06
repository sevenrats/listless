"""Listless – FastAPI application factory."""

from collections import defaultdict
from contextlib import asynccontextmanager

from fastapi import FastAPI

from listless.db import AsyncSessionLocal, Base, engine
from listless.providers import ALL_PROVIDERS
from listless.services.id_mapping import seed_mapping_types


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure tables exist and seed lookup rows."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as db:
        await seed_mapping_types(db)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Listless",
        description="Radarr / Sonarr compatible custom-list server with modular providers",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Group providers by name so typed variants (Movie / Series / …)
    # sharing the same slug merge under a single URL prefix.
    by_name: dict[str, list] = defaultdict(list)
    for provider in ALL_PROVIDERS:
        by_name[provider.name].append(provider)

    for name, providers in by_name.items():
        for provider in providers:
            tag = f"{name}:{provider.media_type.value}"
            app.include_router(
                provider.router(),
                prefix=f"/{name}",
                tags=[tag],
            )

    @app.get("/health", tags=["meta"])
    def health():
        return {"status": "ok"}

    return app
