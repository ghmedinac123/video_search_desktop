"""
Búsqueda por lenguaje natural en la base de datos de detecciones.

Responsabilidad ÚNICA: recibir texto del usuario, generar embedding
con CLIP, consultar ChromaDB, y retornar resultados tipados.

Flujo: texto → CLIP embed_text() → ChromaDB search() → SearchResponse

Uso:
    from core.searcher import Searcher

    searcher = Searcher(model_manager=mm, database=db)
    response = searcher.search("mujer con camisa amarilla", n_results=30)
    for result in response.results:
        print(result.score, result.crop_path, result.description)
"""

from __future__ import annotations

import time

from core.database import Database
from core.logger import logger
from core.model_manager import ModelManager
from models.search import SearchQuery, SearchResponse, SearchResult


class Searcher:
    """
    Motor de búsqueda por lenguaje natural.

    Recibe dependencias por constructor (Dependency Inversion).
    NO sabe qué modelo CLIP se está usando — solo llama
    embedder.embed_text() via el ModelManager.
    """

    def __init__(
        self,
        model_manager: ModelManager,
        database: Database,
    ) -> None:
        self._mm = model_manager
        self._db = database

    def search(
        self,
        query_text: str,
        n_results: int = 30,
        min_score: float = 0.0,
        class_filter: str | None = None,
        video_filter: str | None = None,
    ) -> SearchResponse:
        """
        Busca detecciones similares al texto dado.

        Args:
            query_text: Texto en lenguaje natural (español o inglés).
            n_results: Cantidad máxima de resultados.
            min_score: Score mínimo para incluir (0.0 a 1.0).
            class_filter: Filtrar por clase YOLO (ej: "person").
            video_filter: Filtrar por video fuente (ej: "cam01.mp4").

        Returns:
            SearchResponse con resultados ordenados por score.
        """
        if self._mm.embedder is None or not self._mm.embedder.is_loaded():
            raise RuntimeError(
                "Embedder no está cargado. Carga un embedder primero."
            )

        t0 = time.time()

        # Generar embedding del texto de búsqueda
        query_embedding = self._mm.embedder.embed_text(query_text)

        # Consultar ChromaDB
        raw_results = self._db.search(
            query_embedding=query_embedding,
            n_results=n_results,
        )

        # Aplicar filtros opcionales
        filtered = self._apply_filters(
            results=raw_results,
            min_score=min_score,
            class_filter=class_filter,
            video_filter=video_filter,
        )

        elapsed_ms = int((time.time() - t0) * 1000)

        response = SearchResponse(
            query=query_text,
            results=filtered,
            total_results=len(filtered),
            elapsed_ms=elapsed_ms,
        )

        logger.info(
            f"Búsqueda: \"{query_text}\" → "
            f"{response.total_results} resultados en {elapsed_ms}ms"
        )

        return response

    def search_from_query(self, query: SearchQuery) -> SearchResponse:
        """
        Busca usando un objeto SearchQuery tipado.

        Args:
            query: SearchQuery con todos los parámetros.

        Returns:
            SearchResponse con resultados.
        """
        return self.search(
            query_text=query.text,
            n_results=query.n_results,
            min_score=query.min_score,
            class_filter=query.class_filter,
            video_filter=query.video_filter,
        )

    @staticmethod
    def _apply_filters(
        results: list[SearchResult],
        min_score: float = 0.0,
        class_filter: str | None = None,
        video_filter: str | None = None,
    ) -> list[SearchResult]:
        """Aplica filtros opcionales a los resultados."""
        filtered: list[SearchResult] = []

        for r in results:
            # Filtro por score mínimo
            if r.score < min_score:
                continue

            # Filtro por clase YOLO
            if class_filter and r.class_name != class_filter:
                continue

            # Filtro por video fuente
            if video_filter and video_filter not in r.video_source:
                continue

            filtered.append(r)

        return filtered