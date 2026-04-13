"""
Modelo Pydantic para un frame extraído de video.

NOTA: La imagen numpy (np.ndarray) NO se incluye en el modelo.
Se pasa por separado para evitar serialización de arrays grandes.

Uso:
    from models.frame import FrameData
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, computed_field


class FrameData(BaseModel):
    """Metadata de un frame extraído, sin la imagen en sí."""

    frame_index: int
    timestamp_seconds: float
    frame_path: Path
    video_source: Path
    width: int
    height: int

    model_config = ConfigDict(frozen=True)

    @computed_field
    @property
    def timestamp_formatted(self) -> str:
        """Timestamp legible como HH:MM:SS."""
        return str(timedelta(seconds=int(self.timestamp_seconds)))