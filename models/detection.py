"""
Modelos Pydantic para detecciones YOLO.

BoundingBox: coordenadas de la caja delimitadora.
CropData: detección recortada con toda su metadata.

Uso:
    from models.detection import BoundingBox, CropData
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, computed_field


class BoundingBox(BaseModel):
    """Bounding box de una detección YOLO."""

    x1: int
    y1: int
    x2: int
    y2: int

    model_config = ConfigDict(frozen=True)

    @computed_field
    @property
    def width(self) -> int:
        """Ancho del bounding box en píxeles."""
        return self.x2 - self.x1

    @computed_field
    @property
    def height(self) -> int:
        """Alto del bounding box en píxeles."""
        return self.y2 - self.y1

    @computed_field
    @property
    def center(self) -> tuple[int, int]:
        """Centro del bounding box como (x, y)."""
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @computed_field
    @property
    def area(self) -> int:
        """Área en píxeles cuadrados."""
        return self.width * self.height


class CropData(BaseModel):
    """
    Una detección recortada de un frame con toda su metadata.

    El campo description se llena después por el VLM,
    por eso frozen=False.
    """

    crop_id: str
    class_name: str
    confidence: float
    bbox: BoundingBox
    crop_path: Path
    frame_path: Path
    video_source: Path
    timestamp_seconds: float
    description: str = ""

    model_config = ConfigDict(frozen=False)

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        """Timestamp legible como HH:MM:SS."""
        return str(timedelta(seconds=int(self.timestamp_seconds)))