"""
Modelos Pydantic para el catálogo de modelos de IA.

AIModelType: tipo de modelo (detector, embedder, describer).
ModelStatus: estado del ciclo de vida de un modelo.
AIModelInfo: metadatos completos de un modelo registrado.

Uso:
    from models.models_ai import AIModelInfo, AIModelType, ModelStatus
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class AIModelType(str, Enum):
    """Tipo funcional de un modelo de IA."""

    DETECTOR = "detector"
    EMBEDDER = "embedder"
    DESCRIBER = "describer"


class ModelStatus(str, Enum):
    """Estado en el ciclo de vida de un modelo."""

    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class AIModelInfo(BaseModel):
    """
    Metadatos de un modelo de IA disponible en el catálogo.

    Se usa para mostrar en la UI la lista de modelos seleccionables
    con su estado, tamaño, VRAM estimada, etc.
    """

    model_id: str
    display_name: str
    model_type: AIModelType
    repo_id: str
    estimated_vram_gb: float
    estimated_size_gb: float
    description: str = ""
    language: str = "multilingual"
    status: ModelStatus = ModelStatus.NOT_DOWNLOADED
    download_progress: float = 0.0

    model_config = ConfigDict(frozen=False)