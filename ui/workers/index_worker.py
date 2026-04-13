"""
Worker para ejecutar el pipeline de indexacion en background.

Hereda de BaseWorker. Solo implementa execute().
Emite IndexProgress cada frame para actualizar barras en la UI.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.indexer import Indexer
from core.logger import logger
from models.indexing import IndexProgress, IndexResult


class IndexWorker(BaseWorker):
    """Ejecuta el pipeline de indexacion sin bloquear la UI."""

    progress = Signal(object)
    finished = Signal(object)

    def __init__(
        self,
        indexer: Indexer,
        video_path: Path,
        interval: int | None = None,
    ) -> None:
        super().__init__()
        self._indexer = indexer
        self._video_path = video_path
        self._interval = interval

    def execute(self) -> None:
        """Ejecuta el pipeline completo."""
        result = self._indexer.index_video(
            video_path=self._video_path,
            interval=self._interval,
            on_progress=lambda p: self.progress.emit(p),
        )
        self.finished.emit(result)

    def cancel(self) -> None:
        """Cancela el pipeline via el Indexer."""
        super().cancel()
        self._indexer.cancel()

    def pause(self) -> None:
        """Pausa el pipeline."""
        self._indexer.pause()

    def resume(self) -> None:
        """Reanuda el pipeline."""
        self._indexer.resume()
