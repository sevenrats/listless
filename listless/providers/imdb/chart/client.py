"""IMDb chart scraper client.

Fetches the IMDb ``moviemeter`` and ``tvmeter`` chart pages, extracts
titles from the embedded ``__NEXT_DATA__`` JSON, and returns normalised
results that the router can feed through the ID-mapping pipeline.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import StrEnum

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class ChartKind(StrEnum):
    """Maps to the IMDb chart URL slug."""

    MOVIE_METER = "moviemeter"
    TV_METER = "tvmeter"


@dataclass(frozen=True, slots=True)
class ImdbChartTitle:
    """A single entry scraped from an IMDb meter chart."""

    imdb_id: str
    title: str
    year: str | None


class ImdbChartClient:
    """Scrapes IMDb ``/chart/{kind}`` pages for ranked title lists."""

    def __init__(self, timeout: float = 20.0) -> None:
        self._timeout = timeout

    # ------------------------------------------------------------------ public

    def get_chart(self, kind: ChartKind) -> list[ImdbChartTitle]:
        """Fetch and parse an IMDb meter chart, returning all titles found."""
        url = f"https://www.imdb.com/chart/{kind.value}"
        html = self._fetch(url)
        return self._parse_next_data(html)

    # ------------------------------------------------------------------ private

    def _fetch(self, url: str) -> str:
        with httpx.Client(
            headers=_HEADERS,
            follow_redirects=True,
            timeout=self._timeout,
            http2=True,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.text

    @staticmethod
    def _parse_next_data(html: str) -> list[ImdbChartTitle]:
        """Extract titles from the ``script#__NEXT_DATA__`` blob."""
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.select_one("script#__NEXT_DATA__")
        if not tag or not tag.string:
            log.warning("__NEXT_DATA__ tag not found in IMDb response")
            return []

        data = json.loads(tag.string)

        edges = (
            data.get("props", {})
            .get("pageProps", {})
            .get("pageData", {})
            .get("chartTitles", {})
            .get("edges", [])
        )

        results: list[ImdbChartTitle] = []
        for edge in edges:
            node = edge.get("node") or {}
            imdb_id = node.get("id")
            title = (node.get("titleText") or {}).get("text")

            year: str | None = None
            ry = node.get("releaseYear") or {}
            if "year" in ry and ry["year"] is not None:
                year = str(ry["year"])

            if imdb_id and title:
                results.append(
                    ImdbChartTitle(imdb_id=imdb_id, title=title, year=year)
                )

        return results
