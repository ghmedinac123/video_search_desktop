"""
Sistema de logging centralizado basado en loguru.

Se configura UNA VEZ al iniciar la aplicación con setup_logger().
Después se importa desde cualquier módulo:

    from core.logger import logger

    logger.info("Modelo cargado en GPU")
    logger.debug(f"VRAM usada: {vram:.1f} GB")
    logger.error(f"Error al procesar: {e}")

Características:
    - Consola con colores + archivo rotativo sin colores.
    - Silencia el ruido de librerías externas (torch, transformers, etc.)
    - Niveles configurables desde .env (LOG_LEVEL=DEBUG/INFO/WARNING)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from loguru import logger

# ────────────────────────────────────────────────────────
# Librerías externas que generan ruido excesivo.
# Se silencian a WARNING: solo pasan errores reales.
# ────────────────────────────────────────────────────────
SILENCED_LOGGERS: list[str] = [
    # Transformers / HuggingFace
    "transformers",
    "transformers.modeling_utils",
    "transformers.configuration_utils",
    "transformers.tokenization_utils_base",
    "transformers.generation",
    "transformers.utils",
    "huggingface_hub",
    "huggingface_hub.file_download",
    "huggingface_hub.utils",
    # PyTorch
    "torch",
    "torch.nn.modules",
    "torch.cuda",
    # Ultralytics (YOLO)
    "ultralytics",
    "ultralytics.engine",
    "ultralytics.utils",
    "ultralytics.nn",
    # ChromaDB
    "chromadb",
    "chromadb.config",
    "chromadb.segment",
    "chromadb.api",
    # Sentence Transformers
    "sentence_transformers",
    "sentence_transformers.util",
    # HTTP / Red
    "httpx",
    "httpcore",
    "urllib3",
    "requests",
    # Otros
    "PIL",
    "filelock",
    "accelerate",
    "bitsandbytes",
    "numba",
    "onnxruntime",
    "matplotlib",
]

# Formatos de log
LOG_FORMAT_CONSOLE: str = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level.icon} {level:<8}</level> | "
    "<cyan>{module}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

LOG_FORMAT_FILE: str = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level:<8} | "
    "{name}:{function}:{line} | "
    "{message}"
)


def _silence_external_loggers() -> None:
    """Pone todos los loggers ruidosos en WARNING."""
    for logger_name in SILENCED_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def setup_logger(
    level: str = "INFO",
    log_dir: Path = Path("./logs"),
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> None:
    """
    Configura el logger global. Llamar UNA VEZ al iniciar la app.

    Args:
        level: Nivel mínimo (DEBUG, INFO, WARNING, ERROR).
        log_dir: Carpeta donde se guardan los logs.
        rotation: Cuándo rotar el archivo (ej: "10 MB", "1 day").
        retention: Cuánto tiempo conservar logs viejos.
    """
    # Crear carpeta de logs
    log_dir.mkdir(parents=True, exist_ok=True)

    # Limpiar handlers previos de loguru
    logger.remove()

    # Handler de consola (con colores)
    logger.add(
        sys.stderr,
        format=LOG_FORMAT_CONSOLE,
        level=level.upper(),
        colorize=True,
    )

    # Handler de archivo (sin colores, rotación automática)
    log_file = log_dir / "video_search.log"
    logger.add(
        str(log_file),
        format=LOG_FORMAT_FILE,
        level="DEBUG",  # Archivo siempre guarda todo
        rotation=rotation,
        retention=retention,
        encoding="utf-8",
        enqueue=True,  # Thread-safe
    )

    # Silenciar librerías ruidosas
    _silence_external_loggers()

    logger.info(f"Logger configurado — nivel: {level}, archivo: {log_file}")