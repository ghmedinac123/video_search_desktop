"""
Configuracion global de la aplicacion.

Lee automaticamente desde .env usando pydantic-settings.

Uso:
    from models.settings import get_settings
    settings = get_settings()
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Configuracion centralizada — una sola fuente de verdad."""

    # ── Rutas ──
    data_dir: Path = Path("./data")
    chromadb_dir: Path = Path("./data/chromadb")
    output_dir: Path = Path("./output")
    frames_dir: Path = Path("./output/frames")
    crops_dir: Path = Path("./output/crops")
    log_dir: Path = Path("./logs")
    models_cache_dir: Path = Path("./models_cache")

    # ── ChromaDB ──
    collection_name: str = "video_search"

    # ── Modelos por defecto (livianos) ──
    default_detector: str = "yolo11n"
    default_embedder: str = "jina-clip-v2"
    default_describer: str = "moondream2-4bit"

    # ── Procesamiento ──
    frame_interval: int = 2
    yolo_confidence: float = 0.45
    min_crop_size: int = 30
    crop_padding: int = 10

    # ── VLM Prompts ──
    qwen_prompt: str = (
        "Describe esta imagen de camara de seguridad en UNA oracion detallada. "
        "Incluye: tipo de persona u objeto, genero, ropa (colores exactos y tipo), "
        "accesorios, accion, direccion de movimiento. Solo la descripcion, nada mas."
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
            self.models_cache_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def setup_model_environment(self) -> None:
        """
        Configura variables de entorno para que HuggingFace y Ultralytics
        descarguen modelos DENTRO del proyecto, no en cache del sistema.

        Llamar UNA VEZ al iniciar la app, ANTES de importar modelos.
        """
        import os
        cache_path = str(self.models_cache_dir.resolve())

        # HuggingFace descarga aqui (CLIP, Qwen, Moondream)
        os.environ["HF_HOME"] = cache_path
        os.environ["HUGGINGFACE_HUB_CACHE"] = str(
            Path(cache_path) / "huggingface"
        )

        # Ultralytics descarga YOLO aqui
        os.environ["YOLO_CONFIG_DIR"] = str(
            Path(cache_path) / "ultralytics"
        )

        # Sentence-transformers usa el mismo cache de HF
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(
            Path(cache_path) / "sentence_transformers"
        )

        # HuggingFace token para descargas mas rapidas
        hf_token = os.getenv("HF_TOKEN", "")
        if hf_token:
            os.environ["HF_TOKEN"] = hf_token


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Retorna la instancia singleton de settings. Cache en memoria."""
    return AppSettings()
