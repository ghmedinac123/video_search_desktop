"""
Modelo Pydantic para metadata de un archivo de video.

Se extrae al cargar un video con OpenCV antes de procesarlo.

Uso:
    from models.video import VideoMetadata
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, computed_field


class VideoMetadata(BaseModel):
    """Metadata extraída de un archivo de video."""

    file_path: Path
    file_name: str
    duration_seconds: float
    fps: float
    total_frames: int
    width: int
    height: int
    codec: str = "unknown"
    file_size_mb: float = 0.0

    model_config = ConfigDict(frozen=True)

    @computed_field
    @property
    def duration_formatted(self) -> str:
        """Duración legible como HH:MM:SS."""
        return str(timedelta(seconds=int(self.duration_seconds)))

    @computed_field
    @property
    def resolution(self) -> str:
        """Resolución como WxH."""
        return f"{self.width}x{self.height}"