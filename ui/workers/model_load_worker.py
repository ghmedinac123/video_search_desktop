"""
Worker para cargar modelos en GPU en background.

Hereda de BaseWorker. Solo implementa execute().
Emite signal por cada modelo cargado para actualizar UI.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.model_manager import ModelManager
from core.logger import logger


class ModelLoadWorker(BaseWorker):
    """Carga modelos en GPU sin bloquear la UI."""

    model_loaded = Signal(str)
    all_loaded = Signal()

    def __init__(
        self,
        manager: ModelManager,
        detector_id: str | None = None,
        embedder_id: str | None = None,
        describer_id: str | None = None,
    ) -> None:
        super().__init__()
        self._manager = manager
        self._detector_id = detector_id
        self._embedder_id = embedder_id
        self._describer_id = describer_id

    def execute(self) -> None:
        """Carga cada modelo seleccionado en GPU."""
        if self._detector_id and not self.is_cancelled:
            logger.info(f"Cargando detector: {self._detector_id}")
            self._manager.load_detector(self._detector_id)
            self.model_loaded.emit(self._detector_id)

        if self._embedder_id and not self.is_cancelled:
            logger.info(f"Cargando embedder: {self._embedder_id}")
            self._manager.load_embedder(self._embedder_id)
            self.model_loaded.emit(self._embedder_id)

        if self._describer_id and not self.is_cancelled:
            logger.info(f"Cargando describer: {self._describer_id}")
            self._manager.load_describer(self._describer_id)
            self.model_loaded.emit(self._describer_id)

        if not self.is_cancelled:
            self.all_loaded.emit()
