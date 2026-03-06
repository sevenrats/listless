"""Tests for the provider base classes."""

from fastapi import APIRouter

from listless.providers.base import MovieListProvider, SeriesListProvider
from listless.schemas import MediaType


class _DummyMovieProvider(MovieListProvider):
    @property
    def name(self) -> str:
        return "test"

    def router(self) -> APIRouter:
        return APIRouter()


class _DummySeriesProvider(SeriesListProvider):
    @property
    def name(self) -> str:
        return "test"

    def router(self) -> APIRouter:
        return APIRouter()


def test_movie_provider_media_type():
    p = _DummyMovieProvider()
    assert p.media_type == MediaType.MOVIE


def test_series_provider_media_type():
    p = _DummySeriesProvider()
    assert p.media_type == MediaType.SERIES


def test_provider_name():
    assert _DummyMovieProvider().name == "test"
    assert _DummySeriesProvider().name == "test"


def test_provider_router_returns_apirouter():
    assert isinstance(_DummyMovieProvider().router(), APIRouter)
    assert isinstance(_DummySeriesProvider().router(), APIRouter)
