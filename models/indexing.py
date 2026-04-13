"""
Modelos Pydantic para el pipeline de indexacion.

IndexStage: etapa actual del pipeline.
IndexProgress: estado en tiempo real para la UI.
IndexResult: resumen final al completar.

Uso:
    from models.indexing import IndexStage, IndexProgress, IndexResult
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class IndexStage(str, Enum):
    """Etapa actual del pipeline de indexacion."""

    IDLE = "idle"
    EXTRACTING_FRAMES = "extracting_frames"
    DETECTING = "detecting"
    EMBEDDING = "embedding"
    DESCRIBING = "describing"
    STORING = "storing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class IndexProgress(BaseModel):
    """
    Estado actual del pipeline — emitido cada frame procesado.

    La UI lee este modelo para actualizar las 4 barras de progreso,
    los contadores y el tiempo estimado.
    """

    stage: IndexStage = IndexStage.IDLE
    frames_total: int = 0
    frames_processed: int = 0
    detections_total: int = 0
    detections_processed: int = 0
    crops_stored: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: float = 0.0
    fps_processing: float = 0.0
    current_frame_path: str = ""
    error_message: str = ""

    model_config = ConfigDict(frozen=False)


class IndexResult(BaseModel):
    """Resumen final despues de indexar un video completo."""

    video_source: str
    total_frames: int
    total_detections: int
    total_stored: int
    elapsed_seconds: float
    fps_processing: float
    collection_total: int

    model_config = ConfigDict(frozen=True)
