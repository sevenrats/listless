"""Cache-first ID mapping service: IMDb ↔ TMDb ↔ TVDb.

Translates external IDs using the TMDb ``/find`` and ``/external_ids``
endpoints, with a SQLite write-through cache so repeat look-ups are free.
"""

import logging
import time

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_upsert
from sqlalchemy.ext.asyncio import AsyncSession

from listless.config import settings
from listless.db.models import IdMapping, MappingType

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bootstrap helper
# ---------------------------------------------------------------------------

async def seed_mapping_types(db: AsyncSession) -> None:
    """Ensure the ``tv`` and ``movie`` rows exist in *mapping_types*."""
    for t in ("tv", "movie"):
        stmt = sqlite_upsert(MappingType).values(type=t).on_conflict_do_nothing()
        await db.execute(stmt)
    await db.commit()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class IdMappingService:
    """Resolve external media IDs with a SQLite-backed write-through cache."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._tmdb_key = settings.tmdb_api_key
        self._tmdb_api = settings.tmdb_api_base
        self._timeout = settings.default_http_timeout

    # ------------------------------------------------------------------ upserts

    async def _upsert_by_imdb(
        self,
        *,
        imdb: str,
        type_: str,
        tmdb: str | None = None,
        tvdb: str | None = None,
    ) -> None:
        now = int(time.time())
        stmt = sqlite_upsert(IdMapping).values(
            imdb=imdb,
            tmdb=tmdb,
            tvdb=tvdb,
            type=type_,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["imdb", "type"],
            set_={
                "tmdb": func.coalesce(stmt.excluded.tmdb, IdMapping.tmdb),
                "tvdb": func.coalesce(stmt.excluded.tvdb, IdMapping.tvdb),
                "updated_at": now,
            },
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def _upsert_by_tmdb(
        self,
        *,
        tmdb: str,
        type_: str,
        tvdb: str | None = None,
    ) -> None:
        now = int(time.time())
        stmt = sqlite_upsert(IdMapping).values(
            imdb=None,
            tmdb=tmdb,
            tvdb=tvdb,
            type=type_,
            created_at=now,
            updated_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["tmdb", "type"],
            set_={
                "tvdb": func.coalesce(stmt.excluded.tvdb, IdMapping.tvdb),
                "updated_at": now,
            },
        )
        await self._db.execute(stmt)
        await self._db.commit()

    # ----------------------------------------------------------- public look-ups

    async def imdb_to_tmdb(self, imdb_id: str, type_: str) -> int | None:
        """IMDb → TMDb via ``/find``, cache-first.  Misses are cached."""
        imdb_id = imdb_id.strip()
        if not imdb_id:
            return None
        if type_ not in ("movie", "tv"):
            raise ValueError(f"Invalid type: {type_!r}")

        # 1) cache check
        result = await self._db.execute(
            select(IdMapping.tmdb).where(
                IdMapping.imdb == imdb_id, IdMapping.type == type_
            )
        )
        row = result.first()
        if row is not None:
            return int(row.tmdb) if row.tmdb is not None else None

        # 2) API look-up
        if not self._tmdb_key:
            log.warning("TMDB API key not set – cannot resolve %s", imdb_id)
            return None

        params = {"api_key": self._tmdb_key, "external_source": "imdb_id"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(f"{self._tmdb_api}/find/{imdb_id}", params=params)
            r.raise_for_status()
            data = r.json()

        bucket = "movie_results" if type_ == "movie" else "tv_results"
        results = data.get(bucket) or []
        tmdb_id: int | None = int(results[0]["id"]) if results else None

        # 3) cache the result (hit *or* miss)
        await self._upsert_by_imdb(
            imdb=imdb_id,
            type_=type_,
            tmdb=str(tmdb_id) if tmdb_id is not None else None,
        )
        return tmdb_id

    async def tmdb_to_tvdb(self, tmdb_id: int) -> int | None:
        """TMDb TV → TVDb via ``/tv/{id}/external_ids``, cache-first.

        Cached misses (tvdb NULL) always trigger a re-check because TVDb
        mappings can appear retroactively.
        """
        if tmdb_id is None:
            return None

        type_ = "tv"
        tmdb_str = str(int(tmdb_id))

        # 1) cache – only trust positive hits
        result = await self._db.execute(
            select(IdMapping.tvdb).where(
                IdMapping.tmdb == tmdb_str, IdMapping.type == type_
            )
        )
        row = result.first()
        if row is not None and row.tvdb is not None:
            val = self._normalize_tvdb(row.tvdb)
            if val is not None:
                return val

        # 2) API look-up
        if not self._tmdb_key:
            log.warning("TMDB API key not set – cannot resolve tmdb=%s", tmdb_str)
            return None

        params = {"api_key": self._tmdb_key}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(
                f"{self._tmdb_api}/tv/{tmdb_str}/external_ids", params=params
            )
            r.raise_for_status()
            data = r.json()

        tvdb_int = self._normalize_tvdb(data.get("tvdb_id"))

        # 3) cache
        await self._upsert_by_tmdb(
            tmdb=tmdb_str,
            type_=type_,
            tvdb=str(tvdb_int) if tvdb_int is not None else None,
        )
        return tvdb_int

    async def imdb_to_tvdb(self, imdb_id: str) -> int | None:
        """IMDb → TMDb TV → TVDb, cache-first chain."""
        tmdb_id = await self.imdb_to_tmdb(imdb_id, "tv")
        if tmdb_id is None:
            return None
        return await self.tmdb_to_tvdb(tmdb_id)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _normalize_tvdb(val) -> int | None:
        if val is None:
            return None
        if isinstance(val, int):
            return None if val == 0 else val
        s = str(val).strip().lower()
        if s in ("", "0", "none", "null"):
            return None
        try:
            n = int(s)
        except ValueError:
            return None
        return None if n == 0 else n
