"""Thin async-friendly wrapper around the JustWatch public GraphQL API."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

JUSTWATCH_GRAPHQL = "https://apis.justwatch.com/graphql"

POPULAR_TITLES_QUERY = """\
query GetPopularTitles(
  $first: Int!,
  $after: String,
  $sortRandomSeed: Int!,
  $sortBy: PopularTitlesSorting!,
  $filter: TitleFilter,
  $country: Country!,
  $language: Language!
) {
  popularTitles(
    first: $first
    after: $after
    sortRandomSeed: $sortRandomSeed
    sortBy: $sortBy
    filter: $filter
    country: $country
  ) {
    totalCount
    pageInfo {
      endCursor
      hasNextPage
    }
    edges {
      node {
        id
        objectType
        content(country: $country, language: $language) {
          title
          originalReleaseYear
          shortDescription
          externalIds {
            imdbId
            tmdbId
          }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True, slots=True)
class JustWatchTitle:
    """Normalised result from the JustWatch GraphQL API."""

    justwatch_id: str
    object_type: str  # "MOVIE" | "SHOW"
    title: str
    year: int | None
    imdb_id: str | None
    tmdb_id: int | None


class JustWatchClient:
    """Paginated client for JustWatch ``popularTitles`` queries."""

    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    # ------------------------------------------------------------------ public

    def get_popular(
        self,
        *,
        country: str = "US",
        language: str = "en",
        content_types: list[str] | None = None,
        providers: list[str] | None = None,
        genres: list[str] | None = None,
        monetization_types: list[str] | None = None,
        min_year: int | None = None,
        max_year: int | None = None,
        sort_by: str = "POPULAR",
        limit: int = 40,
    ) -> list[JustWatchTitle]:
        """Fetch up to *limit* titles, transparently paginating if needed."""

        title_filter: dict = {}
        if content_types:
            title_filter["objectTypes"] = content_types
        if providers:
            title_filter["packages"] = providers
        if genres:
            title_filter["genres"] = genres
        if monetization_types:
            title_filter["monetizationTypes"] = monetization_types

        release_year: dict = {}
        if min_year is not None:
            release_year["min"] = min_year
        if max_year is not None:
            release_year["max"] = max_year
        if release_year:
            title_filter["releaseYear"] = release_year

        all_titles: list[JustWatchTitle] = []
        cursor: str | None = None
        remaining = limit

        while remaining > 0:
            page_size = min(remaining, 100)
            variables: dict = {
                "first": page_size,
                "after": cursor or "",
                "sortRandomSeed": 0,
                "sortBy": sort_by,
                "filter": title_filter,
                "country": country,
                "language": language,
            }

            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    JUSTWATCH_GRAPHQL,
                    json={"query": POPULAR_TITLES_QUERY, "variables": variables},
                )
                resp.raise_for_status()
                data = resp.json()

            popular = data.get("data", {}).get("popularTitles", {})
            edges = popular.get("edges", [])
            if not edges:
                break

            for edge in edges:
                node = edge.get("node") or {}
                content = node.get("content") or {}
                ext = content.get("externalIds") or {}

                tmdb_id = self._safe_int(ext.get("tmdbId"))

                all_titles.append(
                    JustWatchTitle(
                        justwatch_id=node.get("id", ""),
                        object_type=node.get("objectType", ""),
                        title=content.get("title", ""),
                        year=content.get("originalReleaseYear"),
                        imdb_id=ext.get("imdbId") or None,
                        tmdb_id=tmdb_id,
                    )
                )

            page_info = popular.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
            remaining -= len(edges)

        return all_titles[:limit]

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _safe_int(val) -> int | None:
        """Coerce a value to a positive ``int`` or ``None``."""
        if val is None:
            return None
        try:
            n = int(val)
            return n if n > 0 else None
        except (ValueError, TypeError):
            return None
