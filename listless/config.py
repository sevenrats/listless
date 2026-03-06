"""App-wide configuration, read from environment variables prefixed LISTLESS_."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:////app/data/listless.db"
    tmdb_api_key: str = ""
    tmdb_api_base: str = "https://api.themoviedb.org/3"
    default_http_timeout: float = 20.0

    model_config = {"env_prefix": "LISTLESS_", "env_file": ".env"}

    @property
    def is_sqlite(self) -> bool:
        """True when the configured database URL targets SQLite."""
        return self.database_url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        """True when the configured database URL targets PostgreSQL."""
        return self.database_url.startswith("postgresql")

    @property
    def sync_database_url(self) -> str:
        """Return a synchronous variant of the database URL (for Alembic)."""
        url = self.database_url
        replacements = {
            "+aiosqlite": "",
            "+asyncpg": "+psycopg2",
        }
        for old, new in replacements.items():
            url = url.replace(old, new)
        return url


settings = Settings()
