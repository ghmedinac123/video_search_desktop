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
from datetime import datetime

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
        class_filter: list[str] | None = None,
        camera_filter: list[str] | None = None,
        video_filter: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> SearchResponse:
        """
        Busca detecciones similares al texto dado, con filtros opcionales.

        Args:
            query_text: Texto en lenguaje natural (espanol o ingles).
            n_results: Cantidad maxima de resultados.
            min_score: Score minimo para incluir (0.0 a 1.0).
            class_filter: Lista de clases YOLO permitidas.
            camera_filter: Lista de camera_id permitidos.
            video_filter: Substring filtro por video fuente (post-query).
            date_from: Fecha desde (datetime).
            date_to: Fecha hasta (datetime).

        Returns:
            SearchResponse con resultados ordenados por score.
        """
        if self._mm.embedder is None or not self._mm.embedder.is_loaded():
            raise RuntimeError(
                "Embedder no esta cargado. Carga un embedder primero."
            )

        t0 = time.time()

        query_embedding = self._mm.embedder.embed_text(query_text)

        ts_from = date_from.timestamp() if date_from else None
        ts_to = date_to.timestamp() if date_to else None

        raw_results = self._db.search(
            query_embedding=query_embedding,
            n_results=n_results,
            class_filter=class_filter,
            camera_filter=camera_filter,
            date_from=ts_from,
            date_to=ts_to,
        )

        # Filtros que ChromaDB no maneja: min_score y video_filter substring
        filtered = self._apply_post_filters(
            results=raw_results,
            min_score=min_score,
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
            f"Busqueda: \"{query_text}\" → "
            f"{response.total_results} resultados en {elapsed_ms}ms"
        )

        return response

    def search_from_query(self, query: SearchQuery) -> SearchResponse:
        """Busca usando un objeto SearchQuery tipado."""
        return self.search(
            query_text=query.text,
            n_results=query.n_results,
            min_score=query.min_score,
            class_filter=query.class_filter,
            camera_filter=query.camera_filter,
            video_filter=query.video_filter,
            date_from=query.date_from,
            date_to=query.date_to,
        )

    @staticmethod
    def _apply_post_filters(
        results: list[SearchResult],
        min_score: float = 0.0,
        video_filter: str | None = None,
    ) -> list[SearchResult]:
        """Aplica filtros que ChromaDB no maneja directamente."""
        filtered: list[SearchResult] = []
        for r in results:
            if r.score < min_score:
                continue
            if video_filter and video_filter not in r.video_source:
                continue
            filtered.append(r)
        return filtered