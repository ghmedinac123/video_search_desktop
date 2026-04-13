"""
Configuración global de la aplicación.

Lee automáticamente desde .env usando pydantic-settings.
Cada campo tiene un valor por defecto sensato — el .env es opcional.

Uso:
    from models.settings import get_settings
    settings = get_settings()
    print(settings.chromadb_dir)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Configuración centralizada — una sola fuente de verdad."""

    # ── Rutas ──
    data_dir: Path = Path("./data")
    chromadb_dir: Path = Path("./data/chromadb")
    output_dir: Path = Path("./output")
    frames_dir: Path = Path("./output/frames")
    crops_dir: Path = Path("./output/crops")
    log_dir: Path = Path("./logs")

    # ── ChromaDB ──
    collection_name: str = "video_search"

    # ── Modelos por defecto ──
    default_detector: str = "yolo11m"
    default_embedder: str = "jina-clip-v2"
    default_describer: str = "qwen2.5-vl-7b-q4"

    # ── Procesamiento ──
    frame_interval: int = 2
    yolo_confidence: float = 0.45
    min_crop_size: int = 30
    crop_padding: int = 10

    # ── VLM Prompts ──
    qwen_prompt: str = (
        "Describe esta imagen de cámara de seguridad en UNA oración detallada. "
        "Incluye: tipo de persona u objeto, género, ropa (colores exactos y tipo), "
        "accesorios, acción, dirección de movimiento. Solo la descripción, nada más."
    )
    moondream_prompt: str = (
        "Describe this security camera image in ONE detailed sentence. "
        "Include: person or object type, gender, clothing colors and type, "
        "accessories, action, direction of movement."
    )

    # ── Logging ──
    log_level: str = "INFO"
    log_rotation: str = "10 MB"
    log_retention: str = "7 days"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        """Crea todos los directorios necesarios si no existen. Idempotente."""
        for directory in (
            self.data_dir,
            self.chromadb_dir,
            self.output_dir,
            self.frames_dir,
            self.crops_dir,
            self.log_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Retorna la instancia singleton de settings. Cache en memoria."""
    return AppSettings()