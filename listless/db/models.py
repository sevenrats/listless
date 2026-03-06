"""ORM models for the id-mapping cache."""

from sqlalchemy import Column, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class MappingType(Base):
    """Lookup table constraining id_mappings.type to 'tv' | 'movie'."""

    __tablename__ = "mapping_types"

    type = Column(String, primary_key=True)


class IdMapping(Base):
    """Write-through cache row: IMDb ↔ TMDb ↔ TVDb for a given media type."""

    __tablename__ = "id_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    imdb = Column(String, nullable=True)
    tmdb = Column(String, nullable=True)
    tvdb = Column(String, nullable=True)
    type = Column(String, ForeignKey("mapping_types.type"), nullable=False)
    created_at = Column(Integer, nullable=False)
    updated_at = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("imdb", "type", name="uq_id_map_imdb_type"),
        UniqueConstraint("tmdb", "type", name="uq_id_map_tmdb_type"),
        Index("idx_id_map_lookup_imdb_type", "imdb", "type"),
        Index("idx_id_map_lookup_tmdb_type", "tmdb", "type"),
    )
