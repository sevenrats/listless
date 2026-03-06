"""App-wide configuration, read from environment variables prefixed LISTLESS_."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:////app/data/listless.db"
    tmdb_api_key: str = ""
    tmdb_api_base: str = "https://api.themoviedb.org/3"
    default_http_timeout: float = 20.0

    model_config = {"env_prefix": "LISTLESS_", "env_file": ".env"}


settings = Settings()
