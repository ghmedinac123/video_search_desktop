"""
Worker para descargar modelos AI en background.

Hereda de BaseWorker. Solo implementa execute().
Emite progreso por modelo para actualizar barras en la UI.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.model_registry import ModelRegistry
from core.logger import logger


class ModelDownloadWorker(BaseWorker):
    """Descarga modelos en background sin bloquear la UI."""

    progress = Signal(str, float)
    finished = Signal()

    def __init__(self, registry: ModelRegistry, model_ids: list[str]) -> None:
        super().__init__()
        self._registry = registry
        self._model_ids = model_ids

    def execute(self) -> None:
        """Descarga cada modelo secuencialmente."""
        for model_id in self._model_ids:
            if self.is_cancelled:
                logger.info("Descarga cancelada por el usuario")
                return

            logger.info(f"Descargando: {model_id}")
            self._registry.download_model(
                model_id=model_id,
                on_progress=lambda mid, p: self.progress.emit(mid, p),
            )
            self.progress.emit(model_id, 1.0)

        self.finished.emit()
