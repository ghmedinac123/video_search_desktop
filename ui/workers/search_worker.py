"""
Worker para ejecutar busquedas en background.

Hereda de BaseWorker. Solo implementa execute().
Acepta un SearchQuery tipado o un texto simple, y emite SearchResponse.
"""

from __future__ import annotations

from PySide6.QtCore import Signal

from ui.workers.base_worker import BaseWorker
from core.searcher import Searcher
from core.logger import logger
from models.search import SearchQuery, SearchResponse


class SearchWorker(BaseWorker):
    """Ejecuta busqueda por texto sin bloquear la UI."""

    results = Signal(object)

    def __init__(
        self,
        searcher: Searcher,
        query: SearchQuery | None = None,
        query_text: str | None = None,
        n_results: int = 30,
    ) -> None:
        super().__init__()
        self._searcher = searcher
        if query is not None:
            self._query = query
        elif query_text is not None:
            self._query = SearchQuery(
                text=query_text, n_results=n_results
            )
        else:
            raise ValueError("Se requiere query o query_text")

    def execute(self) -> None:
        """Ejecuta la busqueda."""
        response = self._searcher.search_from_query(self._query)
        self.results.emit(response)
