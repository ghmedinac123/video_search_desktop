"""
Wrapper sobre ChromaDB embebido — patrón Repository.

Responsabilidad ÚNICA: persistir y consultar embeddings + metadata.
NO sabe nada de YOLO, CLIP, o modelos. Solo datos.

ChromaDB corre embebido (PersistentClient) — sin Docker, sin servidor.
Los datos se guardan en ./data/chromadb/ como archivos SQLite.

Uso:
    from core.database import Database

    db = Database()
    db.store(crop_id="vid1__f001__d000", embedding=[0.1, ...], metadata={...})
    results = db.search(query_embedding=[0.2, ...], n_results=30)
    stats = db.get_stats()
    db.reset()
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import chromadb

from core.logger import logger
from models.database import CollectionStats
from models.search import SearchResult
from models.settings import get_settings


class Database:
    """
    Wrapper sobre ChromaDB embebido.

    Usa PersistentClient para que los datos sobrevivan entre
    reinicios de la aplicación. Upsert idempotente: si el crop_id
    ya existe, se actualiza en vez de duplicar.
    """

    def __init__(
        self,
        chromadb_dir: Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        """
        Crea o abre la base de datos embebida. Idempotente.

        Args:
            chromadb_dir: Carpeta donde se guardan los datos.
                          Default: lee de settings (.env).
            collection_name: Nombre de la colección.
                             Default: lee de settings (.env).
        """
        settings = get_settings()
        self._chromadb_dir = chromadb_dir or settings.chromadb_dir
        self._collection_name = collection_name or settings.collection_name

        # Crear directorio si no existe
        Path(self._chromadb_dir).mkdir(parents=True, exist_ok=True)

        # Conectar ChromaDB embebido
        self._client = chromadb.PersistentClient(
            path=str(self._chromadb_dir),
        )

        # Crear o abrir colección con distancia coseno
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"ChromaDB conectado — colección: '{self._collection_name}' "
            f"— registros: {self.count:,} — ruta: {self._chromadb_dir}"
        )

    def store(
        self,
        crop_id: str,
        embedding: list[float],
        metadata: dict[str, Any],
        description: str = "",
    ) -> None:
        """
        Almacena un crop en la colección. Upsert idempotente.

        Args:
            crop_id: Identificador único del crop.
            embedding: Vector de embedding generado por CLIP.
            metadata: Diccionario con class_name, confidence,
                      timestamp, video_source, paths, bbox, etc.
            description: Descripción en lenguaje natural del VLM.
        """
        self._collection.upsert(
            ids=[crop_id],
            embeddings=[embedding],
            metadatas=[metadata],
            documents=[description] if description else None,
        )

    def search(
        self,
        query_embedding: list[float],
        n_results: int = 30,
    ) -> list[SearchResult]:
        """
        Busca los crops más similares al embedding de consulta.

        Args:
            query_embedding: Vector generado por CLIP desde texto.
            n_results: Cantidad máxima de resultados.

        Returns:
            Lista de SearchResult ordenados por score descendente.
        """
        raw = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "distances", "documents"],
        )

        results: list[SearchResult] = []

        if not raw["ids"][0]:
            return results

        for i, crop_id in enumerate(raw["ids"][0]):
            meta = raw["metadatas"][0][i]
            distance = raw["distances"][0][i]
            score = round(1.0 - distance, 4)

            results.append(
                SearchResult(
                    crop_id=crop_id,
                    score=score,
                    class_name=meta.get("class_name", "unknown"),
                    confidence=meta.get("confidence", 0.0),
                    timestamp_seconds=meta.get("timestamp_seconds", 0.0),
                    video_source=meta.get("video_source", ""),
                    frame_path=meta.get("frame_path", ""),
                    crop_path=meta.get("crop_path", ""),
                    description=meta.get("description", ""),
                    bbox=meta.get("bbox", ""),
                )
            )

        return results

    def get_stats(self) -> CollectionStats:
        """Retorna estadísticas de la colección."""
        total = self.count

        # Obtener videos únicos y distribución de clases
        indexed_videos: list[str] = []
        class_distribution: dict[str, int] = {}

        if total > 0:
            # Peek para obtener muestra (ChromaDB limita a 10000)
            peek_limit = min(total, 10000)
            sample = self._collection.peek(limit=peek_limit)

            if sample["metadatas"]:
                videos_set: set[str] = set()
                for meta in sample["metadatas"]:
                    # Videos únicos
                    video = meta.get("video_source", "")
                    if video:
                        videos_set.add(video)

                    # Distribución de clases
                    cls = meta.get("class_name", "unknown")
                    class_distribution[cls] = class_distribution.get(cls, 0) + 1

                indexed_videos = sorted(videos_set)

        # Calcular uso de disco
        disk_usage = self._calculate_disk_usage()

        return CollectionStats(
            collection_name=self._collection_name,
            total_records=total,
            indexed_videos=indexed_videos,
            class_distribution=class_distribution,
            disk_usage_mb=disk_usage,
        )

    def get_indexed_videos(self) -> list[str]:
        """Retorna lista de videos que han sido indexados."""
        return self.get_stats().indexed_videos

    def reset(self) -> None:
        """
        Elimina y recrea la colección. Borra TODOS los datos.
        Idempotente: si ya fue eliminada, la recrea vacía.
        """
        logger.warning(f"Eliminando colección '{self._collection_name}'")
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            pass

        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Colección '{self._collection_name}' recreada vacía")

    @property
    def count(self) -> int:
        """Cantidad total de registros en la colección."""
        return self._collection.count()

    # ── Métodos privados ──

    def _calculate_disk_usage(self) -> float:
        """Calcula el uso de disco de la carpeta ChromaDB en MB."""
        try:
            total_bytes = sum(
                f.stat().st_size
                for f in Path(self._chromadb_dir).rglob("*")
                if f.is_file()
            )
            return round(total_bytes / (1024 * 1024), 2)
        except Exception:
            return 0.0