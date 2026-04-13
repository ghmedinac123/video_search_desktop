"""
Worker para ejecutar busquedas en background.

Hereda de BaseWorker. Solo implementa execute().
Emite SearchResponse con los resultados para la UI.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.searcher import Searcher
from core.logger import logger
from models.search import SearchResponse


class SearchWorker(BaseWorker):
    """Ejecuta busqueda por texto sin bloquear la UI."""

    results = Signal(object)

    def __init__(
        self,
        searcher: Searcher,
        query_text: str,
        n_results: int = 30,
    ) -> None:
        super().__init__()
        self._searcher = searcher
        self._query_text = query_text
        self._n_results = n_results

    def execute(self) -> None:
        """Ejecuta la busqueda."""
        response = self._searcher.search(
            query_text=self._query_text,
            n_results=self._n_results,
        )
        self.results.emit(response)
