"""
Modelos Pydantic para búsqueda.

SearchQuery: lo que el usuario pide.
SearchResult: un resultado individual.
SearchResponse: respuesta completa con timing.

Uso:
    from models.search import SearchQuery, SearchResult, SearchResponse
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, computed_field


class SearchQuery(BaseModel):
    """Consulta de búsqueda del usuario."""

    text: str
    n_results: int = 30
    min_score: float = 0.0
    class_filter: list[str] | None = None
    camera_filter: list[str] | None = None
    video_filter: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None

    model_config = ConfigDict(frozen=True)

    def has_filters(self) -> bool:
        """True si la consulta tiene algun filtro activo."""
        return any([
            self.class_filter,
            self.camera_filter,
            self.video_filter,
            self.date_from,
            self.date_to,
        ])


class SearchResult(BaseModel):
    """Un resultado individual de búsqueda desde ChromaDB."""

    crop_id: str
    score: float
    class_name: str
    confidence: float
    timestamp_seconds: float
    video_source: str
    frame_path: str
    crop_path: str
    description: str = ""
    bbox: str = ""

    model_config = ConfigDict(frozen=True)

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        """Timestamp legible como HH:MM:SS."""
        return str(timedelta(seconds=int(self.timestamp_seconds)))


class SearchResponse(BaseModel):
    """Respuesta completa de una búsqueda con timing."""

    query: str
    results: list[SearchResult]
    total_results: int
    elapsed_ms: int

    model_config = ConfigDict(frozen=True)