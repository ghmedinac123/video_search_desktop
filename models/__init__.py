"""
Modelos Pydantic del proyecto — tipado fuerte para todas las capas.

Uso:
    from models import AppSettings, GPUInfo, CropData, SearchResult
    from models import get_settings
"""

from models.camera import CameraConfig, CameraStatus, CameraStore
from models.database import CollectionStats
from models.detection import BoundingBox, CropData
from models.frame import FrameData
from models.gpu import GPUInfo, VRAMStatus
from models.indexing import IndexProgress, IndexResult, IndexStage
from models.models_ai import AIModelInfo, AIModelType, ModelStatus
from models.search import SearchQuery, SearchResponse, SearchResult
from models.settings import AppSettings, get_settings
from models.video import VideoMetadata

__all__: list[str] = [
    # Settings
    "AppSettings",
    "get_settings",
    # GPU
    "GPUInfo",
    "VRAMStatus",
    # AI Models
    "AIModelInfo",
    "AIModelType",
    "ModelStatus",
    # Video
    "VideoMetadata",
    # Frame
    "FrameData",
    # Detection
    "BoundingBox",
    "CropData",
    # Search
    "SearchQuery",
    "SearchResult",
    "SearchResponse",
    # Indexing
    "IndexStage",
    "IndexProgress",
    "IndexResult",
    # Database
    "CollectionStats",
    # Cameras (RTSP v2.0)
    "CameraConfig",
    "CameraStatus",
    "CameraStore",
]