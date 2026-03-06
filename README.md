[![Coverage](https://coverage.crandall.codes/badge/sevenrats/listless/b/main)](https://coverage.crandall.codes/sevenrats/listless/b/main)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow?logo=buymeacoffee)](https://buymeacoffee.com/sevenrats)

# Listless

A self-hosted custom-list server that speaks the **Radarr** and **Sonarr** import list protocol. Point your \*arr apps at Listless and it will feed them titles from JustWatch, IMDb, and TMDB — no proprietary list services required.

## How It Works

Listless is a lightweight FastAPI server that aggregates titles from multiple upstream sources and returns them in the JSON format Radarr and Sonarr expect from custom lists. Each **provider** exposes one or more endpoints: movie endpoints return `[{"TmdbId": …}]` for Radarr, and series endpoints return `[{"TvdbId": …}]` for Sonarr.

An internal **ID-mapping service** backed by a database write-through cache (SQLite or PostgreSQL) translates between IMDb, TMDB, and TVDB identifiers automatically using the TMDB API, so providers only need to know one external ID to produce the right output.

## Providers

| Provider | Endpoint | Type | Description |
|---|---|---|---|
| **JustWatch** | `/justwatch/movies` | Radarr | Popular movies filtered by country, streaming service, genre, etc. |
| **JustWatch** | `/justwatch/series` | Sonarr | Popular series filtered by country, streaming service, genre, etc. |
| **IMDb Charts** | `/imdb/chart/movies` | Radarr | IMDb most-popular movies chart |
| **IMDb Charts** | `/imdb/chart/series` | Sonarr | IMDb most-popular TV series chart |
| **TMDB Discover** | `/tmdb/discover/movies` | Radarr | TMDB discover endpoint — pass any [discover filter](https://developer.themoviedb.org/reference/discover-movie) as a query param |
| **TMDB Discover** | `/tmdb/discover/series` | Sonarr | TMDB discover endpoint — pass any [discover filter](https://developer.themoviedb.org/reference/discover-tv) as a query param |
| **TMDB Popular** | `/tmdb/popular/movies` | Radarr | Currently [popular movies](https://developer.themoviedb.org/reference/movie-popular-list) on TMDB |
| **TMDB Popular** | `/tmdb/popular/series` | Sonarr | Currently [popular TV](https://developer.themoviedb.org/reference/tv-series-popular-list) on TMDB |

## Quick Start

### Docker Compose (recommended)

1. Create a `.env` file:

   ```env
   LISTLESS_TMDB_API_KEY=your_tmdb_v3_api_key
   ```

2. Start the service:

   ```bash
   docker compose up -d
   ```

Listless will be available at `http://localhost:8000`. The SQLite database is persisted in a named Docker volume.

#### Using PostgreSQL

To use PostgreSQL instead of SQLite, uncomment the `listless-pg` and `postgres` services in `docker-compose.yml` (and comment out the default `listless` service), or simply set the `LISTLESS_DATABASE_URL` env var in your `.env`:

```env
LISTLESS_DATABASE_URL=postgresql+asyncpg://listless:listless@postgres:5432/listless
```

### Run Locally

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Set your TMDB API key
export LISTLESS_TMDB_API_KEY=your_tmdb_v3_api_key

# Start the server
uv run python main.py
```

## Configuration

All settings are read from environment variables prefixed with `LISTLESS_` (or from a `.env` file).

| Variable | Default | Description |
|---|---|---|
| `LISTLESS_TMDB_API_KEY` | *(empty)* | **Required.** Your TMDB v3 API key — used for ID mapping and TMDB providers. |
| `LISTLESS_DATABASE_URL` | `sqlite+aiosqlite:////app/data/listless.db` | SQLAlchemy async connection string. Use `postgresql+asyncpg://user:pass@host/db` for PostgreSQL. |
| `LISTLESS_TMDB_API_BASE` | `https://api.themoviedb.org/3` | TMDB API base URL. |
| `LISTLESS_DEFAULT_HTTP_TIMEOUT` | `20.0` | Default timeout in seconds for upstream HTTP requests. |

## Adding to Radarr / Sonarr

1. Go to **Settings → Import Lists → + → Custom List**.
2. Set the **List URL** to the Listless endpoint you want, for example:
   ```
   http://listless:8000/justwatch/movies?country=US&providers=nfx,dnp&limit=100
   ```
3. Save, and Radarr/Sonarr will periodically import titles from the list.

## Example Requests

```bash
# JustWatch: top 50 movies on Netflix in the US
curl "http://localhost:8000/justwatch/movies?country=US&providers=nfx&limit=50"

# JustWatch: popular series on Disney+ in the UK, sorted by popularity
curl "http://localhost:8000/justwatch/series?country=GB&providers=dnp&sort_by=POPULAR&limit=40"

# IMDb: most popular movies (top 25)
curl "http://localhost:8000/imdb/chart/movies?limit=25"

# IMDb: most popular TV series
curl "http://localhost:8000/imdb/chart/series"

# TMDB Discover: sci-fi movies from the last year
curl "http://localhost:8000/tmdb/discover/movies?with_genres=878&recent_days=365&n=50"

# TMDB Popular: top 20 popular movies
curl "http://localhost:8000/tmdb/popular/movies?n=20"

# Health check
curl "http://localhost:8000/health"
```

## API Documentation

FastAPI auto-generates interactive docs. Once the server is running, visit:

- **Swagger UI** — `http://localhost:8000/docs`
- **ReDoc** — `http://localhost:8000/redoc`

## Architecture

```
listless/
├── app.py              # FastAPI application factory
├── config.py           # Pydantic settings (env vars)
├── schemas.py          # RadarrItem / SonarrItem response models
├── db/                 # SQLAlchemy async engine, session, ORM models
├── services/           # ID-mapping cache (IMDb ↔ TMDB ↔ TVDB)
└── providers/          # Modular provider packages
    ├── base.py         #   Abstract ListProvider / MovieListProvider / SeriesListProvider
    ├── justwatch/      #   JustWatch GraphQL API
    ├── imdb/chart/     #   IMDb popularity charts
    └── tmdb/           #   TMDB discover & popular
        ├── discover/
        └── popular/
```

Providers follow a simple pattern: implement `name`, `media_type`, and `router()` on a subclass of `MovieListProvider` or `SeriesListProvider`. The app factory discovers all providers, groups them by name, and mounts their routers automatically.

## Database & Migrations

Listless uses async SQLAlchemy and supports **SQLite** (default) and **PostgreSQL** backends. Tables are created automatically on startup. For schema evolution, [Alembic](https://alembic.sqlalchemy.org/) is configured:

```bash
# Generate a new migration after changing models
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests
uv run pytest

# Run with auto-reload
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## License

See [pyproject.toml](pyproject.toml) for package metadata.
