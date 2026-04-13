"""
Modelo Pydantic para estadisticas de la coleccion ChromaDB.

Uso:
    from models.database import CollectionStats
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CollectionStats(BaseModel):
    """Estadisticas de la coleccion ChromaDB."""

    collection_name: str
    total_records: int
    indexed_videos: list[str] = []
    class_distribution: dict[str, int] = {}
    disk_usage_mb: float = 0.0

    model_config = ConfigDict(frozen=True)
