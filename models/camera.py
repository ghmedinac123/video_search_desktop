"""
Modelos Pydantic para configuracion y estado de camaras RTSP.

CameraConfig: configuracion persistente de una camara (se guarda en JSON).
CameraStatus: estado en tiempo real de una camara conectada.

Uso:
    from models.camera import CameraConfig, CameraStatus, CameraStore
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from models.settings import get_settings


class CameraConfig(BaseModel):
    """Configuracion persistente de una camara RTSP."""

    camera_id: str
    name: str
    rtsp_url: str
    enabled: bool = True
    interval_seconds: int = 2

    model_config = ConfigDict(frozen=False)


class CameraStatus(BaseModel):
    """Estado en tiempo real de una camara conectada."""

    camera_id: str
    connected: bool = False
    fps_processing: float = 0.0
    frames_captured: int = 0
    detections_total: int = 0
    last_frame_time: str = ""
    error_message: str = ""

    model_config = ConfigDict(frozen=False)


class CameraStore:
    """
    Persistencia de configuraciones de camaras en JSON.

    Responsabilidad UNICA: leer/escribir cameras.json.
    El archivo vive en data/cameras.json dentro del proyecto.

    Uso:
        store = CameraStore()
        store.save(cameras_list)
        cameras = store.load()
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._file_path = settings.data_dir / "cameras.json"
        settings.data_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[CameraConfig]:
        """Lee camaras desde JSON. Retorna lista vacia si no existe."""
        if not self._file_path.exists():
            return []
        try:
            data = json.loads(self._file_path.read_text(encoding="utf-8"))
            return [CameraConfig(**cam) for cam in data]
        except Exception:
            return []

    def save(self, cameras: list[CameraConfig]) -> None:
        """Guarda camaras a JSON. Sobreescribe el archivo."""
        data = [cam.model_dump() for cam in cameras]
        self._file_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, camera: CameraConfig) -> None:
        """Agrega una camara y guarda."""
        cameras = self.load()
        # Evitar duplicados por camera_id
        cameras = [c for c in cameras if c.camera_id != camera.camera_id]
        cameras.append(camera)
        self.save(cameras)

    def remove(self, camera_id: str) -> None:
        """Elimina una camara por ID y guarda."""
        cameras = self.load()
        cameras = [c for c in cameras if c.camera_id != camera_id]
        self.save(cameras)

    def update(self, camera: CameraConfig) -> None:
        """Actualiza una camara existente y guarda."""
        self.add(camera)  # add ya reemplaza por camera_id
